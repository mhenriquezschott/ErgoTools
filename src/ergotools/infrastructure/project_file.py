"""Owned SQLite connection for an explicitly new-format single-project file.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import sqlite3
from pathlib import Path
from types import TracebackType

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.lifft_serialization import encode_lifft
from ergotools.infrastructure.lifft_store import LifftSqliteStore, StoreFormatError


class ProjectFile:
    """Own one repository connection; close explicitly or use a context manager.

    Single-writer and owner-thread usage only. This is not legacy .ergprj support,
    a project-switch coordinator or an implementation of Save As.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Adopt a validated connection; factories handle cleanup on failure.

        Args:
            connection: Newly acquired connection whose successful validation transfers
                close ownership to this object.

        Returns:
            None after validating the diagnostic LiFFT-only project format and
            foreign-document exclusion.

        Raises:
            StoreFormatError: Draft/project markers or source ownership are unsupported.
            ValueError: Recorded metadata/default units are invalid.
            sqlite3.DatabaseError: Metadata/source ownership queries fail.
            RuntimeError: Connection is not idle/default-mode.
        """
        self._connection = connection
        self._store = LifftSqliteStore(connection)
        rows = connection.execute(
            "SELECT format, version, project_id, title, default_units "
            "FROM project_metadata"
        ).fetchall()
        if len(rows) != 1 or rows[0][:2] != ("ergotools.project", 1):
            raise StoreFormatError("Unsupported project metadata format.")
        _, _, project_id, title, units = rows[0]
        self._metadata = ProjectMetadata(project_id, title, MeasurementSystem(units))
        if connection.execute(
            "SELECT 1 FROM draft_documents WHERE project_id != ? LIMIT 1", (project_id,)
        ).fetchone():
            raise StoreFormatError("Project contains foreign document identities.")
        self._closed = False

    @property
    def metadata(self) -> ProjectMetadata:
        """Expose immutable project defaults without changing saved document units.

        Args:
            None.

        Returns:
            Validated immutable project identity/title/default units; source units are
            unchanged.
        """
        return self._metadata

    @classmethod
    def create(cls, path: Path, metadata: ProjectMetadata) -> "ProjectFile":
        """Create only a nonexistent destination; remove our incomplete file on failure.

        Parent directories are caller-owned. Never overwrite, initialize or adopt an
        existing file. Creation is not crash-atomic publication of a project.

        Args:
            path: Nonexistent destination with a caller-created parent directory.
            metadata: Validated identity/title/default units for the diagnostic project.

        Returns:
            New owned initialized repository without a source document.

        Raises:
            FileExistsError: Destination already exists and is never removed.
            OSError: Exclusive file creation or cleanup fails.
            sqlite3.DatabaseError: Initialization fails; owned partial file is removed.
            ValueError: Post-creation format/metadata validation fails.
        """
        with path.open("xb"):
            pass
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(path)
            LifftSqliteStore.create(connection)
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
                        1,
                        metadata.project_id,
                        metadata.title,
                        metadata.default_units.value,
                    ),
                )
            return cls(connection)
        except BaseException:
            if connection is not None:
                connection.close()
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def create_with_document(
        cls,
        path: Path,
        metadata: ProjectMetadata,
        document_id: str,
        initial: LifftDraft,
    ) -> "ProjectFile":
        """Initialize a project and first draft; remove incomplete files on failure.

        Validate the source before creating the file. Existing destinations are never
        removed. Successful return owns a fully persisted first document;
        interruption/power-loss recovery remains outside this creation contract.

        Args:
            path: Nonexistent destination; never overwrite another file.
            metadata: Validated identity/title/default units.
            document_id: Exact first source identity.
            initial: LiFFT source validated before file creation.

        Returns:
            New owned repository with the exact first source persisted.

        Raises:
            ValueError: Identity/source validation fails.
            FileExistsError: Destination already exists.
            OSError: Creation or failed-initialization cleanup fails.
            sqlite3.DatabaseError: Creation/save fails; owned partial file is removed.
        """
        key = DocumentKey(metadata.project_id, document_id)
        encode_lifft(initial)
        project = cls.create(path, metadata)
        try:
            project.save(key, initial)
            return project
        except BaseException:
            project.close()
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def open(cls, path: Path) -> "ProjectFile":
        """Open an existing format for read/write, never create missing files.

        Args:
            path: Existing diagnostic native LiFFT project path.

        Returns:
            Owned validated read/write handle; candidate connection closes on validation
            failure.

        Raises:
            sqlite3.DatabaseError: Existing file cannot be opened or queried.
            StoreFormatError: File metadata/format/source ownership is unsupported.
            ValueError: Metadata/default units are invalid.
        """
        uri = path.absolute().as_uri() + "?mode=rw"
        connection = sqlite3.connect(uri, uri=True)
        try:
            return cls(connection)
        except BaseException:
            connection.close()
            raise

    def _check(self, document: DocumentKey) -> None:
        """No storage read or ownership change.

        Args:
            document: Requested exact project/document identity.

        Returns:
            None when open and the source belongs to this project.

        Raises:
            RuntimeError: Repository has already closed.
            ValueError: Source belongs to another project.
        """
        if self._closed:
            raise RuntimeError("Project repository is closed.")
        if document.project_id != self.metadata.project_id:
            raise ValueError("Document belongs to another project.")

    def load(self, document: DocumentKey) -> LifftDraft:
        """Load only this project's document through the validated draft adapter.

        Args:
            document: Exact project/document source identity.

        Returns:
            Validated saved LiFFT source.

        Raises:
            RuntimeError: Repository is closed or its connection is busy.
            ValueError: Ownership/format/source validation fails.
            KeyError: The source identity is absent.
            sqlite3.DatabaseError: Read fails.
        """
        self._check(document)
        return self._store.load(document)

    def save(self, document: DocumentKey, state: LifftDraft) -> None:
        """Commit only this project's document without changing project defaults.

        Args:
            document: Exact same-project source identity to upsert.
            state: Validated LiFFT replacement source with recorded units.

        Returns:
            None after atomic source persistence; project defaults remain unchanged.

        Raises:
            RuntimeError: Repository is closed or connection is not idle.
            ValueError: Ownership/format/source validation fails.
            sqlite3.DatabaseError: Write fails and rolls back.
        """
        self._check(document)
        self._store.save(document, state)

    def close(self) -> None:
        """Release the owned connection once; dirty consent belongs to the lifecycle.

        Args:
            None.

        Returns:
            None after releasing the connection once; failure leaves retry possible.

        Raises:
            sqlite3.Error: SQLite connection close fails.
        """
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __enter__(self) -> "ProjectFile":
        """Use an open handle in a resource scope.

        Args:
            None.

        Returns:
            This owned open repository for use in a with scope.

        Raises:
            RuntimeError: Repository has already closed.
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
            error_type: Active exception class, or None for ordinary scope exit.
            error: Active exception instance, or None.
            traceback: Active traceback, or None; never inspected or persisted.

        Returns:
            None; close only, without suppressing the original scope exception or saving
            drafts.

        Raises:
            sqlite3.Error: Connection close fails.
        """
        self.close()
