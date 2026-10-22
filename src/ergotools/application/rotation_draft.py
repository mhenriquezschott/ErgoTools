"""Retained JROT project drafts and exact complete-scheme preparation.

Application layer. Incomplete grids survive window closure in the project session;
the existing native schema still stores complete schemes only. Save validates this
contract instead of dropping partial rows or introducing draft/history tables.
"""

from dataclasses import dataclass, replace

from ergotools.application.rotation_access import RotationRepository
from ergotools.application.rotation_history import RotationEditState
from ergotools.application.rotation_pool import rotation_pool
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import RotationMode, RotationScheme


@dataclass(frozen=True, slots=True)
class RotationProjectDraft:
    """Retain scheme identity, partial choices and frozen scientific provenance.

    Attributes:
        scheme_id: Literal entered identity, possibly blank while editing.
        state: Exact partial grid and scope without widgets or mutable state.
        loaded: Original complete scheme metadata, or None for a newly entered scheme.
    """

    scheme_id: str
    state: RotationEditState
    loaded: RotationScheme | None

    @property
    def data_token(self) -> object:
        """Separate persistable intent from view-only risk-tool selection.

        Args:
            None.

        Returns:
            Immutable data identity; display tool and pending scope do not make the
            project dirty by themselves.
        """
        return (
            self.scheme_id,
            self.state.cells,
            self.state.scope,
            self.state.mode,
            self.state.primary_kind,
        )

    @property
    def has_data(self) -> bool:
        """Distinguish an untouched empty editor from entered project content.

        Args:
            None.

        Returns:
            True when a scheme ID or any worker/target choice has been entered.
        """
        return bool(self.scheme_id) or any(any(row) for row in self.state.cells)

    def scheme(self) -> RotationScheme:
        """Prepare the same complete scheme as the original table's Save operation.

        Args:
            None.

        Returns:
            Validated complete scheme with frozen workers, targets and provenance.

        Raises:
            DraftError: Identity or a row/block choice is missing. No row is omitted.
            ValueError: Complete source identities/provenance are invalid.
            KeyError: A chosen key is absent from the retained frozen pool.
        """
        if not self.scheme_id or any(
            any(key is None for key in row) for row in self.state.cells
        ):
            raise DraftError(
                InputIssue("project.rotation_draft_incomplete", "rotation")
            )
        workers = {
            worker.link.worker_id: worker.link for worker in self.state.pool.workers
        }
        targets = {
            target.target.key: target.target for target in self.state.pool.targets
        }
        links = []
        rotations = []
        keys: list[str] = []
        for row in self.state.cells:
            worker_id = row[0]
            assert worker_id is not None
            selected = tuple(key for key in row[1:] if key is not None)
            links.append(workers[worker_id])
            rotations.append(WorkerRotation(worker_id, selected))
            keys.extend(selected)
        return RotationScheme(
            self.state.pool.project_id,
            self.scheme_id,
            self.loaded.name
            if self.loaded and self.loaded.scheme_id == self.scheme_id
            else self.scheme_id,
            tuple(links),
            tuple(targets[key] for key in dict.fromkeys(keys)),
            tuple(rotations),
            self.state.scope,
            self.state.mode or RotationMode.MANUAL,
            self.state.primary_kind,
            self.loaded.description
            if self.loaded and self.loaded.scheme_id == self.scheme_id
            else None,
        )


def refresh_rotation_draft(
    repository: RotationRepository, draft: RotationProjectDraft
) -> RotationProjectDraft:
    """Refresh current Job values without altering retained worker/target choices.

    Args:
        repository: Borrowed current project catalog reader.
        draft: Partial or complete retained scheme, possibly closed while Jobs changed.

    Returns:
        Draft with current Job/tool values and unchanged arrangements. Changed numeric
        outputs remove optimization provenance; metadata/unit/source changes alone do
        not claim a different numerical optimum. No solver or repository write occurs.

    Raises:
        ValueError: Current risks have foreign ownership or invalid Job parents.
        KeyError: A retained target's Job has been removed outside guarded editing.
    """
    jobs = repository.load_jobs()
    risks = repository.load_job_risk()
    risks.validate_jobs(jobs)
    names = {job.job_id: job.name for job in jobs.jobs}
    fresh = rotation_pool(repository, draft.state.scope)
    selected_workers = {row[0] for row in draft.state.cells if row[0] is not None}
    selected_targets = {
        key for row in draft.state.cells for key in row[1:] if key is not None
    }
    targets = {target.target.key: target for target in fresh.targets}
    for target in draft.state.pool.targets:
        if target.target.key in selected_targets:
            targets[target.target.key] = replace(
                target,
                job_name=names[target.target.job_id],
                values=risks.for_job(target.target.job_id),
            )
    workers = {worker.link.worker_id: worker for worker in fresh.workers}
    for worker in draft.state.pool.workers:
        if worker.link.worker_id in selected_workers:
            updated_worker = workers.get(worker.link.worker_id, worker)
            workers[worker.link.worker_id] = replace(updated_worker, link=worker.link)
    numeric_changed = any(
        {
            (m.kind, m.cumulative_damage, m.probability_percent)
            for m in target.values.measurements
        }
        != {
            (m.kind, m.cumulative_damage, m.probability_percent)
            for m in targets[target.target.key].values.measurements
        }
        for target in draft.state.pool.targets
        if target.target.key in selected_targets
    )
    pool = replace(
        fresh, workers=tuple(workers.values()), targets=tuple(targets.values())
    )
    state = replace(draft.state, pool=pool)
    if numeric_changed:
        state = replace(
            state, mode=RotationMode.MANUAL, primary_kind=None, manual_edit=True
        )
    return replace(draft, state=state)


def stage_rotation_draft(repository: RotationRepository, value: object | None) -> None:
    """Prepare a complete accepted draft for the sole project Save boundary.

    Args:
        repository: Borrowed private project repository; native writes remain in memory.
        value: Retained JROT draft, or None before opening the editor.

    Returns:
        None; exact complete schemes are staged only when changed. No durable commit
        occurs, and repository reference validation remains authoritative.

    Raises:
        DraftError: Entered draft is incomplete.
        ValueError: Complete draft has invalid frozen references.
    """
    if isinstance(value, RotationProjectDraft) and value.has_data:
        candidate = refresh_rotation_draft(repository, value).scheme()
        if candidate not in repository.load_rotation_schemes():
            repository.save_rotation_scheme(candidate)
