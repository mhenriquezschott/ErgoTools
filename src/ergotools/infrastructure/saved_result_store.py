"""Encode the sole source-bound calculation per assessment version as native JSON.

Infrastructure codec/store; the project repository owns transactions and lifetime.
Version 3 envelopes retain calculator float precision without additional rounding or
display clipping. One primary key replaces its previous value atomically. Old
imported/rounded envelopes are discarded and recalculated by the external utility.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import json
import sqlite3

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.historical_results import (
    HistoricalAssessmentResult,
    HistoricalTaskResult,
)
from ergotools.application.session import DocumentKey
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.draft_json import (
    DocumentFormatError,
    document_fields,
    document_number,
    document_text,
    unique_object,
)


class SavedResultStore:
    """Read strict result envelopes; the project adapter owns transactions."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Borrow the repository connection without I/O or transaction changes.

        Args:
            connection: Dedicated native project connection owned by the repository.

        Returns:
            None. The caller remains responsible for commit, rollback and close.
        """
        self._connection = connection

    @staticmethod
    def create_schema(connection: sqlite3.Connection) -> None:
        """Create the one-result-per-version schema in the caller's transaction.

        Args:
            connection: Native connection with a caller-owned write transaction.

        Returns:
            None. Existing rows remain unchanged; primary key prevents duplicates.

        Raises:
            sqlite3.Error: Native table/foreign-key creation fails.
        """
        connection.execute(
            "CREATE TABLE IF NOT EXISTS saved_assessment_results "
            "(project_id TEXT NOT NULL, "
            "document_id TEXT NOT NULL, payload TEXT NOT NULL, "
            "PRIMARY KEY(project_id, document_id), "
            "FOREIGN KEY(project_id, document_id) "
            "REFERENCES draft_documents(project_id, document_id) ON DELETE CASCADE)"
        )

    @staticmethod
    def encode(result: HistoricalAssessmentResult) -> str:
        """Encode and validate one calculation without changing its numeric precision.

        Validation happens before a database write; no imported-result envelope or
        historical duplicate is accepted.

        Args:
            result: Source-bound complete/partial calculation with valid unit label.

        Returns:
            Version-3 native JSON. Float representation round-trips Python values;
            summary damage/percent are neither rounded nor display-clipped here.

        Raises:
            ValueError: Nonfinite values cannot be serialized.
            DocumentFormatError: Status, units, source or task envelope is invalid.
        """
        payload = json.dumps(
            {
                "version": 3,
                "source": encode_assessment(result.source),
                "status": result.calculation_status,
                "damage": result.damage,
                "percent": result.probability_percent,
                "units": result.unit_label,
                "issues": result.issue_keys,
                "tasks": [
                    {
                        "moment": row.moment,
                        "damage": row.damage,
                        "share": row.share_percent,
                    }
                    for row in result.tasks
                ],
            },
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        SavedResultStore.decode(payload)
        return payload

    @staticmethod
    def decode(payload: str) -> HistoricalAssessmentResult:
        """Decode strict native calculated output without recalculating inputs.

        Old envelope versions require external recalculation rather than a native
        fallback decoder. No I/O, display formatting or state mutation occurs.

        Args:
            payload: Version-3 result JSON with its exact source snapshot.

        Returns:
            Immutable complete/partial calculation retaining stored float values.
            Missing quantities remain None, not inferred zero-risk measurements.

        Raises:
            DocumentFormatError: Version/status, duplicated fields, numeric values,
                source, units, row counts or envelope structure are invalid.
        """
        try:
            data = document_fields(
                json.loads(payload, object_pairs_hook=unique_object),
                {
                    "version",
                    "source",
                    "status",
                    "damage",
                    "percent",
                    "units",
                    "issues",
                    "tasks",
                },
            )
            version = data["version"]
            if type(version) is not int or version != 3:
                raise DocumentFormatError("Unsupported saved result version.")
            source = decode_assessment(document_text(data["source"]))
            status = EvaluationStatus(document_text(data["status"]))
            if status not in (EvaluationStatus.COMPLETE, EvaluationStatus.PARTIAL):
                raise DocumentFormatError(
                    "Saved result is not a successful calculation."
                )
            units = document_text(data["units"])
            MeasurementSystem(units.lower())
            raw_tasks, raw_issues = data["tasks"], data["issues"]
            if not isinstance(raw_tasks, list) or not isinstance(raw_issues, list):
                raise DocumentFormatError("Result rows and issues must be arrays.")
            if len(raw_tasks) != len(source.tasks):
                raise DocumentFormatError("Result row count does not match source.")
            tasks = []
            for raw in raw_tasks:
                row = document_fields(raw, {"moment", "damage", "share"})
                tasks.append(
                    HistoricalTaskResult(
                        document_number(row["moment"]),
                        document_number(row["damage"]),
                        document_number(row["share"]),
                    )
                )
            return HistoricalAssessmentResult(
                source,
                document_number(data["damage"]),
                document_number(data["percent"]),
                tuple(tasks),
                units,
                status,
                tuple(document_text(issue) for issue in raw_issues),
            )
        except (ValueError, TypeError, OverflowError, RecursionError) as error:
            raise DocumentFormatError("Invalid saved assessment result.") from error

    def write(self, document: DocumentKey, payload: str) -> None:
        """Replace the sole result within the caller's atomic source/result write.

        Primary-key replacement retains no prior/imported output beside this row.

        Args:
            document: Project-scoped assessment version identity.
            payload: Already validated native JSON produced by encode().

        Returns:
            None. The caller commits/rolls back both source and result together.

        Raises:
            RuntimeError: No caller-owned transaction is active.
            sqlite3.Error: The result write or reference constraint fails.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Saved results require a caller-owned transaction.")
        self._connection.execute(
            "INSERT INTO saved_assessment_results VALUES (?, ?, ?) "
            "ON CONFLICT(project_id, document_id) "
            "DO UPDATE SET payload=excluded.payload",
            (document.project_id, document.document_id, payload),
        )

    def read(self, document: DocumentKey) -> HistoricalAssessmentResult | None:
        """Read the sole result for an assessment version without side effects.

        Args:
            document: Project-scoped assessment version identity to look up.

        Returns:
            Decoded calculation, or None if absent/invalidated. The caller checks that
            the result source matches any unsaved active editor inputs.

        Raises:
            DocumentFormatError: The stored native envelope is malformed/obsolete.
            sqlite3.Error: The native table cannot be queried.
        """
        row = self._connection.execute(
            "SELECT payload FROM saved_assessment_results "
            "WHERE project_id=? AND document_id=?",
            (document.project_id, document.document_id),
        ).fetchone()
        return None if row is None else self.decode(row[0])
