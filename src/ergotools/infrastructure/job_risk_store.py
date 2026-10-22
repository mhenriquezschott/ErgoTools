"""Transactional current Job/tool risks and retained calculator sources.

Infrastructure layer. One row per Job/tool replaces profile and evidence storage.
Borrow the owning connection; preserve atomic details/risk updates and rollback.
No scientific calculation, legacy-schema decoding or UI logic occurs here.
"""

import json
import sqlite3
from collections.abc import Callable
from hashlib import sha256

from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_management import delete_job, save_job_details
from ergotools.domain.job_risk import (
    JobRiskCatalog,
    JobRiskMeasurement,
    JobRiskValues,
    JobTaskResult,
)
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.draft_json import unique_object
from ergotools.infrastructure.draft_store import _idle
from ergotools.infrastructure.lifft_store import StoreFormatError


def create_risk_schema(connection: sqlite3.Connection, project_id: str) -> None:
    """Create only current risk rows inside a caller-owned transaction.

    Args:
        connection: Borrowed owner-thread connection with an active transaction.
        project_id: Exact parent project validated without storing a redundant marker.

    Returns:
        None; primary/foreign keys enforce one real Job/tool row.

    Raises:
        RuntimeError: No explicit transaction exists.
    """
    if not connection.in_transaction:
        raise RuntimeError("Risk schema creation requires an active transaction.")
    JobRiskCatalog(project_id)
    connection.execute(
        "CREATE TABLE risk_measurements (job_id TEXT NOT NULL "
        "REFERENCES jobs(id) ON DELETE CASCADE, kind TEXT NOT NULL "
        "CHECK(kind IN ('lifft','duet','tst')), damage REAL, "
        "probability REAL, unit TEXT, source TEXT, position INTEGER "
        "NOT NULL, task_results TEXT, PRIMARY KEY(job_id,kind), "
        "UNIQUE(job_id,position))"
    )


def _encode_task_results(item: JobRiskMeasurement) -> str | None:
    """Encode one current output set with an exact canonical input digest.

    Args:
        item: Validated source-bound current Job/tool values.

    Returns:
        Version-one JSON containing the source digest and exact task outputs, or None
        for direct/uncalculated values. No duplicate input or old result is stored.
    """
    if not item.task_results:
        return None
    assert item.source is not None
    return json.dumps(
        {
            "version": 1,
            "source_sha256": sha256(
                encode_assessment(item.source).encode("utf-8")
            ).hexdigest(),
            "tasks": [
                [row.moment, row.damage, row.share_percent] for row in item.task_results
            ],
        },
        allow_nan=False,
        separators=(",", ":"),
    )


def _decode_task_results(
    payload: str | None, source: AssessmentDraft | None
) -> tuple[JobTaskResult, ...]:
    """Validate that saved current outputs still belong to their exact task inputs.

    Args:
        payload: Native task-output JSON, absent for direct/uncalculated values.
        source: Decoded current source; no legacy decoder or recalculation is used.

    Returns:
        Exact typed per-task rows in source order, or an empty tuple when absent.

    Raises:
        ValueError: Envelope/version/source digest or task shape is invalid.
        TypeError: Malformed nested data cannot construct typed task rows.
    """
    if payload is None:
        return ()
    data = json.loads(payload, object_pairs_hook=unique_object)
    if (
        not isinstance(data, dict)
        or set(data) != {"version", "source_sha256", "tasks"}
        or type(data["version"]) is not int
        or data["version"] != 1
        or source is None
        or data["source_sha256"]
        != sha256(encode_assessment(source).encode("utf-8")).hexdigest()
        or not isinstance(data["tasks"], list)
        or any(not isinstance(row, list) or len(row) != 3 for row in data["tasks"])
    ):
        raise ValueError("Job task outputs do not match their saved source.")
    return tuple(JobTaskResult(*row) for row in data["tasks"])


