"""Reviewed original header, worker navigation, association bar and footer.

Ported from setupTopWidgets/setupNavigationButtons/setupTabsTopControls and
setupWorkspaceFooter. This view owns selector/filter state, never SQL or drafts.
The localized Project caption identifies the shared toolbar's action scope;
the separate brand caption identifies the loaded project.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QAbstractAnimation, QSignalBlocker, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractButton,
    QAction,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkCatalog
from ergotools.presentation.desktop.alphabet_navigation import AlphabetNavigation
from ergotools.presentation.desktop.assessment_location_browser import (
    AssessmentLocationBrowser,
)
from ergotools.presentation.desktop.buffered_controls import BufferedControls
from ergotools.presentation.desktop.combo_popup import style_combo_popup
from ergotools.presentation.desktop.expandable_section import ExpandableSection
from ergotools.presentation.desktop.main_navigation_text import navigation_text
from ergotools.presentation.desktop.project_caption import ProjectCaption
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

    # Display intent only; the integrated host owns project preference acceptance.
    context_expanded_changed = pyqtSignal(bool)

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
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._select_worker = select_worker
        self._catalog: WorkCatalog | None = None
        self._current_worker: str | None = None
        self._filter: str | None = None
        self._order = WorkerOrder.ID
        self.language = Language.ENGLISH
        self._texts: list[tuple[QLabel | QAbstractButton | QAction, str, str]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QFrame(self)
        header.setObjectName("brandHeader")
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
        self.project_label = ProjectCaption()
        brand_box.addWidget(brand)
        brand_box.addWidget(self.project_label)
        identity.addLayout(brand_box)
        header_layout.addLayout(identity, 1)
        # A separate caption scopes the existing actions without widening buttons
        # or repeating the loaded project's name from the brand area.
        toolbar_panel = QFrame(header)
        toolbar_panel.setObjectName("projectToolbarPanel")
        toolbar_box = QVBoxLayout(toolbar_panel)
        toolbar_box.setContentsMargins(0, 0, 0, 0)
        toolbar_box.setSpacing(0)
        self.toolbar_title = QLabel("Project", toolbar_panel)
        self.toolbar_title.setObjectName("projectToolbarTitle")
        # Reserve the complete font box, including lowercase descenders, while
        # keeping the zero-padding caption close to the toolbar's top edge.
        self.toolbar_title.setFixedHeight(
            max(20, self.toolbar_title.fontMetrics().height() + 2)
        )
        self.toolbar_title.setAlignment(
            Qt.Alignment(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignTop
        )
        header.setFixedHeight(self.toolbar_title.height() + 106)
        self._texts.append((self.toolbar_title, "Project", ""))
        toolbar_box.addWidget(self.toolbar_title)
        self.toolbar = QToolBar(toolbar_panel)
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
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
        toolbar_box.addWidget(self.toolbar)
        header_layout.addWidget(toolbar_panel)
        layout.addWidget(header)
        worker_bar = QFrame()
        self.worker_bar = worker_bar
        self._context_project: str | None = None
        self._context_expanded = False
        self._animate_context = False
        worker_bar.setObjectName("contextBar")
        worker_bar_layout = QVBoxLayout(worker_bar)
        worker_bar_layout.setContentsMargins(14, 7, 12, 7)
        worker_bar_layout.setSpacing(2)
        worker_area = BufferedControls()
        self.worker_controls = worker_area
        worker_area.setMinimumWidth(0)
        worker_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        worker_area.setFixedHeight(65)
        worker_area.setObjectName("workerControls")
        worker_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        worker_grid = QGridLayout(worker_area)
        worker_grid.setContentsMargins(0, 0, 0, 0)
        worker_grid.setHorizontalSpacing(6)
        worker_grid.setVerticalSpacing(1)
        worker_icon = QLabel()
        worker_icon.setPixmap(icons["worker"].pixmap(26, 26))
        worker_icon.setFixedSize(28, 28)
        self._worker_icon = worker_icon
        worker_grid.addWidget(worker_icon, 0, 0)
        worker_label = QLabel("Worker")
        worker_label.setObjectName("contextLabel")
        self._texts.append((worker_label, "Worker", ""))
        worker_grid.addWidget(worker_label, 0, 1)
        self.workers = QComboBox()
        style_combo_popup(self.workers)
        self.workers.setMinimumWidth(0)
        self.workers.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.workers.currentIndexChanged.connect(self._worker_changed)
        worker_grid.addWidget(self.workers, 0, 2)
        worker_grid.setColumnStretch(2, 1)
        self.buttons: dict[str, QAbstractButton] = {}
        self.alphabet = AlphabetNavigation("All", self.filter_workers)
        self.alphabet.setStyleSheet(
            self.alphabet.styleSheet()
            + "QPushButton#copyAlphabetButton { border: 0; border-radius: 3px; "
            "background: transparent; color: #416487; font-size: 11px; height: 27px; } "
            "QPushButton#copyAlphabetButton:checked { "
            "background: #0B326C; color: white; } "
            'QPushButton#copyAlphabetButton[currentInitial="true"] { '
            "font-weight: 900; font-size: 13px; color: #001C2B; } "
            "QPushButton#copyAlphabetButton:checked { color: white; } "
            "QPushButton#copyAlphabetButton:hover:enabled { font-size: 16px; "
            "background: #DDF3F5; color: #0B326C; } "
            "QPushButton#copyAlphabetButton:disabled { color: #C7D0D7; }"
        )
        self.alphabet.setFixedHeight(28)
        for letter in self.alphabet.buttons.values():
            letter.setFixedHeight(28)
        self.alphabet_buttons = self.alphabet.buttons
        self.alphabet_group = self.alphabet.group
        worker_grid.addWidget(self.alphabet, 1, 2, Qt.AlignmentFlag.AlignTop)
        self.order_button = self._worker_button(
            "order",
            "A-Z",
            "alphabet_order",
            "Change worker ordering.",
            icons,
            self.change_order,
        )
        worker_grid.addWidget(self.order_button, 0, 3)
        navigation = QWidget()
        arrows = QHBoxLayout(navigation)
        arrows.setContentsMargins(0, 0, 0, 0)
        arrows.setSpacing(3)
        self.nav_buttons = []
        for caption, icon, position in (
            ("First worker", "first", 0),
            ("Previous worker", "previous", -1),
            ("Next worker", "next", 1),
            ("Last worker", "last", 2),
        ):
            button = QToolButton()
            button.setObjectName("workerNavigationButton")
            button.setFixedSize(38, 36)
            button.setIcon(icons[icon])
            button.setIconSize(QSize(24, 24))
            button.clicked.connect(
                lambda checked, position=position: self.navigate(position)
            )
            self._texts.append((button, "", caption))
            self.nav_buttons.append(button)
            arrows.addWidget(button)
        for key, caption, icon, tip in (
            ("workers", "Workers", "worker_management", "Open Worker Management."),
            (
                "search",
                "Search",
                "search",
                (
                    "Find and open a saved assessment by worker, workplace, and "
                    "the active ergonomic tool."
                ),
            ),
            (
                "transfer",
                "Transfer",
                "transfer_worker_data",
                "Transfer worker assessment data to another context.",
            ),
        ):
            button = self._worker_button(
                key, caption, icon, tip, icons, actions.get(key)
            )
            button.setFixedHeight(36)
            arrows.addWidget(button)
        worker_grid.addWidget(navigation, 0, 4)
        self.context_disclosure = QToolButton()
        self.context_disclosure.setObjectName("assessmentContextDisclosure")
        self.context_disclosure.setCheckable(True)
        self.context_disclosure.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.context_disclosure.setIconSize(QSize(18, 18))
        self.context_disclosure.setFixedHeight(36)
        self.context_disclosure.toggled.connect(self._toggle_context)

        self.context_disclosure.setFixedHeight(28)
        self.location_browser = AssessmentLocationBrowser(icons)
        self.context_frame = ExpandableSection(self.location_browser)
        self.standalone_button = self._button(
            "standalone",
            "Standalone assessment",
            "worker",
            "Open this worker's standalone assessment for the current tool.",
            icons,
            actions.get("standalone"),
        )
        self.standalone_button.setObjectName("standaloneAssessmentButton")
        self.standalone_button.setFixedHeight(36)
        worker_grid.addWidget(self.standalone_button, 0, 5)
        self.location_browser.summary.setObjectName("supportingText")
        self.location_browser.summary.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Fixed
        )
        assessment_status = QWidget()
        status_layout = QHBoxLayout(assessment_status)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        status_layout.addWidget(self.location_browser.summary, 1)
        status_layout.addWidget(self.context_disclosure, 0, Qt.AlignmentFlag.AlignRight)
        worker_grid.addWidget(assessment_status, 1, 3, 1, 3)
        self.context_frame.animation.stateChanged.connect(self._context_motion_changed)
        self.location_browser.summary.show()
        add_assessment = actions.get("add_assessment")
        if add_assessment is not None:
            self.location_browser.add_button.clicked.connect(add_assessment)
        else:
            self.location_browser.add_button.setEnabled(False)
        delete_assessment = actions.get("delete_assessment")
        if delete_assessment is not None:
            self.location_browser.delete_button.clicked.connect(delete_assessment)
        else:
            self.location_browser.delete_button.setEnabled(False)
        worker_bar_layout.addWidget(worker_area)
        worker_bar_layout.addWidget(self.context_frame)
        layout.addWidget(worker_bar)
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
        footer_layout.addStretch()
        footer_layout.addWidget(self.file_label)
        self.footer.setAutoFillBackground(True)

    def _context_motion_changed(
        self, state: QAbstractAnimation.State, _previous: QAbstractAnimation.State
    ) -> None:
        """Buffer the unchanged upper strip only while the lower browser is moving.

        Args:
            state: Accepted animation state, independent of source/ownership.
            _previous: Prior state; reversal releases then renews the buffer.

        Returns:
            None; native controls remain the sole owners of input and focus.
        """
        if state == QAbstractAnimation.State.Running:
            self.worker_controls.freeze()
        else:
            self.worker_controls.thaw()

    def _toggle_context(self, expanded: bool) -> None:
        """Request context visibility independently of the active assessment.

        Args:
            expanded: Explicit visibility intent; restoration blocks signals.

        Returns:
            None; the host records the project preference and refreshes visibility.
        """
        self._animate_context = True
        self.context_expanded_changed.emit(expanded)

    def update_context_visibility(
        self,
        project_id: str | None,
        language: Language,
        saved_expanded: bool | None = None,
    ) -> None:
        """Restore the context disclosure without changing the open assessment.

        Args:
            project_id: Open project identity; None disables the toggle and browser.
            language: Interface language only, independent of saved names.
            saved_expanded: Explicit expansion, or None for the collapsed default.

        Returns:
            None; explicit user toggles animate the nested worker-area height.
            Project restoration settles immediately; repeated refreshes preserve
            in-flight animation, source selection and task text.
        """
        spanish = language is Language.SPANISH
        self.context_disclosure.setText(
            ("Evaluación" if spanish else "Assessment")
            + f" ({self.location_browser.assessment_count})"
        )
        self.context_disclosure.setToolTip(
            (
                "Mostrar u ocultar el contexto de evaluación "
                "sin cambiar los datos abiertos."
            )
            if spanish
            else (
                "Show or hide assessment context without changing the open assessment."
            )
        )
        self.context_disclosure.setEnabled(project_id is not None)
        expanded = project_id is not None and bool(saved_expanded)
        with QSignalBlocker(self.context_disclosure):
            self.context_disclosure.setChecked(expanded)
        self.context_disclosure.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )
        project_changed = project_id != self._context_project
        changed = expanded != self._context_expanded
        animate = self._animate_context and self.isVisible() and not project_changed
        self._animate_context = False
        if changed or project_changed:
            self._context_expanded = expanded
            self._context_project = project_id
            self.context_frame.set_expanded(expanded, animate=animate)

    def set_modified(self, modified: bool) -> None:
        """Update only the brand status without rebuilding stable worker controls.

        Args:
            modified: Accepted project/display changes need main Save.

        Returns:
            None; literal project title and all worker selections remain unchanged.
        """
        caption = (
            self.project_label.text()
            .removesuffix("  •  Modified")
            .removesuffix("  •  Modificado")
        )
        if modified:
            caption += (
                "  •  Modificado"
                if self.language is Language.SPANISH
                else "  •  Modified"
            )
        self.project_label.setText(caption)

    def update_assessment_selection(self, *, standalone: bool, available: bool) -> None:
        """Highlight the actual source and advertise available workplace choices.

        Args:
            standalone: The open source or preview has no workplace owner.
            available: A real worker/tool view exists; empty projects highlight nothing.

        Returns:
            None; highlight changes never select, save or create data.
        """
        self.standalone_button.setProperty(
            "assessmentCurrent", available and standalone
        )
        style = self.standalone_button.style()
        assert style is not None
        style.unpolish(self.standalone_button)
        style.polish(self.standalone_button)
        self.standalone_button.update()
        count = self.location_browser.assessment_count
        spanish = self.language is Language.SPANISH
        self.context_disclosure.setText(
            ("Evaluación" if spanish else "Assessment") + f" ({count})"
        )

    def _worker_button(
        self,
        key: str,
        caption: str,
        icon: str,
        tip: str,
        icons: Mapping[str, QIcon],
        callback: Callable[[], None] | None,
    ) -> QToolButton:
        """Build a compact worker action aligned with the selector row.

        Args:
            key: Stable action identity stored for enablement and localization.
            caption: Localized through the existing main navigation text catalog.
            icon: Packaged asset identity; no platform asset lookup.
            tip: Existing descriptive tooltip.
            icons: Injected processed icon catalog.
            callback: Existing host command; None disables an unavailable action.

        Returns:
            Native 36-pixel button with icon beside its caption; commands stay external.
        """
        button = QToolButton()
        button.setObjectName("workerActionButton")
        button.setText(caption)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIcon(icons[icon])
        button.setIconSize(QSize(22, 22))
        button.setFixedHeight(36)
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.buttons[key] = button
        self._texts.append((button, caption, tip))
        if callback is not None:
            button.clicked.connect(callback)
        else:
            button.setEnabled(False)
        return button

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
        if self.context_frame.animation.state() == QAbstractAnimation.State.Running:
            # Source/tool/language changes must be visible immediately, not cached.
            self.context_frame.set_expanded(self._context_expanded, animate=False)
        self.worker_controls.thaw()
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
            "standalone",
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
                button.setFixedWidth(
                    button.fontMetrics().horizontalAdvance(button.text()) + 12
                )
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
