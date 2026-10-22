"""Reviewed original header, worker navigation, association bar and footer.

Ported from setupTopWidgets/setupNavigationButtons/setupTabsTopControls and
setupWorkspaceFooter. This view owns selector/filter state, never SQL or drafts.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from string import ascii_uppercase

from PyQt5.QtCore import QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkCatalog
from ergotools.presentation.desktop.combo_popup import style_combo_popup
from ergotools.presentation.desktop.main_navigation_text import navigation_text
from ergotools.presentation.worker_options import WorkerOrder, worker_options

# Original main toolbar action ordering, English captions and explanatory tooltips.
_TOOLBAR = (
    ("undo", "Undo", "Undo the previous edit."),
    ("redo", "Redo", "Redo the next edit."),
    ("new", "New", "Create a new project."),
    ("open", "Open", "Open an existing Ergo Tools project."),
    ("save", "Save", "Save the current project and assessment data."),
    ("plot", "PLOT", "Open the Plant-Layout Organizational Tool."),
    ("jrot", "JROT", "Open the Job Rotation Optimization Tool."),
    ("organization", "Organization", "Manage workplace organization."),
    ("jobs", "Jobs", "Manage Jobs and current risk values."),
)


class MainNavigation(QWidget):
    """Original shared controls with explicit worker IDs and injected actions."""

    def __init__(
        self,
        icons: Mapping[str, QIcon],
        actions: Mapping[str, Callable[[], None]],
        select_worker: Callable[[str], None],
        *,
        parent: QWidget | None = None,
    ) -> None:
        """Build reference controls; unsupported actions stay visibly disabled.

        Args:
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            actions: Host operations indexed by existing navigation action identity.
            select_worker: Callback receiving an exact saved worker ID after selector
                acceptance.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self._select_worker = select_worker
        self._catalog: WorkCatalog | None = None
        self._current_worker: str | None = None
        self._filter: str | None = None
        self._order = WorkerOrder.ID
        self.language = Language.ENGLISH
        self._arrows: list[QLabel] = []
        self._texts: list[tuple[QLabel | QPushButton | QAction, str, str]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QFrame(self)
        header.setObjectName("brandHeader")
        header.setFixedHeight(112)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 10, 8)
        identity = QHBoxLayout()
        identity.setSpacing(12)
        logo = QLabel()
        logo.setObjectName("brandLogo")
        logo.setFixedSize(82, 82)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setToolTip("ErgoTools")
        logo.setPixmap(icons["ergotools_logo"].pixmap(80, 80))
        identity.addWidget(logo)
        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        brand = QLabel("ErgoTools")
        brand.setObjectName("brandName")
        self.project_label = QLabel()
        self.project_label.setObjectName("projectName")
        brand_box.addWidget(brand)
        brand_box.addWidget(self.project_label)
        identity.addLayout(brand_box)
        header_layout.addLayout(identity, 1)
        self.toolbar = QToolBar(header)
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setFixedHeight(90)
        self.toolbar.setIconSize(QSize(38, 38))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar_actions: dict[str, QAction] = {}
        for key, caption, tip in _TOOLBAR:
            icon = (
                "job_management"
                if key == "jobs"
                else "plant"
                if key == "organization"
                else key
            )
            action = QAction(icons[icon], caption, self)
            self.toolbar_actions[key] = action
            self._texts.append((action, caption, tip))
            if key in actions:
                action.triggered.connect(actions[key])
            else:
                action.setEnabled(False)
            self.toolbar.addAction(action)
            widget = self.toolbar.widgetForAction(action)
            assert widget is not None
            widget.setFixedHeight(75)
            if key in ("undo", "redo"):
                # Mouse history commands leave native typing ownership with fields
                # only for keyboard shortcuts; the toolbar replays project history.
                widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if key in ("redo", "save", "jrot"):
                self.toolbar.addSeparator()
        # Menu-only operations retain their callbacks without occupying toolbar space.
        for key, caption in (
            ("settings", "Settings"),
            ("help", "Help"),
            ("export", "Export"),
        ):
            action = QAction(icons[key], caption, self)
            action.triggered.connect(actions[key])
            self.toolbar_actions[key] = action
            self._texts.append((action, caption, caption))
        # Preserve mainToolbar CSS spacing/padding when Qt caches inherited metrics.
        toolbar_layout = self.toolbar.layout()
        assert toolbar_layout is not None
        toolbar_layout.setSpacing(3)
        toolbar_layout.setContentsMargins(7, 7, 7, 7)
        header_layout.addWidget(self.toolbar)
        layout.addWidget(header)
        worker_bar = QFrame()
        worker_bar.setObjectName("contextBar")
        worker_bar_layout = QVBoxLayout(worker_bar)
        worker_bar_layout.setContentsMargins(14, 7, 12, 7)
        worker_bar_layout.setSpacing(2)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        worker_icon = QLabel()
        worker_icon.setPixmap(icons["worker"].pixmap(26, 26))
        worker_icon.setFixedSize(28, 28)
        worker_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        worker_icon.setToolTip("Worker associated with the assessment currently shown.")
        self._worker_icon = worker_icon
        row.addWidget(worker_icon)
        worker_label = QLabel("Worker")
        worker_label.setObjectName("contextLabel")
        self._texts.append((worker_label, "Worker", ""))
        row.addWidget(worker_label)
        self.workers = QComboBox()
        style_combo_popup(self.workers)
        self.workers.setMinimumWidth(280)
        self.workers.currentIndexChanged.connect(self._worker_changed)
        row.addWidget(self.workers, 1)
        self.buttons: dict[str, QPushButton] = {}
        self.order_button = self._button(
            "order",
            "A-Z",
            "alphabet_order",
            "Change worker ordering.",
            icons,
            self.change_order,
        )
        row.addWidget(self.order_button)
        for key, caption, icon, tip in (
            ("workers", "Workers", "worker_management", "Open Worker Management."),
            (
                "search",
                "Search",
                "search",
                (
                    "Find and open a saved assessment by worker, "
                    "workplace, and the active ergonomic tool."
                ),
            ),
            (
                "transfer",
                "Transfer",
                "transfer_worker_data",
                "Transfer worker assessment data to another context.",
            ),
            (
                "refresh",
                "Refresh",
                "refresh",
                "Reload workers and assessment context values from the project.",
            ),
        ):
            button = self._button(key, caption, icon, tip, icons, actions.get(key))
            if key == "transfer":
                button.setIconSize(QSize(30, 30))
            row.addWidget(button)
        row.addSpacing(10)
        self.nav_buttons = []
        for caption, icon, position in (
            ("First worker", "first", 0),
            ("Previous worker", "previous", -1),
            ("Next worker", "next", 1),
            ("Last worker", "last", 2),
        ):
            button = QPushButton()
            button.setObjectName("navButton")
            button.setFixedSize(38, 36)
            button.setIcon(icons[icon])
            button.setIconSize(QSize(24, 24))
            button.clicked.connect(
                lambda checked, position=position: self.navigate(position)
            )
            self._texts.append((button, "", caption))
            self.nav_buttons.append(button)
            row.addWidget(button)
        worker_bar_layout.addLayout(row)
        alphabet_row = QHBoxLayout()
        alphabet_row.setContentsMargins(100, 0, 0, 0)
        alphabet_row.setSpacing(3)
        alphabet_label = QLabel("Last name")
        alphabet_label.setObjectName("supportingText")
        alphabet_label.setFixedWidth(68)
        alphabet_label.setAlignment(
            Qt.AlignmentFlag(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        )
        self._texts.append(
            (
                alphabet_label,
                "Last name",
                ("Filter the worker selector by the first letter of the last name."),
            )
        )
        alphabet_row.addWidget(alphabet_label)
        alphabet_row.addSpacing(5)
        self.alphabet_group = QButtonGroup(self)
        self.alphabet_group.setExclusive(True)
        self.alphabet_buttons: dict[str, QPushButton] = {}
        for value in ("All", *ascii_uppercase):
            button = QPushButton(value)
            button.setObjectName("mainAlphabetButton")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.clicked.connect(
                lambda checked, value=value: self.filter_workers(value)
            )
            self.alphabet_group.addButton(button)
            self.alphabet_buttons[value] = button
            alphabet_row.addWidget(button)
        alphabet_row.addStretch(1)
        worker_bar_layout.addLayout(alphabet_row)
        layout.addWidget(worker_bar)
        self.context_frame = QFrame(self)
        self.context_frame.setObjectName("contextBar")
        self.context_frame.hide()
        self._context_project: str | None = None
        self._organization_present = False
        context_layout = QVBoxLayout(self.context_frame)
        context_layout.setContentsMargins(14, 6, 12, 6)
        context_layout.setSpacing(6)
        association = QHBoxLayout()
        association.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Assessment context")
        title.setObjectName("contextLabel")
        self._texts.append(
            (
                title,
                "Assessment context",
                (
                    "Worker, Job, workplace, and shift associated "
                    "with the active assessment."
                ),
            )
        )
        association.addWidget(title)
        context_widget = QWidget()
        summary = QHBoxLayout(context_widget)
        summary.setContentsMargins(0, 0, 0, 0)
        summary.setSpacing(5)
        self.context_labels = tuple(QLabel() for _ in range(5))
        for label in self.context_labels:
            label.setObjectName("contextSummary")
            summary.addWidget(label)
            arrow = QLabel()
            arrow.setObjectName("contextArrow")
            arrow.setPixmap(icons["next"].pixmap(14, 14))
            arrow.setFixedSize(16, 16)
            arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._arrows.append(arrow)
            arrow.setToolTip("Next workplace level")
            summary.addWidget(arrow)
        self.job_label = QLabel()
        self.job_label.setObjectName("contextSummary")
        summary.addWidget(self.job_label)
        summary.addStretch(1)
        association.addWidget(context_widget, 1)
        context_button = self._button(
            "context",
            "Select assessment context",
            "station",
            (
                "Select which classified Job and workplace "
                "assessment to view. This does not move data."
            ),
            icons,
            actions["context"],
        )
        context_button.setObjectName("primaryOutlineButton")
        context_button.setIconSize(QSize(24, 24))
        self.follow_worker_button = self._button(
            "follow_worker",
            "Follow worker",
            "",
            "Restore this worker's last-used valid assessment context.",
            icons,
            actions["follow_worker"],
        )
        self.keep_context_button = self._button(
            "keep_context",
            "Keep context",
            "",
            "Keep this workplace while navigating workers.",
            icons,
            actions["keep_context"],
        )
        self.context_mode_group = QButtonGroup(self)
        self.context_mode_group.setExclusive(True)
        for button in (self.keep_context_button, self.follow_worker_button):
            button.setCheckable(True)
            button.setObjectName("contextModeButton")
            self.context_mode_group.addButton(button)
            association.addWidget(button)
        self.follow_worker_button.setChecked(True)
        association.addWidget(context_button)
        organization = self._button(
            "organization",
            "Manage organization",
            "plant",
            "Manage plants, sections, lines, stations, and shifts.",
            icons,
            actions["organization"],
        )
        organization.setObjectName("primaryOutlineButton")
        organization.setFixedWidth(210)
        organization.setIconSize(QSize(26, 26))
        organization.hide()
        context_layout.addLayout(association)
        self.associate_button = self._button(
            "associate",
            "Associate assessment...",
            "station",
            "Associate this saved assessment; its inputs and results stay unchanged.",
            icons,
            actions.get("associate"),
        )
        context_layout.addWidget(self.associate_button, 0, Qt.AlignmentFlag.AlignRight)
        self.footer = QFrame(self)
        self.footer.setObjectName("workspaceFooter")
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        self.tool_label = QLabel("Tool: LiFFT")
        self.tool_label.setMinimumWidth(115)
        self.unit_label = QLabel()
        self.file_label = QLabel()
        footer_layout.addWidget(self.tool_label)
        footer_layout.addWidget(self.unit_label)
        self.context_toggle = QCheckBox(self.footer)
        self.context_toggle.setObjectName("contextLabel")
        self.context_toggle.toggled.connect(self.context_frame.setVisible)
        footer_layout.addWidget(self.context_toggle)
        footer_layout.addStretch()
        footer_layout.addWidget(self.file_label)
        self.footer.setAutoFillBackground(True)

    def update_context_visibility(
        self, project_id: str | None, has_organization: bool, language: Language
    ) -> None:
        """Show optional organization controls without reserving collapsed height.

        Args:
            project_id: Open project identity; None clears prior view state.
            has_organization: Real organization exists, including names such as Default.
            language: Interface language, independent of saved organization names.

        Returns:
            None. Empty projects start collapsed. Opening a project with organization,
            or adding its first plant, expands the controls. Manual collapse remains
            session-local; reopening a populated project expands it again.
        """
        self.context_toggle.setText(
            "Contexto de evaluación"
            if language is Language.SPANISH
            else "Assessment context"
        )
        self.context_toggle.setToolTip(
            "Mostrar u ocultar la organización opcional de la evaluación."
            if language is Language.SPANISH
            else "Show or hide optional assessment organization controls."
        )
        self.context_toggle.setEnabled(project_id is not None)
        if project_id != self._context_project or (
            has_organization and not self._organization_present
        ):
            self.context_toggle.setChecked(has_organization)
        self._context_project = project_id
        self._organization_present = has_organization
        self.context_frame.setVisible(self.context_toggle.isChecked())

    def _button(
        self,
        key: str,
        caption: str,
        icon: str,
        tip: str,
        icons: Mapping[str, QIcon],
        callback: Callable[[], None] | None,
    ) -> QPushButton:
        """Build one original styled navigation button with a packaged icon.

        Build one original styled navigation button with a packaged icon and optional
        host action.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.
            caption: Visible control heading; record identities remain separate item
                data.
            icon: Stable packaged icon identity; an empty string omits the icon.
            tip: Localized tooltip explaining the associated navigation action.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            callback: Optional operation connected to the control; absent callbacks
                leave it disabled.

        Returns:
            New styled owned navigation button; unavailable operations stay disabled.
        """
        button = QPushButton(caption)
        button.setObjectName("compactButton")
        if icon:
            button.setIcon(icons[icon])
        button.setIconSize(QSize(22, 22))
        self.buttons[key] = button
        self._texts.append((button, caption, tip))
        if callback is not None:
            button.clicked.connect(callback)
        else:
            button.setEnabled(False)
        return button

    def _text(self, text: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            text: Literal control text or user input; interpretation follows this
                method's stated policy.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        return navigation_text(text, self.language)

    def update_state(
        self,
        catalog: WorkCatalog | None,
        current_worker: str | None,
        workplace: WorkplaceContext | None,
        job: tuple[str, str] | None,
        project: str | None,
        system: MeasurementSystem,
        language: Language,
        *,
        project_loaded: bool = True,
    ) -> None:
        """Render committed ownership; blocked selectors never activate other data.

        Args:
            catalog: Immutable loaded catalog used for selection; no caption-based
                identity inference.
            current_worker: Saved worker ID owning the committed assessment, or None
                with no active owner.
            workplace: Exact committed workplace/shift context, or None for an unbound
                source.
            job: Optional stored job ID/name pair for the association bar.
            project: Current project's displayed name, or None when no project is
                loaded.
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            project_loaded: Whether navigation may expose project-dependent actions.

        Returns:
            None.
        """
        self.language = language
        self._catalog = catalog
        self._current_worker = current_worker
        if catalog is None:
            self._filter = None
        elif current_worker is not None and self._filter is not None:
            worker = next(w for w in catalog.workers if w.worker_id == current_worker)
            if not (worker.last_name or "").upper().startswith(self._filter):
                self._filter = None
        self._populate()
        for widget, caption, tip in self._texts:
            widget.setText(self._text(caption))
            widget.setToolTip(self._text(tip))
        organization = self.toolbar.widgetForAction(
            self.toolbar_actions["organization"]
        )
        assert organization is not None
        organization.setMinimumWidth(
            organization.fontMetrics().horizontalAdvance(self._text("Organization"))
            + 16
        )
        self.order_button.setText("A-Z" if self._order is WorkerOrder.ID else "0-9")
        self.workers.setToolTip(
            self._text(
                "Select the worker whose assessment data you want to view or edit."
            )
        )
        self._worker_icon.setToolTip(
            self._text("Worker associated with the assessment currently shown.")
        )
        for arrow in self._arrows:
            arrow.setToolTip(self._text("Next workplace level"))
        self.job_label.setToolTip(
            self._text("Job performed in this assessment context.")
        )
        self.tool_label.setToolTip(
            self._text("The ergonomic assessment tool currently selected.")
        )
        self.unit_label.setToolTip(
            self._text("The measurement system used by the current project.")
        )
        self.file_label.setToolTip(
            self._text("The project currently open in Ergo Tools.")
        )
        project_text = (
            project if project_loaded and project else self._text("No project loaded")
        )
        caption = self._text("Current Project") + ": " + project_text
        self.project_label.setText(
            caption
            + ("  •  " + self._text("Loaded") if project_loaded and project else "")
        )
        values = (
            (
                workplace.plant_name,
                workplace.section_name,
                workplace.line_name,
                workplace.station_id,
                workplace.shift_id,
            )
            if workplace is not None
            else ("—",) * 5
        )
        for label, level, value in zip(
            self.context_labels,
            ("Plant", "Section", "Line", "Station", "Shift"),
            values,
            strict=True,
        ):
            label.setText(self._text(level) + ": " + value)
            label.setToolTip(self._text(level) + ": " + value)
        self.job_label.setText(
            self._text("Job")
            + ": "
            + (" | ".join(job) if job else self._text("Unclassified"))
        )
        self.tool_label.setText(self._text("Tool") + ": LiFFT")
        self.unit_label.setText(
            self._text("Units") + ": " + self._text(system.value.capitalize())
        )
        self.file_label.setText(caption)
        for key in ("save", "jobs"):
            self.toolbar_actions[key].setEnabled(catalog is not None)
        for key in (
            "workers",
            "search",
            "refresh",
            "context",
            "organization",
            "follow_worker",
            "keep_context",
        ):
            self.buttons[key].setEnabled(catalog is not None)
        self.workers.setEnabled(catalog is not None and bool(catalog.workers))
        self.order_button.setEnabled(self.workers.isEnabled())
        for button in self.nav_buttons:
            button.setEnabled(self.workers.isEnabled())

    def _populate(self) -> None:
        """Rebuild the worker selector/alphabet availability.

        Rebuild the worker selector/alphabet availability from the loaded catalog under
        signal blocking, preserving exact committed ownership.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self._catalog
        with QSignalBlocker(self.workers):
            self.workers.clear()
            if catalog is not None:
                surnames = {w.worker_id: w.last_name or "" for w in catalog.workers}
                for option in worker_options(catalog, self._order):
                    if self._filter is None or surnames[
                        option.worker_id
                    ].upper().startswith(self._filter):
                        self.workers.addItem(option.label, option.worker_id)
                self.workers.setCurrentIndex(
                    self.workers.findData(self._current_worker)
                )
        letters = (
            {(w.last_name or "")[:1].upper() for w in catalog.workers}
            if catalog
            else set()
        )
        initial = (
            next(
                (
                    (w.last_name or "")[:1].upper()
                    for w in catalog.workers
                    if w.worker_id == self._current_worker
                ),
                "",
            )
            if catalog
            else ""
        )
        for value, button in self.alphabet_buttons.items():
            with QSignalBlocker(button):
                button.setChecked(value == (self._filter or "All"))
            button.setEnabled(
                catalog is not None and (value == "All" or value in letters)
            )
            button.setText(self._text("All") if value == "All" else value)
            if value == "All":
                # Spanish caption needs room; the alphabet row's stretch absorbs it.
                width = 34 if self.language is Language.SPANISH else 18
                button.setStyleSheet(f"min-width: {width}px; max-width: {width}px;")
            button.setToolTip(
                self._text("Show every worker")
                if value == "All"
                else self._text("Show last names beginning with") + " " + value
            )
            button.setProperty("currentInitial", value == initial)
            style = button.style()
            assert style is not None
            style.unpolish(button)
            style.polish(button)

    def filter_workers(self, value: str) -> None:
        """Apply surname initials using stored names, never parsing display text.

        Args:
            value: Full literal value to display/elide or worker alphabet filter
                sentinel, as specified by this helper.

        Returns:
            None.
        """
        self._filter = None if value == "All" else value
        self._populate()
        if self.workers.currentIndex() < 0 and self.workers.count():
            self.workers.setCurrentIndex(0)

    def change_order(self) -> None:
        """Toggle reference worker ID/surname ordering without switching source.

        Args:
            None.

        Returns:
            None.
        """
        self._order = (
            WorkerOrder.LAST_NAME if self._order is WorkerOrder.ID else WorkerOrder.ID
        )
        self._populate()
        self.order_button.setText("A-Z" if self._order is WorkerOrder.ID else "0-9")

    def navigate(self, position: int) -> None:
        """Move through the currently filtered worker selector.

        Args:
            position: Source first/previous/next/last navigation sentinel resolved
                against the filtered worker list.

        Returns:
            None.
        """
        if not self.workers.count():
            return
        index = self.workers.currentIndex()
        target = (
            0
            if position == 0
            else self.workers.count() - 1
            if position == 2
            else index + position
        )
        if 0 <= target < self.workers.count():
            self.workers.setCurrentIndex(target)

    def _worker_changed(self, index: int) -> None:
        """Validate the selected item's stored worker ID.

        Validate the selected item's stored worker ID, restore the committed combo
        selection and delegate source activation to the host.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.

        Raises:
            ValueError: Worker option requires a stored ID.
        """
        if index >= 0:
            identity = self.workers.itemData(index)
            if not isinstance(identity, str):
                raise ValueError("Worker option requires a stored ID.")
            # Retain the committed label until the owning transition succeeds.
            with QSignalBlocker(self.workers):
                self.workers.setCurrentIndex(
                    self.workers.findData(self._current_worker)
                )
            self._select_worker(identity)
