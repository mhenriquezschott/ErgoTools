"""Strict current named-scenario codec with exact immutable run evidence.

Infrastructure layer. Encode typed planning data and source-bound Job measurements,
not calculated display caches. Current older schemes keep their separate unchanged
codec. No original-schema migration, clock inference or recalculation occurs here.
"""

import hashlib
import json
from datetime import date, datetime
from typing import cast

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobTaskResult
from ergotools.domain.rotation import (
    RotationBackend,
    RotationRisk,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.domain.rotation_planning import RotationPlanningProblem
from ergotools.domain.rotation_scenario import (
    RotationCoefficient,
    RotationDraftRow,
    RotationInputs,
    RotationRun,
    RotationScenario,
    complete_rotation_rows,
)
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.domain.work_hierarchy import LineKey
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.draft_json import (
    document_fields,
    document_number,
    document_text,
    unique_object,
)
from ergotools.infrastructure.rotation_constraint_serialization import (
    boundary_value,
    read_boundary,
    read_rule,
    rule_value,
)
from ergotools.infrastructure.rotation_timing_store import (
    decode_rotation_timing,
    encode_rotation_timing,
)


def canonical_json(value: object) -> str:
    """Encode deterministic exact JSON for current payloads and run integrity digests.

    Args:
        value: JSON-compatible typed projection.

    Returns:
        Stable Unicode JSON; floats keep their native roundtrip precision.

    Raises:
        ValueError: Projection includes a nonfinite number.
        TypeError: Projection contains an unsupported object.
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _array(value: object, width: int | None = None) -> list[object]:
    """Require an array and optionally a fixed row width without coercion.

    Args:
        value: Decoded array/row.
        width: Required row width, or None for variable-length arrays.

    Returns:
        Original list after structural validation.

    Raises:
        ValueError: Value is not an array or has the wrong width.
    """
    if not isinstance(value, list) or (width is not None and len(value) != width):
        raise ValueError("Invalid rotation array shape.")
    return cast(list[object], value)


def _text(value: object) -> str | None:
    """Require optional literal text without stripping user descriptions.

    Args:
        value: Decoded primitive.

    Returns:
        Original text or None.

    Raises:
        ValueError: Supplied value is not text/null.
    """
    if value is not None and not isinstance(value, str):
        raise ValueError("Expected optional rotation text.")
    return value


def _integer(value: object) -> int:
    """Require an exact integer rather than Boolean or fractional coercion.

    Args:
        value: Decoded primitive.

    Returns:
        Original integer.

    Raises:
        ValueError: Primitive is not an exact integer.
    """
    if type(value) is not int:
        raise ValueError("Expected whole rotation integer.")
    return value


def _optional_integer(value: object) -> int | None:
    """Read explicit absent or exact identity/clock integer.

    Args:
        value: Decoded primitive.

    Returns:
        None or an exact non-Boolean integer.

    Raises:
        ValueError: Primitive has an incompatible type.
    """
    return None if value is None else _integer(value)


def _rows(rows: tuple[WorkerRotation | RotationDraftRow, ...] | None) -> object:
    """Project observed/proposed rows while retaining the absence of a baseline.

    Args:
        rows: Typed schedule or explicit None.

    Returns:
        Primitive rows or JSON null; an absent baseline never becomes an empty seed.
    """
    return None if rows is None else [[r.worker_id, r.target_keys] for r in rows]


def _read_rows(value: object) -> tuple[WorkerRotation | RotationDraftRow, ...] | None:
    """Read immutable schedule rows without inferring staffing or observations.

    Args:
        value: Primitive rows or explicit null.

    Returns:
        Typed schedule or None.

    Raises:
        ValueError: Row shape, identities or targets are invalid.
    """
    if value is None:
        return None
    rows = [_array(r, 2) for r in _array(value)]
    result: list[WorkerRotation | RotationDraftRow] = []
    for row in rows:
        targets = tuple(_text(k) for k in _array(row[1]))
        if any(k is None for k in targets):
            result.append(RotationDraftRow(document_text(row[0]), targets))
        else:
            result.extend(
                complete_rotation_rows(
                    (RotationDraftRow(document_text(row[0]), targets),)
                )
            )
    return tuple(result)


def _inputs(value: RotationInputs) -> dict[str, object]:
    """Project current or frozen input identity/time/schedule fields exactly once.

    Args:
        value: Complete typed draft or run input snapshot.

    Returns:
        Primitive named input fields without inferred defaults.
    """
    return {
        "planned_date": value.planned_date.isoformat() if value.planned_date else None,
        "line": [value.line.plant_name, value.line.section_name, value.line.line_name]
        if value.line
        else None,
        "shift_id": value.shift_id,
        "start_minute": value.start_minute,
        "timing": encode_rotation_timing(value.timing) if value.timing else None,
        "workers": [[w.worker_id, w.assignment_id] for w in value.workers],
        "targets": [[t.job_id, t.placement_id] for t in value.targets],
        "tools": [k.value for k in value.tools],
        "baseline": _rows(value.baseline),
        "proposed": _rows(value.proposed),
        "rules": [rule_value(r) for r in value.rules],
        "previous": boundary_value(value.previous),
        "following": boundary_value(value.following),
        "scope": [
            [c.plant_name, c.section_name, c.line_name, c.station_id, c.shift_id]
            for c in value.scope
        ],
    }


def _read_inputs(value: object, version: int) -> RotationInputs:
    """Decode strict draft/run inputs, preserving unknown older dates and times.

    Args:
        value: Complete primitive input object.
        version: Outer scenario codec; version one has no rule/boundary fields.

    Returns:
        Immutable validated structural plan.

    Raises:
        ValueError: Fields, ISO date, clocks or collection/domain types are invalid.
    """
    d = document_fields(
        value,
        {
            "planned_date",
            "line",
            "shift_id",
            "start_minute",
            "timing",
            "workers",
            "targets",
            "tools",
            "baseline",
            "proposed",
            "scope",
        }
        | ({"rules", "previous", "following"} if version >= 2 else set()),
    )
    text = _text(d["planned_date"])
    planned = date.fromisoformat(text) if text is not None else None
    if planned is not None and planned.isoformat() != text:
        raise ValueError("Rotation date must be canonical ISO local date.")
    line = _array(d["line"], 3) if d["line"] is not None else None
    workers = [_array(r, 2) for r in _array(d["workers"])]
    targets = [_array(r, 2) for r in _array(d["targets"])]
    contexts = [_array(r, 5) for r in _array(d["scope"])]
    timing = _text(d["timing"])
    return RotationInputs(
        planned,
        LineKey(*(document_text(v) for v in line)) if line is not None else None,
        _text(d["shift_id"]),
        _optional_integer(d["start_minute"]),
        decode_rotation_timing(timing) if timing is not None else None,
        tuple(
            RotationWorkerLink(document_text(r[0]), _optional_integer(r[1]))
            for r in workers
        ),
        tuple(
            RotationTarget(document_text(r[0]), _optional_integer(r[1]))
            for r in targets
        ),
        tuple(AssessmentKind(document_text(k)) for k in _array(d["tools"])),
        _read_rows(d["baseline"]),
        _read_rows(d["proposed"]),
        tuple(WorkplaceContext(*(document_text(v) for v in row)) for row in contexts),
        tuple(read_rule(r) for r in _array(d["rules"])) if version >= 2 else (),
        read_boundary(d["previous"]) if version >= 2 else None,
        read_boundary(d["following"]) if version >= 2 else None,
    )


def _coefficient(value: RotationCoefficient) -> dict[str, object]:
    """Project one frozen Job input/output including direct/source distinction.

    Args:
        value: Complete typed coefficient with original source units/results.

    Returns:
        Primitive exact evidence and literal frozen labels.
    """
    m = value.measurement
    return {
        "target": value.target_key,
        "name": value.job_name,
        "kind": m.kind.value,
        "damage": m.cumulative_damage,
        "probability": m.probability_percent,
        "unit": m.unit,
        "source": encode_assessment(m.source) if m.source else None,
        "task_results": [[r.moment, r.damage, r.share_percent] for r in m.task_results],
        "task_names": value.task_names,
    }


def _read_coefficient(value: object) -> RotationCoefficient:
    """Decode exact source/result evidence without consulting live Job/task catalogs.

    Args:
        value: Complete primitive coefficient object.

    Returns:
        Frozen typed coefficient; later renames/deletions cannot reinterpret it.

    Raises:
        ValueError: Shapes, model, values or source/results are invalid.
    """
    d = document_fields(
        value,
        {
            "target",
            "name",
            "kind",
            "damage",
            "probability",
            "unit",
            "source",
            "task_results",
            "task_names",
        },
    )
    source = _text(d["source"])
    rows = [_array(r, 3) for r in _array(d["task_results"])]
    return RotationCoefficient(
        document_text(d["target"]),
        document_text(d["name"]),
        JobRiskMeasurement(
            AssessmentKind(document_text(d["kind"])),
            document_number(d["damage"]),
            document_number(d["probability"]),
            _text(d["unit"]),
            decode_assessment(source) if source is not None else None,
            tuple(JobTaskResult(*(document_number(v) for v in row)) for row in rows),
        ),
        tuple(_text(v) for v in _array(d["task_names"])),
    )


def _run(value: RotationRun) -> dict[str, object]:
    """Project immutable run evidence with a digest over its exact encoded context.

    Args:
        value: Typed accepted run; solver acceptance remains an application contract.

    Returns:
        Complete primitive run with integrity fingerprint and explicit model version.
    """
    data: dict[str, object] = {
        "inputs": _inputs(value.inputs),
        "coefficients": [_coefficient(c) for c in value.coefficients],
        "arrangement": _rows(value.arrangement),
        "backend": value.backend.value,
        "stages": [s.value for s in value.stages],
        "settings": value.settings,
        "completed_at": value.completed_at.isoformat(),
        "contract_version": value.contract_version,
        "worker_labels": value.worker_labels,
    }
    data["fingerprint"] = hashlib.sha256(
        canonical_json(data).encode("utf-8")
    ).hexdigest()
    return data


def _read_run(value: object, version: int) -> RotationRun:
    """Verify the run fingerprint before reconstructing exact outcome evidence.

    Args:
        value: Complete primitive run object.
        version: Outer codec selecting exact input-field compatibility.

    Returns:
        Immutable run context; no live catalog or optimizer is read.

    Raises:
        ValueError: Digest, timestamp, settings or typed run invariants are invalid.
    """
    d = document_fields(
        value,
        {
            "inputs",
            "coefficients",
            "arrangement",
            "backend",
            "stages",
            "settings",
            "completed_at",
            "contract_version",
            "worker_labels",
            "fingerprint",
        },
    )
    expected = document_text(d["fingerprint"])
    body = {k: v for k, v in d.items() if k != "fingerprint"}
    if hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest() != expected:
        raise ValueError("Saved rotation run fingerprint does not match.")
    settings = [_array(r, 2) for r in _array(d["settings"])]
    rows = _read_rows(d["arrangement"])
    if rows is None:
        raise ValueError("A run requires its accepted arrangement.")
    timestamp = document_text(d["completed_at"])
    completed = datetime.fromisoformat(timestamp)
    if completed.isoformat() != timestamp:
        raise ValueError("Run timestamp must be canonical ISO UTC.")
    run = RotationRun(
        _read_inputs(d["inputs"], version),
        tuple(_read_coefficient(c) for c in _array(d["coefficients"])),
        complete_rotation_rows(rows),
        RotationBackend(document_text(d["backend"])),
        tuple(RotationSolveStatus(document_text(s)) for s in _array(d["stages"])),
        tuple((document_text(r[0]), document_text(r[1])) for r in settings),
        completed,
        _integer(d["contract_version"]),
        tuple(document_text(s) for s in _array(d["worker_labels"])),
    )

    if run.contract_version == 2:
        risks = tuple(
            RotationRisk(
                c.target_key, c.measurement.kind, c.measurement.probability_percent
            )
            for c in run.coefficients
            if c.measurement.probability_percent is not None
        )
        RotationPlanningProblem(run.inputs, risks).validate_schedule(run.arrangement)
    return run


def is_scenario_payload(payload: str) -> bool:
    """Recognize only the current guided tag, without claiming full validation.

    Args:
        payload: Current native rotation JSON.

    Returns:
        True for guided records; callers still decode them strictly before use.

    Raises:
        ValueError: JSON is malformed or repeats a member.
    """
    data: object = json.loads(payload, object_pairs_hook=unique_object)
    return (
        isinstance(data, dict) and data.get("format") == "ergotools.rotation-scenario"
    )


def encode_scenario(value: RotationScenario) -> str:
    """Encode one current scenario without altering any older scheme representation.

    Args:
        value: Complete typed independent scenario.

    Returns:
        Version-two guided JSON, distinct from the legacy-compatible scheme family.
    """
    return canonical_json(
        {
            "format": "ergotools.rotation-scenario",
            "version": 2,
            "project_id": value.project_id,
            "scenario_id": value.scenario_id,
            "name": value.name,
            "description": value.description,
            "source_scenario_id": value.source_scenario_id,
            "inputs": _inputs(value.inputs),
            "run": _run(value.run) if value.run else None,
            "legacy_mode": value.legacy_mode.value if value.legacy_mode else None,
            "legacy_primary_kind": value.legacy_primary_kind.value
            if value.legacy_primary_kind
            else None,
        }
    )


def decode_scenario(payload: str) -> RotationScenario:
    """Decode strict current guided data, rejecting unknown and duplicate fields.

    Args:
        payload: Current guided JSON with explicit format/version.

    Returns:
        Typed scenario retaining current inputs and separate immutable run context.

    Raises:
        ValueError: JSON, codec, field types or domain invariants are invalid.
    """
    d = document_fields(
        json.loads(payload, object_pairs_hook=unique_object),
        {
            "format",
            "version",
            "project_id",
            "scenario_id",
            "name",
            "description",
            "source_scenario_id",
            "inputs",
            "run",
            "legacy_mode",
            "legacy_primary_kind",
        },
    )
    if (
        d["format"] != "ergotools.rotation-scenario"
        or type(d["version"]) is not int
        or d["version"] not in (1, 2)
    ):
        raise ValueError("Unsupported rotation scenario codec.")
    mode = _text(d["legacy_mode"])
    kind = _text(d["legacy_primary_kind"])
    return RotationScenario(
        document_text(d["project_id"]),
        document_text(d["scenario_id"]),
        document_text(d["name"]),
        _read_inputs(d["inputs"], _integer(d["version"])),
        _text(d["description"]),
        _text(d["source_scenario_id"]),
        _read_run(d["run"], _integer(d["version"])) if d["run"] is not None else None,
        RotationMode(mode) if mode is not None else None,
        AssessmentKind(kind) if kind is not None else None,
    )


def scenario_payload_version(payload: str) -> int:
    """Inspect the explicit codec capability before allowing an older native marker.

    Args:
        payload: Guided native JSON, still subject to full strict decoding.

    Returns:
        Exact codec integer; no unknown payload is treated as version one.

    Raises:
        ValueError: The payload is not a versioned guided scenario.
    """
    data: object = json.loads(payload, object_pairs_hook=unique_object)
    if (
        not isinstance(data, dict)
        or data.get("format") != "ergotools.rotation-scenario"
    ):
        raise ValueError("Expected a guided rotation payload.")
    return _integer(data.get("version"))
