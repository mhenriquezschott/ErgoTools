"""Tagged mixed-assessment envelope over strict model-specific source codecs.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import json

from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.infrastructure.draft_json import (
    DocumentFormatError,
    document_fields,
    unique_object,
)
from ergotools.infrastructure.duet_serialization import decode_duet, encode_duet
from ergotools.infrastructure.lifft_serialization import decode_lifft, encode_lifft
from ergotools.infrastructure.tst_serialization import decode_tst, encode_tst


def decode_assessment(payload: str) -> AssessmentDraft:
    """Reject unknown model/version or mismatched nested format; never infer a tool.

    Args:
        payload: Complete versioned source JSON text; null fields represent unfinished
            input, not zero.

    Returns:
        Supported immutable source selected by an exact matching outer model tag and
        strict nested format.

    Raises:
        DocumentFormatError: Outer model/version/fields or nested source format is
            unsupported, ambiguous or malformed.
    """
    try:
        data = document_fields(
            json.loads(payload, object_pairs_hook=unique_object),
            {"format", "version", "kind", "source"},
        )
        if (
            data["format"] != "ergotools.assessment-document"
            or type(data["version"]) is not int
            or data["version"] != 1
        ):
            raise DocumentFormatError("Unsupported assessment envelope.")
        nested = json.dumps(data["source"], allow_nan=False)
        if data["kind"] == "lifft":
            return decode_lifft(nested)
        if data["kind"] == "duet":
            return decode_duet(nested)
        if data["kind"] == "tst":
            return decode_tst(nested)
        raise DocumentFormatError("Unsupported assessment kind.")
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise DocumentFormatError("Invalid assessment document.") from error


def encode_assessment(draft: AssessmentDraft) -> str:
    """Encode only supported sources with an explicit matching model tag.

    Args:
        draft: Immutable source draft with original task identities, order and units; no
            calculations are serialized.

    Returns:
        Deterministic tagged envelope containing only the strict supported source
        representation, never a parallel result cache.

    Raises:
        DocumentFormatError: The source model is unsupported or its nested codec rejects
            malformed input.
        ValueError: Nested JSON encoding rejects a nonfinite source value.
    """
    if isinstance(draft, LifftDraft):
        kind, payload = "lifft", encode_lifft(draft)
    elif isinstance(draft, DuetDraft):
        kind, payload = "duet", encode_duet(draft)
    elif isinstance(draft, TstDraft):
        kind, payload = "tst", encode_tst(draft)
    else:
        raise DocumentFormatError("Unsupported assessment source type.")
    return json.dumps(
        {
            "format": "ergotools.assessment-document",
            "version": 1,
            "kind": kind,
            "source": json.loads(payload),
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
