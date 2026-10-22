"""Workplace-first assignment intent shared by Worker Management and association.

Presentation adapter. Select a real station through the existing location hierarchy,
then a project shift and an optional compatible Job. Inputs are immutable snapshots;
acceptance returns explicit identities only. This dialog never creates assignments,
writes projects or infers membership from displayed labels.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.language import Language
from ergotools.domain.plot_scope import hierarchy_paths
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.theme.worker_management import (
    WORKER_MANAGEMENT_STYLE,
)
from ergotools.presentation.desktop.worker_text import worker_text


class WorkplaceAssignmentDialog(QDialog):
    """Return a station/shift and optional placement without committing a mutation.

    Attributes:
        selected_workplace: Exact current workplace intent, absent until a station and
            shift are selected.
        selected_placement_id: Optional compatible Job placement identity.
        tree: Location hierarchy; only actual station leaves establish a workplace.
        shift: Saved project shift choices, independent of the location tree.
        job: Optional Jobs filtered to the selected workplace and shift.
    """

    def __init__(
        self,
        hierarchy: WorkHierarchy,
        jobs: JobCatalog,
        worker_id: str,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        current: WorkplaceContext | None = None,
        placement_id: int | None = None,
        reuse_existing: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Build a hierarchy, shift and optional Job picker from saved snapshots.

        Args:
            hierarchy: Saved location/shift membership; empty parents remain visible.
            jobs: Same-project Job placements and worker workplace assignments.
            worker_id: Literal saved worker identity shown in supporting text.
            icons: Approved packaged assets, never loaded from the reference tree.
            language: English/Spanish labels; saved identifiers stay literal.
            current: Optional exact workplace to preselect when changing an assignment.
            placement_id: Optional matching Job to preselect with current.
            reuse_existing: Association mode reuses an existing active worker context
                and locks its Job rather than silently reclassifying it.
            parent: Qt owner, independent of any worker-management implementation.

        Returns:
            None. Opening/cancelling the picker never writes data.

        Raises:
            ValueError: Supplied catalogs belong to different projects.
        """
        super().__init__(parent)
        jobs.validate_hierarchy(hierarchy)
        self._jobs, self._worker_id = jobs, worker_id
        self._language, self._reuse_existing = language, reuse_existing
        self.selected_workplace: WorkplaceContext | None = None
        self.selected_placement_id: int | None = None
        self._stations: dict[StationKey, QTreeWidgetItem] = {}
        self.setObjectName("workplaceAssignmentDialog")
        self.setWindowTitle(
            self._text("Associate assessment" if reuse_existing else "Assign workplace")
        )
        self.setMinimumSize(740, 560)
        self.setStyleSheet(WORKER_MANAGEMENT_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        self.heading = QLabel(self.windowTitle())
        self.heading.setObjectName("dialogTitle")
        layout.addWidget(self.heading)
        description = QLabel(
            self._text(
                (
                    "Choose the workplace and shift for {worker_id}. "
                    "An existing assignment "
                    "is reused; otherwise one is created with the optional Job "
                    "on acceptance."
                )
                if reuse_existing
                else (
                    "Choose the workplace and shift for {worker_id}, "
                    "then optionally a Job."
                )
            ).format(worker_id=worker_id)
        )
        description.setObjectName("supportingText")
        description.setWordWrap(True)
        layout.addWidget(description)
        self.tree = QTreeWidget()
        self.tree.setObjectName("workplaceTree")
        self.tree.setHeaderLabels(
            [self._text("Workplace hierarchy"), self._text("Type")]
        )
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        items: dict[tuple[str, ...], QTreeWidgetItem] = {}
        for path in hierarchy_paths(hierarchy):
            kind = ("Plant", "Section", "Line", "Station")[len(path) - 1]
            item = QTreeWidgetItem([path[-1], self._text(kind)])
            item.setIcon(0, icons[kind.lower()])
            if len(path) == 1:
                self.tree.addTopLevelItem(item)
            else:
                items[path[:-1]].addChild(item)
            items[path] = item
            if len(path) == 4:
                station = StationKey(*path)
                self._stations[station] = item
                item.setData(0, Qt.ItemDataRole.UserRole, station)
        self.tree.expandToDepth(2)
        layout.addWidget(self.tree, 1)
        form = QFormLayout()
        self.shift, self.job = QComboBox(), QComboBox()
        for shift in hierarchy.work.shifts:
            self.shift.addItem(shift, shift)
        form.addRow(self._text("Shift"), self.shift)
        form.addRow(self._text("Job (optional)"), self.job)
        layout.addLayout(form)
        self.note = QLabel()
        self.note.setObjectName("notificationLabel")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        accept_button = buttons.button(QDialogButtonBox.Ok)
        cancel = buttons.button(QDialogButtonBox.Cancel)
        assert accept_button is not None and cancel is not None
        self.accept_button = accept_button
        self.accept_button.setText(self.windowTitle())
        self.accept_button.setObjectName("primaryOutlineButton")
        self.accept_button.setIcon(icons["station"])
        self.accept_button.setIconSize(QSize(24, 24))
        cancel.setText(self._text("Cancel"))
        cancel.setIcon(icons["cancel"])
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.tree.itemSelectionChanged.connect(self.update_selection)
        self.shift.currentIndexChanged.connect(self.update_selection)
        self.job.currentIndexChanged.connect(self._job_changed)
        self.update_selection()
        if current is not None:
            self.select_workplace(current, placement_id)

    def _text(self, text: str) -> str:
        """Resolve application-owned captions without translating saved identifiers.

        Args:
            text: English localization key.

        Returns:
            Existing English/Spanish worker workflow wording.
        """
        return worker_text(text, self._language)

    def select_workplace(
        self, workplace: WorkplaceContext, placement_id: int | None = None
    ) -> None:
        """Project an exact existing assignment when opening Change or association.

        Args:
            workplace: Explicit station ancestry and shift to select, never a caption.
            placement_id: Optional Job placement at that workplace to preselect.

        Returns:
            None. Missing membership leaves selection unaccepted; no fallback is made.
        """
        self.shift.setCurrentIndex(self.shift.findData(workplace.shift_id))
        station = StationKey(
            workplace.plant_name,
            workplace.section_name,
            workplace.line_name,
            workplace.station_id,
        )
        self.tree.setCurrentItem(self._stations.get(station))
        self.update_selection()
        if not self._reuse_existing:
            self.job.setCurrentIndex(max(0, self.job.findData(placement_id)))

    def update_selection(self) -> None:
        """Filter optional Jobs and reuse existing ownership in association mode.

        Args:
            None.

        Returns:
            None. Parent rows/empty catalogs cannot be accepted. Existing association
            Job ownership is shown and locked, including a retained inactive Job.
        """
        item = self.tree.currentItem()
        station = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        shift = self.shift.currentData()
        self.selected_workplace = (
            station.at_shift(shift)
            if isinstance(station, StationKey) and isinstance(shift, str)
            else None
        )
        self.selected_placement_id = None
        with QSignalBlocker(self.job):
            self.job.clear()
            self.job.addItem(self._text("No Job"), None)
            active_jobs = {job.job_id: job for job in self._jobs.jobs if job.active}
            for placement in self._jobs.placements:
                if (
                    placement.active
                    and placement.job_id in active_jobs
                    and placement.workplace == self.selected_workplace
                ):
                    self.job.addItem(
                        f"{placement.job_id} | {active_jobs[placement.job_id].name}",
                        placement.placement_id,
                    )
            existing = (
                next(
                    (
                        a
                        for a in self._jobs.assignments
                        if a.active
                        and a.worker.worker_id == self._worker_id
                        and a.worker.workplace == self.selected_workplace
                    ),
                    None,
                )
                if self._reuse_existing
                else None
            )
            if existing is not None:
                index = self.job.findData(existing.placement_id)
                if index < 0:
                    placement = next(
                        p
                        for p in self._jobs.placements
                        if p.placement_id == existing.placement_id
                    )
                    job = next(
                        j for j in self._jobs.jobs if j.job_id == placement.job_id
                    )
                    self.job.addItem(
                        f"{job.job_id} | {job.name}", placement.placement_id
                    )
                    index = self.job.count() - 1
                self.job.setCurrentIndex(index)
            self.job.setEnabled(
                self.selected_workplace is not None
                and self.job.count() > 1
                and existing is None
            )
        self._job_changed()
        self.accept_button.setEnabled(self.selected_workplace is not None)
        self.note.setText(
            self._text(
                "Existing workplace assignment will be reused; its Job stays unchanged."
                if existing is not None
                else (
                    "A Job is optional. Only Jobs available at this workplace "
                    "and shift are shown."
                )
                if self.selected_workplace is not None
                else (
                    "Select a station and shift. Create them in Organization "
                    "if none are available."
                )
            )
        )

    def _job_changed(self) -> None:
        """Read the optional explicit placement identity after dropdown selection.

        Args:
            None.

        Returns:
            None. None is a valid No Job choice, never an incomplete assignment.
        """
        self.selected_placement_id = self.job.currentData()

    def accept_selection(self) -> None:
        """Accept only a complete workplace/shift; Job remains optional.

        Args:
            None.

        Returns:
            None. The host owns validation, consent, transaction and saved history.
        """
        if self.selected_workplace is not None:
            self.accept()
