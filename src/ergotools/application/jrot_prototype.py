"""Disposable developer JROT data and calculations; no persistence capability.

Application layer. Copy immutable catalog values through read-only ports, keep temporary
Job/task names separately from production DTOs, and prepare the unchanged optimizer.
No repository is retained by a session; no schema, settings, history or file is written.
"""

from dataclasses import dataclass, field, replace
from statistics import mean, pstdev

from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.rotation_pool import RotationPoolReader
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem, project_model_input
from ergotools.domain.rotation import RotationProblem, RotationRisk, WorkerRotation
from ergotools.domain.work_hierarchy import WorkHierarchy


@dataclass(frozen=True, slots=True)
class PrototypeCatalog:
    """Detached source snapshot, never a writable project handle.

    Attributes:
        title: Source project caption or explicit sample caption.
        hierarchy: Existing immutable organization/workers, absent without a project.
        jobs: Existing immutable Job/placement catalog, absent without a project.
        risks: Existing immutable current Job values, absent without a project.
    """

    title: str
    hierarchy: WorkHierarchy | None = None
    jobs: JobCatalog | None = None
    risks: JobRiskCatalog | None = None


def read_prototype_catalog(reader: RotationPoolReader, title: str) -> PrototypeCatalog:
    """Detach the three existing catalogs without retaining any mutation port.

    Args:
        reader: Borrowed read-only catalog capability; called on its owner thread.
        title: Literal source project caption.

    Returns:
        Immutable snapshot; the prototype never receives the reader itself.
    """
    return PrototypeCatalog(
        title, reader.load_hierarchy(), reader.load_jobs(), reader.load_job_risk()
    )


@dataclass(slots=True)
class PrototypeJob:
    """One temporary Job copy or explicit sample, discarded with its dialog.

    Attributes:
        key: Session-local identity, never a project Job/assessment creation request.
        name: Editable temporary display name.
        origin: Visible Project, Sample or Entered source caption.
        measurements: Detached per-tool sources/results; source edits replace entries.
        task_names: Temporary names keyed by stable task ID, without codec changes.
        skipped: Tools intentionally not assessed for this demonstration.
    """

    key: str
    name: str
    origin: str
    measurements: dict[AssessmentKind, JobRiskMeasurement] = field(default_factory=dict)
    task_names: dict[str, str] = field(default_factory=dict)
    skipped: set[AssessmentKind] = field(default_factory=set)

    def status(self, kinds: tuple[AssessmentKind, ...]) -> str:
        """Derive Job progress from usable values, never a stored completion flag.

        Args:
            kinds: Nonempty tools requested by the current prototype analysis.

        Returns:
            Ready, In progress or Not entered; skipped never substitutes zero.
        """
        complete = sum(
            kind not in self.skipped
            and kind in self.measurements
            and self.measurements[kind].complete
            for kind in kinds
        )
        if complete == len(kinds):
            return "Ready"
        return "In progress" if self.measurements or self.skipped else "Not entered"


def metric_prototype_source(source: AssessmentDraft) -> AssessmentDraft:
    """Copy dimensional tasks to cm/N using the existing unit projection policy.

    Args:
        source: Original Job source, never mutated or saved by the prototype.

    Returns:
        Metric copy, retaining task IDs, repetitions and explicit ST convention.
    """
    if isinstance(source, DuetDraft):
        return source
    tasks = tuple(
        replace(
            task,
            lever_arm=project_model_input(
                task.lever_arm,
                "lever_arm",
                task.task_id,
                source.system,
                MeasurementSystem.METRIC,
            ),
            load=project_model_input(
                task.load, "load", task.task_id, source.system, MeasurementSystem.METRIC
            ),
        )
        for task in source.tasks
    )
    if isinstance(source, LifftDraft):
        return replace(
            source,
            system=MeasurementSystem.METRIC,
            tasks=tuple(task for task in tasks if isinstance(task, LifftTask)),
        )
    return replace(
        source,
        system=MeasurementSystem.METRIC,
        tasks=tuple(task for task in tasks if isinstance(task, TstTask)),
    )


def sample_prototype_job(index: int) -> PrototypeJob:
    """Build explicitly labeled, fully calculated metric sample tasks for a demo.

    Args:
        index: Zero-based sample selection; four patterns repeat for larger examples.

    Returns:
        Private calculated Job; existing scientific evaluators supply every result.
    """
    position = index % 4
    names = ("Wire cutting", "Assembly", "Inspection", "Packing")
    arm = (30.0, 45.0, 55.0, 25.0)[position]
    load = (49.05, 100.0, 150.0, 75.0)[position]
    reps = (100.0, 500.0, 1000.0, 300.0)[position]
    key = f"sample-{index + 1}"
    sources: tuple[AssessmentDraft, ...] = (
        LifftDraft(MeasurementSystem.METRIC, (LifftTask(key + "-l", arm, load, reps),)),
        DuetDraft((DuetTask(key + "-d", (2, 4, 6, 8)[position], 700.0),)),
        TstDraft(
            MeasurementSystem.METRIC,
            (TstTask(key + "-s", TstDirection.HANDLING_LOADS, arm, load, reps),),
        ),
    )
    job = PrototypeJob(key, names[position], "Sample")
    for kind, source in zip(AssessmentKind, sources, strict=True):
        job.measurements[kind] = calculate_job_measurement(
            "developer-prototype", key, source, MeasurementSystem.METRIC
        )
        job.task_names[source.tasks[0].task_id] = names[position] + " task"
    return job


