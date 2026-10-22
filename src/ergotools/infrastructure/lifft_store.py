"""Typed Lifft adapter over shared transactional version-one draft storage.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.infrastructure.draft_store import SqliteDraftStore
from ergotools.infrastructure.draft_store import StoreFormatError as StoreFormatError
from ergotools.infrastructure.lifft_serialization import decode_lifft, encode_lifft


class LifftSqliteStore(SqliteDraftStore[LifftDraft]):
    """Store only Lifft source drafts; reject other tool database markers."""

    format_id = "ergotools.drafts"

    def encode(self, state: LifftDraft) -> str:
        """Validate and encode before starting a write transaction.

        Args:
            state: Validated immutable LiFFT source; missing inputs stay absent.

        Returns:
            Strict JSON source payload preserving recorded inputs/units without
            calculation.

        Raises:
            ValueError: Source is untyped or contains invalid fields/values.
        """
        return encode_lifft(state)

    def decode(self, payload: str) -> LifftDraft:
        """Load a complete validated source draft.

        Args:
            payload: Complete saved LiFFT source JSON text.

        Returns:
            Strictly validated immutable LiFFT source, retaining row identities and
            missing inputs.

        Raises:
            ValueError: Payload JSON, schema, model, version or values are invalid.
        """
        return decode_lifft(payload)
