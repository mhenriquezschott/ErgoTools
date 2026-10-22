"""Own native SQLite project storage and atomic cross-feature persistence.

Infrastructure repository implementing application storage ports for assessments,
ownership, organization, PLOT geometry/images and JROT schemes. It owns connection
lifetime and transaction boundaries; desktop policy belongs to the workspace.
Native format 19 stores one source-bound calculated result per assessment.
Integrated editing stages transactions privately until one complete project Save;
direct adapter clients retain their explicit durable-write behavior.
Original XML/SQLite decoding belongs exclusively to the removable tool.
This adapter never imports that tool or recalculates stored scientific outputs.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import zlib
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Concatenate

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.assessment_catalog import AssessmentEntry
from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.application.job_assignment import assign_worker
from ergotools.application.project_workspace import OwnedProject
from ergotools.application.session import DocumentKey
from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessment_transfer import TransferRequest, plan_transfer
from ergotools.domain.assessments.context import AssessmentContext, WorkplaceContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskValues
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_positions import PlotPositions
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation_scheme import RotationMode, RotationScheme
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.assessment_binding_store import (
    AssessmentBindingStore,
    create_binding_schema,
)
from ergotools.infrastructure.assessment_history_store import (
    AssessmentHistoryStore,
    create_history_schema,
)
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.infrastructure.draft_store import _idle
from ergotools.infrastructure.job_catalog_store import (
    JobCatalogStore,
    create_job_schema,
)
from ergotools.infrastructure.job_risk_store import JobRiskStore, create_risk_schema
from ergotools.infrastructure.lifft_store import LifftSqliteStore, StoreFormatError
from ergotools.infrastructure.plant_image_import import validate_plant_image
from ergotools.infrastructure.plant_layout_store import (
    PlantLayoutStore,
    create_layout_schema,
)
from ergotools.infrastructure.plot_position_store import (
    PlotPositionStore,
    create_position_schema,
)
from ergotools.infrastructure.project_preferences_store import (
    read_precision,
    write_precision,
)
from ergotools.infrastructure.project_snapshot import ProjectSnapshot
from ergotools.infrastructure.rotation_scheme_store import (
    RotationSchemeStore,
    create_rotation_schema,
)
from ergotools.infrastructure.saved_result_store import SavedResultStore
from ergotools.infrastructure.work_hierarchy_store import (
    WorkHierarchyStore,
    create_hierarchy_schema,
    encode_hierarchy,
)


def _project_edit[**P, T](
    operation: Callable[Concatenate[AssessmentProjectFile, P], T],
) -> Callable[Concatenate[AssessmentProjectFile, P], T]:
    """Report one successful outer repository mutation to its editing owner.

    Args:
        operation: Existing transactional adapter operation, preserving its signature.

    Returns:
        Wrapped operation; nested writes form one accepted history action. Failed
        writes emit no notification and retain the operation's rollback behavior.
    """

    @wraps(operation)
    def changed(self: AssessmentProjectFile, /, *args: P.args, **kwargs: P.kwargs) -> T:
        """Invoke an owned write and notify only after successful completion.

        Args:
            self: Borrowed native repository receiving the original operation.
            args: Original positional operation arguments.
            kwargs: Original keyword operation arguments.

        Returns:
            Unchanged operation result; no durable publication in editing mode.
        """
        outer = self._edit_depth == 0
        self._edit_depth += 1
        try:
            result = operation(self, *args, **kwargs)
        finally:
            self._edit_depth -= 1
        if outer and self._editing_changed is not None:
            self._editing_changed(operation.__name__)
        return result

    return changed


class AssessmentProjectFile:
    """Own one repository connection; close explicitly or use a context manager.

    Single-writer and owner-thread usage only. This is not legacy .ergprj support,
    or a project-switch coordinator. Snapshot publication supports Save As/backup.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Adopt a native connection and validate its supported metadata/catalogs.

        Args:
            connection: Caller-supplied SQLite connection; repository owns it after
                successful construction. Factory methods close it on failure.

        Returns:
            None. Stores are composed for the native format's supported capabilities.

        Raises:
            RuntimeError: The acquired connection is not idle/default-mode.
            StoreFormatError: Format, metadata or cross-feature identities are invalid.
                Earlier converted formats 12/13 require the separate migration utility.
            sqlite3.Error: Native metadata or catalogs cannot be queried.
            ValueError: A stored enum or domain value is invalid.

        Single-writer, owner-thread access is required. No original-format data is
        interpreted and no converter is invoked during construction.
        """
        self._editing_changed: Callable[[str], None] | None = None
        self._durable_connection: sqlite3.Connection | None = None
        self._edit_depth = 0
        connection.execute("PRAGMA foreign_keys=ON")
        self._connection = connection
        rows = connection.execute(
            "SELECT format, version, project_id, title, default_units "
            "FROM project_metadata"
        ).fetchall()
        if (
            len(rows) != 1
            or rows[0][0] != "ergotools.project"
            or rows[0][1] not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 19)
        ):
            raise StoreFormatError("Unsupported project metadata format.")
        _, version, project_id, title, units = rows[0]
        self._store: LifftSqliteStore | AssessmentSqliteStore
        self._store = (
            LifftSqliteStore(connection)
            if version == 1
            else AssessmentSqliteStore(connection)
        )
        self._format_version: int = version
        description = None
        created_at = None
        language = None
        if version >= 8:
            details = connection.execute(
                "SELECT description, created_at, language FROM project_details"
            ).fetchall()
            if len(details) != 1:
                raise StoreFormatError("Project details must contain one record.")
            description, timestamp, language_code = details[0]
            try:
                if timestamp is not None:
                    created_at = datetime.fromisoformat(timestamp)
                    if created_at.isoformat(timespec="seconds") != timestamp:
                        raise ValueError("Noncanonical project creation timestamp.")
                language = (
                    Language(language_code) if language_code is not None else None
                )
                self._metadata = ProjectMetadata(
                    project_id,
                    title,
                    MeasurementSystem(units),
                    description,
                    created_at,
                    language,
                )
            except (TypeError, ValueError) as error:
                raise StoreFormatError("Invalid project details.") from error
        else:
            self._metadata = ProjectMetadata(
                project_id, title, MeasurementSystem(units)
            )
        self._metadata = replace(self._metadata, precision=read_precision(connection))
        if connection.execute(
            "SELECT 1 FROM draft_documents WHERE project_id != ? LIMIT 1", (project_id,)
        ).fetchone():
            raise StoreFormatError("Project contains foreign document identities.")
        self._risk: JobRiskStore | None = None
        self._history = (
            AssessmentHistoryStore(connection, project_id) if version >= 6 else None
        )
        self._jobs = (
            JobCatalogStore(
                connection,
                project_id,
                validate_change=self._validate_job_change if version >= 6 else None,
            )
            if version >= 5
            else None
        )
        self._hierarchy = (
            WorkHierarchyStore(
                connection,
                project_id,
                validate_jobs=self._validate_hierarchy_change,
            )
            if version >= 4
            else None
        )
        if self._hierarchy is not None:
            self._hierarchy.read()
        self._bindings = (
            AssessmentBindingStore(
                connection,
                project_id,
                validate_owner=self._hierarchy.validate_owner
                if self._hierarchy
                else None,
            )
            if 3 <= version < 6
            else None
        )
        if self._history is not None:
            assert self._jobs is not None
            self._history.read(self._jobs.read())
        if version >= 7:
            self._risk = JobRiskStore(
                connection,
                project_id,
                self._risk_jobs,
                self._invalidate_job_optimization,
            )
            self._risk.read()
        if version >= 9:
            PlantLayoutStore(connection).validate_images()
        if version >= 10:
            assert self._hierarchy is not None and self._jobs is not None
            try:
                PlotPositionStore(connection, project_id).read().validate(
                    self._hierarchy.read(), self._jobs.read()
                )
            except (ValueError, KeyError) as error:
                raise StoreFormatError(
                    "Invalid saved PLOT geometry ownership."
                ) from error
        self._closed = False

        if version >= 11:
            try:
                self._validate_rotations()
            except (ValueError, KeyError) as error:
                raise StoreFormatError("Invalid saved rotation ownership.") from error

    def begin_editing(self, changed: Callable[[str], None]) -> None:
        """Move editor writes to private memory, retaining the durable connection.

        Args:
            changed: Application callback after each successful outer mutation.

        Returns:
            None; all existing repositories now borrow the private connection.

        Raises:
            RuntimeError: The repository is closed or already in editing mode.
            sqlite3.Error: Copying the validated native project fails.
        """
        if self._closed or self._durable_connection is not None:
            raise RuntimeError("Project editing is already active or closed.")
        durable = self._connection
        private = sqlite3.connect(":memory:")
        try:
            durable.backup(private)
            AssessmentProjectFile.__init__(self, private)
        except BaseException:
            private.close()
            raise
        self._durable_connection = durable
        self._editing_changed = changed

    def editing_checkpoint(self) -> bytes:
        """Capture all session data as compressed native bytes without file I/O.

        Args:
            None.

        Returns:
            Immutable adapter-private checkpoint including assets and exact outputs.

        Raises:
            RuntimeError: Private editing has not been started.
        """
        if self._durable_connection is None:
            raise RuntimeError("Private project editing is unavailable.")
        return zlib.compress(self._connection.serialize())

    def restore_editing_checkpoint(self, checkpoint: bytes) -> None:
        """Validate a same-project checkpoint before replacing private state.

        Args:
            checkpoint: Compressed native bytes produced by editing_checkpoint.

        Returns:
            None; durable data remains untouched. Existing borrowed repository
            capability objects remain usable after their stores are recomposed.

        Raises:
            ValueError: Checkpoint belongs to another project.
            RuntimeError: Private editing is unavailable.
            sqlite3.Error: Checkpoint validation or restoration fails.
            zlib.error: Checkpoint compression is invalid.
        """
        durable = self._durable_connection
        if durable is None:
            raise RuntimeError("Private project editing is unavailable.")
        candidate_connection = sqlite3.connect(":memory:")
        try:
            candidate_connection.deserialize(zlib.decompress(checkpoint))
            candidate = AssessmentProjectFile(candidate_connection)
            if candidate.metadata.project_id != self.metadata.project_id:
                raise ValueError("Checkpoint belongs to another project.")
            callback = self._editing_changed
            self._connection.deserialize(zlib.decompress(checkpoint))
            AssessmentProjectFile.__init__(self, self._connection)
            self._durable_connection = durable
            self._editing_changed = callback
        finally:
            candidate_connection.close()

    def editing_records(self) -> frozenset[tuple[str, str]]:
        """List existing business identities for precise removal confirmations.

        Args:
            None.

        Returns:
            Stable entity-kind and identity pairs; source/result/configuration rows
            are represented by their assessment rather than counted separately.
        """
        records: set[tuple[str, str]] = set()
        if self._hierarchy is not None:
            hierarchy = self.load_hierarchy()
            records.update(("worker", w.worker_id) for w in hierarchy.work.workers)
            records.update(("plant", p) for p in hierarchy.plants)
            records.update(("station", str(s)) for s in hierarchy.work.stations)
            records.update(("shift", str(s)) for s in hierarchy.work.shifts)
            records.update(("section", str(s)) for s in hierarchy.sections)
            records.update(("line", str(s)) for s in hierarchy.lines)
        if self._jobs is not None:
            jobs = self.load_jobs()
            records.update(("job", j.job_id) for j in jobs.jobs)
            records.update(
                ("assignment", str(a.assignment_id)) for a in jobs.assignments
            )
            records.update(("placement", str(p.placement_id)) for p in jobs.placements)
        records.update(
            ("assessment", a.document.document_id) for a in self.list_assessments()
        )
        if self._format_version >= 11:
            records.update(
                ("rotation", s.scheme_id) for s in self.load_rotation_schemes()
            )
        return frozenset(records)

    def snapshot_saved(self, location: str) -> AssessmentProjectFile:
        """Copy the durable baseline, excluding all accepted but unsaved editor data.

        Args:
            location: New exclusive native backup destination.

        Returns:
            Owned validated backup, preserving original session connection/history.
        """
        connection = sqlite3.connect(":memory:")
        try:
            source = self._durable_connection or self._connection
            source.backup(connection)
            with AssessmentProjectFile(connection) as saved:
                return saved.snapshot(location, None, None)
        finally:
            connection.close()

    def commit_editing(self) -> None:
        """Atomically publish the complete private database through SQLite backup.

        Args:
            None.

        Returns:
            None only after all project data is committed together. SQLite rolls
            back an unsuccessful destination backup, retaining private edits for retry.

        Raises:
            RuntimeError: Private editing is unavailable or a write is active.
            sqlite3.Error: Destination cannot be written; the previous file survives.
        """
        if self._durable_connection is None or self._connection.in_transaction:
            raise RuntimeError("Project is not ready for a complete Save.")
        self._connection.backup(self._durable_connection)

    @property
    def format_version(self) -> int:
        """Expose the opened project version without performing implicit migration.

        Args:
            None.

        Returns:
            Current native format version, without querying or upgrading storage.
        """
        return self._format_version

    @property
    def metadata(self) -> ProjectMetadata:
        """Expose immutable project defaults without changing saved document units.

        Args:
            None.

        Returns:
            Validated immutable project defaults; existing source units are unchanged.
        """
        return self._metadata

    @classmethod
    def create(cls, path: Path, metadata: ProjectMetadata) -> AssessmentProjectFile:
        """Create version two at a nonexistent destination; clean up on failure.

        Parent directories are caller-owned. Never overwrite, initialize or adopt an
        existing file. Creation is not crash-atomic publication of a project.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-two mixed-tool repository; caller must
            close it.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=2)

    @classmethod
    def create_empty(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create a current project without workers, organization or orphan assessments.

        Args:
            path: Nonexistent destination; existing files are never overwritten.
            metadata: Validated project identity and display defaults.

        Returns:
            Owned format-19 repository with empty functional catalogs. The caller closes
            it; assessments are created only after an explicit worker selection/Save.

        Raises:
            FileExistsError: Destination already exists.
            OSError: Exclusive creation fails; incomplete files are cleaned up.
            sqlite3.Error: Schema initialization fails and rolls back.
            ValueError: Metadata or ownership validation fails.
        """
        return cls._create(path, metadata, version=19)

    @classmethod
    def create_contextual(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create version three explicitly; never upgrade an existing project.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-three context-binding repository.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=3)

    @classmethod
    def create_catalogued(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create version four explicitly with an empty validated work hierarchy.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-four repository with an empty hierarchy.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=4)

    @classmethod
    def create_with_jobs(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create version five explicitly with empty catalogs and job relationships.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-five repository with empty job
            relationships.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=5)

    @classmethod
    def create_historical(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create version six explicitly with assignment-scoped ownership.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-six assignment-history repository.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=6)

    @classmethod
    def create_with_job_risks(
        cls, path: Path, metadata: ProjectMetadata
    ) -> AssessmentProjectFile:
        """Create version seven explicitly; never upgrade or overwrite old files.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            Owned initialized diagnostic format-seven full-project repository with empty
            current Job values.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return cls._create(path, metadata, version=7)

    @classmethod
    def create_initialized_historical(
        cls,
        path: Path,
        metadata: ProjectMetadata,
        hierarchy: WorkHierarchy,
        jobs: JobCatalog,
        entry: AssignmentAssessment,
        initial: AssessmentDraft,
    ) -> AssessmentProjectFile:
        """Create a historical project with explicit setup and its first source.

        Validate project, assignment and model ownership before filesystem writes.
        Recorded source units remain independent of project defaults. No workers, jobs,
        versions or current flags are inferred from display labels.

        Existing destinations are never adopted or removed. On initialization failure,
        close and remove only the newly created project. Setup uses separate adapter
        transactions; crash-atomic publication and concurrent readers during creation
        are outside this owner-thread factory contract. The caller owns the returned
        connection and must close it.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.
            hierarchy: Complete validated hierarchy with explicit
                worker/plant/section/line/station/shift identities.
            jobs: Complete validated same-project job/placement/assignment catalog; None
                in rotation validation retains saved jobs.
            entry: Explicit worker/tool ownership with an optional workplace assignment
                for the new source.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.

        Returns:
            Owned format-six repository with exact setup and first historically owned
            source persisted.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if hierarchy.work.project_id != metadata.project_id:
            raise ValueError("Setup hierarchy belongs to another project.")
        jobs.validate_hierarchy(hierarchy)
        AssessmentHistory(metadata.project_id, (entry,)).validate_jobs(jobs)
        if assessment_kind(initial) != entry.kind:
            raise ValueError("Initial source does not match the selected model.")
        encode_assessment(initial)
        project = cls.create_historical(path, metadata)
        try:
            project.save_hierarchy(hierarchy)
            project.save_jobs(jobs)
            project.create_historical_assessment(entry, initial)
            return project
        except BaseException:
            project.close()
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def _create(
        cls, path: Path, metadata: ProjectMetadata, *, version: int
    ) -> AssessmentProjectFile:
        """Initialize one explicitly selected native schema at an exclusive new path.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.
            version: Explicit diagnostic native schema version selected by the factory,
                not inferred from data or file extension.

        Returns:
            Owned initialized repository at the explicitly requested schema version;
            only this factory's partial file is removed on failure.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if version < 8 and any(
            value is not None
            for value in (metadata.description, metadata.created_at, metadata.language)
        ):
            raise ValueError("Project details require format version eight.")
        with path.open("xb"):
            pass
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(path)
            AssessmentSqliteStore.create(connection)
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "CREATE TABLE project_metadata (format TEXT NOT NULL, "
                    "version INTEGER NOT NULL, "
                    "project_id TEXT NOT NULL, title TEXT NOT NULL, "
                    "default_units TEXT NOT NULL)"
                )
                connection.execute(
                    "INSERT INTO project_metadata VALUES (?, ?, ?, ?, ?)",
                    (
                        "ergotools.project",
                        version,
                        metadata.project_id,
                        metadata.title,
                        metadata.default_units.value,
                    ),
                )
                write_precision(connection, metadata.precision)
                if version >= 8:
                    connection.execute(
                        "CREATE TABLE project_details (description TEXT, "
                        "created_at TEXT, language TEXT)"
                    )
                    connection.execute(
                        "INSERT INTO project_details VALUES (?, ?, ?)",
                        (
                            metadata.description,
                            metadata.created_at.isoformat(timespec="seconds")
                            if metadata.created_at is not None
                            else None,
                            metadata.language.value
                            if metadata.language is not None
                            else None,
                        ),
                    )
                if version >= 9:
                    create_layout_schema(connection)
                if 3 <= version < 6:
                    create_binding_schema(connection)
                if version >= 4:
                    create_hierarchy_schema(connection, metadata.project_id)
                if version >= 5:
                    create_job_schema(connection)
                if version >= 6:
                    create_history_schema(connection)
                if version >= 7:
                    create_risk_schema(connection, metadata.project_id)
                if version >= 10:
                    create_position_schema(connection)
                if version >= 11:
                    create_rotation_schema(connection)
            return cls(connection)
        except BaseException:
            if connection is not None:
                connection.close()
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def create_from_snapshot(
        cls, path: Path, snapshot: ProjectSnapshot
    ) -> AssessmentProjectFile:
        """Publish a complete new-format project without replacing any destination.

        Args:
            path: Nonexistent native destination on a hard-link-capable filesystem.
            snapshot: Fully typed catalogs, sources, maps, schemes and native results.

        Returns:
            Open format-19 repository owned by the caller; close it after use.

        Raises:
            ValueError: Input relationships, model payloads or image data are invalid.
            FileExistsError: Destination exists, including a concurrent publication.
            OSError: Temporary-file creation, exclusive publication or I/O fails.
            sqlite3.Error: Native initialization or reopening fails.

        Validate typed input before filesystem writes. Initialize only a hidden
        same-directory file; committed records must reopen and match the complete
        input before exclusive hard-link publication. An existing destination or
        unsupported hard-link filesystem raises without an overwriting fallback.
        The caller owns the returned connection. A valid published file remains
        if final reopening fails. Power-loss durability is not certified.
        """
        snapshot.validate()
        for item in snapshot.assessments:
            encode_assessment(item.source)
        for _, image in snapshot.images:
            validate_plant_image(image)
        if path.exists():
            raise FileExistsError(path)
        descriptor, name = tempfile.mkstemp(
            prefix=".ergotools-conversion-", suffix=".sqlite", dir=path.parent
        )
        os.close(descriptor)
        temporary = Path(name)
        try:
            # _create exclusively reserves its own file; remove only our empty
            # mkstemp reservation, never the user's destination.
            temporary.unlink()
            with cls._create(temporary, snapshot.metadata, version=19) as project:
                project._initialize_snapshot(snapshot)
            with cls.open(temporary) as candidate:
                candidate._verify_snapshot(snapshot)
            os.link(temporary, path)
            return cls.open(path)
        finally:
            temporary.unlink(missing_ok=True)

    def _initialize_snapshot(self, snapshot: ProjectSnapshot) -> None:
        """Initialize a reserved empty repository in one caller-independent transaction.

        Args:
            snapshot: Validated complete creation input; units and precision are kept.

        Returns:
            None after commit. Any failed write rolls back the complete initialization.

        Raises:
            StoreFormatError: Initialized native content fails integrity checking.
            RuntimeError: Required creation transaction/store capability is absent.
            ValueError: Creation-only storage finds conflicting records/provenance.
            sqlite3.Error: A write, reference constraint or integrity check fails.

        This private creation path preserves retired/approved historical references; it
        does not apply editing transitions or copy original-format database tables.
        """
        connection = self._connection
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE work_catalog SET payload=? WHERE singleton=1",
                (encode_hierarchy(snapshot.hierarchy),),
            )
            # Creation is not an edit: no approved-version/current flags may be
            # altered to satisfy the ordinary guarded management operations.
            JobCatalogStore(connection, self.metadata.project_id).write_in_transaction(
                snapshot.jobs, snapshot.hierarchy
            )
            self._risk_store().initialize_in_transaction(snapshot.risks)
            assert isinstance(self._store, AssessmentSqliteStore)
            for item in snapshot.assessments:
                self._store.insert_in_transaction(
                    DocumentKey(self.metadata.project_id, item.ownership.document_id),
                    item.source,
                )
            self._history_store().initialize_in_transaction(
                AssessmentHistory(
                    self.metadata.project_id,
                    tuple(item.ownership for item in snapshot.assessments),
                ),
                snapshot.jobs,
            )
            images = PlantLayoutStore(connection)
            for plant, image in snapshot.images:
                images.write_in_transaction(plant, image)
            images.validate_hierarchy(snapshot.hierarchy)
            PlotPositionStore(
                connection, self.metadata.project_id
            ).write_in_transaction(snapshot.positions)
            rotations = RotationSchemeStore(connection, self.metadata.project_id)
            for scheme in snapshot.rotations:
                rotations.write_in_transaction(scheme)
            if snapshot.saved_results:
                SavedResultStore.create_schema(connection)
                for identity, result in snapshot.saved_results:
                    SavedResultStore(connection).write(
                        DocumentKey(self.metadata.project_id, identity),
                        SavedResultStore.encode(result),
                    )
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise StoreFormatError("Initialized project failed integrity checking.")

    def _verify_snapshot(self, snapshot: ProjectSnapshot) -> None:
        """Compare reopened native content with the exact creation input.

        Args:
            snapshot: Expected catalogs, sources, results and images.

        Returns:
            None when every persisted value matches, including image/result precision.

        Raises:
            ValueError: A reopened source, catalog or image violates domain validation.
            RuntimeError: Repository/connection is closed or not idle.
            StoreFormatError: Reopened content differs from the supplied snapshot.
            sqlite3.Error: A native record cannot be read.

        Reads only; exclusive publication occurs after this verification succeeds.
        """
        if (
            self.metadata != snapshot.metadata
            or self.load_hierarchy() != snapshot.hierarchy
            or self.load_jobs() != snapshot.jobs
            or self.load_job_risk() != snapshot.risks
            or self.load_history().entries
            != tuple(item.ownership for item in snapshot.assessments)
            or self.load_plot_positions() != snapshot.positions
            or {scheme.scheme_id: scheme for scheme in self.load_rotation_schemes()}
            != {scheme.scheme_id: scheme for scheme in snapshot.rotations}
        ):
            raise StoreFormatError("Initialized project catalogs do not match input.")
        for item in snapshot.assessments:
            if (
                self.load(
                    DocumentKey(self.metadata.project_id, item.ownership.document_id)
                )
                != item.source
            ):
                raise StoreFormatError("Initialized assessment does not match input.")
        for identity, result in snapshot.saved_results:
            if (
                self.load_saved_result(DocumentKey(self.metadata.project_id, identity))
                != result
            ):
                raise StoreFormatError("Initialized saved result does not match input.")
        expected_images = dict(snapshot.images)
        for plant in snapshot.hierarchy.plants:
            if self.load_plant_image(plant) != expected_images.get(plant):
                raise StoreFormatError("Initialized plant image does not match input.")

    def load_saved_result(
        self, document: DocumentKey
    ) -> HistoricalAssessmentResult | None:
        """Read this assessment version's sole calculation without recomputing.

        Args:
            document: Existing project-scoped assessment version identity.

        Returns:
            Source-bound calculation or None when not calculated/invalidated.

        Raises:
            ValueError: The identity belongs to another project.
            RuntimeError: The repository is closed.
            StoreFormatError: The native result envelope is malformed.
            sqlite3.Error: Native result storage cannot be queried.
        """
        self._check(document)
        exists = self._connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='saved_assessment_results'"
        ).fetchone()
        return SavedResultStore(self._connection).read(document) if exists else None

    @_project_edit
    def save_result(
        self, document: DocumentKey, result: HistoricalAssessmentResult
    ) -> None:
        """Replace this version's source and sole calculated output atomically.

        Args:
            document: Existing project-scoped assessment identity.
            result: Detached fresh result with source units and calculation status.

        Returns:
            None after atomic commit. No previous/imported result is kept separately.

        Raises:
            ValueError: The identity is foreign or result lacks fresh provenance.
            StoreFormatError: This native format cannot store mixed-tool results.
            RuntimeError: The repository is closed or a transaction is already active.
            sqlite3.Error: A source/result write fails; both writes roll back.
        """
        self._check(document)
        if result.calculation_status is None:
            raise ValueError("Fresh saved result requires calculation provenance.")
        if not isinstance(self._store, AssessmentSqliteStore):
            raise StoreFormatError("Saved results require mixed assessment storage.")
        _idle(self._connection)
        payload = SavedResultStore.encode(result)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            SavedResultStore.create_schema(self._connection)
            self._store.save_in_transaction(document, result.source)
            SavedResultStore(self._connection).write(document, payload)

    @classmethod
    def create_with_document(
        cls,
        path: Path,
        metadata: ProjectMetadata,
        document_id: str,
        initial: AssessmentDraft,
        *,
        format_version: int = 2,
    ) -> AssessmentProjectFile:
        """Initialize a project and first draft; remove incomplete files on failure.

        Validate the source before creating the file. Existing destinations are never
        removed. Successful return owns a fully persisted first document;
        interruption/power-loss recovery remains outside this creation contract.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.
            document_id: Exact stable source identity for first-document creation.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.
            format_version: Explicit supported initial diagnostic schema version,
                integer 2 through 11.

        Returns:
            Owned repository with exact first source persisted at the explicit
            diagnostic version.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        key = DocumentKey(metadata.project_id, document_id)
        encode_assessment(initial)
        if type(format_version) is not int or format_version not in (
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            19,
        ):
            raise ValueError("Unsupported initial project format.")
        project = cls._create(path, metadata, version=format_version)
        try:
            project.save(key, initial)
            return project
        except BaseException:
            project.close()
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def open(cls, path: Path) -> AssessmentProjectFile:
        """Open an existing format for read/write, never create missing files.

        Args:
            path: Nonexistent destination with an existing parent for creation, or
                existing native project for open; no overwrite fallback.

        Returns:
            Owned validated read/write repository for an existing file; candidate
            connection closes on validation failure.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        uri = path.absolute().as_uri() + "?mode=rw"
        connection = sqlite3.connect(uri, uri=True)
        try:
            return cls(connection)
        except BaseException:
            connection.close()
            raise

    def _check(self, document: DocumentKey) -> None:
        """Reject closed repositories and foreign document identities before access.

        Args:
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.

        Returns:
            None when the repository is open and the requested identity belongs to its
            project.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if document.project_id != self.metadata.project_id:
            raise ValueError("Document belongs to another project.")

    def load(self, document: DocumentKey) -> AssessmentDraft:
        """Load only this project's document through the validated draft adapter.

        Args:
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.

        Returns:
            Complete validated saved source with its exact row order, units and ST
            convention.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
            KeyError: The requested exact saved source, scheme or Job identity is
                absent.
        """
        self._check(document)
        return self._store.load(document)

    @_project_edit
    def save(self, document: DocumentKey, state: AssessmentDraft) -> None:
        """Save inputs and invalidate a calculation when those inputs change.

        Args:
            document: Existing project-scoped assessment version identity.
            state: Replacement source with unchanged tool identity and its own units.

        Returns:
            None after commit. Unchanged inputs keep their sole saved result;
            changed inputs remove it in the same transaction until Calculate/Save.

        Raises:
            ValueError: The identity is foreign or source is invalid.
            StoreFormatError: Tool identity changes or native storage is invalid.
            RuntimeError: Repository is closed or a transaction is already active.
            sqlite3.Error: Source/result invalidation fails; both roll back.
        """
        self._check(document)
        if isinstance(self._store, LifftSqliteStore):
            if not isinstance(state, LifftDraft):
                raise StoreFormatError(
                    "Version-one projects only support LiFFT drafts."
                )
            self._store.save(document, state)
        else:
            _idle(self._connection)
            assert isinstance(self._store, AssessmentSqliteStore)
            with self._connection:
                self._connection.execute("BEGIN IMMEDIATE")
                row = self._connection.execute(
                    "SELECT payload FROM draft_documents "
                    "WHERE project_id=? AND document_id=?",
                    (document.project_id, document.document_id),
                ).fetchone()
                existing = None if row is None else decode_assessment(row[0])
                self._store.save_in_transaction(document, state)
                if (
                    existing != state
                    and self._connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='saved_assessment_results'"
                    ).fetchone()
                ):
                    self._connection.execute(
                        "DELETE FROM saved_assessment_results "
                        "WHERE project_id=? AND document_id=?",
                        (document.project_id, document.document_id),
                    )

    def snapshot(
        self,
        location: str,
        document: DocumentKey | None,
        state: AssessmentDraft | None,
    ) -> AssessmentProjectFile:
        """Publish an exclusive complete snapshot retaining all saved metadata.

        Args:
            location: Nonexistent native copy destination on a hard-link-capable
                filesystem; parent must already exist.
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.
            state: Immutable replacement source retaining model identity and recorded
                units; None in snapshot copies only saved data.

        Returns:
            New owned exclusive complete project copy, optionally containing the
            supplied source edits.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return self._snapshot(location, document, state)

    def snapshot_with_metadata(
        self,
        location: str,
        document: DocumentKey | None,
        state: AssessmentDraft | None,
        metadata: ProjectMetadata,
    ) -> AssessmentProjectFile:
        """Edit details only in a full-project copy; preserve the original identity.

        Formats seven/eight have all required full-project schemas. Earlier partial
        formats retain their ordinary snapshot capability without an implicit
        application-data migration.

        Args:
            location: Nonexistent native copy destination on a hard-link-capable
                filesystem; parent must already exist.
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.
            state: Immutable replacement source retaining model identity and recorded
                units; None in snapshot copies only saved data.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            New owned complete copy with requested display metadata and unchanged stable
            project identity.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._format_version < 7:
            raise StoreFormatError("Copy metadata requires a full-project format.")
        if metadata.project_id != self.metadata.project_id:
            raise ValueError("Copy metadata cannot change project identity.")
        return self._snapshot(location, document, state, metadata=metadata)

    def _update_snapshot_metadata(
        self, connection: sqlite3.Connection, metadata: ProjectMetadata
    ) -> None:
        """Edit display details only inside the temporary snapshot database.

        Args:
            connection: Borrowed or newly acquired owner-thread SQLite connection as
                specified; factory-returned project owns close lifetime.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.

        Returns:
            None after display details/defaults and required details schema commit only
            in the temporary copied database.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            if self._format_version == 7:
                connection.execute(
                    "CREATE TABLE project_details (description TEXT, "
                    "created_at TEXT, language TEXT)"
                )
            else:
                connection.execute("DELETE FROM project_details")
            connection.execute(
                "INSERT INTO project_details VALUES (?, ?, ?)",
                (
                    metadata.description,
                    metadata.created_at.isoformat(timespec="seconds")
                    if metadata.created_at is not None
                    else None,
                    metadata.language.value if metadata.language is not None else None,
                ),
            )
            write_precision(connection, metadata.precision)
            connection.execute(
                "UPDATE project_metadata SET version = ?, title = ?, default_units = ?",
                (
                    max(8, self._format_version),
                    metadata.title,
                    metadata.default_units.value,
                ),
            )

    @_project_edit
    def update_display_settings(self, metadata: ProjectMetadata) -> None:
        """Commit project units and precision without altering any assessment.

        Args:
            metadata: Same project identity/title/details with requested display
                defaults.

        Returns:
            None; publish in-memory metadata only after the transaction commits.

        Raises:
            ValueError: Non-display metadata differs from the owned project.
            RuntimeError: The connection already has a transaction.
            sqlite3.Error: The preference write fails and rolls back.
        """
        if (
            replace(
                metadata,
                default_units=self.metadata.default_units,
                precision=self.metadata.precision,
            )
            != self.metadata
        ):
            raise ValueError("Only project display settings may change here.")
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            write_precision(self._connection, metadata.precision)
            self._connection.execute(
                "UPDATE project_metadata SET default_units = ?",
                (metadata.default_units.value,),
            )
        self._metadata = metadata

    def snapshot_prepared(
        self,
        location: str,
        prepare: Callable[[OwnedProject[AssessmentDraft]], None],
        metadata: ProjectMetadata | None = None,
    ) -> AssessmentProjectFile:
        """Stage retained tool edits before publishing a complete project copy.

        Args:
            location: Nonexistent same-filesystem destination; never overwritten.
            prepare: Synchronous application callback writing only to the temporary
                repository. Any failure prevents publication and removes staging data.
            metadata: Optional validated same-identity project display details.

        Returns:
            Newly owned complete native copy. Only final reopen failure may leave a
            fully published destination without an acquired handle.

        Raises:
            OSError: Staging or exclusive publication fails.
            ValueError: Source edits or metadata violate native identity contracts.
            sqlite3.Error: Backup, preparation or validation fails before publication.
        """
        return self._snapshot(location, None, None, metadata=metadata, prepare=prepare)

    def _snapshot(
        self,
        location: str,
        document: DocumentKey | None,
        state: AssessmentDraft | None,
        *,
        metadata: ProjectMetadata | None = None,
        prepare: Callable[[OwnedProject[AssessmentDraft]], None] | None = None,
    ) -> AssessmentProjectFile:
        """Publish a complete SQLite snapshot without overwriting any destination.

        SQLite backup includes committed WAL content, unlike raw file copying. Optional
        source edits are written only into the temporary copy. Validate it and close its
        connection before exclusive same-directory publication. A filesystem without
        hard-link support raises instead of using a partial or overwriting fallback.
        Crash recovery/power-loss durability is not certified. A valid published copy is
        retained if final reopen fails.

        Args:
            location: Nonexistent native copy destination on a hard-link-capable
                filesystem; parent must already exist.
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.
            state: Immutable replacement source retaining model identity and recorded
                units; None in snapshot copies only saved data.
            metadata: Validated immutable project identity, title and unit defaults;
                copied display details never change project identity.
            prepare: Optional synchronous operation applied only to the private copy
                before validation and exclusive publication.

        Returns:
            New owned validated copy after exclusive publication; a complete file
            remains if final reopening fails.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            FileExistsError: Destination already exists, including a race at exclusive
                publication.
            OSError: Exclusive creation, temporary storage, publication or owned-file
                cleanup fails.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        _idle(self._connection)
        if (document is None) != (state is None):
            raise ValueError(
                "Snapshot source identity and state must be supplied together."
            )
        if document is not None:
            self._check(document)
            assert state is not None
            encode_assessment(state)
        destination = Path(location)
        if destination.exists():
            raise FileExistsError(destination)
        descriptor, name = tempfile.mkstemp(
            prefix=".ergotools-snapshot-", suffix=".sqlite", dir=destination.parent
        )
        os.close(descriptor)
        temporary = Path(name)
        try:
            connection = sqlite3.connect(temporary)
            try:
                self._connection.backup(connection)
                if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise StoreFormatError(
                        "Project snapshot failed integrity checking."
                    )
                if metadata is not None:
                    self._update_snapshot_metadata(connection, metadata)
                copy = AssessmentProjectFile(connection)
                if document is not None:
                    assert state is not None
                    copy.save(document, state)
                if prepare is not None:
                    prepare(copy)
                # Validate every persisted source, not just the selected assessment.
                for entry in copy.list_assessments():
                    copy.load(entry.document)
            finally:
                connection.close()
            os.link(temporary, destination)
        finally:
            temporary.unlink()
        return AssessmentProjectFile.open(destination)

    def list_assessments(self) -> tuple[AssessmentEntry, ...]:
        """List persisted identities/models/counts without touching the active draft.

        Args:
            None.

        Returns:
            Validated saved source identities/models/row counts in binary document-ID
            order; no editor state is read.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        return tuple(
            AssessmentEntry(key, assessment_kind(source), len(source.tasks))
            for key, source in self._store.list_documents(self.metadata.project_id)
        )

    @_project_edit
    def insert_assessment(
        self, document: DocumentKey, initial: AssessmentDraft
    ) -> None:
        """Create only a new ID, with explicit project-version compatibility.

        Args:
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.

        Returns:
            None after exclusive source insertion; existing IDs remain protected.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._check(document)
        if isinstance(self._store, LifftSqliteStore):
            if not isinstance(initial, LifftDraft):
                raise StoreFormatError(
                    "Version-one projects only support LiFFT drafts."
                )
            self._store.insert(document, initial)
        else:
            self._store.insert(document, initial)

    def _binding_store(self) -> AssessmentBindingStore:
        """Require the diagnostic context-binding storage capability.

        Args:
            None.

        Returns:
            Borrowed context-binding store only for supported pre-history diagnostic
            formats.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._format_version >= 6:
            raise StoreFormatError("Historical projects require assignment ownership.")
        if self._bindings is None:
            raise StoreFormatError(
                "Assessment ownership requires project version three."
            )
        return self._bindings

    @_project_edit
    def bind_assessment(self, binding: AssessmentBinding) -> None:
        """Bind an existing persisted draft without changing its source or history.

        Args:
            binding: Exact document and project/worker/workplace/model ownership to
                bind/create atomically.

        Returns:
            None after an existing source receives immutable context ownership
            atomically.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._check(binding.document)
        self._binding_store().bind(binding)

    @_project_edit
    def create_bound_assessment(
        self, binding: AssessmentBinding, initial: AssessmentDraft
    ) -> None:
        """Insert a new source and ownership together; any failure rolls both back.

        Args:
            binding: Exact document and project/worker/workplace/model ownership to
                bind/create atomically.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.

        Returns:
            None after exclusive source and ownership insertion commit together; any
            failure rolls back both.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._check(binding.document)
        bindings = self._binding_store()
        if assessment_kind(initial) != binding.context.kind:
            raise ValueError("Initial assessment model does not match its context.")
        encode_assessment(initial)
        _idle(self._connection)
        assert isinstance(self._store, AssessmentSqliteStore)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            self._store.insert_in_transaction(binding.document, initial)
            bindings.bind_in_transaction(binding)

    def assessment_binding(self, document: DocumentKey) -> AssessmentBinding | None:
        """Read ownership; missing raises KeyError, unbound returns None.

        Args:
            document: Exact project/document identity; snapshot accepts None only
                together with state=None for saved-data-only copying.

        Returns:
            Validated context binding, or None for an existing unbound source; an absent
            source raises KeyError.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
            KeyError: The requested exact saved source, scheme or Job identity is
                absent.
        """
        self._check(document)
        store = self._binding_store()
        self.load(document)
        return store.get(document)

    def find_assessment(self, context: AssessmentContext) -> DocumentKey | None:
        """Resolve exact project ownership without activating a session.

        Args:
            context: Full exact project/worker/workplace/model identity to resolve;
                display captions never substitute for identity.

        Returns:
            Exact saved source key for full context ownership, or None when unoccupied.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        store = self._binding_store()
        if context.worker.project_id != self.metadata.project_id:
            raise ValueError("Assessment belongs to another project.")
        return store.find(context)

    def _hierarchy_store(self) -> WorkHierarchyStore:
        """Require the open hierarchy storage capability.

        Args:
            None.

        Returns:
            Borrowed hierarchy store for this open format-four-or-later repository.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._hierarchy is None:
            raise StoreFormatError("Catalog persistence requires project version four.")
        return self._hierarchy

    def _validate_hierarchy_change(self, hierarchy: WorkHierarchy) -> None:
        """Protect all saved feature references before hierarchy replacement.

        Args:
            hierarchy: Complete validated hierarchy with explicit
                worker/plant/section/line/station/shift identities.

        Returns:
            None when saved jobs, maps, geometry and rotations remain valid under the
            proposed hierarchy.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._jobs is not None:
            self._jobs.validate_hierarchy(hierarchy)
        if self._format_version >= 9:
            PlantLayoutStore(self._connection).validate_hierarchy(hierarchy)
        if self._format_version >= 10:
            PlotPositionStore(
                self._connection, self.metadata.project_id
            ).read().validate_hierarchy(hierarchy)

        if self._format_version >= 11:
            for scheme in RotationSchemeStore(
                self._connection, self.metadata.project_id
            ).read():
                scheme.validate_hierarchy(hierarchy)

    def load_plant_image(self, plant: str) -> PlantLayoutImage | None:
        """Load an exact saved plant; older projects have no embedded image records.

        Args:
            plant: Exact saved plant identity whose encoded map is read/replaced.

        Returns:
            Validated saved encoded map, or None when this saved plant has no embedded
            image capability/record.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        hierarchy = self.load_hierarchy()
        if plant not in hierarchy.plants:
            raise ValueError("Plant is not in the saved hierarchy.")
        if self._format_version < 9:
            return None
        return PlantLayoutStore(self._connection).read(plant)

    def read(self, plant: str) -> bytes | None:
        """Implement the read-only PLOT image port on the owned project connection.

        Args:
            plant: Exact saved plant identity whose encoded map is read/replaced.

        Returns:
            Original saved encoded image bytes, or None when this exact plant has no
            map.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        image = self.load_plant_image(plant)
        return image.data if image is not None else None

    @_project_edit
    def save_plant_image(self, plant: str, image: PlantLayoutImage) -> None:
        """Explicitly save a validated map, upgrading full projects atomically to nine.

        Opening/previewing does not migrate. Version seven gains absent details; version
        eight retains its details. Partial formats are not implicitly upgraded. On
        failure schema, old map and in-memory version are preserved.

        Args:
            plant: Exact saved plant identity whose encoded map is read/replaced.
            image: Validated encoded plant map with original pixel dimensions and
                unchanged bytes.

        Returns:
            None after map and any required full-project schema/version upgrade commit
            atomically.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._format_version < 7:
            raise StoreFormatError("Plant layout saving requires a full project.")
        validate_plant_image(image)
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            if plant not in self._hierarchy_store().read().plants:
                raise ValueError("Plant is not in the saved hierarchy.")
            if self._format_version == 7:
                self._connection.execute(
                    "CREATE TABLE project_details (description TEXT, "
                    "created_at TEXT, language TEXT)"
                )
                self._connection.execute(
                    "INSERT INTO project_details VALUES (NULL, NULL, NULL)"
                )
            if self._format_version < 9:
                create_layout_schema(self._connection)
            PlantLayoutStore(self._connection).write_in_transaction(plant, image)
            version = max(9, self._format_version)
            self._connection.execute(
                "UPDATE project_metadata SET version = ?", (version,)
            )
        self._format_version = version

    def load_plot_positions(self) -> PlotPositions:
        """Read saved geometry; older formats return empty without migration.

        Args:
            None.

        Returns:
            Validated saved original-image geometry, or empty geometry in a supported
            older full format without positions.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        hierarchy = self.load_hierarchy()
        jobs = self.load_jobs()
        positions = (
            PlotPositionStore(self._connection, self.metadata.project_id).read()
            if self._format_version >= 10
            else PlotPositions(self.metadata.project_id)
        )
        positions.validate(hierarchy, jobs)
        return positions

    @_project_edit
    def save_plot_positions(self, positions: PlotPositions) -> None:
        """Explicitly save geometry, upgrading full formats to ten atomically.

        Existing maps/details and assessment sources are preserved. Reading never
        upgrades; partial formats are rejected. Failure rolls back schema, prior
        geometry and version before the in-memory version can change.

        Args:
            positions: Complete same-project station/assignment geometry in
                original-image pixels, retaining marker style and flags.

        Returns:
            None after geometry and any required full-project schema/version upgrade
            commit atomically.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._format_version < 7:
            raise StoreFormatError("PLOT position saving requires a full project.")
        if not isinstance(positions, PlotPositions):
            raise ValueError("PLOT positions require a typed snapshot.")
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            positions.validate(self._hierarchy_store().read(), self._job_store().read())
            if self._format_version == 7:
                self._connection.execute(
                    "CREATE TABLE project_details (description TEXT, "
                    "created_at TEXT, language TEXT)"
                )
                self._connection.execute(
                    "INSERT INTO project_details VALUES (NULL, NULL, NULL)"
                )
            if self._format_version < 9:
                create_layout_schema(self._connection)
            if self._format_version < 10:
                create_position_schema(self._connection)
            PlotPositionStore(
                self._connection, self.metadata.project_id
            ).write_in_transaction(positions)
            version = max(10, self._format_version)
            self._connection.execute(
                "UPDATE project_metadata SET version = ?", (version,)
            )
        self._format_version = version

    def load_hierarchy(self) -> WorkHierarchy:
        """Load exact ordered catalog data; never infer missing ancestors.

        Args:
            None.

        Returns:
            Validated exact ordered hierarchy with protected saved-reference checks.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        store = self._hierarchy_store()
        _idle(self._connection)
        return store.read()

    @_project_edit
    def save_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Atomically replace catalog data without orphaning bound assessments.

        Args:
            hierarchy: Complete validated hierarchy with explicit
                worker/plant/section/line/station/shift identities.

        Returns:
            None after atomic hierarchy replacement preserving every protected
            reference.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._hierarchy_store().save(hierarchy)

    @_project_edit
    def replace_hierarchy(
        self, expected: WorkHierarchy, replacement: WorkHierarchy
    ) -> None:
        """Replace only the expected saved catalog, checked under the write lock.

        Args:
            expected: Exact saved hierarchy/jobs/history/risk snapshot to compare under
                the write lock.
            replacement: Complete proposed immutable replacement preserving same-project
                and protected reference identities.

        Returns:
            None after expected-value guarded atomic hierarchy replacement.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._hierarchy_store().save(replacement, expected=expected)

    @_project_edit
    def replace_worker_catalogs(
        self,
        expected_hierarchy: WorkHierarchy,
        replacement_hierarchy: WorkHierarchy,
        expected_jobs: JobCatalog,
        replacement_jobs: JobCatalog,
    ) -> None:
        """Atomically save worker metadata and assignment classification changes.

        Args:
            expected_hierarchy: Exact saved hierarchy shown when the worker form was
                opened.
            replacement_hierarchy: Complete proposed worker/demographic hierarchy to
                commit with classifications.
            expected_jobs: Exact saved job/placement/assignment catalog shown by the
                form.
            replacement_jobs: Complete proposed worker classification catalog to commit
                with hierarchy metadata.

        Returns:
            None after hierarchy and classifications commit together and read back
            exactly; failures roll back both.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        hierarchy = self._hierarchy_store()
        jobs = self._job_store()
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            if hierarchy.read() != expected_hierarchy:
                raise ValueError("Worker catalog changed since the expected snapshot.")
            if self._format_version >= 10:
                PlotPositionStore(
                    self._connection, self.metadata.project_id
                ).read().validate_hierarchy(replacement_hierarchy)
            if self._format_version >= 11:
                self._validate_rotations(
                    hierarchy=replacement_hierarchy, jobs=replacement_jobs
                )
            if self._history is not None:
                workers = {w.worker_id for w in replacement_hierarchy.work.workers}
                if any(
                    e.worker_id not in workers
                    for e in self._history.read(jobs.read()).entries
                ):
                    raise ValueError("Assessment references a missing worker.")
            jobs.write_in_transaction(
                replacement_jobs, replacement_hierarchy, expected=expected_jobs
            )
            self._connection.execute(
                "UPDATE work_catalog SET payload=? WHERE singleton=1",
                (encode_hierarchy(replacement_hierarchy),),
            )
            if (
                hierarchy.read() != replacement_hierarchy
                or jobs.read() != replacement_jobs
            ):
                raise ValueError("Saved worker records do not match the form.")

    def _job_store(self) -> JobCatalogStore:
        """Require the open job/assignment storage capability.

        Args:
            None.

        Returns:
            Borrowed jobs store for this open format-five-or-later repository.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._jobs is None:
            raise StoreFormatError("Job persistence requires project version five.")
        return self._jobs

    def load_jobs(self) -> JobCatalog:
        """Load validated job relationships with current hierarchy membership.

        Args:
            None.

        Returns:
            Validated job/assignment catalog and hierarchy membership from one read
            transaction.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        store = self._job_store()
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN")
            self._hierarchy_store().read()
            return store.read()

    @_project_edit
    def save_jobs(self, catalog: JobCatalog) -> None:
        """Replace job relationship snapshots atomically; not a reassignment command.

        Args:
            catalog: Complete validated same-project job/placement/assignment catalog to
                persist in explicit order.

        Returns:
            None after atomic ordered job/placement/assignment snapshot replacement.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._job_store().save(catalog, self._hierarchy_store().read)

    @_project_edit
    def replace_jobs(self, expected: JobCatalog, replacement: JobCatalog) -> None:
        """Replace only the expected saved jobs, checked under the write lock.

        Args:
            expected: Exact saved hierarchy/jobs/history/risk snapshot to compare under
                the write lock.
            replacement: Complete proposed immutable replacement preserving same-project
                and protected reference identities.

        Returns:
            None after expected-value guarded atomic job snapshot replacement.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._job_store().save(
            replacement, self._hierarchy_store().read, expected=expected
        )

    @property
    def supports_assignment_history(self) -> bool:
        """Expose historical format capability without reading database tables.

        Args:
            None.

        Returns:
            True only while open and supporting assignment history; no I/O.
        """
        return not self._closed and self._history is not None

    def _history_store(self) -> AssessmentHistoryStore:
        """Require the open assignment-history storage capability.

        Args:
            None.

        Returns:
            Borrowed assignment-history store for this open format-six-or-later
            repository.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._history is None:
            raise StoreFormatError("Assessment history requires project version six.")
        return self._history

    def load_history(self) -> AssessmentHistory:
        """Read validated ownership and source links from one database snapshot.

        Args:
            None.

        Returns:
            Validated assignment ownership and source-model links from one saved read
            snapshot.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        history = self._history_store()
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN")
            self._hierarchy_store().read()
            return history.read(self._job_store().read())

    @_project_edit
    def delete_historical_assessment(
        self, expected: AssessmentHistory, document_id: str
    ) -> AssessmentHistory:
        """Atomically remove one saved source and owner; never delete other versions.

        The write lock covers ownership comparison, source deletion and position
        compaction. Adapter failures roll back all changes. No version promotion,
        worker/assignment deletion or legacy-format conversion occurs.

        Args:
            expected: Exact saved hierarchy/jobs/history/risk snapshot to compare under
                the write lock.
            document_id: Exact stable source identity for first-document creation.

        Returns:
            Committed history after exact source/ownership removal and
            insertion-position compaction; other versions remain unchanged.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
            KeyError: The requested exact saved source, scheme or Job identity is
                absent.
        """
        history = self._history_store()
        if expected.project_id != self.metadata.project_id:
            raise ValueError("Assessment history belongs to another project.")
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            self._hierarchy_store().read()
            return history.delete(expected, document_id, self._job_store().read())

    def validate_historical_creation(
        self, entry: AssignmentAssessment, initial: AssessmentDraft
    ) -> None:
        """Preflight ownership/source conflicts without writing or changing history.

        Args:
            entry: Explicit worker/tool ownership with an optional workplace assignment
                for the new source.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.

        Returns:
            None after read-only source/model/worker/optional-assignment/ID
            preflight.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        history = self._history_store()
        if assessment_kind(initial) != entry.kind:
            raise ValueError("Historical ownership model does not match source.")
        encode_assessment(initial)
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN")
            self._hierarchy_store().read()
            jobs = self._job_store().read()
            current = history.read(jobs)
            AssessmentHistory(
                self.metadata.project_id, (*current.entries, entry)
            ).validate_jobs(jobs)
            if self._connection.execute(
                "SELECT 1 FROM draft_documents WHERE project_id=? AND document_id=?",
                (self.metadata.project_id, entry.document_id),
            ).fetchone():
                raise ValueError("Assessment identity already exists.")

    @_project_edit
    def create_historical_assessment(
        self,
        entry: AssignmentAssessment,
        initial: AssessmentDraft,
        *,
        result: HistoricalAssessmentResult | None = None,
    ) -> None:
        """Commit a new source and historical owner together, or neither.

        Args:
            entry: Explicit worker/tool ownership with an optional workplace assignment
                for the new source.
            initial: Validated immutable assessment source; recorded units and ST
                convention are preserved without calculation.
            result: Optional sole calculation matching the initial source; commit it
                with source and ownership in the same SQLite transaction.

        Returns:
            None after exclusive source and historical ownership creation commit
            atomically.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        history = self._history_store()
        key = DocumentKey(self.metadata.project_id, entry.document_id)
        self._check(key)
        if assessment_kind(initial) != entry.kind:
            raise ValueError("Historical ownership model does not match source.")
        if result is not None and (
            result.source != initial or result.calculation_status is None
        ):
            raise ValueError("Initial calculation must match its source.")
        payload = SavedResultStore.encode(result) if result is not None else None
        _idle(self._connection)
        assert isinstance(self._store, AssessmentSqliteStore)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            self._hierarchy_store().read()
            jobs = self._job_store().read()
            history.read(jobs)
            self._store.insert_in_transaction(key, initial)
            history.insert(entry, jobs)
            if payload is not None:
                SavedResultStore.create_schema(self._connection)
                SavedResultStore(self._connection).write(key, payload)

    @_project_edit
    def transfer_assessments(
        self,
        expected_jobs: JobCatalog,
        expected_history: AssessmentHistory,
        request: TransferRequest,
        document_ids: Mapping[AssessmentKind, str],
    ) -> AssessmentHistory:
        """Copy selected versions and their sole matching results atomically.

        Args:
            expected_jobs: Catalog snapshot shown when the transfer was prepared.
            expected_history: Version/ownership snapshot to recheck under the lock.
            request: Source assignment, destination owner, tools and Copy/Move choice.
            document_ids: Newly allocated destination identity for each selected tool.

        Returns:
            Committed ownership history. Copy keeps source versions; Move removes
            selected sources only after destination inputs/results are inserted.

        Raises:
            ValueError: Catalogs changed, identities conflict or selection is invalid.
            RuntimeError: Connection is closed or already owns a transaction.
            sqlite3.Error: A write fails; the entire transfer rolls back.

        Repeat conflict/membership checks under the write lock. Older versions,
        current Job risks and unrelated source/assignment records remain intact.
        Any insert/delete/catalog error rolls back the entire transfer.
        """
        history = self._history_store()
        _idle(self._connection)
        assert isinstance(self._store, AssessmentSqliteStore)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            hierarchy = self._hierarchy_store().read()
            jobs = self._job_store().read()
            current = history.read(jobs)
            if jobs != expected_jobs or current != expected_history:
                raise ValueError("Transfer catalogs changed; reopen the form.")
            plan = plan_transfer(hierarchy.work, jobs, current, request, document_ids)
            payloads = tuple(
                decode_assessment(
                    self._connection.execute(
                        "SELECT payload FROM draft_documents "
                        "WHERE project_id=? AND document_id=?",
                        (self.metadata.project_id, source.document_id),
                    ).fetchone()[0]
                )
                for source, _ in plan.copies
            )
            if plan.jobs != jobs:
                self._job_store().write_in_transaction(
                    plan.jobs, hierarchy, expected=jobs
                )
            for (source, entry), state in zip(plan.copies, payloads, strict=True):
                source_key = DocumentKey(self.metadata.project_id, source.document_id)
                result = self.load_saved_result(source_key)
                destination_key = DocumentKey(
                    self.metadata.project_id, entry.document_id
                )
                self._store.insert_in_transaction(destination_key, state)
                history.insert(entry, plan.jobs)
                if result is not None and result.source == state:
                    # Preserve the sole source-bound result at saved calculator
                    # precision/units; transferring does not recalculate it.
                    payload = SavedResultStore.encode(result)
                    SavedResultStore.create_schema(self._connection)
                    SavedResultStore(self._connection).write(destination_key, payload)
            for document_id in plan.removed_documents:
                current = history.delete(
                    history.read(plan.jobs), document_id, plan.jobs
                )
            return history.read(plan.jobs)

    def _risk_jobs(self) -> JobCatalog:
        # Called only within a risk-store transaction, including open validation.
        """Read parent jobs inside the risk store's existing transaction.

        Args:
            None.

        Returns:
            Validated saved jobs after hierarchy/reference checks, inside the existing
            risk-store transaction.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        assert self._hierarchy is not None and self._jobs is not None
        self._hierarchy.read()
        return self._jobs.read()

    def _validate_job_change(
        self, current: JobCatalog, replacement: JobCatalog
    ) -> None:
        """Protect historical assessment, profile, geometry and rotation ownership.

        Args:
            current: Validated saved job catalog before the proposed transition.
            replacement: Complete proposed immutable replacement preserving same-project
                and protected reference identities.

        Returns:
            None when assessment ownership, profiles, geometry and frozen rotations
            remain valid under proposed jobs.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        if self._history is not None:
            self._history.validate_change(current, replacement)
        if self._risk is not None:
            self._risk.validate_job_change(current, replacement)
        if self._format_version >= 10:
            PlotPositionStore(
                self._connection, self.metadata.project_id
            ).read().validate_job_change(current, replacement)

        if self._format_version >= 11:
            self._validate_rotations(jobs=replacement)

    def _validate_rotations(
        self, *, hierarchy: WorkHierarchy | None = None, jobs: JobCatalog | None = None
    ) -> None:
        """Validate every frozen scheme against saved or proposed catalog references.

        Args:
            hierarchy: Optional proposed hierarchy; None retains saved hierarchy.
            jobs: Complete validated same-project job/placement/assignment catalog; None
                in rotation validation retains saved jobs.

        Returns:
            None when every saved scheme retains exact valid hierarchy/Job/placement
            references.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        current_jobs = self._job_store().read()
        # Borrowed transaction: read() would demand an idle connection and start
        # another transaction. _read validates the catalog on this exact handle.
        risks = self._risk_store()._read(current_jobs)
        for scheme in RotationSchemeStore(
            self._connection, self.metadata.project_id
        ).read():
            if jobs is not None:
                scheme.validate_job_change(current_jobs, jobs)
            scheme.validate_references(
                hierarchy if hierarchy is not None else self._hierarchy_store().read(),
                jobs if jobs is not None else current_jobs,
                risks,
            )

    def _invalidate_job_optimization(self, job_ids: frozenset[str]) -> None:
        """Keep saved arrangements but remove obsolete optimization provenance.

        Args:
            job_ids: Jobs whose current numeric outputs changed in this transaction.

        Returns:
            None; affected optimized schemes become manual without solving or changing
            worker/Job cells. Any failure rolls back the enclosing Job edit as well.

        Raises:
            sqlite3.Error: Reading or writing a dependent scheme fails.
            StoreFormatError: A dependent saved payload is invalid.
        """
        if self._format_version < 11:
            return
        store = RotationSchemeStore(self._connection, self.metadata.project_id)
        for scheme in store.read():
            if scheme.mode is not RotationMode.MANUAL and any(
                target.job_id in job_ids for target in scheme.targets
            ):
                store.write_in_transaction(
                    replace(scheme, mode=RotationMode.MANUAL, primary_kind=None)
                )

    def load_rotation_schemes(self) -> tuple[RotationScheme, ...]:
        """Read exact saved links; older full formats return empty without upgrade.

        Args:
            None.

        Returns:
            Validated schemes in identity order, or empty for older supported full
            formats; never an implicit upgrade.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._risk_store()
        _idle(self._connection)
        if self._format_version < 11:
            return ()
        with self._connection:
            self._connection.execute("BEGIN")
            self._validate_rotations()
            return RotationSchemeStore(
                self._connection, self.metadata.project_id
            ).read()

    @_project_edit
    def save_rotation_scheme(self, scheme: RotationScheme) -> None:
        """Explicitly save one complete scheme, atomically upgrading full formats.

        Failure preserves all prior data and the in-memory format. Reading, optimizing
        and comparing do not invoke this operation. Job/placement links remain exact;
        scientific values always come from the current Job catalog.

        Args:
            scheme: Complete validated same-project rotation with exact frozen
                Jobs/placements/worker assignments.

        Returns:
            None after complete scheme and required full-project schema/version upgrade
            commit atomically.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        self._risk_store()
        if not isinstance(scheme, RotationScheme):
            raise ValueError("Rotation saving requires a typed scheme.")
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            jobs = self._job_store().read()
            risks = self._risk_store()._read(jobs)
            scheme.validate_references(self._hierarchy_store().read(), jobs, risks)
            store = RotationSchemeStore(self._connection, self.metadata.project_id)
            if self._format_version == 7:
                self._connection.execute(
                    "CREATE TABLE project_details (description TEXT, "
                    "created_at TEXT, language TEXT)"
                )
                self._connection.execute(
                    "INSERT INTO project_details VALUES (NULL,NULL,NULL)"
                )
            if self._format_version < 9:
                create_layout_schema(self._connection)
            if self._format_version < 10:
                create_position_schema(self._connection)
            if self._format_version < 11:
                create_rotation_schema(self._connection)
            store.write_in_transaction(scheme)
            version = max(11, self._format_version)
            self._connection.execute(
                "UPDATE project_metadata SET version = ?", (version,)
            )
        self._format_version = version

    @_project_edit
    def delete_rotation_scheme(self, scheme_id: str) -> None:
        """Delete exactly one saved scheme after caller consent; never upgrade.

        Args:
            scheme_id: Exact existing rotation identity to delete after caller consent.

        Returns:
            None after exact scheme deletion; no format upgrade or other scheme write.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
            KeyError: The requested exact saved source, scheme or Job identity is
                absent.
        """
        self._risk_store()
        if self._format_version < 11:
            raise KeyError(scheme_id)
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            RotationSchemeStore(
                self._connection, self.metadata.project_id
            ).delete_in_transaction(scheme_id)

    @property
    def supports_job_risk(self) -> bool:
        """Expose current Job risk capability without I/O or automatic migration.

        Args:
            None.

        Returns:
            True only while open and supporting current Job risks; no I/O.
        """
        return not self._closed and self._risk is not None

    def _risk_store(self) -> JobRiskStore:
        """Require the open job-risk storage capability.

        Args:
            None.

        Returns:
            Borrowed risk store for this open format-seven-or-later repository.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if self._risk is None:
            raise StoreFormatError("Job risks require a full risk-capable project.")
        return self._risk

    def load_job_risk(self) -> JobRiskCatalog:
        """Read current risks and parent Jobs from the same validated snapshot.

        Args:
            None.

        Returns:
            Current risks, task sources and parent Jobs from one read
            snapshot.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return self._risk_store().read()

    @_project_edit
    def delete_job(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job_id: str,
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Delete a job and its owned records while protecting assessment history.

        Args:
            expected_jobs: Exact saved job/placement/assignment catalog shown by the
                form.
            expected_risk: Exact saved current risk catalog shown by the management
                form.
            job_id: Exact saved Job identity selected for deletion.

        Returns:
            Committed job/risk catalogs after guarded deletion preserving assessment and
            frozen rotation references.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """

        def validate(current: JobCatalog, replacement: JobCatalog) -> None:
            """Protect assessment and frozen rotation references before job deletion.

            Reject a job linked to historical assessments before deletion; validate
            remaining assignment and saved rotation references in the same transaction.

            Args:
                current: Validated saved job catalog before the proposed transition.
                replacement: Complete proposed immutable replacement preserving
                    same-project and protected reference identities.

            Returns:
                None when the job is not referenced by assessments and historical/frozen
                rotation ownership remains valid.

            Raises:
                sqlite3.Error: A native schema/source/catalog read or write fails; owned
                    write transactions roll back.
                RuntimeError: Repository is closed, required idle transaction state is
                    absent or SQLite owner-thread access is violated.
                StoreFormatError: Native schema/capability, saved payload or
                    cross-feature references are unsupported or corrupt.
                ValueError: Requested project/source/catalog identity, expected-state
                    comparison or domain/reference validation fails.
            """
            history = self._history_store().read(current)
            placements = {
                item.placement_id
                for item in current.placements
                if item.job_id == job_id
            }
            assignments = {
                item.assignment_id
                for item in current.assignments
                if item.placement_id in placements
            }
            if any(entry.assignment_id in assignments for entry in history.entries):
                raise ValueError(
                    "This job is referenced by an assessment and cannot be deleted."
                )
            self._history_store().validate_change(current, replacement)
            if self._format_version >= 11:
                self._validate_rotations(jobs=replacement)

        return self._risk_store().delete_job(
            expected_jobs,
            expected_risk,
            job_id,
            validate,
            self._job_store().delete_in_transaction,
        )

    @_project_edit
    def save_job_details(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job: Job,
        values: JobRiskValues | None,
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Save Job Management fields and current risk values in one transaction.

        Existing assignments and worker assessments are untouched. Each tool may use
        direct values or an independent calculator source. Numeric changes invalidate
        dependent optimization provenance while retaining all schedule arrangements.
        Invalid input or storage failure rolls back every composed write.

        Args:
            expected_jobs: Exact saved job/placement/assignment catalog shown by the
                form.
            expected_risk: Exact saved current risk catalog shown by the management
                form.
            job: Validated literal job form fields; assignment/placement history is
                retained.
            values: Optional replacement risks; None preserves current values.
                An empty set removes risks without deleting the Job.

        Returns:
            Committed job/risk pair from one management form Save; assessment sources
            and historical assignments stay unchanged.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
            StoreFormatError: Native schema/capability, saved payload or cross-feature
                references are unsupported or corrupt.
            ValueError: Requested project/source/catalog identity, expected-state
                comparison or domain/reference validation fails.
        """
        return self._risk_store().save_job(
            expected_jobs,
            expected_risk,
            job,
            values,
            self._job_store().save_details_in_transaction,
        )

    def close(self) -> None:
        """Release the owned connection once; dirty consent belongs to the lifecycle.

        Args:
            None.

        Returns:
            None after releasing the connection once; a close failure leaves retry
            possible.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
        """
        if not self._closed:
            self._connection.close()
            if self._durable_connection is not None:
                self._durable_connection.close()
            self._closed = True

    def __enter__(self) -> AssessmentProjectFile:
        """Use an open handle in a resource scope.

        Args:
            None.

        Returns:
            This open owned repository for context-scoped resource use.

        Raises:
            RuntimeError: Repository is closed, required idle transaction state is
                absent or SQLite owner-thread access is violated.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        return self

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close without suppressing exceptions or implicitly saving drafts.

        Args:
            error_type: Active exception class, or None at ordinary context-scope exit.
            error: Active exception instance, or None; no exception text is persisted.
            traceback: Active traceback, or None; not inspected or suppressed.

        Returns:
            None after close; never save inputs or suppress the scope exception.

        Raises:
            sqlite3.Error: A native schema/source/catalog read or write fails; owned
                write transactions roll back.
        """
        self.close()

    @_project_edit
    def associate_assessment(
        self, document_id: str, assignment_id: int
    ) -> AssessmentHistory:
        """Associate one standalone assessment with its worker's active workplace.

        Args:
            document_id: Exact saved standalone source identity, never a caption.
            assignment_id: Active destination assignment for the same worker. A Job
                placement is optional; the complete workplace/shift must exist.

        Returns:
            Validated ownership after atomic association. Inputs, result payloads and
            document identity remain unchanged; no other tool is implicitly associated.

        Raises:
            ValueError: The source is assigned, destination belongs to another worker,
                destination is inactive, or that assignment/tool already has data.
            KeyError: Assessment or destination identity is absent.
            sqlite3.Error: Read/update fails; the transaction rolls back.
            RuntimeError: Repository is closed or a transaction is already active.
        """
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            return self._associate_assessment_in_transaction(
                document_id, assignment_id, self._job_store().read()
            )

    def _associate_assessment_in_transaction(
        self, document_id: str, assignment_id: int, jobs: JobCatalog
    ) -> AssessmentHistory:
        """Validate and bind exact ownership in a caller-owned repository transaction.

        Args:
            document_id: Saved standalone assessment identity.
            assignment_id: Explicit existing or just-created destination assignment.
            jobs: Current validated catalog in this same transaction.

        Returns:
            Complete history after the sole ownership-link update. No source/result
            row is rewritten; the caller owns commit and rollback.

        Raises:
            RuntimeError: No caller-owned transaction exists.
            KeyError: Source or destination is missing.
            ValueError: Worker/activity/standalone or uniqueness constraints fail.
            sqlite3.Error: Ownership read/update fails; caller must roll back.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Association requires a caller-owned transaction.")
        store = self._history_store()
        history = store.read(jobs)
        entry = next((e for e in history.entries if e.document_id == document_id), None)
        owner = next(
            (a for a in jobs.assignments if a.assignment_id == assignment_id), None
        )
        if entry is None or owner is None:
            raise KeyError(document_id if entry is None else assignment_id)
        if (
            entry.assignment_id is not None
            or not owner.active
            or owner.worker.worker_id != entry.worker_id
        ):
            raise ValueError(
                "Association requires a standalone assessment "
                "and matching active worker assignment."
            )
        if history.current_for(assignment_id, entry.kind) is not None:
            raise ValueError("Destination already has an assessment for this tool.")
        self._connection.execute(
            "UPDATE assessment_ownership SET assignment_id=? WHERE document_id=?",
            (assignment_id, document_id),
        )
        return store.read(jobs)

    @_project_edit
    def associate_assessment_at_workplace(
        self,
        document_id: str,
        workplace: WorkplaceContext,
        placement_id: int | None,
        *,
        effective_date: date,
    ) -> AssignmentAssessment:
        """Atomically reuse/create a real workplace assignment and bind one assessment.

        Args:
            document_id: Saved standalone source whose worker identity is authoritative.
            workplace: Explicit station and shift validated against saved organization.
            placement_id: Optional Job placement. An existing active worker assignment
                is reused only with the same Job; this operation never reclassifies it.
            effective_date: Explicit calendar date for a new assignment's start.

        Returns:
            Exact associated ownership; inputs/results retain their original bytes.
            Integrated editing records the complete operation as one shared Undo step.

        Raises:
            RuntimeError: Repository is closed or its connection is already active.
            ValueError: Source/context, date, Job or existing ownership conflicts.
            KeyError: Saved source/worker/workplace membership is missing.
            sqlite3.Error: Any read/write fails; the complete transaction rolls back.
        """
        if type(effective_date) is not date:
            raise ValueError("Effective date must be a calendar date.")
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            hierarchy = self._hierarchy_store().read()
            jobs = self._job_store().read()
            history = self._history_store().read(jobs)
            entry = next(
                (e for e in history.entries if e.document_id == document_id), None
            )
            if entry is None:
                raise KeyError(document_id)
            if entry.assignment_id is not None:
                raise ValueError("Select a saved standalone assessment first.")
            worker = hierarchy.work.worker_context(entry.worker_id, workplace)
            current = next(
                (a for a in jobs.assignments if a.active and a.worker == worker), None
            )
            if current is not None:
                if current.placement_id != placement_id:
                    raise ValueError(
                        "Existing workplace assignment has a different Job; "
                        "change it in Worker Management."
                    )
                assignment_id = current.assignment_id
            else:
                change = assign_worker(
                    jobs,
                    worker,
                    placement_id,
                    effective_date=effective_date,
                    creation_note="Created while associating an assessment.",
                    new_assignment_id=max(
                        (a.assignment_id for a in jobs.assignments), default=0
                    )
                    + 1,
                )
                self._job_store().write_in_transaction(
                    change.jobs, hierarchy, expected=jobs
                )
                jobs, assignment_id = change.jobs, change.assignment_id
            associated = self._associate_assessment_in_transaction(
                document_id, assignment_id, jobs
            )
            return next(e for e in associated.entries if e.document_id == document_id)
