"""Isolated, disposable English/cm/N JROT Yes-path developer workflow.

Presentation layer. Read detached catalogs, edit scratch Jobs and call existing
calculation/optimization ports. No project handle, save callback, Undo stack or export
or settings writer enters this dialog. Production JROT and its widgets are unchanged.
"""

from collections.abc import Callable, Mapping
from contextlib import suppress
from copy import deepcopy
from functools import partial

from PyQt5.QtCore import QDate, QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QCloseEvent, QColor, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.jrot_prototype import (
    PrototypeCatalog,
    PrototypeJob,
    PrototypeSession,
    project_prototype_jobs,
    prototype_statistics,
    prototype_worker_values,
    sample_prototype_job,
)
from ergotools.application.rotation_optimization import RotationOptimizer
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.risk import classify_probability
from ergotools.domain.rotation import RotationSolution, WorkerRotation
from ergotools.presentation.desktop.jrot_prototype_selectors import (
    PrototypeOption,
    PrototypeRecordChoice,
    PrototypeScopeDialog,
)
from ergotools.presentation.desktop.jrot_prototype_solve import PrototypeSolveThread
from ergotools.presentation.desktop.jrot_prototype_widgets import (
    PROTOTYPE_STYLE,
    PrototypeDrawer,
    PrototypeTaskGrid,
    prototype_button,
    prototype_card,
)
from ergotools.presentation.desktop.rotation_display import measurement_color
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES

# Eight pages group the seven overview stages: validation shares task entry, reports
# remain disabled on comparison, and setup/results use explicit substeps.
_PAGES = (
    (
        "01 / SETUP",
        "Rotation setup",
        "Define the shift and the people and Jobs in this rotation.",
    ),
    (
        "01 / SETUP",
        "Jobs in this rotation",
        "Reuse project values or explore with clearly labeled temporary Jobs.",
    ),
    (
        "01 / SETUP",
        "Workers & restrictions",
        "Choose the participants. Restrictions can be explored as a visual preview.",
    ),
    (
        "02 / ASSIGNMENTS",
        "Current rotation matrix",
        "Describe the current situation: exactly one worker per Job in every block.",
    ),
    (
        "03-04 / TASKS & VALIDATION",
        "Assess the Jobs",
        "Use existing values or calculate metric task inputs, one Job and tool at"
        " a time.",
    ),
    (
        "05 / BASELINE",
        "Understand the starting point",
        "Review intrinsic Job values and the workers' equal-block schedule averages.",
    ),
    (
        "06 / RESULTS",
        "Explore a suggested rotation",
        "Run the real solver with the current values. Nothing is applied to your "
        "project.",
    ),
    (
        "06-07 / COMPARISON & REPORTS",
        "Review the difference",
        "Compare the same workers, Jobs and workload before and after redistribution.",
    ),
)
# Visible branded English names are separate from persisted/internal tool enum values.
_TOOL_NAMES = {
    AssessmentKind.LIFFT: "LiFFT",
    AssessmentKind.DUET: "DUET",
    AssessmentKind.TST: "ST",
}


