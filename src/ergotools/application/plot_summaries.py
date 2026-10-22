"""Read-only original PLOT summary calculations, independent of chart rendering.

Application layer. Prepare immutable analysis/history values through injected ports. Qt
controls, chart rendering, SQL transactions and user consent remain outside this module;
only explicitly supplied persistence callbacks can write.
"""

from dataclasses import dataclass
from math import fsum, isfinite, sqrt

from ergotools.application.plot_results import PlotResults, PlotWorkerResult
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.work_catalog import StationKey


@dataclass(frozen=True, slots=True)
class RiskAverage:
    """Observed percentage mean and population deviation, never standard error.

    Missing values do not become zero observations.

    Attributes:
        count: Number of available observations.
        mean_percent: Mean on 0-100 scale, or None when count is zero.
        deviation_percent: Population standard deviation in percentage points, or None
            when count is zero.
    """

    count: int
    mean_percent: float | None
    deviation_percent: float | None


def risk_average(values: tuple[float, ...]) -> RiskAverage:
    """Return source arithmetic mean and population (N) standard deviation.

    Args:
        values: Observed finite outcome percentages on 0-100 scale; zero is valid and
            missing observations are excluded.

    Returns:
        Count, arithmetic mean and population standard deviation in percent; empty
        observations yield None quantities.

    Raises:
        ValueError: An observation is boolean, nonnumeric, nonfinite or outside 0-100.
    """
    if any(
        type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 100
        for value in values
    ):
        raise ValueError("PLOT risk observations must be finite percentages in 0-100.")
    if not values:
        return RiskAverage(0, None, None)
    mean = fsum(values) / len(values)
    return RiskAverage(
        len(values),
        mean,
        sqrt(fsum((value - mean) ** 2 for value in values) / len(values)),
    )


@dataclass(frozen=True, slots=True)
class WorkerSummary:
    """Selected-tool enabled assignment statistics.

    Age uses current year minus birth year; paired differences use the same
    individual/job observations.

    Attributes:
        total: Enabled selected-tool assignment row count, including absent numeric
            results.
        average_age: Mean known year-based age, or None.
        males: Rows with literal Male category.
        females: Rows with literal Female category.
        male_damage: Mean available male dimensionless damage, or None.
        female_damage: Mean available female dimensionless damage, or None.
        male_risk: Available male risk percentage statistics.
        female_risk: Available female risk percentage statistics.
        damage: Mean available dimensionless damage across selected rows.
        risk: Available selected-row risk percentage statistics.
        comparable_count: Rows with both individual and applicable job probability.
        applicable_job_risk_percent: Mean job risk for the paired population only, or
            None.
        difference_percentage_points: Mean individual minus job risk for paired rows, or
            None.
    """

    total: int
    average_age: float | None
    males: int
    females: int
    male_damage: float | None
    female_damage: float | None
    male_risk: RiskAverage
    female_risk: RiskAverage
    damage: float | None
    risk: RiskAverage
    comparable_count: int
    applicable_job_risk_percent: float | None
    difference_percentage_points: float | None


@dataclass(frozen=True, slots=True)
class JobSummary:
    """Placement-weighted selected-tool job statistics and exact identity counts.

    Attributes:
        unique_jobs: Distinct active job identities in scope.
        placements: Active scoped placement row count.
        positioned_stations: Unique scoped stations with a saved anchor.
        unpositioned_stations: Unique scoped stations without a saved anchor.
        jobs_with_risks: Distinct Jobs with current complete selected-tool values.
        damage: Placement-weighted mean available dimensionless damage, or None.
        risk: Placement-weighted observed risk percent statistics.
        minimum_risk_percent: Minimum observed percent, or None.
        maximum_risk_percent: Maximum observed percent, or None.
    """

    unique_jobs: int
    placements: int
    positioned_stations: int
    unpositioned_stations: int
    jobs_with_risks: int
    damage: float | None
    risk: RiskAverage
    minimum_risk_percent: float | None
    maximum_risk_percent: float | None


@dataclass(frozen=True, slots=True)
class ToolRiskGroup:
    """One tool chart series and optional literal grouping category.

    Attributes:
        kind: Scientific tool identity.
        group: Literal sex or decade label, or None for overall tool series.
        risk: Available observed percentage statistics for the group.
    """

    kind: AssessmentKind
    group: str | None
    risk: RiskAverage


@dataclass(frozen=True, slots=True)
class PlacedJobRisk:
    """One unique-job chart bar retaining its active placement multiplicity.

    Attributes:
        job_id: Exact job identity used for grouping.
        placement_count: Number of active placements of that job in the selected scope.
        risk_percent: First available approved tool risk percent for the job, or None.
        damage: First available approved dimensionless damage for the job, or None.
    """

    job_id: str
    placement_count: int
    risk_percent: float | None
    damage: float | None