def project_prototype_jobs(catalog: PrototypeCatalog) -> tuple[PrototypeJob, ...]:
    """Copy active project Jobs; calculations/metric conversion remain disposable.

    Args:
        catalog: Detached project catalogs, or the empty/sample snapshot.

    Returns:
        Temporary Jobs. Direct values remain exact; dimensional task sources are
        recalculated only in the prototype after metric conversion, never in storage.
    """
    if catalog.jobs is None:
        return ()
    result = []
    for job in catalog.jobs.jobs:
        if not job.active:
            continue
        copied = PrototypeJob(
            "project-" + job.job_id, job.name or job.job_id, "Project"
        )
        values = catalog.risks.for_job(job.job_id) if catalog.risks else None
        if values is not None:
            for measurement in values.measurements:
                if measurement.source is not None:
                    source = metric_prototype_source(measurement.source)
                    if measurement.complete:
                        measurement = calculate_job_measurement(
                            "developer-prototype",
                            copied.key,
                            source,
                            MeasurementSystem.METRIC,
                        )
                    else:
                        measurement = JobRiskMeasurement(
                            measurement.kind, source=source
                        )
                copied.measurements[measurement.kind] = measurement
        result.append(copied)
    return tuple(result)


@dataclass(slots=True)
class PrototypeSession:
    """Mutable window-owned scratch state, without history or persistence.

    Attributes:
        jobs: Selected temporary Job copies, one per participating worker.
        workers: Selected stable project IDs or explicitly labeled temporary IDs.
        worker_names: Literal display captions keyed by those session IDs.
        current: Accepted baseline cells; changes invalidate solution in the view.
        restrictions: Display-only worker rules; deliberately absent from solver input.
    """

    jobs: list[PrototypeJob] = field(default_factory=list)
    workers: list[str] = field(default_factory=list)
    worker_names: dict[str, str] = field(default_factory=dict)
    current: tuple[WorkerRotation, ...] = ()
    restrictions: list[tuple[str, str, str]] = field(default_factory=list)

    def problem(
        self, kinds: tuple[AssessmentKind, ...], seconds: float
    ) -> RotationProblem:
        """Validate equal-block complete staffing and supply current tool coefficients.

        Args:
            kinds: Exactly one tool or all three; pairs are intentionally unavailable.
            seconds: Existing solver per-stage wall-time limit in seconds.

        Returns:
            Immutable original optimization input. Restrictions are preview-only.

        Raises:
            ValueError: Tools, staffing, cells or calculations are invalid.
        """
        if len(kinds) not in (1, 3) or len(set(kinds)) != len(kinds):
            raise ValueError("Choose one tool or all three tools for this prototype.")
        if (
            not self.jobs
            or len(self.jobs) != len(self.workers)
            or len({job.key for job in self.jobs}) != len(self.jobs)
            or len(set(self.workers)) != len(self.workers)
            or tuple(row.worker_id for row in self.current) != tuple(self.workers)
        ):
            raise ValueError("Choose unique workers and Jobs, with one worker per Job.")
        keys = {job.key for job in self.jobs}
        if not self.current or len({len(row.target_keys) for row in self.current}) != 1:
            raise ValueError("Complete the current rotation matrix first.")
        for block in range(len(self.current[0].target_keys)):
            if {row.target_keys[block] for row in self.current} != keys:
                raise ValueError(
                    f"Block {block + 1}: assign exactly one worker per Job."
                )
        risks = []
        for job in self.jobs:
            for kind in kinds:
                value = job.measurements.get(kind)
                if kind in job.skipped or value is None or not value.complete:
                    raise ValueError(f"Calculate {kind.value} for {job.name} first.")
                assert value.probability_percent is not None
                risks.append(RotationRisk(job.key, kind, value.probability_percent))
        return RotationProblem(self.current, tuple(risks), seconds)

    def dispose(self) -> None:
        """Drop all accepted scratch inputs when the window closes.

        Args:
            None.

        Returns:
            None; never call a project or preference mutation operation.
        """
        self.jobs.clear()
        self.workers.clear()
        self.worker_names.clear()
        self.current = ()
        self.restrictions.clear()


def prototype_worker_values(
    schedule: tuple[WorkerRotation, ...], jobs: list[PrototypeJob], kind: AssessmentKind
) -> tuple[float, ...]:
    """Evaluate the unchanged JROT equal-block average, independently of the widgets.

    Args:
        schedule: Complete accepted baseline or independently validated solver output.
        jobs: Current temporary measurements, not a database reader.
        kind: Complete tool whose probability is displayed on the 0-100 scale.

    Returns:
        One unrounded average per worker; never an individual injury prediction.

    Raises:
        ValueError: A requested calculated probability is missing.
    """
    values: dict[str, float] = {}
    for job in jobs:
        probability = job.measurements[kind].probability_percent
        if probability is None:
            raise ValueError("Complete calculated values are required.")
        values[job.key] = probability
    return tuple(mean(values[key] for key in row.target_keys) for row in schedule)


def prototype_statistics(
    values: tuple[float, ...],
) -> tuple[float, float, float, float]:
    """Summarize worker schedule averages in percentage points, using population SD.

    Args:
        values: Nonempty complete worker averages, not heterogeneous tool mixtures.

    Returns:
        Mean, maximum, population SD and max-minus-min range in that order.
    """
    return mean(values), max(values), pstdev(values), max(values) - min(values)
