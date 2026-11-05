"""Transactional mixed-assessment storage with immutable document model identity.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import sqlite3
from collections.abc import Callable

from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.draft_store import SqliteDraftStore, StoreFormatError


class AssessmentSqliteStore(SqliteDraftStore[AssessmentDraft]):
    """Store tagged assessments; a document ID cannot be reassigned to another tool."""

    format_id = "ergotools.assessment-drafts"

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        validate_source: Callable[[AssessmentDraft], None] | None = None,
    ) -> None:
        """Retain optional full-project reference validation for locked source writes.

        Args:
            connection: Borrowed native connection, validated by the base store.
            validate_source: Owning project's reference validator, or None for
                standalone diagnostics. Called inside source write transactions.

        Returns:
            None; no source is changed during construction.
        """
        super().__init__(connection)
        self._validate_source = validate_source

    def encode(self, state: AssessmentDraft) -> str:
        """Validate source and tag before the transaction starts.

        Args:
            state: Validated immutable tagged LiFFT/DUET/ST source; missing inputs stay
                absent.

        Returns:
            Strict JSON source payload preserving recorded inputs/units without
            calculation.

        Raises:
            ValueError: Source is untyped or contains invalid fields/values.
        """
        return encode_assessment(state)

    def decode(self, payload: str) -> AssessmentDraft:
        """Validate the entire tagged source on load.

        Args:
            payload: Complete saved tagged LiFFT/DUET/ST source JSON text.

        Returns:
            Strictly validated immutable tagged LiFFT/DUET/ST source, retaining row
            identities and missing inputs.

        Raises:
            ValueError: Payload JSON, schema, model, version or values are invalid.
        """
        return decode_assessment(payload)

    def validate_replacement(
        self, existing: str | None, state: AssessmentDraft
    ) -> None:
        """Check stored model identity under the write lock; reject corrupt sources.

        Run inside the write transaction so model identity cannot change between check
        and upsert.

        Args:
            existing: Previous saved tagged source payload, or None for new identity.
            state: Proposed typed source whose concrete model must remain unchanged.

        Returns:
            None when model identity is preserved.

        Raises:
            StoreFormatError: Replacement changes the existing source model.
            ValueError: The prior saved payload is corrupt.
        """
        if self._validate_source is not None:
            self._validate_source(state)
        if existing is not None and type(self.decode(existing)) is not type(state):
            raise StoreFormatError("An existing assessment cannot change model type.")