@dataclass(frozen=True, slots=True)
class PlotSummary:
    """Read-only selected-tool totals and all-tool chart datasets.

    Attributes:
        workers: Enabled selected-tool worker statistics.
        jobs: Scoped placed-job statistics.
        tools: One overall risk group per scientific tool.
        sexes: Male/Female risk groups per tool.
        ages: Observed decade-bin groups per tool, retaining empty intermediate bins.
        placed_jobs: Unique-job bars in exact job-ID order.
    """

    workers: WorkerSummary
    jobs: JobSummary
    tools: tuple[ToolRiskGroup, ...]
    sexes: tuple[ToolRiskGroup, ...]
    ages: tuple[ToolRiskGroup, ...]
    placed_jobs: tuple[PlacedJobRisk, ...]


def _mean(values: tuple[float, ...]) -> float | None:
    """Pure helper; no rounding or denominator padding.

    Args:
        values: Available numeric observations with a shared scale; missing observations
            already excluded.

    Returns:
        Accurately summed arithmetic mean, or None for no observations.
    """
    return fsum(values) / len(values) if values else None


def _risks(rows: tuple[PlotWorkerResult, ...]) -> tuple[float, ...]:
    """No writes or gauge clipping.

    Args:
        rows: Saved worker assessment summaries; missing probability remains excluded.

    Returns:
        Available probabilities projected from 0-1 to percent, preserving observed
        zeros.
    """
    return tuple(
        row.assessment.probability * 100
        for row in rows
        if row.assessment.probability is not None
    )


def _damage(rows: tuple[PlotWorkerResult, ...]) -> float | None:
    """Average available dimensionless worker damage without substituting zeros.

    Args:
        rows: Saved worker assessment summaries; absent damage is excluded.

    Returns:
        Mean dimensionless cumulative damage, or None when no observation is available.
    """
    return _mean(
        tuple(
            row.assessment.total_damage
            for row in rows
            if row.assessment.total_damage is not None
        )
    )


def _sex(row: PlotWorkerResult) -> str | None:
    """Read the literal saved sex category without translating user data.

    Args:
        row: Worker result containing optional demographic details.

    Returns:
        Literal saved sex category, or None when details/category are absent.
    """
    return row.worker.details.sex if row.worker.details else None


def _age(row: PlotWorkerResult, current_year: int) -> int | None:
    """Preserve the original year-only policy rather than birthday-adjusted age.

    Args:
        row: Worker result with optional ISO birth date.
        current_year: Caller-supplied calendar year.

    Returns:
        Current year minus birth year, or None when birth date is absent.
    """
    details = row.worker.details
    return (
        current_year - int(details.birth_date[:4])
        if details and details.birth_date
        else None
    )


