"""Strict native Shift timing codec and caller-transaction SQLite adapter.

Infrastructure layer. Persist relative-minute templates only; clocks come from the
current hierarchy and rotation instances will own explicit copies. Reads never create
storage, invent a break or alter an optimizer/calculator/saved arrangement.
"""

import json
import sqlite3

from ergotools.application.rotation_timing import ShiftTimingTemplate
from ergotools.domain.rotation_timing import MinuteInterval, RotationTiming, TimedBreak
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.draft_json import document_fields, unique_object
from ergotools.infrastructure.draft_store import StoreFormatError


def create_rotation_timing_schema(connection: sqlite3.Connection) -> None:
    """Create empty template storage inside an explicitly owned schema transaction.

    Args:
        connection: Borrowed project connection with an active write transaction.

    Returns:
        None after creating the one current functional table.

    Raises:
        RuntimeError: Caller has no schema transaction.
        sqlite3.Error: Schema creation fails; caller must roll back.
    """
    if not connection.in_transaction:
        raise RuntimeError("Timing schema creation requires a project transaction.")
    connection.execute(
        "CREATE TABLE shift_timing_templates (shift_id TEXT PRIMARY KEY NOT NULL, "
        "payload TEXT NOT NULL)"
    )


def decode_rotation_timing(payload: str) -> RotationTiming:
    """Decode exact whole-minute timing without coercion or unknown fields.

    Args:
        payload: Current native template JSON; no original-format interpretation.

    Returns:
        Validated immutable minute accounting, independent of a particular Shift ID.

    Raises:
        StoreFormatError: JSON structure, codec version, types or timing are invalid.
    """
    try:
        record = document_fields(
            json.loads(payload, object_pairs_hook=unique_object),
            {
                "format",
                "version",
                "shift_minutes",
                "breaks",
                "block_minutes",
                "equal_blocks",
                "subtract_breaks",
            },
        )
        if (
            record["format"] != "ergotools.rotation-timing"
            or type(record["version"]) is not int
            or record["version"] != 1
        ):
            raise ValueError("Unsupported rotation timing codec.")
        if not isinstance(record["breaks"], list) or not isinstance(
            record["block_minutes"], list
        ):
            raise ValueError("Timing collections must be arrays.")
        breaks = []
        for value in record["breaks"]:
            pause = document_fields(value, {"start", "end", "name"})
            if (
                type(pause["start"]) is not int
                or type(pause["end"]) is not int
                or (pause["name"] is not None and not isinstance(pause["name"], str))
            ):
                raise ValueError("Invalid break fields.")
            breaks.append(
                TimedBreak(MinuteInterval(pause["start"], pause["end"]), pause["name"])
            )
        span = record["shift_minutes"]
        blocks = record["block_minutes"]
        equal, subtract = record["equal_blocks"], record["subtract_breaks"]
        if (
            type(span) is not int
            or any(type(n) is not int for n in blocks)
            or type(equal) is not bool
            or type(subtract) is not bool
        ):
            raise ValueError("Timing requires exact minutes and Boolean options.")
        return RotationTiming(span, tuple(breaks), tuple(blocks), equal, subtract)
    except (ValueError, TypeError, KeyError) as error:
        raise StoreFormatError("Invalid saved rotation timing.") from error


def encode_rotation_timing(timing: RotationTiming) -> str:
    """Encode one typed timing with stable primitive fields and no derived duplication.

    Args:
        timing: Complete validated relative-minute plan.

    Returns:
        Compact ASCII JSON containing only authoritative timing inputs.
    """
    return json.dumps(
        {
            "format": "ergotools.rotation-timing",
            "version": 1,
            "shift_minutes": timing.shift_minutes,
            "breaks": [
                {"start": b.interval.start, "end": b.interval.end, "name": b.name}
                for b in timing.breaks
            ],
            "block_minutes": timing.block_minutes,
            "equal_blocks": timing.equal_blocks,
            "subtract_breaks": timing.subtract_breaks,
        },
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class RotationTimingStore:
    """Borrow project storage; caller owns connection, transaction and publication."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Retain the borrowed owner-thread connection without reading or writing.

        Args:
            connection: Existing validated project connection.

        Returns:
            None; no schema creation or transaction starts.
        """
        self._connection = connection

    def read(self) -> tuple[ShiftTimingTemplate, ...]:
        """Read typed templates in deterministic Shift identity order.

        Args:
            None.

        Returns:
            Complete catalog; empty means no reusable timings have been accepted.

        Raises:
            sqlite3.Error: Schema/read fails.
            StoreFormatError: Saved owner or timing is malformed.
        """
        try:
            return tuple(
                ShiftTimingTemplate(identity, decode_rotation_timing(payload))
                for identity, payload in self._connection.execute(
                    "SELECT shift_id,payload FROM "
                    "shift_timing_templates ORDER BY shift_id"
                )
            )
        except ValueError as error:
            raise StoreFormatError("Invalid saved Shift timing owner.") from error

    def replace_in_transaction(
        self,
        shift_id: str,
        expected: RotationTiming | None,
        replacement: RotationTiming | None,
        hierarchy: WorkHierarchy,
    ) -> None:
        """Check current owner/value under the write lock and replace one template.

        Args:
            shift_id: Exact project-wide owner; unknown identities are rejected.
            expected: Exact prior timing; None requires absence.
            replacement: Validated timing, or None for explicit removal.
            hierarchy: Current organization for membership/span checks.

        Returns:
            None after one write or an exact no-op; caller owns rollback/commit.

        Raises:
            RuntimeError: Caller has no write transaction.
            ValueError: Owner/value is stale, missing or incompatible with Shift clocks.
            sqlite3.Error: Read/write fails; caller must roll back.
            StoreFormatError: Existing timing payload is malformed.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Timing replacement requires a project transaction.")
        if shift_id not in hierarchy.work.shifts:
            raise ValueError("Select an existing Shift.")
        current = next((t.timing for t in self.read() if t.shift_id == shift_id), None)
        if current != expected:
            raise ValueError("Shift timing changed; reload before editing.")
        if replacement is not None:
            ShiftTimingTemplate(shift_id, replacement).validate(hierarchy)
        if current == replacement:
            return
        if replacement is None:
            self._connection.execute(
                "DELETE FROM shift_timing_templates WHERE shift_id=?", (shift_id,)
            )
        else:
            self._connection.execute(
                "INSERT INTO shift_timing_templates VALUES (?,?) ON CONFLICT(shift_id) "
                "DO UPDATE SET payload=excluded.payload",
                (shift_id, encode_rotation_timing(replacement)),
            )
