"""Current named rotation catalog over the existing rotation_schemes table.

Infrastructure layer. Old rows keep their bytes, identities and timestamps. Guided rows
have a distinct strict codec and expected-state writes. The project owns transactions,
reference validation, history and publication; reading never creates scenarios or dates.
"""

import sqlite3

from ergotools.application.rotation_scenarios import (
    scenario_from_scheme,
    scenario_order,
)
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.rotation_scenario import RotationScenario
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_preferences_store import (
    read_last_rotation,
    write_last_rotation,
)
from ergotools.infrastructure.rotation_scenario_serialization import (
    decode_scenario,
    encode_scenario,
    is_scenario_payload,
)
from ergotools.infrastructure.rotation_scheme_store import _decode


class RotationScenarioStore:
    """Borrow rotation storage; the project retains transactions and lifetime."""

    def __init__(self, connection: sqlite3.Connection, project_id: str) -> None:
        """Retain borrowed owner-thread storage and exact project identity.

        Args:
            connection: Borrowed validated current project connection.
            project_id: Stable owning project identity.

        Returns:
            None; no reads, writes or schema creation.
        """
        self.connection, self.project_id = connection, project_id

    def read(self, *, guided_only: bool = False) -> tuple[RotationScenario, ...]:
        """Read current and compatible older plans without inferring missing metadata.

        Args:
            guided_only: True returns only records using the guided codec.

        Returns:
            Case-insensitive name/ID ordered typed records; no fallback is persisted.

        Raises:
            StoreFormatError: Payload or row/project identity is invalid.
            sqlite3.Error: Rotation rows cannot be read.
        """
        result = []
        try:
            for identity, payload in self.connection.execute(
                "SELECT scheme_id,payload FROM rotation_schemes"
            ):
                guided = is_scenario_payload(payload)
                scenario = (
                    decode_scenario(payload)
                    if guided
                    else scenario_from_scheme(_decode(payload))
                )
                if (
                    scenario.project_id != self.project_id
                    or scenario.scenario_id != identity
                ):
                    raise ValueError("Saved rotation identity does not match its row.")
                if guided or not guided_only:
                    result.append(scenario)
        except (ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
            raise StoreFormatError("Invalid saved rotation scenario.") from error
        return tuple(sorted(result, key=scenario_order))

    def replace_in_transaction(
        self,
        expected: RotationScenario | None,
        replacement: RotationScenario | None,
        hierarchy: WorkHierarchy,
        jobs: JobCatalog,
    ) -> None:
        """Accept one guarded edit and coherent selection under the write lock.

        Args:
            expected: Latest exact record, or None for creation.
            replacement: New complete draft/run record, or None for explicit deletion.
            hierarchy: Current owning hierarchy for draft membership checks.
            jobs: Current Jobs/placements/assignments, never rewritten here.

        Returns:
            None; accepted creation selects the new identity, deleting the active record
            clears selection, and other edits preserve the independent view state.

        Raises:
            RuntimeError: No caller transaction is active.
            ValueError: Identity, ownership or expected state is invalid/stale.
            sqlite3.Error: Writing fails; caller must roll back.
            StoreFormatError: Existing records are invalid.
        """
        if not self.connection.in_transaction:
            raise RuntimeError(
                "Rotation scenario writes require a project transaction."
            )
        if expected is None and replacement is None:
            raise ValueError(
                "A scenario edit requires an expected or replacement record."
            )
        identity = (
            replacement.scenario_id
            if replacement is not None
            else expected.scenario_id
            if expected is not None
            else ""
        )
        if expected is not None and expected.scenario_id != identity:
            raise ValueError("A rotation identity cannot change during editing.")
        current = next((s for s in self.read() if s.scenario_id == identity), None)
        if current != expected:
            raise ValueError("Rotation changed; reload before editing.")
        if replacement is not None:
            if (
                replacement.project_id != self.project_id
                or hierarchy.work.project_id != self.project_id
                or jobs.project_id != self.project_id
            ):
                raise ValueError("Rotation belongs to a different project.")
            if (
                replacement.inputs.planned_date is None
                and replacement.legacy_mode is None
            ):
                raise ValueError("A new rotation requires its planned local date.")
            replacement.inputs.validate_references(hierarchy, jobs)
        if current == replacement:
            return
        if replacement is None:
            self.connection.execute(
                "DELETE FROM rotation_schemes WHERE scheme_id=?", (identity,)
            )
            if read_last_rotation(self.connection) == identity:
                write_last_rotation(self.connection, None)
        else:
            self.connection.execute(
                "INSERT INTO rotation_schemes(scheme_id,payload) VALUES (?,?) "
                "ON CONFLICT(scheme_id) DO UPDATE SET payload=excluded.payload,"
                "updated_at=CURRENT_TIMESTAMP",
                (identity, encode_scenario(replacement)),
            )
            if current is None:
                write_last_rotation(self.connection, identity)


def validate_scenario_job_change(
    scenario: RotationScenario, current: JobCatalog, replacement: JobCatalog
) -> None:
    """Protect current referenced assignment/placement ownership through catalog edits.

    Args:
        scenario: Saved guided plan; frozen old run labels/inputs are independent
            evidence.
        current: Previously validated catalog.
        replacement: Proposed complete replacement catalog.

    Returns:
        None; descriptions/activity may change without rewriting referenced ownership.

    Raises:
        ValueError: A referenced assignment or placement is deleted/reowned.
    """
    before = {a.assignment_id: a for a in current.assignments}
    after = {a.assignment_id: a for a in replacement.assignments}
    old_places = {p.placement_id: p for p in current.placements}
    new_places = {p.placement_id: p for p in replacement.placements}
    for worker in scenario.inputs.workers:
        if worker.assignment_id is not None:
            old, new = before.get(worker.assignment_id), after.get(worker.assignment_id)
            if (
                old is None
                or new is None
                or (old.worker, old.placement_id) != (new.worker, new.placement_id)
            ):
                raise ValueError("Rotation references the original worker assignment.")
    for target in scenario.inputs.targets:
        if target.placement_id is not None:
            old_place, new_place = (
                old_places.get(target.placement_id),
                new_places.get(target.placement_id),
            )
            if (
                old_place is None
                or new_place is None
                or (old_place.job_id, old_place.workplace)
                != (new_place.job_id, new_place.workplace)
            ):
                raise ValueError("Rotation references the original Job placement.")