def summarize_plot(results: PlotResults, *, current_year: int) -> PlotSummary:
    """Aggregate saved enabled assignment results using reviewed source grouping.

    Hidden or unplaced workers remain included when enabled. Draft geometry/settings are
    not applied here; callers publish a new summary only from saved results.
    Missing/scientific-review evidence never becomes low/zero risk. Units do not affect
    dimensionless damage or outcome percentages. No project data is modified.

    Args:
        results: Complete saved PLOT dataset with saved marker enable flags.
        current_year: Positive integer calendar year used by the original age policy.

    Returns:
        Selected-tool worker/job statistics and all-tool/sex/decade/job chart series;
        missing evidence is excluded from numeric denominators.

    Raises:
        ValueError: Year or any observed risk percentage is invalid.
    """
    if type(current_year) is not int or current_year < 1:
        raise ValueError("PLOT summaries require a positive integer year.")

    def enabled(row: PlotWorkerResult) -> bool:
        """Test the saved marker enable flag.

        Visibility and position do not determine eligibility; only a disabled marker
        suppresses a summary row.

        Args:
            row: Saved worker result whose assignment marker is inspected.

        Returns:
            True for an absent marker or an explicitly enabled saved marker.
        """
        marker = results.positions.marker(row.assessment.assignment_id)
        return marker is None or marker.enabled

    rows = tuple(row for row in results.workers if enabled(row))
    all_rows = tuple(row for row in results.all_tools if enabled(row))
    males = tuple(row for row in rows if _sex(row) == "Male")
    females = tuple(row for row in rows if _sex(row) == "Female")
    ages = tuple(
        float(age) for row in rows if (age := _age(row, current_year)) is not None
    )
    pairs = tuple(
        (
            row.assessment.probability * 100,
            row.job_risk.measurement.probability_percent,
        )
        for row in rows
        if row.assessment.probability is not None
        and row.job_risk is not None
        and row.job_risk.measurement.probability_percent is not None
    )
    workers = WorkerSummary(
        len(rows),
        _mean(ages),
        len(males),
        len(females),
        _damage(males),
        _damage(females),
        risk_average(_risks(males)),
        risk_average(_risks(females)),
        _damage(rows),
        risk_average(_risks(rows)),
        len(pairs),
        _mean(tuple(job for _, job in pairs)),
        _mean(tuple(individual - job for individual, job in pairs)),
    )
    job_rows = results.jobs
    risks = tuple(
        row.risk.measurement.probability_percent
        for row in job_rows
        if row.risk is not None and row.risk.measurement.probability_percent is not None
    )
    damages = tuple(
        row.risk.measurement.cumulative_damage
        for row in job_rows
        if row.risk is not None and row.risk.measurement.cumulative_damage is not None
    )
    stations = {
        StationKey(
            row.placement.workplace.plant_name,
            row.placement.workplace.section_name,
            row.placement.workplace.line_name,
            row.placement.workplace.station_id,
        )
        for row in job_rows
    }
    positioned = {
        station
        for station in stations
        if results.positions.station_position(station) is not None
    }
    jobs = JobSummary(
        len({row.job.job_id for row in job_rows}),
        len(job_rows),
        len(positioned),
        len(stations - positioned),
        len({row.job.job_id for row in job_rows if row.risk is not None}),
        _mean(damages),
        risk_average(risks),
        min(risks) if risks else None,
        max(risks) if risks else None,
    )
    tools = tuple(
        ToolRiskGroup(
            kind,
            None,
            risk_average(
                _risks(tuple(row for row in all_rows if row.assessment.kind is kind))
            ),
        )
        for kind in AssessmentKind
    )
    sexes = tuple(
        ToolRiskGroup(
            kind,
            sex,
            risk_average(
                _risks(
                    tuple(
                        row
                        for row in all_rows
                        if row.assessment.kind is kind and _sex(row) == sex
                    )
                )
            ),
        )
        for sex in ("Male", "Female")
        for kind in AssessmentKind
    )
    age_values = tuple(
        age for row in all_rows if (age := _age(row, current_year)) is not None
    )
    starts = (
        range((min(age_values) // 10) * 10, (max(age_values) // 10 + 1) * 10, 10)
        if age_values
        else ()
    )
    age_groups = tuple(
        ToolRiskGroup(
            kind,
            f"{start}-{start + 9}",
            risk_average(
                _risks(
                    tuple(
                        row
                        for row in all_rows
                        if row.assessment.kind is kind
                        and (age := _age(row, current_year)) is not None
                        and start <= age < start + 10
                    )
                )
            ),
        )
        for kind in AssessmentKind
        for start in starts
    )
    placed_jobs = tuple(
        PlacedJobRisk(
            identity,
            sum(row.job.job_id == identity for row in job_rows),
            next(
                (
                    row.risk.measurement.probability_percent
                    for row in job_rows
                    if row.job.job_id == identity and row.risk is not None
                ),
                None,
            ),
            next(
                (
                    row.risk.measurement.cumulative_damage
                    for row in job_rows
                    if row.job.job_id == identity and row.risk is not None
                ),
                None,
            ),
        )
        for identity in sorted({row.job.job_id for row in job_rows})
    )
    return PlotSummary(workers, jobs, tools, sexes, age_groups, placed_jobs)


@dataclass(frozen=True, slots=True)
class StationHighlight:
    """Warning observations strictly above 50 percent grouped by full station identity.

    Attributes:
        station: Full plant/section/line/station identity; shifts aggregate at the
            station.
        count: Number of observed high-risk rows at this station.
        average_percent: Mean of the above-threshold observations only.
        maximum_percent: Largest above-threshold observed percent.
    """

    station: StationKey
    count: int
    average_percent: float
    maximum_percent: float


def plot_highlights(results: PlotResults) -> tuple[StationHighlight, ...]:
    """Summarize saved high-risk rows for the original View details workflow.

    Workers use enabled assignments; Job mode uses active placements. Missing evidence
    stays absent. The source strict >50% threshold is retained. Full
    plant/section/line/station ownership prevents merging equal station IDs in different
    branches. Geometry, previews, units and storage are irrelevant.

    Args:
        results: Applied saved dataset and marker enable flags; risk_view selects worker
            or job observations.

    Returns:
        Full-station-identity warning rows sorted by hierarchy, each counting only
        observed risks strictly above 50 percent.

    Raises:
        ValueError: An observed probability is nonfinite, boolean or outside 0-100
            percent.
    """
    observations: list[tuple[StationKey, float]] = []
    if results.selection.risk_view is PlotRiskView.JOB:
        for row in results.jobs:
            if row.risk is None:
                continue
            value = row.risk.measurement.probability_percent
            place = row.placement.workplace
            if value is not None:
                observations.append(
                    (
                        StationKey(
                            place.plant_name,
                            place.section_name,
                            place.line_name,
                            place.station_id,
                        ),
                        value,
                    )
                )
    else:
        for worker in results.workers:
            marker = results.positions.marker(worker.assessment.assignment_id)
            value = worker.assessment.probability
            if value is None or (marker is not None and not marker.enabled):
                continue
            place = worker.assessment.owner.workplace
            observations.append(
                (
                    StationKey(
                        place.plant_name,
                        place.section_name,
                        place.line_name,
                        place.station_id,
                    ),
                    value * 100,
                )
            )
    grouped: dict[StationKey, list[float]] = {}
    for station, value in observations:
        risk_average((value,))
        if value > 50:
            grouped.setdefault(station, []).append(value)
    return tuple(
        StationHighlight(station, len(values), fsum(values) / len(values), max(values))
        for station, values in sorted(
            grouped.items(),
            key=lambda item: (
                item[0].plant_name,
                item[0].section_name,
                item[0].line_name,
                item[0].station_id,
            ),
        )
    )
