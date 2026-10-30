"""Read-only worker and Job catalogs for the shared assessment-copy picker.

Presentation layer. Adapt existing workspace snapshots into immutable picker rows.
Worker contexts retain real standalone/assignment ownership; Job values are global
per Job/tool. Acceptance rechecks source values without calculation or linking.
The destination Job window owns confirmation, persistence and shared history.
"""

from collections.abc import Mapping
from contextlib import suppress

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_copy_picker import (
    CopyCandidate,
    CopySource,
    JobValuePicker,
)


class JobAssessmentDialog(JobValuePicker):
    """Browse each worker's standalone and real workplace assessment contexts."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        kind: AssessmentKind,
        icons: Mapping[str, QIcon],
        language: Language,
        parent: QWidget | None = None,
        *,
        convention: DecimalConvention = DecimalConvention.POINT,
    ) -> None:
        """Read worker/context catalogs without navigating the main assessment editor.

        Args:
            workspace: Borrowed read-only project capabilities; caller owns lifetime.
            kind: Exact tool requested by the destination Job.
            icons: Packaged navigation and workplace icons.
            language: UI wording only; names remain literal.
            parent: Job window owning replacement consent/history.
            convention: Explicit decimal separator for result display.

        Returns:
            None; missing/stale results remain visible but cannot be copied.
        """
        hierarchy = workspace.read_hierarchy().hierarchy.work
        catalog = workspace.read_jobs().jobs
        history = workspace.read_history().history
        assignments = {a.assignment_id: a for a in catalog.assignments}
        placements = {p.placement_id: p for p in catalog.placements}
        jobs = {j.job_id: j for j in catalog.jobs}
        sources = []
        spanish = language is Language.SPANISH
        for worker in hierarchy.workers:
            candidates = []
            for entry in history.entries:
                if entry.kind is not kind or entry.worker_id != worker.worker_id:
                    continue
                measurement = None
                with suppress(ValueError):
                    measurement = workspace.job_measurement_from_assessment(
                        entry.document_id
                    )
                job_caption = ""
                shift = ""
                path: tuple[str, ...] = (
                    "Evaluación independiente" if spanish else "Standalone assessment",
                )
                if entry.assignment_id is not None:
                    assignment = assignments[entry.assignment_id]
                    place = assignment.worker.workplace
                    placement = (
                        placements.get(assignment.placement_id)
                        if assignment.placement_id is not None
                        else None
                    )
                    job_caption = (
                        ("Sin trabajo" if spanish else "No Job")
                        if placement is None
                        else f"{placement.job_id} · {jobs[placement.job_id].name}"
                    )
                    shift = place.shift_id
                    path = (
                        place.plant_name,
                        place.section_name,
                        place.line_name,
                        place.station_id,
                        ("Turno " if spanish else "Shift ") + shift,
                    )
                candidates.append(
                    CopyCandidate(
                        entry.document_id, path, job_caption, shift, measurement
                    )
                )
            caption = ", ".join(
                part for part in (worker.last_name, worker.first_name) if part
            )
            sources.append(CopySource(worker.worker_id, caption, tuple(candidates)))
        super().__init__(
            tuple(sources),
            kind,
            icons,
            language,
            convention,
            workspace.job_measurement_from_assessment,
            worker_sources=True,
            project_id=catalog.project_id,
            units=workspace.project_metadata.default_units
            if workspace.project_metadata
            else MeasurementSystem.METRIC,
            parent=parent,
        )


class JobCopyDialog(JobValuePicker):
    """Browse other Jobs and recheck their selected-tool values at acceptance."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        kind: AssessmentKind,
        icons: Mapping[str, QIcon],
        language: Language,
        exclude_job: str,
        parent: QWidget | None = None,
        *,
        convention: DecimalConvention = DecimalConvention.POINT,
    ) -> None:
        """Build independent Job-source choices without exposing a second main selector.

        Args:
            workspace: Borrowed open-project capabilities; no write operation is used.
            kind: Exact tool requested by the destination Job.
            icons: Packaged navigation/hierarchy icons.
            language: Interface wording, never stored identities.
            exclude_job: Destination identity omitted from source choices.
            parent: Destination window owning replacement consent and replay.
            convention: Explicit decimal separator for display only.

        Returns:
            None; Jobs without a current measurement cannot be copied.
        """
        self._workspace = workspace
        self._kind = kind
        catalog = workspace.read_jobs().jobs
        risk = workspace.read_job_risk().risk
        sources = []
        for job in catalog.jobs:
            if job.job_id == exclude_job:
                continue
            item = next(
                (m for m in risk.for_job(job.job_id).measurements if m.kind is kind),
                None,
            )
            caption = (
                "Valores del trabajo"
                if language is Language.SPANISH
                else "Job assessment values"
            )
            sources.append(
                CopySource(
                    job.job_id,
                    job.name,
                    (CopyCandidate(job.job_id, (caption,), job.name, "", item),),
                )
            )
        super().__init__(
            tuple(sources),
            kind,
            icons,
            language,
            convention,
            self._resolve_job,
            worker_sources=False,
            project_id=catalog.project_id,
            units=workspace.project_metadata.default_units
            if workspace.project_metadata
            else MeasurementSystem.METRIC,
            parent=parent,
        )

    def _resolve_job(self, identity: str) -> JobRiskMeasurement:
        """Recheck one selected-tool measurement without writing or calculating.

        Args:
            identity: Exact selected source Job identity.

        Returns:
            Current immutable inputs and outputs for that Job/tool.

        Raises:
            ValueError: The Job has no current value for the selected tool.
        """
        value = next(
            (
                m
                for m in self._workspace.read_job_risk()
                .risk.for_job(identity)
                .measurements
                if m.kind is self._kind
            ),
            None,
        )
        if value is None:
            raise ValueError("Source Job has no selected-tool data.")
        return value