class JobRiskStore:
    """Validate current risks against real Jobs inside borrowed transactions."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        project_id: str,
        jobs_loader: Callable[[], JobCatalog],
        risks_changed: Callable[[frozenset[str]], None] | None = None,
    ) -> None:
        """Retain the owner connection and transaction-scoped Job reader.

        Args:
            connection: Borrowed connection; caller owns thread/close lifetime.
            project_id: Exact owning project identity.
            jobs_loader: Same-connection reader, never commits or opens another handle.
            risks_changed: Same-transaction callback invalidating dependent optimization
                provenance after numerical risk changes; absent for isolated stores.

        Returns:
            None; no read or schema mutation occurs.
        """
        self._connection = connection
        self._project_id = project_id
        self._jobs_loader = jobs_loader
        self._risks_changed = risks_changed

    def _read(self, jobs: JobCatalog) -> JobRiskCatalog:
        """Decode current rows and task sources without recalculating their values.

        Args:
            jobs: Current real parent Jobs from the same transaction.

        Returns:
            Validated current risk catalog in stable Job/tool order.

        Raises:
            StoreFormatError: A stored source, tool, quantity or parent is invalid.
        """
        grouped: dict[str, list[JobRiskMeasurement]] = {}
        try:
            for (
                job_id,
                kind,
                damage,
                probability,
                unit,
                source,
                task_results,
            ) in self._connection.execute(
                "SELECT job_id,kind,damage,probability,unit,source,task_results FROM "
                "risk_measurements ORDER BY job_id,position"
            ):
                decoded_source = None if source is None else decode_assessment(source)
                grouped.setdefault(job_id, []).append(
                    JobRiskMeasurement(
                        AssessmentKind(kind),
                        damage,
                        probability,
                        unit,
                        decoded_source,
                        _decode_task_results(task_results, decoded_source),
                    )
                )
            result = JobRiskCatalog(
                self._project_id,
                tuple(
                    JobRiskValues(key, tuple(value)) for key, value in grouped.items()
                ),
            )
            result.validate_jobs(jobs)
            return result
        except (ValueError, TypeError, KeyError) as error:
            raise StoreFormatError("Invalid current Job risk values.") from error

    def validate_job_change(self, current: JobCatalog, replacement: JobCatalog) -> None:
        """Protect each current risk set's parent Job inside the job-write transaction.

        Args:
            current: Validated saved catalog before the proposed transition.
            replacement: Proposed immutable catalog after the transition, retaining
                protected identities.

        Returns:
            None when every existing risk set retains a valid parent in the proposed job
            catalog.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Project/risk/source invariants, parent jobs,
                expected saved data or verified round trip are invalid.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Risk reference checks require an active transaction.")
        self._read(current).validate_jobs(replacement)

    def read(self) -> JobRiskCatalog:
        """Read current values and Job ownership in one SQLite read transaction.

        Args:
            None.

        Returns:
            Validated risk/job evidence from one owned read transaction; connection
            ownership stays with the project.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Project/risk/source invariants, parent jobs,
                expected saved data or verified round trip are invalid.
        """
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN")
            return self._read(self._jobs_loader())

    def _write(self, current: JobRiskCatalog, replacement: JobRiskCatalog) -> None:
        """Replace only changed Job risk sets inside the active transaction.

        Args:
            current: Previously validated current catalog.
            replacement: Validated desired catalog with no versions or evidence.

        Returns:
            None; unchanged Job/tool rows are not rewritten.

        Raises:
            RuntimeError: No enclosing transaction exists.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Risk writes require an active transaction.")
        changed: set[str] = set()
        for job_id in sorted(
            {v.job_id for v in (*current.values, *replacement.values)}
        ):
            previous, updated = current.for_job(job_id), replacement.for_job(job_id)
            if previous == updated:
                continue
            if {
                (m.kind, m.cumulative_damage, m.probability_percent)
                for m in previous.measurements
            } != {
                (m.kind, m.cumulative_damage, m.probability_percent)
                for m in updated.measurements
            }:
                changed.add(job_id)
            self._connection.execute(
                "DELETE FROM risk_measurements WHERE job_id=?", (job_id,)
            )
            for position, item in enumerate(updated.measurements):
                self._connection.execute(
                    "INSERT INTO risk_measurements VALUES (?,?,?,?,?,?,?,?)",
                    (
                        job_id,
                        item.kind.value,
                        item.cumulative_damage,
                        item.probability_percent,
                        item.unit,
                        encode_assessment(item.source)
                        if item.source is not None
                        else None,
                        position,
                        _encode_task_results(item),
                    ),
                )

        if changed and self._risks_changed is not None:
            self._risks_changed(frozenset(changed))

    def initialize_in_transaction(self, catalog: JobRiskCatalog) -> None:
        """Insert a complete current catalog during exclusive native snapshot creation.

        Args:
            catalog: Same-project values with real parent Jobs already inserted.

        Returns:
            None; caller owns rollback/publication if validation fails.

        Raises:
            ValueError: Store is populated or project/Job ownership differs.
        """
        catalog.validate_jobs(self._jobs_loader())
        if (
            catalog.project_id != self._project_id
            or self._connection.execute(
                "SELECT 1 FROM risk_measurements LIMIT 1"
            ).fetchone()
        ):
            raise ValueError(
                "Risk initialization requires an empty store in the same project."
            )
        self._write(JobRiskCatalog(self._project_id), catalog)

    def delete_job(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job_id: str,
        validate_change: Callable[[JobCatalog, JobCatalog], None],
        write_job: Callable[[str], None],
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Delete all job-owned risk/placement records atomically after history checks.

        Callbacks borrow this same transaction and must not commit it. Any failed check
        or write rolls back current risks, measurements and job relationships.

        Args:
            expected_jobs: Exact saved job/assignment catalog used as the conflict
                precondition.
            expected_risk: Exact saved current risk catalog used as the conflict
                precondition.
            job_id: Exact saved job identity for the requested operation.
            validate_change: Optional same-transaction guard protecting referenced
                assignment/placement identities before catalog replacement.
            write_job: Same-transaction job mutation callback; caller owns
                commit/rollback and it must not acquire another connection.

        Returns:
            Committed jobs/risk pair after guarded atomic
            Job/tool/placement deletion.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Project/risk/source invariants, parent jobs,
                expected saved data or verified round trip are invalid.
        """
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            jobs = self._jobs_loader()
            risk = self._read(jobs)
            if jobs != expected_jobs or risk != expected_risk:
                raise ValueError("Job details changed since the form was loaded.")
            saved_jobs, saved_risk = delete_job(jobs, risk, job_id)
            validate_change(jobs, saved_jobs)
            self._connection.execute(
                "DELETE FROM risk_measurements WHERE job_id=?", (job_id,)
            )
            write_job(job_id)
            actual_jobs = self._jobs_loader()
            if actual_jobs != saved_jobs or self._read(actual_jobs) != saved_risk:
                raise ValueError(
                    "Saved records differ from the requested job deletion."
                )
            return saved_jobs, saved_risk

    def save_job(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job: Job,
        values: JobRiskValues | None,
        write_job: Callable[[Job], None],
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Commit job fields and current form values together, or roll back both.

        write_job borrows this connection and must not commit. Integrated editing uses
        private backing; only main Save publishes the complete project. Diagnostic
        callers retain their explicit connection transaction boundary.

        Args:
            expected_jobs: Exact saved job/assignment catalog used as the conflict
                precondition.
            expected_risk: Exact saved current risk catalog used as the conflict
                precondition.
            job: Validated literal job form fields; placements/assignments are separate
                records.
            values: Optional replacement current values; None
                preserves the domain operation's current replacement policy.
            write_job: Same-transaction job mutation callback; caller owns
                commit/rollback and it must not acquire another connection.

        Returns:
            Committed jobs/risk pair after atomic form-field/current-risk update; active
            assessment source is unaffected.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Project/risk/source invariants, parent jobs,
                expected saved data or verified round trip are invalid.
        """
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            jobs = self._jobs_loader()
            risk = self._read(jobs)
            if jobs != expected_jobs or risk != expected_risk:
                raise ValueError("Job details changed since the form was loaded.")
            saved_jobs, saved_risk = save_job_details(jobs, risk, job, values)
            saved_job = next(
                item for item in saved_jobs.jobs if item.job_id == job.job_id.strip()
            )
            write_job(saved_job)
            self._write(risk, saved_risk)
            actual_jobs = self._jobs_loader()
            if actual_jobs != saved_jobs or self._read(actual_jobs) != saved_risk:
                raise ValueError("Saved job details differ from the form contents.")
            return saved_jobs, saved_risk
