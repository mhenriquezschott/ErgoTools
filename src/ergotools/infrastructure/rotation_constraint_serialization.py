"""Strict codecs for hard rules and frozen neighboring boundaries.

Infrastructure layer. No project lookup, risk inference, solver or clock
normalization occurs here. Unknown rule tags and extra fields fail rather than
silently relaxing rules.
"""

from datetime import datetime

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationRisk
from ergotools.domain.rotation_constraints import (
    BoundaryExposure,
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
    RotationBoundary,
    RotationRule,
)
from ergotools.infrastructure.draft_json import (
    document_fields,
    document_number,
    document_text,
)


def rule_value(rule: RotationRule) -> dict[str, object]:
    """Encode one supported exact typed rule.

    Args:
        rule: Active validated restriction.

    Returns:
        Strict tagged primitive object, never a UI label.
    """
    if isinstance(rule, NoAdjacentHigh):
        return {
            "type": "no_adjacent_high",
            "worker": rule.worker_id,
            "previous": rule.previous,
            "following": rule.following,
        }
    return {
        "type": "fixed" if isinstance(rule, FixedPosition) else "excluded",
        "worker": rule.worker_id,
        "target": rule.target_key,
    }


def read_rule(value: object) -> RotationRule:
    """Decode a known active restriction without accepting unknown extra options.

    Args:
        value: Primitive tagged record.

    Returns:
        Typed immutable hard rule.

    Raises:
        ValueError: Type/tag/fields/Boolean intentions are invalid or unsupported.
    """
    if not isinstance(value, dict):
        raise ValueError("Invalid rotation rule object.")
    tag = value.get("type")
    if tag == "no_adjacent_high":
        d = document_fields(value, {"type", "worker", "previous", "following"})
        if type(d["previous"]) is not bool or type(d["following"]) is not bool:
            raise ValueError("Boundary flags must be Boolean.")
        return NoAdjacentHigh(document_text(d["worker"]), d["previous"], d["following"])
    if tag not in ("fixed", "excluded"):
        raise ValueError("Unsupported active rotation restriction type.")
    d = document_fields(value, {"type", "worker", "target"})
    cls = FixedPosition if tag == "fixed" else ExcludedPosition
    return cls(document_text(d["worker"]), document_text(d["target"]))


def boundary_value(boundary: RotationBoundary | None) -> object:
    """Encode exact copied boundary evidence or explicit absence.

    Args:
        boundary: Fixed neighboring-run context.

    Returns:
        Primitive object; no live catalog values are substituted.
    """
    if boundary is None:
        return None
    return {
        "scenario": boundary.scenario_id,
        "signature": boundary.run_signature,
        "start": boundary.start.isoformat(),
        "end": boundary.end.isoformat(),
        "workers": [
            {
                "worker": w.worker_id,
                "target": w.target_key,
                "risks": [
                    {"kind": r.kind.value, "probability": r.probability_percent}
                    for r in w.risks
                ],
            }
            for w in boundary.workers
        ],
    }


def read_boundary(value: object) -> RotationBoundary | None:
    """Decode exact naive local clocks and frozen tool evidence.

    Args:
        value: Primitive copied context or None.

    Returns:
        Typed snapshot without claiming its referenced current run remains fresh.

    Raises:
        ValueError: Collection shape, times, evidence or domain fields are invalid.
    """
    if value is None:
        return None
    d = document_fields(value, {"scenario", "signature", "start", "end", "workers"})
    if not isinstance(d["workers"], list):
        raise ValueError("Invalid boundary worker collection.")
    clocks = []
    for field in ("start", "end"):
        text = document_text(d[field])
        clock = datetime.fromisoformat(text)
        if clock.isoformat() != text:
            raise ValueError("Boundary clocks must be canonical ISO local datetimes.")
        clocks.append(clock)
    rows = []
    for item in d["workers"]:
        row = document_fields(item, {"worker", "target", "risks"})
        key = document_text(row["target"])
        if not isinstance(row["risks"], list):
            raise ValueError("Invalid frozen boundary risk collection.")
        risks = []
        for item_risk in row["risks"]:
            r = document_fields(item_risk, {"kind", "probability"})
            number = document_number(r["probability"])
            if number is None:
                raise ValueError("Neighbor risk cannot be missing or inferred as zero.")
            risks.append(
                RotationRisk(key, AssessmentKind(document_text(r["kind"])), number)
            )
        rows.append(BoundaryExposure(document_text(row["worker"]), key, tuple(risks)))
    return RotationBoundary(
        document_text(d["scenario"]),
        document_text(d["signature"]),
        clocks[0],
        clocks[1],
        tuple(rows),
    )