class JrotPrototypeDialog(QDialog):
    """Own one scratch session and bounded solver lifetime until the window closes."""

    def __init__(
        self,
        catalog: PrototypeCatalog,
        optimizer: RotationOptimizer,
        icons: Mapping[str, QIcon],
        parent: QWidget | None = None,
    ) -> None:
        """Compose the full Yes workflow without a repository or mutation callback.

        Args:
            catalog: Immutable source snapshot; may be empty for an all-sample preview.
            optimizer: Existing single-tool/all-three solver through the application
                port.
            icons: Existing packaged artwork; no assets are generated or modified.
            parent: Main-window owner; prototype closes before its catalogs can switch.

        Returns:
            None; sample calculations are local, and no preference/project is opened.
        """
        super().__init__(parent)
        self.setObjectName("jrotPrototype")
        self.setWindowTitle("JROT · Workflow prototype")
        self.setMinimumSize(1120, 760)
        self.resize(1440, 940)
        self.setStyleSheet(PROTOTYPE_STYLE)
        apply_dialog_theme(self)
        self.catalog = catalog
        self.optimizer = optimizer
        self.icons = icons
        self.session = PrototypeSession()
        self.available_jobs = list(project_prototype_jobs(catalog))
        samples = [sample_prototype_job(i) for i in range(12)]
        for index, job in enumerate(samples, 1):
            job.name += f" (S{index:02})"
        self.available_jobs.extend(samples)
        self.available_jobs.extend(
            PrototypeJob(f"entered-{i}", f"New Job {i}", "Entered")
            for i in range(1, 13)
        )
        self._default_count = (
            min(6, len(catalog.jobs.jobs), len(catalog.hierarchy.work.workers))
            if catalog.jobs
            and catalog.jobs.jobs
            and catalog.hierarchy
            and catalog.hierarchy.work.workers
            else 4
        )
        self.session.jobs = deepcopy(self.available_jobs[: self._default_count])
        self._job_cache = {job.key: job for job in self.available_jobs}
        self._job_cache.update((job.key, job) for job in self.session.jobs)
        self.solution: RotationSolution | None = None
        self.worker: PrototypeSolveThread | None = None
        self._close_pending = False
        self._page = 0
        self._matrix_signature: tuple[tuple[str, ...], tuple[str, ...], int] | None = (
            None
        )
        self._selected_job = 0
        self._job_choices: list[PrototypeRecordChoice] = []
        self._job_names: list[QLineEdit] = []
        self._worker_choices: list[PrototypeRecordChoice] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(12)
        brand, brand_layout = prototype_card("")
        brand.setObjectName("prototypeBrand")
        brand_heading = brand_layout.takeAt(0)
        assert brand_heading is not None
        brand_label = brand_heading.widget()
        assert brand_label is not None
        brand_label.deleteLater()
        brand_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(icons["jrot"].pixmap(QSize(42, 42)))
        brand_row.addWidget(icon)
        titles = QVBoxLayout()
        title = QLabel("Job Rotation Optimization")
        title.setObjectName("prototypeTitle")
        titles.addWidget(title)
        titles.addWidget(QLabel("A guided workspace · Developer prototype"))
        brand_row.addLayout(titles, 1)
        badge = QLabel("SESSION ONLY\nNo project changes")
        badge.setAlignment(Qt.AlignmentFlag.AlignRight)
        brand_row.addWidget(badge)
        brand_layout.addLayout(brand_row)
        root.addWidget(brand)
        body = QHBoxLayout()
        body.setSpacing(14)
        captions = (
            "1.1  Shift && boundaries",
            "1.2  Jobs",
            "1.3  Workers && restrictions",
            "02   Current assignments",
            "3-4  Tasks && validation",
            "05   Baseline summary",
            "6.1  Suggested rotation",
            "6.2 / 7  Compare && report",
        )
        self.drawer = PrototypeDrawer(captions, self.go)
        body.addWidget(self.drawer)
        self.content = QWidget()
        content = QVBoxLayout(self.content)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(10)
        self.eyebrow = QLabel()
        self.eyebrow.setObjectName("eyebrow")
        self.heading = QLabel()
        self.heading.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("supporting")
        content.addWidget(self.eyebrow)
        content.addWidget(self.heading)
        content.addWidget(self.subtitle)
        self.error = QLabel()
        self.error.setObjectName("prototypeError")
        self.error.setWordWrap(True)
        self.error.hide()
        content.addWidget(self.error)
        self.pages = QStackedWidget()
        self.page_layouts: list[QVBoxLayout] = []
        for _ in _PAGES:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 3, 0)
            layout.setSpacing(12)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
            self.page_layouts.append(layout)
        content.addWidget(self.pages, 1)
        body.addWidget(self.content, 1)
        root.addLayout(body, 1)
        self._build_setup()
        self._build_jobs()
        self._build_workers()
        self._build_matrix()
        self._build_assessments()
        self._build_baseline()
        self._build_optimization()
        self._build_comparison()
        footer = QHBoxLayout()
        self.back = prototype_button("←  Back", lambda: self.go(self._page - 1))
        self.back.setMinimumWidth(110)
        self.position = QLabel()
        self.position.setObjectName("supporting")
        footer.addWidget(self.back)
        footer.addWidget(self.position)
        footer.addStretch(1)
        self.close_preview = prototype_button("Close preview", self.reject)
        self.next = prototype_button("Continue  →", self.advance, primary=True)
        self.next.setMinimumWidth(190)
        footer.addWidget(self.close_preview)
        footer.addWidget(self.next)
        root.addLayout(footer)
        self._setup_signature: tuple[object, ...] | None = None
        self._synchronize_choices()
        self._select_assessment_job(0)
        self._refresh_progress()
        self._render_page()

    def _notice(self, text: str) -> QLabel:
        """Create a wrapping preview explanation in the established teal palette.

        Args:
            text: Relevant limitation or source explanation for this page.

        Returns:
            Label adopted by its page layout.
        """
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName("prototypeNotice")
        return label

    def _table(self, headers: list[str], height: int = 260) -> QTableWidget:
        """Build an ordinary scrollable table, retaining complete header widths.

        Args:
            headers: English column captions.
            height: Minimum useful viewport height in logical pixels.

        Returns:
            Table with row selection, alternating colors and intrinsic header minima.
        """
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(height)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        vertical = table.verticalHeader()
        header = table.horizontalHeader()
        assert vertical is not None and header is not None
        vertical.setDefaultSectionSize(46)
        header.setMinimumSectionSize(100)
        header.setSectionResizeMode(QHeaderView.Stretch)
        return table

    def _build_setup(self) -> None:
        """Compose existing hierarchy/shift choices and explicit equal-block boundaries.

        Args:
            None.

        Returns:
            None; no organization record or duration is persisted.
        """
        page = self.page_layouts[0]
        card, layout = prototype_card(
            "Project & analysis scope",
            "Read-only project choices. All working values in this window are "
            "temporary.",
        )
        form = QFormLayout()
        form.addRow("Source project", QLabel(self.catalog.title))
        self._scope_path: tuple[str, ...] | None = None
        self._shift_id = "sample"
        self.shift_options: tuple[tuple[str, str, str, str], ...] = ()
        records = (
            {
                r.keys[0]: dict(r.attributes)
                for r in self.catalog.hierarchy.organization
                if r.kind.value == "Shift"
            }
            if self.catalog.hierarchy
            else {}
        )
        if self.catalog.hierarchy and self.catalog.hierarchy.work.shifts:
            self.shift_options = tuple(
                (
                    key,
                    str(records.get(key, {}).get("description") or ""),
                    str(records.get(key, {}).get("start_time") or "—"),
                    str(records.get(key, {}).get("end_time") or "—"),
                )
                for key in self.catalog.hierarchy.work.shifts
            )
        else:
            self.shift_options = (("sample", "Sample day shift", "08:00", "16:00"),)
        self._shift_id = self.shift_options[0][0]
        self.scope_summary = QLabel()
        self.scope_summary.setWordWrap(True)
        self.shift_summary = QLabel()
        self.shift_summary.setWordWrap(True)
        self.scope_button = prototype_button(
            "Choose workplace and shift…", self.choose_scope
        )
        self.scope_button.setIcon(self.icons["plant"])
        self.scope_button.setIconSize(QSize(28, 28))
        form.addRow("Workplace", self.scope_summary)
        form.addRow("Shift", self.shift_summary)
        form.addRow("", self.scope_button)
        layout.addLayout(form)
        page.addWidget(card)
        card, layout = prototype_card(
            "Is Job rotation currently practiced?",
            "This prototype implements the existing-rotation (Yes) path.",
        )
        choices = QHBoxLayout()
        self.yes = QPushButton("Yes\nEnter the current rotation")
        self.yes.setCheckable(True)
        self.yes.setObjectName("rotationChoice")
        self.no = QPushButton("No\nBaseline mode")
        self.no.setCheckable(True)
        self.no.setObjectName("rotationChoice")
        self.rotation_choices = QButtonGroup(self)
        self.rotation_choices.addButton(self.yes)
        self.rotation_choices.addButton(self.no)
        self.yes.setChecked(True)
        for button in (self.yes, self.no):
            button.setAutoDefault(False)
            button.setMinimumWidth(250)
        choices.addStretch(1)
        choices.addWidget(self.yes)
        choices.addWidget(self.no)
        choices.addStretch(1)
        layout.addLayout(choices)
        self.no_note = self._notice(
            "The No path is not implemented in this prototype. Select Yes to continue."
        )
        self.no_note.hide()
        layout.addWidget(self.no_note)
        page.addWidget(card)
        card, layout = prototype_card(
            "Shift boundaries & participants",
            "Equal blocks use the current JROT weighting. Duration is "
            "descriptive; it does not rescale task repetitions.",
        )
        grid = QGridLayout()
        self.duration = QDoubleSpinBox()
        self.duration.setRange(0.5, 24)
        self.duration.setSingleStep(0.5)
        self.duration.setSuffix(" hours")
        self.duration.setValue(8)
        self.blocks = QSpinBox()
        self.blocks.setRange(1, 12)
        self.blocks.setValue(4)
        self.workers_count = QSpinBox()
        self.workers_count.setRange(1, 12)
        self.workers_count.setValue(self._default_count)
        self.jobs_count = QSpinBox()
        self.jobs_count.setRange(1, 12)
        self.jobs_count.setValue(self._default_count)
        for column, (caption, control) in enumerate(
            (
                ("Shift duration", self.duration),
                ("Time blocks", self.blocks),
                ("Workers", self.workers_count),
                ("Jobs", self.jobs_count),
            )
        ):
            grid.addWidget(QLabel(caption), 0, column)
            grid.addWidget(control, 1, column)
        layout.addLayout(grid)
        self.block_summary = QLabel()
        self.block_summary.setObjectName("cardTitle")
        layout.addWidget(self.block_summary)
        page.addWidget(card)
        page.addStretch(1)
        self.duration.valueChanged.connect(self._update_block_summary)
        self.blocks.valueChanged.connect(self._update_block_summary)
        self.yes.toggled.connect(self._rotation_choice)
        self._shift_selected()

    def _rotation_choice(self) -> None:
        """Keep the unimplemented No branch visible but unable to advance.

        Args:
            None.

        Returns:
            None; the current scratch session is retained if Yes is reselected.
        """
        self.no_note.setVisible(not self.yes.isChecked())
        if hasattr(self, "next") and self._page == 0:
            self.next.setEnabled(self.yes.isChecked())

    def _shift_selected(self) -> None:
        """Display the exact selected ancestry/clocks and suggest elapsed shift hours.

        Args:
            None.

        Returns:
            None; elapsed duration is descriptive, never a repetition multiplier.
        """
        self.scope_summary.setText(
            " / ".join(self._scope_path)
            if self._scope_path
            else "All workplaces · all available Jobs"
        )
        key, description, start, end = next(
            v for v in self.shift_options if v[0] == self._shift_id
        )
        self.shift_summary.setText(f"{key} · {description} · {start} → {end}")
        if start != "—" and end != "—":
            first = sum(
                int(v) * f for v, f in zip(start.split(":"), (60, 1), strict=True)
            )
            last = sum(int(v) * f for v, f in zip(end.split(":"), (60, 1), strict=True))
            self.duration.setValue(((last - first) % 1440 or 1440) / 60)
        self._update_block_summary()

    def choose_scope(self) -> None:
        """Borrow a themed hierarchy/shift picker without opening organization editing.

        Args:
            None.

        Returns:
            None; Cancel retains the exact local selection.
        """
        dialog = PrototypeScopeDialog(
            self.catalog.hierarchy,
            self.icons,
            self.shift_options,
            self._scope_path,
            self._shift_id,
            self,
        )
        try:
            if dialog.exec() == QDialog.Accepted:
                self._scope_path, self._shift_id = dialog.path, dialog.shift_id
                self._shift_selected()
                self._synchronize_choices()
        finally:
            dialog.deleteLater()

    def _update_block_summary(self) -> None:
        """Derive equal block lengths for display without altering model coefficients.

        Args:
            None.

        Returns:
            None; every block retains equal weight in the real solver.
        """
        minutes = self.duration.value() * 60 / self.blocks.value()
        self.block_summary.setText(
            f"{self.blocks.value()} equal blocks · {minutes:g} minutes each"
        )

    def _build_jobs(self) -> None:
        """Prepare project/sample/new Job selection with temporary editable names.

        Args:
            None.

        Returns:
            None; actual Job records and placements remain unchanged.
        """
        page = self.page_layouts[1]
        card, layout = prototype_card(
            "Choose the Jobs",
            "Project = existing values. Sample = calculated demo data. Entered = "
            "a new empty scratch Job.",
        )
        self.job_table = self._table(
            ["Use values from", "Job name in this preview", "Source"], 320
        )
        layout.addWidget(self.job_table)
        page.addWidget(card)
        page.addWidget(
            self._notice(
                "Jobs are activities. Physical Station placement is read-only "
                "context; no Jobs or assignments will be created."
            )
        )
        page.addStretch(1)

    def _populate_jobs(self) -> None:
        """Build Job chooser buttons with source/task availability.

        Args:
            None.

        Returns:
            None; full-ancestry prefix/shift filtering affects project choices only.
        """
        allowed: set[str] | None = None
        if self._scope_path and self.catalog.jobs:
            allowed = {
                "project-" + p.job_id
                for p in self.catalog.jobs.placements
                if p.active
                and p.workplace.shift_id == self._shift_id
                and (
                    p.workplace.plant_name,
                    p.workplace.section_name,
                    p.workplace.line_name,
                )[: len(self._scope_path)]
                == self._scope_path
            }
        options = tuple(
            PrototypeOption(
                job.key,
                (
                    job.key.removeprefix("project-") + " · "
                    if job.origin == "Project"
                    else ""
                )
                + job.name,
                self._job_data_caption(job),
                job.origin,
            )
            for job in self.available_jobs
            if allowed is None or job.origin != "Project" or job.key in allowed
        )
        self.job_table.setRowCount(self.jobs_count.value())
        self._job_choices = []
        self._job_names = []
        used: set[str] = set()
        for row in range(self.jobs_count.value()):
            previous = (
                self.session.jobs[row].key if row < len(self.session.jobs) else ""
            )
            key = (
                previous
                if any(o.key == previous for o in options) and previous not in used
                else next(o.key for o in options if o.key not in used)
            )
            used.add(key)
            choice = PrototypeRecordChoice("Choose a Job", self.icons["job_management"])
            choice.configure(options, key)
            job = self._job_cache[key]
            name, source = QLineEdit(job.name), QLabel(self._job_data_caption(job))
            source.setWordWrap(True)
            self.job_table.setCellWidget(row, 0, choice)
            self.job_table.setCellWidget(row, 1, name)
            self.job_table.setCellWidget(row, 2, source)
            choice.chosen.connect(
                lambda c=choice, n=name, label=source: self._job_selected(c, n, label)
            )
            self._job_choices.append(choice)
            self._job_names.append(name)

    def _job_data_caption(self, job: PrototypeJob) -> str:
        """Explain why values may be ready even when no source tasks were recorded.

        Args:
            job: Detached offered Job or scratch copy.

        Returns:
            Literal source plus input/result availability, without invented tasks.
        """
        tasks = sum(v.source is not None for v in job.measurements.values())
        ready = sum(v.complete for v in job.measurements.values())
        return f"{job.origin} · {ready}/3 calculated tools · " + (
            f"{tasks}/3 with task inputs"
            if tasks
            else "results only"
            if ready
            else "new empty inputs"
        )

    def _job_selected(
        self, choice: PrototypeRecordChoice, name: QLineEdit, origin: QLabel
    ) -> None:
        """Update a row from its record picker; invalidate scratch output.

        Args:
            choice: Owned button carrying the exact accepted Job key.
            name: Temporary editable Job caption.
            origin: Visible task/result availability label.

        Returns:
            None; the original Job and its stored values are untouched.
        """
        job = self._job_cache[choice.key]
        name.setText(job.name)
        origin.setText(self._job_data_caption(job))
        self._invalidate_solution()

    def _accept_jobs(self, validate: bool = True) -> None:
        """Retain Job drafts; optionally check unique named selections for calculation.

        Args:
            validate: Check readiness before baseline/optimization, never navigation.

        Returns:
            None; no project save/creation command exists.

        Raises:
            ValueError: A Job is duplicated or has an empty preview name.
        """
        keys = [choice.key for choice in self._job_choices]
        if validate and len(keys) != len(set(keys)):
            raise ValueError(
                "A Job is selected twice. Choose a different Job in each row."
            )
        jobs = []
        for key, name in zip(keys, self._job_names, strict=True):
            if validate and not name.text().strip():
                raise ValueError("Give each Job a name for this preview.")
            job = self._job_cache[key]
            job.name = name.text().strip() or job.name
            jobs.append(job)
        if [job.key for job in jobs] != [job.key for job in self.session.jobs]:
            self._matrix_signature = None
            self._invalidate_solution()
        self.session.jobs = jobs

    def _build_workers(self) -> None:
        """Compose worker choices and clearly nonfunctional restriction exploration.

        Args:
            None.

        Returns:
            None; restrictions are not passed into the real optimizer.
        """
        page = self.page_layouts[2]
        card, layout = prototype_card(
            "People in this rotation",
            "Reuse worker IDs from the project, or use an explicitly temporary "
            "participant.",
        )
        self.worker_table = self._table(["Worker", "Source"], 210)
        layout.addWidget(self.worker_table)
        page.addWidget(card)
        card, layout = prototype_card(
            "Worker constraints · visual preview",
            "Optional. Continue without adding any restrictions. These controls do not "
            "constrain this prototype's optimization.",
        )
        row = QHBoxLayout()
        self.rule_worker = QComboBox()
        self.rule = QComboBox()
        self.rule.addItems(
            ["Fix to one Job", "Cannot perform Job", "No consecutive high-risk Jobs"]
        )
        self.rule_job = QComboBox()
        row.addWidget(self.rule_worker, 1)
        row.addWidget(self.rule, 1)
        row.addWidget(self.rule_job, 1)
        row.addWidget(prototype_button("Add rule", lambda: self.act(self._add_rule)))
        self.rule.currentIndexChanged.connect(
            lambda: self.rule_job.setEnabled(self.rule.currentIndex() != 2)
        )
        layout.addLayout(row)
        self.rule_table = self._table(["Worker", "Preview rule", "Job", ""], 150)
        layout.addWidget(self.rule_table)
        self.no_rules = self._notice(
            "No restrictions added. Restrictions are optional."
        )
        layout.addWidget(self.no_rules)
        page.addWidget(card)
        page.addStretch(1)

    def _populate_workers(self) -> None:
        """Build named worker pickers with demographics and explicit samples.

        Args:
            None.

        Returns:
            None; no restriction is required and no Worker record is modified.
        """
        real = self.catalog.hierarchy.work.workers if self.catalog.hierarchy else ()
        options = []
        today = QDate.currentDate()
        for worker in real:
            details = worker.details
            birth = (
                QDate.fromString(details.birth_date, "yyyy-MM-dd")
                if details and details.birth_date
                else QDate()
            )
            age = (
                today.year()
                - birth.year()
                - int((today.month(), today.day()) < (birth.month(), birth.day()))
                if birth.isValid()
                else None
            )
            demographic = (
                f"{details.sex or 'Sex not entered'} · "
                f"age {age if age is not None else 'not entered'}"
                if details
                else "Demographics not entered"
            )
            options.append(
                PrototypeOption(
                    worker.worker_id,
                    worker.worker_id
                    + " · "
                    + " ".join(filter(None, (worker.first_name, worker.last_name))),
                    demographic,
                    "Project",
                )
            )
        options.extend(
            PrototypeOption(
                f"preview-worker-{i}",
                f"Worker {i:02} · temporary",
                "Simulated participant",
                "Sample",
            )
            for i in range(1, 13)
        )
        self.worker_table.setMinimumHeight(min(6, self.workers_count.value()) * 46 + 54)
        self.worker_table.setRowCount(self.workers_count.value())
        self._worker_choices = []
        used: set[str] = set()
        for row in range(self.workers_count.value()):
            previous = (
                self.session.workers[row] if row < len(self.session.workers) else ""
            )
            key = (
                previous
                if any(o.key == previous for o in options) and previous not in used
                else next(o.key for o in options if o.key not in used)
            )
            used.add(key)
            choice = PrototypeRecordChoice("Choose a worker", self.icons["worker"])
            choice.configure(tuple(options), key)
            source = QLabel(choice.option.group + " · " + choice.option.details)
            source.setWordWrap(True)
            choice.chosen.connect(
                lambda c=choice, o=source: self._worker_selected(c, o)
            )
            self.worker_table.setCellWidget(row, 0, choice)
            self.worker_table.setCellWidget(row, 1, source)
            self._worker_choices.append(choice)
        self._refresh_rule_choices()
        self._render_rules()

    def _worker_selected(self, choice: PrototypeRecordChoice, origin: QLabel) -> None:
        """Refresh named participant summaries after accepting the record picker.

        Args:
            choice: Owned selector retaining a stable Worker key.
            origin: Row label showing source and available demographics.

        Returns:
            None; all worker selection changes remain local.
        """
        origin.setText(choice.option.group + " · " + choice.option.details)
        self._refresh_rule_choices()
        self._invalidate_solution()

    def _refresh_rule_choices(self) -> None:
        """Project current participant and Job captions into preview rule controls.

        Args:
            None.

        Returns:
            None; no restriction is inferred from database metadata.
        """
        self.rule_worker.clear()
        for choice in self._worker_choices:
            self.rule_worker.addItem(choice.option.caption, choice.key)
        self.rule_job.clear()
        for job in self.session.jobs:
            self.rule_job.addItem(job.name, job.key)

    def _add_rule(self) -> None:
        """Append one display-only rule; several exclusions can be added per worker.

        Args:
            None.

        Returns:
            None; rule duplication is suppressed for clarity.
        """
        target = (
            "" if self.rule.currentIndex() == 2 else str(self.rule_job.currentData())
        )
        entry = (str(self.rule_worker.currentData()), self.rule.currentText(), target)
        if entry not in self.session.restrictions:
            self.session.restrictions.append(entry)
        self._render_rules()

    def _render_rules(self) -> None:
        """Show all temporary rules with reachable removal controls.

        Args:
            None.

        Returns:
            None; missing participant/Job captions remain visible as their old keys.
        """
        names = {job.key: job.name for job in self.session.jobs}
        self.rule_table.setVisible(bool(self.session.restrictions))
        self.no_rules.setVisible(not self.session.restrictions)
        self.rule_table.setRowCount(len(self.session.restrictions))
        for row, (worker, rule, target) in enumerate(self.session.restrictions):
            for column, text in enumerate(
                (worker, rule, names.get(target, target or "All high-risk Jobs"))
            ):
                self.rule_table.setItem(row, column, QTableWidgetItem(text))
            self.rule_table.setCellWidget(
                row, 3, prototype_button("Remove", partial(self._remove_rule, row))
            )

    def _remove_rule(self, index: int) -> None:
        """Remove one preview rule without creating history or changing solver input.

        Args:
            index: Current zero-based rule row.

        Returns:
            None; rebuilt controls receive fresh row indices.
        """
        self.session.restrictions.pop(index)
        self._render_rules()

    def _accept_workers(self, validate: bool = True) -> None:
        """Keep unique participants and names entirely inside the scratch session.

        Args:
            validate: Check uniqueness only for calculation readiness, never Back.

        Returns:
            None; original demographic/assignment records remain unchanged.

        Raises:
            ValueError: A worker is selected more than once.
        """
        keys = [choice.key for choice in self._worker_choices]
        if validate and len(keys) != len(set(keys)):
            raise ValueError(
                "A worker is selected twice. Choose a different worker in each row. "
                "Restrictions are optional."
            )
        if keys != self.session.workers:
            self._matrix_signature = None
            self._invalidate_solution()
        self.session.workers = keys
        self.session.worker_names = {
            key: choice.option.caption
            for key, choice in zip(keys, self._worker_choices, strict=True)
        }

    def _build_matrix(self) -> None:
        """Prepare the editable current rotation, without loading/writing a scheme.

        Args:
            None.

        Returns:
            None; matrix cells store only temporary Job keys.
        """
        page = self.page_layouts[3]
        card, layout = prototype_card(
            "Worker assignment matrix",
            "The starter matrix is simulated. Edit it to represent the current "
            "rotation; every block must use each Job once.",
        )
        self.matrix = self._table(["Worker"], 340)
        layout.addWidget(self.matrix)
        row = QHBoxLayout()
        example = prototype_button("Fill rotating example", self._fill_rotating_example)
        example.setToolTip(
            "Replace temporary assignments with a cyclic example. "
            "This does not run the optimizer or guarantee balanced risk."
        )
        row.addWidget(example)
        row.addStretch(1)
        self.matrix_note = QLabel()
        self.matrix_note.setObjectName("supporting")
        row.addWidget(self.matrix_note)
        layout.addLayout(row)
        page.addWidget(card)
        page.addWidget(
            self._notice(
                "Worker restrictions are preview-only and are not enforced in the"
                " matrix or the solver."
            )
        )
        page.addStretch(1)

    def _populate_matrix(self, rotating: bool = False) -> None:
        """Preserve accepted cells or create an explicit, fully staffed sample.

        Args:
            rotating: True resets to a cyclic example; False retains matching data.

        Returns:
            None; rebuild only on participant/count changes or explicit request.
        """
        signature = (
            tuple(self.session.workers),
            tuple(job.key for job in self.session.jobs),
            self.blocks.value(),
        )
        if signature == self._matrix_signature and not rotating:
            # Preserve exact cells while reflecting renamed scratch Jobs/workers.
            names = {job.key: job.name for job in self.session.jobs}
            for row, worker in enumerate(self.session.workers):
                item = self.matrix.item(row, 0)
                if item is not None:
                    item.setText(self.session.worker_names[worker])
                for column in range(1, self.matrix.columnCount()):
                    choice = self.matrix.cellWidget(row, column)
                    assert isinstance(choice, QComboBox)
                    for index in range(choice.count()):
                        choice.setItemText(index, names[str(choice.itemData(index))])
            return
        self.matrix.setColumnCount(self.blocks.value() + 1)
        self.matrix.setHorizontalHeaderLabels(
            ["Worker", *(f"Block {i + 1}" for i in range(self.blocks.value()))]
        )
        self.matrix.setRowCount(len(self.session.workers))
        for row, worker in enumerate(self.session.workers):
            self.matrix.setItem(
                row, 0, QTableWidgetItem(self.session.worker_names[worker])
            )
            for block in range(self.blocks.value()):
                combo = QComboBox()
                for job in self.session.jobs:
                    combo.addItem(job.name, job.key)
                shift = (
                    block
                    if rotating
                    else (1 if block == self.blocks.value() - 1 else 0)
                )
                combo.setCurrentIndex((row + shift) % len(self.session.jobs))
                combo.currentIndexChanged.connect(self._invalidate_solution)
                self.matrix.setCellWidget(row, block + 1, combo)
        self._matrix_signature = signature
        self.matrix_note.setText(
            f"{len(self.session.workers)} workers · {self.blocks.value()} equal blocks"
        )
        self._invalidate_solution()

    def _fill_rotating_example(self) -> None:
        """Replace scratch assignments with a cyclic example, without optimizing risk.

        Args:
            None.

        Returns:
            None; no project scheme is changed.
        """
        self._populate_matrix(True)

    def _accept_matrix(self, validate: bool = True) -> None:
        """Read current Job keys in worker order for later completeness validation.

        Args:
            validate: Require complete staffing only for readiness, not reviewing steps.

        Returns:
            None; no calculations or database operations occur here.

        Raises:
            ValueError: A block does not assign every participating Job exactly once.
        """
        if not validate and (
            self.matrix.rowCount() != len(self.session.workers)
            or self.matrix.columnCount() != self.blocks.value() + 1
        ):
            return  # A setup change will rebuild the matrix before it is consumed.
        rows = []
        for row, worker in enumerate(self.session.workers):
            keys = []
            for block in range(self.blocks.value()):
                combo = self.matrix.cellWidget(row, block + 1)
                assert isinstance(combo, QComboBox)
                keys.append(str(combo.currentData()))
            rows.append(WorkerRotation(worker, tuple(keys)))
        self.session.current = tuple(rows)
        expected = {job.key for job in self.session.jobs}
        for block in range(self.blocks.value()):
            if validate and {row.target_keys[block] for row in rows} != expected:
                raise ValueError(f"Block {block + 1}: use every Job exactly once.")

    def _build_assessments(self) -> None:
        """Compose Job progress, existing calculators and temporary task-name entry.

        Args:
            None.

        Returns:
            None; no production calculator widgets or DTO definitions are modified.
        """
        page = self.page_layouts[4]
        top = QHBoxLayout()
        top.addWidget(QLabel("Optimize using"))
        self.analysis = QComboBox()
        for kind in AssessmentKind:
            self.analysis.addItem(_TOOL_NAMES[kind])
        self.analysis.addItem("All three tools")
        self.analysis.setCurrentIndex(3)
        self.analysis.currentIndexChanged.connect(self._analysis_changed)
        top.addWidget(self.analysis)
        top.addStretch(1)
        top.addWidget(QLabel("Metric inputs · cm / N · repetitions per day"))
        page.addLayout(top)
        body = QHBoxLayout()
        progress_card, progress = prototype_card("Job progress")
        progress_card.setMinimumWidth(200)
        progress_card.setMaximumWidth(270)
        self.job_progress = QListWidget()
        self.job_progress.setMinimumHeight(280)
        self.job_progress.currentRowChanged.connect(self._select_assessment_job)
        progress.addWidget(self.job_progress)
        body.addWidget(progress_card)
        task_card, task_layout = prototype_card(
            "Task inputs & validation",
            "Names are optional. Blank unused rows are ignored by the existing "
            "calculator; entered incomplete rows require correction.",
        )
        self.job_caption = QLabel()
        self.job_caption.setObjectName("cardTitle")
        task_layout.addWidget(self.job_caption)
        self.task_origin = self._notice("")
        task_layout.addWidget(self.task_origin)
        self.tool_tabs = QTabWidget()
        self.grids: dict[AssessmentKind, PrototypeTaskGrid] = {}
        for kind in AssessmentKind:
            grid = PrototypeTaskGrid(kind)
            grid.changed.connect(self._task_changed)
            self.grids[kind] = grid
            self.tool_tabs.addTab(grid, _TOOL_NAMES[kind])
        self.tool_tabs.currentChanged.connect(self._tool_changed)
        task_layout.addWidget(self.tool_tabs)
        results = QGridLayout()
        for row, title, label in (
            (0, "Cumulative damage", QLabel("—")),
            (1, "Outcome probability", QLabel("—")),
        ):
            caption = QLabel(title)
            caption.setAlignment(
                Qt.Alignment(Qt.AlignmentFlag.AlignRight)
                | Qt.AlignmentFlag.AlignVCenter
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumWidth(140)
            label.setMaximumWidth(240)
            results.addWidget(caption, row, 0)
            results.addWidget(label, row, 1)
            if row == 0:
                self.task_damage = label
            else:
                self.task_probability = label
        results.setColumnStretch(0, 1)
        task_layout.addLayout(results)
        self.task_summary = QLabel()
        self.task_summary.setObjectName("prototypeNotice")
        self.task_summary.setWordWrap(True)
        task_layout.addWidget(self.task_summary)
        buttons = QHBoxLayout()
        buttons.addWidget(
            prototype_button(
                "+ Task", lambda: self.act(lambda: self._resize_task(False))
            )
        )
        buttons.addWidget(
            prototype_button(
                "- Task", lambda: self.act(lambda: self._resize_task(True))
            )
        )
        buttons.addWidget(prototype_button("Clear tool", self._clear_tool))
        buttons.addWidget(
            prototype_button(
                "Calculate", lambda: self.act(self._calculate), primary=True
            ),
            1,
        )
        task_layout.addLayout(buttons)
        links = QHBoxLayout()
        links.addWidget(prototype_button("Skip this tool for now", self._skip_tool))
        links.addStretch(1)
        links.addWidget(prototype_button("Next assessment  →", self._next_assessment))
        links.addWidget(prototype_button("Finish Job  →", self._finish_job))
        task_layout.addLayout(links)
        body.addWidget(task_card, 1)
        page.addLayout(body)
        page.addWidget(
            self._notice(
                "A skipped assessment is unavailable, not zero. Select a single "
                "complete tool or complete all three. Two-tool combinations are "
                "not implemented."
            )
        )
        page.addStretch(1)

    def kinds(self) -> tuple[AssessmentKind, ...]:
        """Return exactly one selected tool or all three; no pair is implied.

        Args:
            None.

        Returns:
            Immutable existing tool identities for calculation completeness and solving.
        """
        return (
            tuple(AssessmentKind)
            if self.analysis.currentIndex() == 3
            else (tuple(AssessmentKind)[self.analysis.currentIndex()],)
        )

    def _analysis_changed(self) -> None:
        """Invalidate the result when requested optimization tools change.

        Args:
            None.

        Returns:
            None; no task source is deleted when switching tools.
        """
        self._invalidate_solution()
        if hasattr(self, "optimized_tabs"):
            self._sync_optimized_tabs()
        if hasattr(self, "job_progress"):
            self._refresh_progress()

    def _refresh_progress(self) -> None:
        """Derive per-Job progress without rebinding focused task controls.

        Args:
            None.

        Returns:
            None; selected Job and unfinished numeric text remain intact.
        """
        with QSignalBlocker(self.job_progress):
            self.job_progress.clear()
            for job in self.session.jobs:
                item = QListWidgetItem(
                    f"{job.name}\n{job.status(self.kinds())} · {job.origin}"
                )
                item.setSizeHint(QSize(180, 64))
                self.job_progress.addItem(item)
            self.job_progress.setCurrentRow(
                min(self._selected_job, len(self.session.jobs) - 1)
            )
        if self.session.jobs:
            self._update_task_summary()

    def _commit_grids(self) -> None:
        """Accept pending scratch numbers before leaving a Job or task page.

        Args:
            None.

        Returns:
            None; incomplete values can remain None without being calculated.

        Raises:
            ValueError: Visible numeric text is invalid.
        """
        for grid in self.grids.values():
            grid.commit()

    def _select_assessment_job(self, index: int) -> None:
        """Switch temporary Jobs while retaining pending task inputs/names.

        Args:
            index: Current selected Job row, or -1 during list rebuilding.

        Returns:
            None; invalid pending input keeps the old Job selected for correction.
        """
        if not 0 <= index < len(self.session.jobs):
            return
        try:
            self._commit_grids()
        except ValueError as error:
            self._show_error(str(error))
            with QSignalBlocker(self.job_progress):
                self.job_progress.setCurrentRow(self._selected_job)
            return
        self._selected_job = index
        job = self.session.jobs[index]
        self.job_caption.setText(f"{job.name} · {job.origin} values")
        for grid in self.grids.values():
            if grid.job is not job:
                grid.bind(job)
        self._update_task_summary()

    def _tool_changed(self) -> None:
        """Refresh selected-tool totals without clearing another tab's inputs.

        Args:
            None.

        Returns:
            None; existing fields remain alive across tool tabs.
        """
        if self.session.jobs:
            self._update_task_summary()

    def _task_changed(self) -> None:
        """Mark previews stale and recalculate only status, never scientific results.

        Args:
            None.

        Returns:
            None; edited source waits for explicit Calculate.
        """
        self._invalidate_solution()
        self._refresh_progress()

    def _current_grid(self) -> PrototypeTaskGrid:
        """Return the selected existing tool's scratch editor.

        Args:
            None.

        Returns:
            Owned task grid; it never has a project connection.
        """
        return self.grids[tuple(AssessmentKind)[self.tool_tabs.currentIndex()]]

    def _update_task_summary(self) -> None:
        """Display exact-backed selected-tool totals or clear availability messages.

        Args:
            None.

        Returns:
            None; direct values remain usable without inventing source tasks.
        """
        job = self.session.jobs[self._selected_job]
        kind = tuple(AssessmentKind)[self.tool_tabs.currentIndex()]
        value = job.measurements.get(kind)
        complete = value is not None and value.complete and kind not in job.skipped
        self.task_damage.setText(
            f"{value.cumulative_damage:.6g}" if complete and value else "—"
        )
        self.task_probability.setText(
            f"{value.probability_percent:.2f}%" if complete and value else "—"
        )
        color = (
            measurement_color(kind, value.cumulative_damage)
            if complete and value and value.cumulative_damage is not None
            else "#EAF2F6"
        )
        for label in (self.task_damage, self.task_probability):
            label.setStyleSheet(
                f"background: {color}; color: #0B326C; "
                "padding: 4px; border-radius: 5px;"
            )
        if kind in job.skipped:
            text = "Skipped for now · unavailable to optimization until calculated."
        elif value and value.complete:
            text = (
                f"{_TOOL_NAMES[kind]} · {job.name} · Calculated results. "
                "These Job values are summarized again in step 05."
            )
            if value.source is None:
                text += (
                    "\nExisting direct values; entering task inputs replaces "
                    "only this temporary copy."
                )
        else:
            text = "Not calculated · enter task inputs, then Calculate."
        self.task_origin.setText(
            f"{job.origin} · Stored results only: no task inputs were recorded. "
            "The blank row is optional; these results can already be used."
            if value and value.complete and value.source is None
            else (
                f"{job.origin} · {len(value.source.tasks)} "
                f"{'saved' if job.origin == 'Project' else 'temporary'} "
                "task input rows "
                "with calculated outputs."
            )
            if value and value.complete and value.source
            else (
                f"{job.origin} · Enter task inputs and Calculate. "
                "Nothing is saved to the project."
            )
        )
        self.task_summary.setText(text)

    def _calculate(self) -> None:
        """Calculate the selected scratch tool using the existing application evaluator.

        Args:
            None.

        Returns:
            None; task outputs and totals stay in memory only.

        Raises:
            ValueError: Inputs are incomplete or the unchanged calculator rejects them.
        """
        grid = self._current_grid()
        grid.commit()
        job = self.session.jobs[self._selected_job]
        measurement = calculate_job_measurement(
            "developer-prototype", job.key, grid.source, MeasurementSystem.METRIC
        )
        job.measurements[grid.kind] = measurement
        job.skipped.discard(grid.kind)
        grid.show_outputs(measurement)
        self._invalidate_solution()
        self._refresh_progress()
        self.error.hide()

    def _resize_task(self, remove: bool) -> None:
        """Resize only the selected tool's scratch tasks.

        Args:
            remove: Remove the selected task rather than append one.

        Returns:
            None; source validation errors remain visible through act.

        Raises:
            ValueError: Task count/selection or pending numeric text is invalid.
        """
        self._current_grid().resize_tasks(remove)

    def _clear_tool(self) -> None:
        """Clear only the current temporary tool to one blank task.

        Args:
            None.

        Returns:
            None; source project data and other Jobs/tools remain unchanged.
        """
        job = self.session.jobs[self._selected_job]
        grid = self._current_grid()
        job.measurements.pop(grid.kind, None)
        job.skipped.discard(grid.kind)
        grid.bind(job)
        self._task_changed()

    def _skip_tool(self) -> None:
        """Keep inputs but mark this Job/tool unavailable until recalculation.

        Args:
            None.

        Returns:
            None; skip never supplies zero to a real solve.
        """
        job = self.session.jobs[self._selected_job]
        job.skipped.add(self._current_grid().kind)
        self._task_changed()
        self._next_assessment()

    def _next_assessment(self) -> None:
        """Navigate tools within the same Job without making an implicit calculation.

        Args:
            None.

        Returns:
            None; the last tool moves to the next Job if available.
        """
        index = self.tool_tabs.currentIndex()
        if index < 2:
            self.tool_tabs.setCurrentIndex(index + 1)
        else:
            self._finish_job()

    def _finish_job(self) -> None:
        """Move to the next Job or validate all selected tools before baseline.

        Args:
            None.

        Returns:
            None; incomplete selected values show an inline error, never a false Ready.
        """
        if self._selected_job + 1 < len(self.session.jobs):
            self.job_progress.setCurrentRow(self._selected_job + 1)
            self.tool_tabs.setCurrentIndex(0)
        else:
            self.advance()

    def _build_baseline(self) -> None:
        """Prepare separate worker-average and intrinsic-Job baseline views.

        Args:
            None.

        Returns:
            None; all figures come from current temporary calculated values.
        """
        page = self.page_layouts[5]
        self.baseline_context = self._notice("")
        page.addWidget(self.baseline_context)
        self.baseline_tabs = QTabWidget()
        self.worker_baseline = self._table(["Worker", "LiFFT", "DUET", "ST"], 300)
        self.job_baseline = self._table(["Job", "LiFFT", "DUET", "ST"], 300)
        self.baseline_tabs.addTab(self.worker_baseline, "Worker schedule averages")
        self.baseline_tabs.addTab(self.job_baseline, "Job risk values")
        page.addWidget(self.baseline_tabs)
        self.legend = self._notice(
            "Current bands: Low ≤25% · Moderate ≤37.5% · Moderate High ≤50% · "
            "High >50%. Worker averages are schedule comparison measures, not new"
            " individual injury probabilities."
        )
        page.addWidget(self.legend)
        page.addWidget(prototype_button("Modify task inputs", lambda: self.go(4)))
        page.addStretch(1)

    def _risk_cell(
        self, value: float | None, kind: AssessmentKind, damage: float | None = None
    ) -> QTableWidgetItem:
        """Use current application risk colors without introducing new bands.

        Args:
            value: Probability percent or unavailable None.
            kind: Tool identity for intrinsic damage color.
            damage: Matching Job damage, absent for worker schedule averages.

        Returns:
            Read-only colored item retaining exact values in its tooltip.
        """
        item = QTableWidgetItem("—" if value is None else f"{value:.1f}%")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if value is not None:
            color = (
                measurement_color(kind, damage)
                if damage is not None
                else RISK_APPEARANCES[classify_probability(value)].color_hex
            )
            item.setBackground(QColor(color))
            item.setToolTip(f"{value!r}% · existing application classification")
        return item

    def _render_baseline(self) -> None:
        """Show selected complete tools and explicitly unavailable other columns.

        Args:
            None.

        Returns:
            None; no stored risk or assessment ownership changes.
        """
        kinds = self.kinds()
        self.baseline_context.setText(
            f"{len(self.session.workers)} workers · {len(self.session.jobs)} Jobs · "
            f"{self.blocks.value()} equal blocks · "
            "Before optimization · "
            f"Analysis: {', '.join(_TOOL_NAMES[k] for k in kinds)}"
        )
        self.worker_baseline.setMinimumHeight(
            max(260, min(6, len(self.session.workers)) * 46 + 55)
        )
        self.job_baseline.setMinimumHeight(
            max(260, min(6, len(self.session.jobs)) * 46 + 55)
        )
        self.worker_baseline.setRowCount(len(self.session.workers))
        self.job_baseline.setRowCount(len(self.session.jobs))
        for row, worker in enumerate(self.session.workers):
            self.worker_baseline.setItem(
                row, 0, QTableWidgetItem(self.session.worker_names[worker])
            )
            for column, kind in enumerate(AssessmentKind, 1):
                average = (
                    prototype_worker_values(
                        self.session.current, self.session.jobs, kind
                    )[row]
                    if kind in kinds
                    else None
                )
                self.worker_baseline.setItem(
                    row, column, self._risk_cell(average, kind)
                )
        for row, job in enumerate(self.session.jobs):
            self.job_baseline.setItem(row, 0, QTableWidgetItem(job.name))
            for column, kind in enumerate(AssessmentKind, 1):
                value = job.measurements.get(kind) if kind in kinds else None
                self.job_baseline.setItem(
                    row,
                    column,
                    self._risk_cell(
                        value.probability_percent if value else None,
                        kind,
                        value.cumulative_damage if value else None,
                    ),
                )

    def _build_optimization(self) -> None:
        """Prepare bounded real solving and an explicit non-applied-constraint warning.

        Args:
            None.

        Returns:
            None; solver threads are created only by the explicit Run button.
        """
        page = self.page_layouts[6]
        card, layout = prototype_card(
            "Find a more balanced rotation",
            "The same Jobs and total workload are retained. Improvement may "
            "reduce maximum exposure or spread while the overall mean stays "
            "unchanged.",
        )
        row = QHBoxLayout()
        self.solve_caption = QLabel()
        self.solve_caption.setObjectName("cardTitle")
        row.addWidget(self.solve_caption, 1)
        row.addWidget(QLabel("Time limit per stage"))
        self.time_limit = QSpinBox()
        self.time_limit.setRange(1, 30)
        self.time_limit.setSuffix(" seconds")
        self.time_limit.setValue(5)
        row.addWidget(self.time_limit)
        self.solve_button = prototype_button(
            "Run optimization", lambda: self.act(self.start_solve), primary=True
        )
        row.addWidget(self.solve_button)
        layout.addLayout(row)
        self.solve_progress = QProgressBar()
        self.solve_progress.setRange(0, 0)
        self.solve_progress.hide()
        layout.addWidget(self.solve_progress)
        self.solve_status = QLabel("Ready to run. No preview has been generated.")
        self.solve_status.setWordWrap(True)
        layout.addWidget(self.solve_status)
        page.addWidget(card)
        self.optimized_tabs = QTabWidget()
        self.optimized_tables: dict[AssessmentKind, QTableWidget] = {}
        self._sync_optimized_tabs()
        page.addWidget(self.optimized_tabs)
        self.result_explanation = self._notice(
            "Job risks appear in block cells; worker schedule averages summarize "
            "the full row. Changing tool tabs does not run another optimization."
        )
        page.addWidget(self.result_explanation)
        self.constraint_notice = self._notice(
            "Prototype limitation: fixed/excluded workers and high-risk "
            "sequencing rules are NOT enforced. Review this result only as an "
            "unconstrained demonstration."
        )
        page.addWidget(self.constraint_notice)
        self.optimized_tabs.currentChanged.connect(self._render_optimized_view)
        page.addStretch(1)

    def _sync_optimized_tabs(self) -> None:
        """Match matrix tabs to analyzed tools and retain an available active tab.

        Args:
            None. Read the current one-tool/all-three analysis choice.

        Returns:
            None; detached tables are deleted when the analyzed tool set changes.
            Switching tabs never changes the optimization objective or schedule.
        """
        kinds = self.kinds()
        selected = self.optimized_tabs.currentWidget()
        selected_kind = next(
            (
                kind
                for kind, table in self.optimized_tables.items()
                if table is selected
            ),
            kinds[0],
        )
        if tuple(self.optimized_tables) != kinds:
            with QSignalBlocker(self.optimized_tabs):
                self.optimized_tabs.clear()
                for table in self.optimized_tables.values():
                    table.deleteLater()
                self.optimized_tables = {}
                for kind in kinds:
                    table = self._table(["Worker"], 300)
                    self.optimized_tables[kind] = table
                    self.optimized_tabs.addTab(table, _TOOL_NAMES[kind])
                self.optimized_tabs.setCurrentIndex(
                    kinds.index(selected_kind) if selected_kind in kinds else 0
                )
        self.optimized_tabs.setEnabled(self.worker is None)

    def _render_optimized_view(self) -> None:
        """Render per-tool matrices for one solution and describe the active tab.

        Args:
            None. Read only the active tool tab and a validated solution.

        Returns:
            None; no solver call, input mutation, history entry or project write.
            Without a solution all tool tables remain empty.
        """
        if self.solution is None:
            for table in self.optimized_tables.values():
                table.setRowCount(0)
            return
        kind = self.kinds()[self.optimized_tabs.currentIndex()]
        for tool, table in self.optimized_tables.items():
            self._render_schedule(table, self.solution.schedule, tool)
        stages = ", ".join(stage.value for stage in self.solution.stages)
        analyzed = ", ".join(_TOOL_NAMES[item] for item in self.kinds())
        self.solve_status.setText(
            f"{self.solution.backend.value.upper()} completed · {stages}. "
            f"Optimized using {analyzed}. Showing {_TOOL_NAMES[kind]} values "
            "for the same schedule; worker rules were not enforced."
        )

    def _render_schedule(
        self,
        table: QTableWidget,
        schedule: tuple[WorkerRotation, ...],
        kind: AssessmentKind,
    ) -> None:
        """Render a real accepted/optimized schedule with complete Job names and risks.

        Args:
            table: Read-only scratch schedule table.
            schedule: Baseline or independently validated optimizer output.
            kind: Display tool for cell values/colors and worker schedule averages;
                does not select the solver objective.

        Returns:
            None; block columns share spare width while worker/average columns fit
            their content. No application scheme widget is altered.
        """
        blocks = len(schedule[0].target_keys)
        table.setColumnCount(blocks + 2)
        table.setHorizontalHeaderLabels(
            [
                "Worker",
                *(f"Block {i + 1}" for i in range(blocks)),
                "Schedule average",
            ]
        )
        table.setMinimumHeight(max(260, min(6, len(schedule)) * 46 + 55))
        table.setRowCount(len(schedule))
        jobs = {job.key: job for job in self.session.jobs}
        averages = prototype_worker_values(schedule, self.session.jobs, kind)
        for row, rotation in enumerate(schedule):
            table.setItem(
                row, 0, QTableWidgetItem(self.session.worker_names[rotation.worker_id])
            )
            for column, key in enumerate(rotation.target_keys, 1):
                job = jobs[key]
                value = job.measurements[kind]
                item = self._risk_cell(
                    value.probability_percent, kind, value.cumulative_damage
                )
                item.setText(f"{job.name}\n{value.probability_percent:.1f}%")
                table.setItem(row, column, item)
            table.setItem(row, blocks + 1, self._risk_cell(averages[row], kind))
        header = table.horizontalHeader()
        assert header is not None
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(blocks + 1, QHeaderView.ResizeToContents)

    def start_solve(self) -> None:
        """Freeze validated equal-block input and start the unchanged real optimizer.

        Args:
            None.

        Returns:
            None; work runs on an owned thread while inputs/navigation are blocked.

        Raises:
            ValueError: Current selected values or staffing are incomplete.
        """
        if self.worker is not None:
            return
        self._ready_problem()
        problem = self.session.problem(self.kinds(), self.time_limit.value())
        self.solution = None
        for table in self.optimized_tables.values():
            table.setRowCount(0)
        self.worker = PrototypeSolveThread(self.optimizer, problem, self.kinds(), self)
        self.worker.finished.connect(self._solve_finished)
        self._set_solving(True)
        self.solve_status.setText(
            "Solving with HiGHS · two stages…"
            if len(self.kinds()) == 3
            else "Solving with CBC…"
        )
        self.worker.start()

    def _set_solving(self, active: bool) -> None:
        """Keep solver inputs stable and the dialog alive during an owned solve.

        Args:
            active: True while a bounded solver is running.

        Returns:
            None; no thread termination or hidden database operation occurs.
        """
        self.drawer.setEnabled(not active)
        self.back.setEnabled(not active)
        self.next.setEnabled(not active)
        self.solve_button.setEnabled(not active)
        self.time_limit.setEnabled(not active)
        self.optimized_tabs.setEnabled(not active)
        self.solve_progress.setVisible(active)

    def _solve_finished(self) -> None:
        """Publish a validated preview only after its solver thread has finished.

        Args:
            None.

        Returns:
            None; a pending Close suppresses results and safely disposes the window.
        """
        worker = self.worker
        assert worker is not None
        worker.wait()
        self.solution = worker.solution
        error = worker.error
        worker.deleteLater()
        self.worker = None
        self._set_solving(False)
        if self._close_pending:
            self.reject()
            return
        if self.solution is None:
            self.solve_status.setText("No valid preview was produced.")
            self._show_error(error or "The solve was cancelled.")
            return
        self._sync_optimized_tabs()
        self._render_optimized_view()
        self.next.setEnabled(True)
        self.next.setText("Compare results  →")

    def _build_comparison(self) -> None:
        """Prepare per-tool summary cards, worker metrics and inactive report controls.

        Args:
            None.

        Returns:
            None; this page has no export writer or Apply-to-project operation.
        """
        page = self.page_layouts[7]
        self.comparison_cards = QHBoxLayout()
        self.metric_cards: dict[AssessmentKind, tuple[QWidget, QLabel]] = {}
        for kind in AssessmentKind:
            card, layout = prototype_card(
                _TOOL_NAMES[kind], "Maximum worker schedule average"
            )
            value = QLabel("—")
            value.setObjectName("metricValue")
            layout.addWidget(value)
            self.metric_cards[kind] = (card, value)
            self.comparison_cards.addWidget(card)
        page.addLayout(self.comparison_cards)
        card, layout = prototype_card(
            "Statistical comparison",
            "Compare worker schedule averages from step 02 with the optimized "
            "assignments, separately for each tool. Job values remain unchanged; "
            "individual worker assessments are not used. Changes are percentage "
            "points; SD is the population SD.",
        )
        self.statistics = self._table(
            [
                "Tool",
                "Metric",
                "Before optimization",
                "After optimization",
                "Change (pp)",
            ],
            300,
        )
        layout.addWidget(self.statistics)
        page.addWidget(card)
        page.addWidget(
            self._notice(
                "These are unconstrained prototype results. Job hazards do not "
                "disappear through redistribution; engineering changes may still "
                "be required. No compliance claim or project update is made."
            )
        )
        reports = QHBoxLayout()
        reports.addStretch(1)
        for text in ("Save report", "Export PDF report"):
            button = QPushButton(text)
            button.setEnabled(False)
            button.setToolTip(
                "Report output is not implemented. This preview writes no files."
            )
            reports.addWidget(button)
        page.addLayout(reports)
        page.addStretch(1)

    def _render_comparison(self) -> None:
        """Display truthful changes without promising population-mean reduction.

        Args:
            None.

        Returns:
            None; no historical risk snapshot or report is persisted.
        """
        assert self.solution is not None
        kinds = self.kinds()
        self.statistics.setRowCount(4 * len(kinds))
        row = 0
        for kind in AssessmentKind:
            card, value = self.metric_cards[kind]
            card.setVisible(kind in kinds)
            if kind not in kinds:
                continue
            before = prototype_statistics(
                prototype_worker_values(self.session.current, self.session.jobs, kind)
            )
            after = prototype_statistics(
                prototype_worker_values(self.solution.schedule, self.session.jobs, kind)
            )
            value.setText(f"{before[1]:.1f}%  →  {after[1]:.1f}%")
            for label, old, new in zip(
                ("Mean", "Maximum", "Population SD", "Range"),
                before,
                after,
                strict=True,
            ):
                for column, text in enumerate(
                    (
                        _TOOL_NAMES[kind],
                        label,
                        f"{old:.1f}%",
                        f"{new:.1f}%",
                        f"{round(new - old, 1) or 0.0:+.1f}",
                    )
                ):
                    self.statistics.setItem(row, column, QTableWidgetItem(text))
                row += 1

    def _invalidate_solution(self) -> None:
        """Discard stale optimization output after changes to scratch scientific inputs.

        Args:
            None.

        Returns:
            None; no main-window history/dirty marker is touched.
        """
        self.solution = None
        if hasattr(self, "optimized_tables"):
            for table in self.optimized_tables.values():
                table.setRowCount(0)
            self.solve_status.setText(
                "Ready to run. Input changes require a fresh solve."
            )
        if hasattr(self, "next") and self._page == 6:
            self.next.setEnabled(self.worker is None)

    def _show_error(self, message: str) -> None:
        """Show a local actionable message without an unowned modal dialog.

        Args:
            message: English field/staffing/calculation/solver explanation.

        Returns:
            None; invalid controls retain their text for correction.
        """
        self.error.setText(message)
        self.error.show()

    def act(self, operation: Callable[[], None]) -> None:
        """Translate expected scratch validation errors into an inline explanation.

        Args:
            operation: Owned synchronous prototype operation.

        Returns:
            None; unexpected programming/adapter failures are not silently hidden.
        """
        self.error.hide()
        try:
            operation()
        except ValueError as error:
            self._show_error(str(error))

    def advance(self) -> None:
        """Advance one substep or close the final disposable comparison page.

        Args:
            None.

        Returns:
            None; never invokes Save or creates an assessment.
        """
        if self._page == 7:
            self.reject()
        elif self._page == 0 and not self.yes.isChecked():
            self._show_error("The No path is not implemented. Select Yes.")
        else:
            self.go(self._page + 1)

    def go(self, index: int) -> None:
        """Navigate review steps freely, retaining scratch data across Back.

        Args:
            index: Any existing page; readiness is checked only for calculations.

        Returns:
            None; expected errors retain the current page and its visible inputs.
        """
        if self.worker is not None or not 0 <= index < len(_PAGES):
            return
        self.act(lambda: self._navigate(index))

    def _navigate(self, index: int) -> None:
        """Review any step freely; readiness gates calculations rather than navigation.

        Args:
            index: Existing page index selected by Back, Continue or the sidebar.

        Returns:
            None; unfinished matrix/selection drafts survive backward navigation.
        """
        if self._page == 4:
            # Intermediate numeric text stays alive in the same owned grids.
            with suppress(ValueError):
                self._commit_grids()
        self._accept_jobs(False)
        self._accept_workers(False)
        self._accept_matrix(False)
        self._synchronize_choices()
        if index == 4:
            self._selected_job = min(self._selected_job, len(self.session.jobs) - 1)
            self._refresh_progress()
            self._select_assessment_job(self._selected_job)
        elif index == 5:
            try:
                self._ready_problem()
            except ValueError as error:
                self.worker_baseline.setRowCount(0)
                self.job_baseline.setRowCount(0)
                self.baseline_context.setText("Baseline not ready: " + str(error))
            else:
                self._render_baseline()
        elif index == 6:
            self._sync_optimized_tabs()
            self._render_optimized_view()
            self.solve_caption.setText(
                "All three tools · HiGHS"
                if len(self.kinds()) == 3
                else f"{_TOOL_NAMES[self.kinds()[0]]} · CBC"
            )
        elif index == 7:
            if self.solution is not None:
                self._render_comparison()
            else:
                self.statistics.setRowCount(0)
                for kind, (card, value) in self.metric_cards.items():
                    card.setVisible(kind in self.kinds())
                    value.setText("Not run yet")
                self._show_error(
                    "No optimized result yet. Review freely, then Run optimization."
                )
        self._page = index
        self._render_page()

    def _synchronize_choices(self) -> None:
        """Reconcile changed setup counts/scope without rebuilding unchanged drafts.

        Args:
            None.

        Returns:
            None; nonmatching setup clears only obsolete scratch solver output.
        """
        signature = (
            self.jobs_count.value(),
            self.workers_count.value(),
            self._scope_path,
            self._shift_id,
        )
        if signature != self._setup_signature:
            self._populate_jobs()
            self._accept_jobs(False)
            self._populate_workers()
            self._accept_workers(False)
            self._setup_signature = signature
            self._invalidate_solution()
        self._populate_matrix()
        self._accept_matrix(False)

    def _ready_problem(self) -> None:
        """Require actual complete inputs only before baseline calculation or solving.

        Args:
            None.

        Returns:
            None; display-only restrictions are deliberately not required.

        Raises:
            ValueError: No branch, count/selection/matrix or selected-tool inputs fail.
        """
        if not self.yes.isChecked():
            raise ValueError("The No path is not implemented. Select Yes to run.")
        if self.jobs_count.value() != self.workers_count.value():
            raise ValueError(
                "Choose the same number of Jobs and workers; restrictions are optional."
            )
        self._commit_grids()
        self._accept_jobs()
        self._accept_workers()
        self._accept_matrix()
        self.session.problem(self.kinds(), self.time_limit.value())

    def _render_page(self) -> None:
        """Synchronize headings/navigation without writing or recalculating data.

        Args:
            None.

        Returns:
            None; footer controls stay outside the scrollable content.
        """
        eyebrow, title, note = _PAGES[self._page]
        self.eyebrow.setText(eyebrow)
        self.heading.setText(title)
        self.subtitle.setText(note)
        self.pages.setCurrentIndex(self._page)
        for index, button in enumerate(self.drawer.buttons):
            button.setChecked(index == self._page)
            button.setEnabled(self.worker is None)
        self.back.setEnabled(self._page > 0)
        self.close_preview.setVisible(self._page != 7)
        self.next.setEnabled(self._page != 0 or self.yes.isChecked())
        self.next.setText(
            "Close preview"
            if self._page == 7
            else "Compare results  →"
            if self._page == 6
            else "Continue  →"
        )
        self.position.setText(
            f"Page {self._page + 1} of {len(_PAGES)} · English · cm / N"
        )

    def reject(self) -> None:
        """Discard all inputs; defer closing until a running solver safely completes.

        Args:
            None.

        Returns:
            None; Escape/window Close cannot destroy an active QThread.
        """
        if self.worker is not None:
            self._close_pending = True
            self.worker.requestInterruption()
            self.solve_status.setText(
                "Finishing the current solver call before closing; its result "
                "will be discarded…"
            )
            return
        self.drawer.animation.stop()
        self.drawer.hide_timer.stop()
        self.session.dispose()
        self._job_cache.clear()
        self.available_jobs.clear()
        super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 - Qt override
        """Honor the same safe discard policy for window-manager close requests.

        Args:
            event: Native close request, ignored only while the solver still owns input.

        Returns:
            None; the modal host owns final widget deletion.
        """
        if event is not None:
            if self.worker is not None:
                self.reject()
                event.ignore()
            else:
                super().closeEvent(event)
