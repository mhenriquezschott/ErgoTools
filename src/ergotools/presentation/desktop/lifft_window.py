"""Integrated assessment workspace using injected project services and packaged icons.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date, datetime
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import uuid4

from PyQt5 import sip
from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QCloseEvent, QColor, QDesktopServices, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.assessment_export import SummaryExportRow
from ergotools.application.assessment_navigation import (
    AssessmentNavigation,
    context_values,
)
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.contracts.body_renderer import (
    AnimatedBodyRenderer,
    BodyRegion,
    BodyRenderer,
    BodyViewState,
    RgbColor,
    SelectableBodyRenderer,
)
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.application.history_access import AssignmentSelection
from ergotools.application.plot_access import PlotRepository
from ergotools.application.project_conversion import ProjectConversion
from ergotools.application.rotation_access import RotationRepository
from ergotools.application.saved_results import result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.application.settings import Language, SettingsStore
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessment_transfer import TransferRequest
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
    task_has_data,
)
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.duet_summary import DuetSummary
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.tst_summary import TstSummary
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.assignment_selection import AssignmentSelector
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)
from ergotools.presentation.desktop.assessment_history_actions import (
    AssessmentHistoryActions,
)
from ergotools.presentation.desktop.assessment_menu import AssessmentMenu
from ergotools.presentation.desktop.assignment_dialog_host import AssignmentDialogHost
from ergotools.presentation.desktop.authors_dialog import AuthorsDialog
from ergotools.presentation.desktop.body_region_panel import BodyRegionPanel
from ergotools.presentation.desktop.duet_presenter import DuetPresenter
from ergotools.presentation.desktop.duet_task_panel import DuetTaskPanel
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
)
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.lifft_presenter import LifftPresenter
from ergotools.presentation.desktop.lifft_task_panel import LifftTaskPanel
from ergotools.presentation.desktop.main_navigation import MainNavigation
from ergotools.presentation.desktop.manual_launcher import open_user_guide
from ergotools.presentation.desktop.organization_dialog import OrganizationDialog
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.desktop.project_details_dialog import ProjectDetailsDialog
from ergotools.presentation.desktop.project_migration_dialog import (
    ProjectMigrationDialog,
)
from ergotools.presentation.desktop.project_properties_dialog import (
    ProjectPropertiesDialog,
)
from ergotools.presentation.desktop.results_sidebar import ResultsSidebar
from ergotools.presentation.desktop.style import WORKSPACE_STYLE
from ergotools.presentation.desktop.text import desktop_text
from ergotools.presentation.desktop.theme.duet_summary import display_duet_summary
from ergotools.presentation.desktop.theme.lifft_summary import display_lifft_summary
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.theme.tst_summary import display_tst_summary
from ergotools.presentation.desktop.tool_data_dialog import ToolDataDialog
from ergotools.presentation.desktop.tool_tab_focus import ToolTabFocus
from ergotools.presentation.desktop.tst_presenter import TstPresenter
from ergotools.presentation.desktop.tst_task_panel import TstTaskPanel
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.worker_search_dialog import (
    WorkerSearchDialog,
    search_assessments,
)
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from ergotools.presentation.edit_context import EditContext
from ergotools.presentation.localization import Translator
from ergotools.presentation.numeric_input import DecimalConvention, format_input_number
from ergotools.presentation.saved_tool_options import saved_tool_options
from ergotools.presentation.summary_csv import summary_csv_table
from ergotools.presentation.worker_options import WorkerOrder, worker_options

# Retained diagnostic single-field editor order: lever arm, load and repetitions; the
# integrated task grid uses the same typed inputs.
_FIELDS: tuple[Literal["lever_arm", "load", "repetitions"], ...] = (
    "lever_arm",
    "load",
    "repetitions",
)
# Module-scoped diagnostic logger; adapters log technical failures while views retain
# user input.
_LOG = logging.getLogger(__name__)


class LifftWindow(QMainWindow):
    """Own widgets/pending text; delegate source and file operations to services."""

    def __init__(
        self,
        presenter: LifftPresenter,
        icons: Mapping[str, QIcon],
        list_documents: Callable[[str], tuple[str, ...]],
        *,
        summary_loader: Callable[[str, AssessmentKind], tuple[SummaryExportRow, ...]]
        | None = None,
        csv_writer: Callable[[str, tuple[tuple[str, ...], ...]], None] | None = None,
        plot_opener: Callable[
            [
                PlotRepository,
                Language,
                MeasurementSystem,
                Callable[[SummaryExportRow], bool],
                QWidget,
            ],
            None,
        ]
        | None = None,
        rotation_opener: Callable[[RotationRepository, Language, QWidget], None]
        | None = None,
        developer_opener: Callable[[QWidget], None] | None = None,
        settings_store: SettingsStore | None = None,
        document_options: Callable[[str, Language], tuple[tuple[str, str], ...]]
        | None = None,
        project_conversion: ProjectConversion | None = None,
        user_guide: bytes | None = None,
        user_guides: Mapping[Language, bytes] | None = None,
        authors_logo: bytes | None = None,
        original_controls: bool = False,
        original_navigation: bool = False,
        renderer_factory: Callable[[QWidget], tuple[QWidget, BodyRenderer]]
        | None = None,
    ) -> None:
        """Build a styled development screen without opening or creating projects.

        Args:
            presenter: Injected tool/workplace coordinator; owns parsing and source
                commands, not these widgets.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            list_documents: Injected reader listing native assessment identities for a
                selected project path.
            summary_loader: Optional reader of saved current summaries by path and tool.
            csv_writer: Optional file writer receiving a destination and complete CSV
                cells.
            plot_opener: Optional owned PLOT launcher borrowing repository, language,
                units and handoff callback.
            rotation_opener: Optional owned JROT launcher borrowing the active rotation
                repository.
            developer_opener: Optional isolated session-only preview launcher; receives
                only its GUI parent, never a save/history callback.
            settings_store: Optional user-settings port; preferences/recent paths are
                separate from project data.
            document_options: Optional native assessment picker reader returning stable
                identity/caption pairs.
            project_conversion: Optional external-process conversion port; conversion
                implementation is outside the app.
            user_guide: Optional packaged guide bytes for the retained historical
                single-guide API.
            user_guides: Optional packaged guides keyed by supported language.
            authors_logo: Optional packaged logo used only by the Authors modal.
            original_controls: Whether to compose the original integrated task controls
                rather than the diagnostic editor.
            original_navigation: Whether to compose the original shared navigation and
                three-column workspace.
            renderer_factory: Optional factory creating a Qt viewport and replaceable
                renderer after QApplication exists.

        Returns:
            None.
        """
        super().__init__()
        self._user_guide = user_guide
        self._user_guides = dict(user_guides) if user_guides is not None else None
        self._authors_logo = authors_logo
        self._summary_loader = summary_loader
        self._csv_writer = csv_writer
        self._plot_opener = plot_opener
        self._rotation_opener = rotation_opener
        self._developer_opener = developer_opener
        self._developer_enabled = False
        self._developer_menu: QMenu | None = None
        self._settings_store = settings_store
        self.assessment_navigation = AssessmentNavigation(
            presenter.workspace, settings_store
        )
        self._project_conversion = project_conversion
        self.main_navigation: MainNavigation | None = None
        self.results_sidebar: ResultsSidebar | None = None
        self.body_panel: BodyRegionPanel | None = None
        self._body_renderer: BodyRenderer | None = None
        self._renderer_factory = renderer_factory
        original_controls = original_controls or original_navigation
        self.icons = icons
        self.duet_presenter = DuetPresenter(presenter.workspace)
        self.duet_panel: DuetTaskPanel | None = None
        self.tst_presenter = TstPresenter(presenter.workspace)
        self.tst_panel: TstTaskPanel | None = None
        self._assessment_menu: AssessmentMenu | None = None
        self.history_actions: AssessmentHistoryActions | None = None
        self._empty_kind = AssessmentKind.LIFFT
        self.presenter = presenter
        self.list_documents = list_documents
        self.document_options = document_options
        self.language = Language.ENGLISH
        self.context: EditContext | None = None
        self.pending = False
        self.task_panel: LifftTaskPanel | None = None
        self._unsaved_backing: TemporaryDirectory[str] | None = None
        self._worker_selection: tuple[str | None, str | None] = (None, None)
        self._job_selection: tuple[str | None, str | None] = (None, None)
        self.buttons: dict[str, QPushButton] = {}
        self.setMinimumSize(960, 680)
        self.resize(1200, 780)
        self.setStyleSheet(WORKSPACE_STYLE)
        root = QWidget()
        root.setObjectName("workspace")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        brand = QFrame()
        brand.setObjectName("brand")
        brand_layout = QHBoxLayout(brand)
        logo = QLabel()
        logo.setPixmap(icons["ergotools_logo"].pixmap(64, 64))
        brand_layout.addWidget(logo)
        title = QLabel("ErgoTools")
        title.setObjectName("brandName")
        brand_layout.addWidget(title)
        self.subtitle = QLabel()
        self.subtitle.setObjectName("subtitle")
        brand_layout.addWidget(self.subtitle)
        brand_layout.addStretch()
        management = self.make_button("job_form_title", self.open_job_management)
        management.setIcon(icons["job_management"])
        management.setIconSize(QSize(24, 24))
        brand_layout.addWidget(management)
        workers = self.make_button("worker_management", self.open_worker_management)
        workers.setIcon(icons["worker_management"])
        workers.setIconSize(QSize(24, 24))
        brand_layout.addWidget(workers)
        self.subtitle.setWordWrap(True)
        layout.addWidget(brand)
        toolbar = QHBoxLayout()
        actions = (
            ("new", self.new_project, "new"),
            ("open", self.open_project, "open"),
            ("save", self.save_project, "save"),
            ("undo", self.undo, "undo"),
            ("redo", self.redo, "redo"),
            ("add", self.add_task, ""),
            ("remove", self.remove_task, "delete"),
        )
        for key, action, icon in actions:
            button = self.make_button(key, action)
            if icon:
                button.setIcon(icons[icon])
                button.setIconSize(QSize(24, 24))
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        context_row = QHBoxLayout()
        context_button = self.make_button(
            "assessment_context", self.choose_assessment_context
        )
        context_button.setIcon(icons["job_management"])
        context_button.setIconSize(QSize(24, 24))
        context_row.addWidget(context_button)
        context_row.addWidget(
            self.make_button(
                "new_assessment", lambda: self.choose_assessment_context(create=True)
            )
        )
        context_row.addStretch()
        layout.addLayout(context_row)
        preferences = QGridLayout()
        self.preference_labels = [QLabel() for _ in range(3)]
        self.units = QComboBox()
        self.decimal = QComboBox()
        self.decimal.addItems(["1.25", "1,25"])
        self.languages = QComboBox()
        self.languages.addItems(["English", "Español"])
        for column, control in enumerate((self.units, self.decimal, self.languages)):
            preferences.addWidget(self.preference_labels[column], 0, column)
            preferences.addWidget(control, 1, column)
        self.units.currentIndexChanged.connect(self.change_preferences)
        self.decimal.currentIndexChanged.connect(self.change_preferences)
        self.languages.currentIndexChanged.connect(self.change_language)
        organization = self.make_button(
            "organization_management", self.open_organization
        )
        organization.setIcon(icons["plant"])
        organization.setIconSize(QSize(24, 24))
        preferences.addWidget(organization, 1, 3)
        layout.addLayout(preferences)
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        content = QHBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setMinimumHeight(42)
        self.table.itemSelectionChanged.connect(self.select_task)
        if original_controls:
            self.table.hide()
            self.task_panel = LifftTaskPanel(
                presenter,
                icons,
                calculate=lambda: self.run(self.calculate),
                clear=lambda: self.run(self.clear_assessment),
                select_context=lambda: self.run(self.open_saved_tool_data),
                invalidate=self.show_result,
                parent=self,
            )
            content.addWidget(self.task_panel, 3)
        else:
            content.addWidget(self.table, 3)
        panel = QFrame(self)
        panel.setObjectName("panel")
        panel.setMinimumWidth(235)
        result_layout = QVBoxLayout(panel)
        self.damage_title = QLabel()
        self.damage_value = QLabel("—")
        self.probability_title = QLabel()
        self.probability_value = QLabel("—")
        self.result_note = QLabel()
        self.result_note.setWordWrap(True)
        for widget in (
            self.damage_title,
            self.damage_value,
            self.probability_title,
            self.probability_value,
            self.result_note,
        ):
            result_layout.addWidget(widget)
        for value in (self.damage_value, self.probability_value):
            value.setObjectName("value")
        result_layout.addStretch()
        calculate = self.make_button("calculate", self.calculate)
        calculate.setObjectName("calculate")
        calculate.setIcon(icons["calculate_light"])
        calculate.setIconSize(QSize(28, 28))
        result_layout.addWidget(calculate)
        if original_controls:
            panel.hide()
        else:
            content.addWidget(panel, 1)
        layout.addLayout(content, 1)
        edit_row = QHBoxLayout()
        self.field = QComboBox()
        self.field.setMinimumWidth(190)
        self.field.currentIndexChanged.connect(self.select_task)
        self.entry = QLineEdit()
        self.entry.textEdited.connect(self.mark_pending)
        self.entry.returnPressed.connect(lambda: self.run(self.apply_edit))
        edit_row.addWidget(self.field)
        edit_row.addWidget(self.entry, 1)
        edit_row.addWidget(self.make_button("apply", self.apply_edit))
        edit_row.addWidget(self.make_button("discard", self.discard_edit))
        layout.addLayout(edit_row)
        if original_controls:
            for index in range(edit_row.count()):
                item = edit_row.itemAt(index)
                if item is not None and item.widget() is not None:
                    edit_widget = item.widget()
                    assert edit_widget is not None
                    edit_widget.hide()
            calculate.hide()
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(42)
        layout.addWidget(self.message)
        self.translate()
        self.refresh()
        if original_navigation:
            self._install_original_navigation()

    def open_organization(self) -> None:
        """Edit workplace identities/details without rebuilding assessment source.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if self.pending or not workspace.supports_assignment_history:
            return
        dialog = OrganizationDialog(
            workspace, self.icons, language=self.language, parent=self
        )
        try:
            dialog.exec()
        finally:
            dialog.close()
            dialog.deleteLater()

    def open_worker_management(self) -> None:
        """Retain worker/assignment edits without changing the assessment context.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if self.pending or not workspace.supports_assignment_history:
            return
        location = workspace.location
        previous_location, selected = self._worker_selection
        dialog = WorkerManagementDialog(
            workspace,
            self.icons,
            self.presenter.system,
            language=self.language,
            selected_worker=selected if previous_location == location else None,
            parent=self,
        )
        try:
            dialog.exec()
            self._worker_selection = (location, dialog.selected_worker_id)
        finally:
            dialog.close()
            dialog.deleteLater()
        worker_id = self._worker_selection[1]
        if worker_id is not None and workspace.active is None:
            self.assessment_navigation.select(
                worker_id,
                self.active_kind(),
                lambda: self._blank_kind(self.active_kind()),
            )
            self.refresh()
        else:
            self.refresh_navigation()

    def open_job_management(self) -> None:
        """Edit jobs modally, retaining this project's last stored job selection.

        Management commits independently of assessment edits. Returning does not rebuild
        the assessment editor or clear its calculation/undo history. Earlier project
        formats require the separately deployed conversion tool before native opening.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if self.pending or not workspace.supports_job_risk:
            return
        location = workspace.location
        previous_location, selected_job = self._job_selection
        dialog = JobManagementDialog(
            workspace,
            self.icons,
            self.presenter.system,
            selected_job=selected_job if previous_location == location else None,
            language=self.language,
            convention=self.presenter.convention,
            parent=self,
        )
        try:
            dialog.exec()
            self._job_selection = (location, dialog.selected_job_id)
        finally:
            dialog.close()
            dialog.deleteLater()
        self.enable_controls()

    def text(self, key: str) -> str:
        """Resolve complete desktop messages for this window's language.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return desktop_text(key, self.language)

    def make_button(self, key: str, action: Callable[[], None]) -> QPushButton:
        """Connect one action through the failure-preserving UI boundary.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.
            action: Host or local operation invoked once through the owning error
                boundary.

        Returns:
            New owned command button connected once to the host error boundary.
        """
        button = QPushButton()
        button.clicked.connect(lambda: self.run(action))
        self.buttons[key] = button
        return button

    def run(self, action: Callable[[], None]) -> None:
        """Show errors and log adapter failures without losing input.

        Args:
            action: Host or local operation invoked once through the owning error
                boundary.

        Returns:
            None.
        """
        try:
            secondary = self.secondary_panel()
            if (
                secondary is not None
                and not (action == self.save_project and self._is_unsaved_project())
                and action
                not in (
                    self.open_task_count,
                    self.open_saved_tool_data,
                    self.search_assessment,
                    self.clear_assessment,
                    self.open_preferences,
                    self.refresh_recent_projects,
                    self.clear_recent_history,
                    self.save_project_as,
                    self.backup_project,
                    self.export_summary_csv,
                    self.open_plot,
                    self.open_rotation,
                    self.open_worker_transfer,
                    self.open_help,
                    self.open_authors,
                    self.new_project,
                )
                and secondary.commit_inputs()
            ):
                self.refresh()
            if self.secondary_panel() is None and self.task_panel is not None:
                selected = self.task_panel.selected_task_id
                if selected in self.task_panel.task_ids:
                    self.table.selectRow(self.task_panel.task_ids.index(selected))
            if (
                self.secondary_panel() is None
                and self.task_panel is not None
                and not (action == self.save_project and self._is_unsaved_project())
                and action
                not in (
                    self.open_task_count,
                    self.open_saved_tool_data,
                    self.search_assessment,
                    self.clear_assessment,
                    self.open_preferences,
                    self.refresh_recent_projects,
                    self.clear_recent_history,
                    self.save_project_as,
                    self.backup_project,
                    self.export_summary_csv,
                    self.open_plot,
                    self.open_rotation,
                    self.open_worker_transfer,
                    self.open_help,
                    self.open_authors,
                    self.new_project,
                )
                and self.task_panel.commit_inputs()
            ):
                self.refresh()
            action()
        except DraftError as error:
            self.message.setText(Translator(self.language).text(error.issue.code))
        except Exception:
            # Final GUI boundary: report/log the failure, retain source and editor text.
            _LOG.exception("Desktop operation failed")
            self.message.setText(self.text("error"))

    def translate(self) -> None:
        """Update labels without changing source values or pending editor text.

        Args:
            None.

        Returns:
            None.
        """
        self.setWindowTitle(
            "Fatigue Failure Risk Assessment Tools"
            if self.main_navigation is not None
            else "ErgoTools · " + self.text("development")
        )
        self.subtitle.setText(self.text("subtitle"))
        for key, button in self.buttons.items():
            button.setText(self.text(key))
            button.setToolTip(self.text(key))
        for label, key in zip(
            self.preference_labels, ("display", "decimal", "language"), strict=True
        ):
            label.setText(self.text(key))
        for combo, keys in (
            (self.units, ("imperial", "metric")),
            (self.field, _FIELDS),
        ):
            index = max(combo.currentIndex(), 0)
            combo.blockSignals(True)
            combo.clear()
            combo.addItems([self.text(key) for key in keys])
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self.damage_title.setText(self.text("damage"))
        self.probability_title.setText(self.text("probability"))
        self.result_note.setText(self.text("result_units"))
        self.entry.setToolTip(self.text("ready"))
        if self._assessment_menu is not None:
            self._assessment_menu.translate(self.language)

    def refresh(self) -> None:
        """Render original source through a fresh context and clear stale results.

        Args:
            None.

        Returns:
            None.
        """
        self._release_unsaved_backing()
        if self.tst_active and self.tst_panel is not None:
            self.context = None
            self.tst_presenter.system = self.presenter.system
            self.tst_presenter.convention = self.presenter.convention
            self.tst_panel.language = self.language
            self.tst_panel.load_source(self.tst_presenter.bind())
            self.message.setText(self.text("original_grid_ready"))
            self._sync_tool_tab()
            self.show_result()
            self.enable_controls()
            self.refresh_navigation()
            return
        if self.duet_active and self.duet_panel is not None:
            self.context = None
            self.duet_presenter.convention = self.presenter.convention
            self.duet_panel.language = self.language
            self.duet_panel.load_source(self.duet_presenter.bind())
            self.message.setText(self.text("original_grid_ready"))
            self._sync_tool_tab()
            self.show_result()
            self.enable_controls()
            self.refresh_navigation()
            return
        self._sync_tool_tab()
        selected = max(self.table.currentRow(), 0)
        self.context = None
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.blockSignals(False)
        self.entry.clear()
        self.damage_value.setText("—")
        self.probability_value.setText("—")
        for label in (self.damage_value, self.probability_value):
            label.setStyleSheet("")
        self.context = self.presenter.bind()
        rows = self.context.view.tasks if self.context is not None else ()
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        units = (
            ("in", "lbf")
            if self.presenter.system is MeasurementSystem.IMPERIAL
            else ("cm", "N")
        )
        self.table.setHorizontalHeaderLabels(
            [
                self.text("task"),
                self.text("lever_arm") + " (" + units[0] + ")",
                self.text("load") + " (" + units[1] + ")",
                self.text("repetitions"),
            ]
        )
        for index, task in enumerate(rows):
            values = (
                str(index + 1),
                *(
                    format_input_number(getattr(task, field), self.presenter.convention)
                    for field in _FIELDS
                ),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(index, column, item)
        if rows:
            self.table.selectRow(min(selected, len(rows) - 1))
        self.table.blockSignals(False)
        source = self.presenter.source()
        active = self.presenter.workspace.active
        self.source_label.setText(
            self.text("source")
            + ": "
            + (self.text(source.system.value) if source else "—")
            + ("  •" if active and active.is_dirty else "")
        )
        self.message.setText(
            self.text(
                ("original_grid_ready" if self.task_panel is not None else "ready")
                if source
                else "empty"
            )
        )
        self.select_task()
        self.show_result()
        if self.task_panel is not None:
            self.task_panel.load_source(self.context, self.language)
        self.enable_controls()
        self.refresh_navigation()

    def select_task(self) -> None:
        """Load full-precision editor text only when no uncommitted input exists.

        Args:
            None.

        Returns:
            None.
        """
        if self.pending:
            return
        row = self.table.currentRow()
        if self.context is not None and 0 <= row < len(self.context.view.tasks):
            task = self.context.view.tasks[row]
            self.entry.setText(
                format_input_number(
                    getattr(task, _FIELDS[self.field.currentIndex()]),
                    self.presenter.convention,
                )
            )
        else:
            self.entry.clear()
        self.enable_controls()

    def mark_pending(self) -> None:
        """Keep input context while disabling interpretation changes.

        Args:
            None.

        Returns:
            None.
        """
        self.pending = True
        self.message.setText(self.text("pending"))
        self.enable_controls()

    def enable_controls(self) -> None:
        """Separate pending editor state from persisted document dirty state.

        Args:
            None.

        Returns:
            None.
        """
        active = self.presenter.workspace.active
        selected = self.table.currentRow() >= 0
        for key, button in self.buttons.items():
            enabled = not self.pending and (
                active is not None
                or key in ("new", "open")
                or (key == "save" and self._is_unsaved_project())
                or (
                    self.presenter.workspace.project_metadata is not None
                    and key
                    in (
                        "worker_management",
                        "organization_management",
                        "job_form_title",
                    )
                )
            )
            if key in ("worker_management", "organization_management"):
                enabled = (
                    enabled and self.presenter.workspace.supports_assignment_history
                )
            elif key == "job_form_title":
                enabled = enabled and self.presenter.workspace.supports_job_risk
            elif key in ("apply", "discard"):
                enabled = self.pending
            elif key == "new_assessment":
                enabled = (
                    not self.pending
                    and self.presenter.workspace.supports_assignment_history
                )
            elif key in (
                "assessment_context",
                "new_assessment",
            ):
                enabled = (
                    enabled and self.presenter.workspace.supports_assignment_history
                )
            elif key == "remove":
                enabled = enabled and selected
            elif key in ("undo", "redo"):
                enabled = (
                    enabled
                    and active is not None
                    and (
                        active.undo_label_key
                        if key == "undo"
                        else active.redo_label_key
                    )
                    is not None
                )
            button.setEnabled(enabled)
        if self._assessment_menu is not None:
            self._assessment_menu.sync()
            for action in (
                self._assessment_menu.close_project_action,
                self._assessment_menu.save_as,
                self._assessment_menu.backup,
                self._assessment_menu.properties,
            ):
                action.setEnabled(self.presenter.workspace.location is not None)
            self._assessment_menu.open_project_folder.setEnabled(
                self.presenter.workspace.location is not None
                and not self._is_unsaved_project()
            )
        if self.history_actions is not None:
            self.history_actions.refresh()
        for control in (
            self.units,
            self.decimal,
            self.languages,
            self.table,
            self.field,
        ):
            control.setEnabled(not self.pending)
        self.entry.setEnabled(active is not None and selected)
        self.refresh_save_controls()

    def refresh_save_controls(self) -> None:
        """Project shared unsaved data and unaccepted task text onto Save controls.

        Application dirty tracking remains authoritative; this projection never
        accepts inputs or writes data. A new temporary project always needs its
        first Save. Pending task text keeps Save available so existing validation
        can explain invalid inputs. Diagnostic sessions retain their prior policy.

        Args:
            None.

        Returns:
            None; toolbar, hidden command button and menu share one availability.
        """
        if sip.isdeleted(self):
            return
        workspace = self.presenter.workspace
        if workspace.editing is None:
            return
        panel = self.secondary_panel() or self.task_panel
        pending = (
            panel is not None and panel.pending and panel.pending_change() is not False
        )
        enabled = self._is_unsaved_project() or workspace.has_unsaved_changes or pending
        self.buttons["save"].setEnabled(enabled)
        if self.main_navigation is not None:
            self.main_navigation.toolbar_actions["save"].setEnabled(enabled)
        if self._assessment_menu is not None:
            self._assessment_menu.actions_by_key["save"].setEnabled(enabled)

    def apply_edit(self) -> None:
        """Commit the deliberately edited field; failed text stays available.

        Args:
            None.

        Returns:
            None.
        """
        if not self.pending or self.context is None:
            return
        task = self.context.view.tasks[self.table.currentRow()]
        self.presenter.commit(
            self.context,
            task.task_id,
            _FIELDS[self.field.currentIndex()],
            self.entry.text(),
        )
        self.pending = False
        self.refresh()

    def discard_edit(self) -> None:
        """Explicitly abandon only uncommitted editor text, not document history.

        Args:
            None.

        Returns:
            None.
        """
        self.pending = False
        self.select_task()
        self.message.setText(
            self.text("original_grid_ready" if self.task_panel is not None else "ready")
        )

    def task_count_context(self) -> str:
        """Identify the active project, worker and workplace for assessment actions.

        Args:
            None.

        Returns:
            Localized context headings with literal user identities. A diagnostic
            source without worker navigation uses its document identity instead.
            No selection, acceptance or persistence occurs here.
        """
        workspace = self.presenter.workspace
        metadata = workspace.project_metadata
        view = self.assessment_navigation.view
        spanish = self.language is Language.SPANISH
        parts = (
            [("Proyecto: " if spanish else "Project: ") + metadata.title]
            if metadata is not None
            else []
        )
        if view is None:
            if workspace.active is not None:
                parts.append(
                    ("Evaluación: " if spanish else "Assessment: ")
                    + workspace.active.document.document_id
                )
        else:
            worker = next(
                (
                    worker
                    for worker in workspace.read_hierarchy().hierarchy.work.workers
                    if worker.worker_id == view.worker_id
                ),
                None,
            )
            name = " ".join(
                value
                for value in ((worker.first_name, worker.last_name) if worker else ())
                if value
            )
            parts.append(
                ("Trabajador: " if spanish else "Worker: ")
                + view.worker_id
                + (" — " + name if name else "")
            )
            if view.workplace is None:
                parts.append(
                    "Evaluación independiente" if spanish else "Standalone assessment"
                )
            else:
                parts.append(
                    ("Lugar de trabajo: " if spanish else "Workplace: ")
                    + " > ".join(context_values(view.workplace)[:4])
                )
                parts.append(
                    ("Turno: " if spanish else "Shift: ") + view.workplace.shift_id
                )
                parts.append(
                    ("Trabajo: " if spanish else "Job: ") + " | ".join(view.job)
                    if view.job is not None
                    else ("Sin trabajo" if spanish else "No Job")
                )
        return "\n".join(parts)

    def task_count_removes_data(self, count: int) -> bool:
        """Inspect only removed rows, including unaccepted text, for loss consent.

        Args:
            count: Requested retained prefix length, already bounded by Settings.

        Returns:
            True if any trailing source row contains data or its editor has entered
            text/nondefault selectors. Invalid text also requires consent; inspection
            never parses, accepts or discards it. Same-count/growth return False.
        """
        source = self.active_source()
        if source is None or count >= len(source.tasks):
            return False
        if any(task_has_data(task) for task in source.tasks[count:]):
            return True
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.pending:
            for row in panel.inputs[count:]:
                for widget in row:
                    if isinstance(widget, QLineEdit) and not widget.isReadOnly():
                        if widget.text().strip():
                            return True
                    elif isinstance(widget, QComboBox) and widget.currentIndex() != 0:
                        return True
        return False

    def confirm_task_reset(self, language: Language, count: int | None = None) -> bool:
        """Confirm removal of populated trailing rows without editing the source.

        Args:
            language: Language selected in Settings, before personal Apply.
            count: Requested retained rows; None retains compatibility with callers
                requesting generic removal consent.

        Returns:
            True only for explicit removal; Cancel/closing preserves form/history.
            The shared project history can restore every truncated row and result.
        """
        spanish = language is Language.SPANISH
        source = self.active_source()
        first = (count + 1) if count is not None else 1
        last = len(source.tasks) if source is not None else first
        dialog = QMessageBox(self)
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[self.active_kind()]
        dialog.setWindowTitle(
            ("Reducir tareas: " if spanish else "Reduce task count: ") + tool
        )
        dialog.setText(
            (
                f"Se eliminarán las filas {first}-{last}, "
                "incluidos datos introducidos. "
                "Deshacer puede restaurarlas. ¿Continuar?"
                if spanish
                else f"Rows {first}-{last} will be removed, including entered data. "
                "Undo can restore them. Continue?"
            )
            + "\n\n"
            + self.task_count_context()
        )
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setStyleSheet(WORKSPACE_STYLE)
        dialog.setIconPixmap(self.icons["help"].pixmap(QSize(40, 40)))
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Cancel)
        remove = dialog.button(QMessageBox.Yes)
        assert remove is not None
        remove.setText("Eliminar filas" if spanish else "Remove rows")
        remove.setIcon(self.icons["filter_apply"])
        cancel = dialog.button(QMessageBox.Cancel)
        assert cancel is not None
        cancel.setText("Cancelar" if spanish else "Cancel")
        cancel.setIcon(self.icons["cancel"])
        try:
            return bool(dialog.exec() == QMessageBox.Yes)
        finally:
            dialog.close()
            dialog.deleteLater()

    def open_preferences(self) -> None:
        """Apply preferences after validating pending text; Cancel edits nothing.

        Project units/decimals are committed on Apply without rewriting sources/results;
        language, decimal mark, camera focus and gauge markers remain personal
        preferences. Gauge changes repaint without changing results/animation. Cancel
        leaves settings and pending text intact. Valid pending task text is committed
        first for ordinary Apply, even if preference persistence fails.
        Count changes accept valid pending text and preserve retained rows. Removing
        populated trailing rows requires consent; invalid text remains for correction.
        Resizing remains one undoable source edit. Personal/project storage errors
        propagate through the host error boundary; the two stores are independent.

        Args:
            None.

        Returns:
            None.
        """
        store = self._settings_store
        if store is None:
            return
        metadata = self.presenter.workspace.project_metadata
        source = self.active_source()
        dialog = PreferencesDialog(
            self.language,
            self.presenter.system,
            self.icons,
            parent=self,
            convention=self.presenter.convention,
            precision=metadata.precision if metadata else DisplayPrecision(),
            task_count=len(source.tasks) if source is not None else None,
            assessment_context=self.task_count_context(),
            tool_name={
                AssessmentKind.LIFFT: "LiFFT",
                AssessmentKind.DUET: "DUET",
                AssessmentKind.TST: "ST",
            }[self.active_kind()],
            project_open=metadata is not None,
            animated_focus=store.load().animated_body_region_focus,
            gauge_markers=store.load().gauge_markers,
            undo_limit=store.load().undo_limit,
            developer_enabled=self._developer_enabled,
        )
        try:
            if dialog.exec() != QDialog.Accepted:
                return
            if dialog.only_developer_changed():
                self.set_developer_mode(dialog.developer_option.isChecked())
                return
            developer_enabled = dialog.developer_option.isChecked()
            language = list(Language)[dialog.language.currentIndex()]
            units = list(MeasurementSystem)[dialog.units.currentIndex()]
            convention = list(DecimalConvention)[dialog.decimal.currentIndex()]
            precision = DisplayPrecision(
                **{key: spin.value() for key, spin in dialog.decimal_fields.items()}
            )
            reset_count = (
                dialog.count.value() if dialog.reset_tasks.isChecked() else None
            )
            undo_limit = dialog.undo_limit.value()
            animated_focus = dialog.animated_focus.isChecked()
            gauge_markers = GaugeMarkerSettings(
                dialog.gauge_ticks.isChecked(),
                dialog.gauge_labels.isChecked(),
                dialog.gauge_interval.value(),
            )
        finally:
            dialog.close()
            dialog.deleteLater()
        panel = self.secondary_panel() or self.task_panel
        if (
            reset_count is not None
            and self.task_count_removes_data(reset_count)
            and not self.confirm_task_reset(language, reset_count)
        ):
            return
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return
        store.save(
            replace(
                store.load(),
                animated_body_region_focus=animated_focus,
                undo_limit=undo_limit,
                gauge_markers=gauge_markers,
                language=language,
                default_units=units,
                decimal_convention=convention,
            )
        )
        editing = self.presenter.workspace.editing
        if editing is not None:
            editing.set_undo_limit(undo_limit)
        if self.results_sidebar is not None:
            self.results_sidebar.risk_gauge.set_marker_settings(gauge_markers)
        if metadata is not None:
            self.presenter.workspace.update_display_settings(
                replace(metadata, default_units=units, precision=precision)
            )
        self.language = language
        self.presenter.system = units
        self.presenter.convention = convention
        for combo, index in (
            (self.units, list(MeasurementSystem).index(units)),
            (self.decimal, list(DecimalConvention).index(convention)),
            (self.languages, list(Language).index(language)),
        ):
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
        renderer: object = self._body_renderer
        if isinstance(renderer, AnimatedBodyRenderer):
            renderer.set_animation_enabled(animated_focus)
        if self._assessment_menu is not None:
            action = self._assessment_menu.camera_animation
            action.blockSignals(True)
            action.setChecked(animated_focus)
            action.blockSignals(False)
        if reset_count is not None:
            presenter = (
                self.tst_presenter
                if self.tst_active
                else self.duet_presenter
                if self.duet_active
                else self.presenter
            )
            presenter.set_task_count(reset_count)
        self.translate()
        self.refresh()
        self.set_developer_mode(developer_enabled)

    def set_developer_mode(self, enabled: bool) -> None:
        """Toggle the preview menu for this main-window session only.

        Args:
            enabled: Runtime visibility; never added to UserSettings or project data.

        Returns:
            None; no source resolution, dirty marker or persistence operation occurs.
        """
        self._developer_enabled = enabled
        if self._developer_menu is not None:
            action = self._developer_menu.menuAction()
            assert action is not None
            action.setVisible(enabled)

    def open_developer_preview(self) -> None:
        """Launch an isolated prototype without accepting main assessment drafts.

        Args:
            None.

        Returns:
            None; the injected composition root detaches read-only catalog values.
        """
        if self._developer_enabled and self._developer_opener is not None:
            self._developer_opener(self)

    def change_gauge_markers(self, settings: GaugeMarkerSettings) -> None:
        """Persist a right-click gauge choice before changing its visible appearance.

        Args:
            settings: Validated personal main/PLOT marker options.

        Returns:
            None; update only user preferences and the gauge. A diagnostic host without
            a settings store applies locally. Result/source and animation are untouched.

        Raises:
            OSError: Preference read/write fails; the existing gauge options remain.
            ValueError: Stored settings are corrupt or unsupported; they are preserved.
        """
        if self._settings_store is not None:
            self._settings_store.save(
                replace(self._settings_store.load(), gauge_markers=settings)
            )
        if self.results_sidebar is not None:
            self.results_sidebar.risk_gauge.set_marker_settings(settings)

    def change_preferences(self) -> None:
        """Rebind after an explicit unit/decimal change with no pending text.

        Args:
            None.

        Returns:
            None.
        """
        secondary = self.secondary_panel()
        if secondary is not None:
            try:
                secondary.commit_inputs()
            except DraftError as error:
                self.message.setText(Translator(self.language).text(error.issue.code))
                for combo, index in (
                    (self.units, list(MeasurementSystem).index(self.presenter.system)),
                    (
                        self.decimal,
                        list(DecimalConvention).index(self.presenter.convention),
                    ),
                ):
                    combo.blockSignals(True)
                    combo.setCurrentIndex(index)
                    combo.blockSignals(False)
                return
        if self.secondary_panel() is None and self.task_panel is not None:
            try:
                self.task_panel.commit_inputs()
            except DraftError as error:
                self.message.setText(Translator(self.language).text(error.issue.code))
                self.units.blockSignals(True)
                self.units.setCurrentIndex(
                    list(MeasurementSystem).index(self.presenter.system)
                )
                self.units.blockSignals(False)
                self.decimal.blockSignals(True)
                self.decimal.setCurrentIndex(
                    list(DecimalConvention).index(self.presenter.convention)
                )
                self.decimal.blockSignals(False)
                return
        self.presenter.system = list(MeasurementSystem)[self.units.currentIndex()]
        self.presenter.convention = list(DecimalConvention)[self.decimal.currentIndex()]
        self.run(self.refresh)

    def change_language(self) -> None:
        """Translate independently of units and decimal preferences.

        Args:
            None.

        Returns:
            None.
        """
        self.language = list(Language)[self.languages.currentIndex()]
        self.translate()
        self.run(self.refresh)

    def add_task(self) -> None:
        """Append an unfinished row and select it for entry.

        Args:
            None.

        Returns:
            None.
        """
        self.presenter.add()
        self.refresh()
        self.table.selectRow(self.table.rowCount() - 1)

    def remove_task(self) -> None:
        """Remove the selected row through undoable source history.

        Args:
            None.

        Returns:
            None.
        """
        if self.context is not None and self.table.currentRow() >= 0:
            self.presenter.remove(
                self.context.view.tasks[self.table.currentRow()].task_id
            )
            self.refresh()

    def undo(self) -> None:
        """Undo the latest accepted navigation/source operation or focused typing.

        Args:
            None.

        Returns:
            None.
        """
        if self.history_actions is not None:
            self.history_actions.replay(redo=False)
            return
        active = self.presenter.workspace.active
        if active is not None:
            active.undo()
            self.refresh()

    def redo(self) -> None:
        """Redo the next accepted navigation/source operation or focused typing.

        Args:
            None.

        Returns:
            None.
        """
        if self.history_actions is not None:
            self.history_actions.replay(redo=True)
            return
        active = self.presenter.workspace.active
        if active is not None:
            active.redo()
            self.refresh()

    def confirm_clear_assessment(self) -> bool:
        """Confirm scoped input/result clearing with Cancel as the safe default.

        Args:
            None.

        Returns:
            True only for explicit Clear assessment; Cancel preserves source/pending
            text. Ownership, row count, units and unrelated tools/workers are retained.
        """
        spanish = self.language is Language.SPANISH
        caption = "Limpiar evaluación" if spanish else "Clear assessment"
        dialog = QMessageBox(self)
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[self.active_kind()]
        dialog.setWindowTitle(caption + ": " + tool)
        dialog.setText(
            (
                "Se borrarán los datos y resultados de esta evaluación. "
                "Se conservarán sus tareas y contexto. "
                "Deshacer puede restaurar los datos."
                if spanish
                else "This assessment's inputs and calculated results will be cleared. "
                "Its tasks and context will be kept. Undo can restore the data."
            )
            + "\n\n"
            + self.task_count_context()
        )
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setStyleSheet(WORKSPACE_STYLE)
        dialog.setIconPixmap(self.icons["delete"].pixmap(QSize(40, 40)))
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Cancel)
        accept = dialog.button(QMessageBox.Yes)
        cancel = dialog.button(QMessageBox.Cancel)
        assert accept is not None and cancel is not None
        accept.setText(caption)
        accept.setIcon(self.icons["delete"])
        cancel.setText("Cancelar" if spanish else "Cancel")
        cancel.setIcon(self.icons["cancel"])
        try:
            return bool(dialog.exec() == QMessageBox.Yes)
        finally:
            dialog.close()
            dialog.deleteLater()

    def clear_assessment(self) -> None:
        """Clear only the active source/results, keeping its owner and editable grid.

        Consent precedes source mutation and invalid pending text is not parsed.
        Existing tool commands preserve task count/IDs and original units; shared
        staging records one reversible operation without publishing the project file.

        Args:
            None.

        Returns:
            None; cancelled consent preserves pending input. Undo restores the exact
            accepted inputs/results; other workers, tools and contexts are untouched.
        """
        workspace = self.presenter.workspace
        if workspace.active is None or not self.confirm_clear_assessment():
            return
        presenter = (self.presenter, self.duet_presenter, self.tst_presenter)[
            (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST).index(
                self.active_kind()
            )
        ]
        presenter.reset_grid()
        presenter.evaluator.clear()
        self.pending = False
        try:
            workspace.stage_assessments(label="assessment.clear")
        finally:
            self.refresh()

    def open_task_count(self) -> None:
        """Open the unified settings window from the original toolbar entry.

        Args:
            None.

        Returns:
            None; task resetting remains opt-in, confirmed and undoable.
        """
        self.open_preferences()

    def calculate(self) -> None:
        """Evaluate committed grid previews; review/invalid states show no totals.

        Args:
            None.

        Returns:
            None.
        """
        secondary = self.secondary_panel()
        if secondary is not None:
            secondary.calculate()
            self.accept_calculated_result()
            return
        active = self.presenter.workspace.active
        if active is not None:
            self.message.clear()
            result = (
                self.presenter.evaluator.evaluate_lifft_grid(active)
                if self.task_panel is not None
                else self.presenter.evaluator.evaluate(active)
            )
            self.show_result()
            if self.task_panel is not None:
                self.task_panel.show_result()
            if result.status is EvaluationStatus.PARTIAL:
                self.message.setText(
                    Translator(self.language).text("evaluation.lifft_incomplete")
                )
            elif result.issues:
                translator = Translator(self.language)
                self.message.setText(
                    "\n".join(
                        dict.fromkeys(
                            translator.text(issue.code) for issue in result.issues
                        )
                    )
                )

        self.accept_calculated_result()

    def accept_calculated_result(self) -> None:
        """Retain a fresh calculation in the open project until its main Save.

        Args:
            None.

        Returns:
            None; scientific evaluation remains with the existing tool presenters.
            Diagnostic workspaces keep their original explicit-save behavior.
        """
        self.presenter.workspace.stage_calculation(self.current_result_snapshot())
        self.refresh_navigation()

    def show_result(self) -> None:
        """Display only a current LiFFT summary and clear obsolete card colors.

        Args:
            None.

        Returns:
            None.
        """
        if self.history_actions is not None:
            self.history_actions.refresh()
        evaluator = (
            self.tst_presenter.evaluator
            if self.tst_active
            else self.duet_presenter.evaluator
            if self.duet_active
            else self.presenter.evaluator
        )
        result = evaluator.current(self.presenter.workspace.active)
        if self.tst_active and result is None:
            self.message.clear()
        if self.secondary_panel() is not None and result is not None:
            self.message.setText(
                Translator(self.language).text("evaluation.lifft_incomplete")
                if result.status is EvaluationStatus.PARTIAL
                else "\n".join(
                    dict.fromkeys(
                        Translator(self.language).text(i.code) for i in result.issues
                    )
                )
            )
        panel = self.secondary_panel() or self.task_panel
        historical = (
            self.presenter.workspace.historical_result()
            if result is None and (panel is None or not panel.pending)
            else None
        )
        if self.results_sidebar is not None:
            self.results_sidebar.update_result(
                self.active_source(),
                result,
                self.language,
                empty_kind=self.active_kind(),
                historical=historical,
                precision=(
                    self.presenter.workspace.project_metadata.precision
                    if self.presenter.workspace.project_metadata
                    else DisplayPrecision()
                ),
            )
        self._show_context_status()
        if self.body_panel is not None:
            self.body_panel.translate(self.language)
            self.body_panel.set_tool(
                self.duet_active, self.language, shoulder=self.tst_active
            )
        if self._body_renderer is not None:
            summary = result.summary if result is not None else None
            color = None
            if isinstance(summary, LifftSummary):
                hex_color = display_lifft_summary(summary).color
                if hex_color is not None:
                    qcolor = QColor(hex_color)
                    color = RgbColor(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
            if isinstance(summary, DuetSummary):
                hex_color = display_duet_summary(summary).color
                if hex_color is not None:
                    qcolor = QColor(hex_color)
                    color = RgbColor(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
            if isinstance(summary, TstSummary):
                hex_color = display_tst_summary(summary).color
                if hex_color is not None:
                    qcolor = QColor(hex_color)
                    color = RgbColor(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
            if historical is not None:
                hex_color = historical_damage_color(historical)
                if hex_color is not None:
                    qcolor = QColor(hex_color)
                    color = RgbColor(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
            region = (
                BodyRegion.SHOULDERS
                if self.tst_active
                else BodyRegion.DISTAL_UPPER_EXTREMITIES
                if self.duet_active
                else BodyRegion.LOW_BACK
            )
            overlays: list[tuple[BodyRegion, RgbColor]] = []
            view = self.assessment_navigation.view
            if view is not None and self.presenter.workspace.active is not None:
                workspace = self.presenter.workspace
                metadata = workspace.project_metadata
                assert metadata is not None
                active = workspace.active
                assert active is not None
                for source in self.assessment_navigation.overlay_sources():
                    if source is active.state:
                        overlay_region, overlay_color = region, color
                    else:
                        session = DocumentSession(
                            DocumentKey(metadata.project_id, "body_preview"),
                            source,
                            persisted=True,
                        )
                        evaluator = AssessmentEvaluator()
                        if isinstance(source, LifftDraft):
                            evaluated = evaluator.evaluate_lifft_grid(session)
                            overlay_region = BodyRegion.LOW_BACK
                            hex_color = (
                                display_lifft_summary(evaluated.summary).color
                                if isinstance(evaluated.summary, LifftSummary)
                                else None
                            )
                        elif isinstance(source, DuetDraft):
                            evaluated = evaluator.evaluate_duet_grid(session)
                            overlay_region = BodyRegion.DISTAL_UPPER_EXTREMITIES
                            hex_color = (
                                display_duet_summary(evaluated.summary).color
                                if isinstance(evaluated.summary, DuetSummary)
                                else None
                            )
                        else:
                            evaluated = evaluator.evaluate_tst_grid(session)
                            overlay_region = BodyRegion.SHOULDERS
                            hex_color = (
                                display_tst_summary(evaluated.summary).color
                                if isinstance(evaluated.summary, TstSummary)
                                else None
                            )
                        sibling_color = QColor(hex_color) if hex_color else None
                        overlay_color = (
                            RgbColor(
                                sibling_color.redF(),
                                sibling_color.greenF(),
                                sibling_color.blueF(),
                            )
                            if sibling_color
                            else None
                        )
                    if overlay_color is not None:
                        overlays.append((overlay_region, overlay_color))
            self._body_renderer.set_state(BodyViewState(region, color, tuple(overlays)))
        self.damage_value.setText("—")
        self.probability_value.setText("—")
        for label in (self.damage_value, self.probability_value):
            label.setStyleSheet("")
        if result is not None and isinstance(result.summary, LifftSummary):
            display = display_lifft_summary(
                result.summary,
                self.presenter.workspace.project_metadata.precision
                if self.presenter.workspace.project_metadata
                else DisplayPrecision(),
            )
            self.damage_value.setText(display.damage_text)
            self.probability_value.setText(display.probability_text)
            if display.color:
                for label in (self.damage_value, self.probability_value):
                    label.setStyleSheet(
                        "color: #1B2933; background: "
                        + display.color
                        + "; padding: 6px; border-radius: 5px;"
                    )

    def resolve_context_text(self) -> bool:
        """Require the existing explicit Apply/Discard controls before navigation.

        Args:
            None.

        Returns:
            False while unfinished input requires explicit resolution; True when context
            navigation may proceed.
        """
        if self.pending:
            self.message.setText(self.text("pending"))
            return False
        return True

    def choose_assessment_context(
        self, *, create: bool = False, worker_id: str | None = None
    ) -> None:
        """Select or create LiFFT data through explicit assignment choices.

        Args:
            create: True requests explicit assessment creation; False selects saved
                assessment data.
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.

        Returns:
            None.

        Raises:
            KeyError: The explicit saved identity or catalog key is absent.
        """
        if not self.resolve_context_text():
            return
        workspace = self.presenter.workspace
        if not workspace.supports_assignment_history:
            return
        if self.main_navigation is not None:
            if create and worker_id is None:
                workers = worker_options(
                    workspace.read_hierarchy().hierarchy.work, WorkerOrder.ID
                )
                worker_id, accepted = self.choose_item(
                    self.text("new_assessment"),
                    self.text("choose_worker"),
                    [w.worker_id for w in workers],
                )
                if not accepted:
                    return
            jobs = workspace.read_jobs().jobs
            if (
                create
                and worker_id is not None
                and not any(
                    a.active and a.worker.worker_id == worker_id
                    for a in jobs.assignments
                )
            ):
                self._select_navigation_worker(worker_id)
                return
            self._browse_context_picker(worker_id)
            return
        hierarchy = workspace.read_hierarchy()
        options = worker_options(hierarchy.hierarchy.work, WorkerOrder.ID)
        if not options:
            return
        if worker_id is None:
            labels = [option.worker_id for option in options]
            label, accepted = self.choose_item(
                self.text("new_assessment" if create else "assessment_context"),
                self.text("choose_worker"),
                labels,
            )
            if not accepted:
                return
            worker = options[labels.index(label)].worker_id
        else:
            if not any(option.worker_id == worker_id for option in options):
                raise KeyError(worker_id)
            worker = worker_id
        host = AssignmentDialogHost(
            workspace,
            self.icons,
            resolve_pending=self.resolve_context_text,
            choose_dirty=self.browse_choice,
            parent=self,
        )
        if create:
            outcome = host.create(worker, uuid4().hex, self.blank_active_source())
        else:
            outcome = host.select(worker, self.active_kind())
        if outcome.completed:
            self.presenter.evaluator.clear()
            self.refresh()

    def open_rotation(self) -> None:
        """Browse modal JROT over saved risks without committing assessment input.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if self._rotation_opener is None or not workspace.supports_rotations:
            return
        self._rotation_opener(workspace.rotation_repository(), self.language, self)

    def open_plot(self) -> None:
        """Browse saved PLOT data without committing unfinished assessment fields.

        Args:
            None; resynchronize main-gauge appearance from shared preferences after
            the modal closes. Assessment source and result data are unchanged.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if self._plot_opener is None or not workspace.supports_job_risk:
            return
        self._plot_opener(
            workspace.plot_repository(),
            self.language,
            self.presenter.system,
            self.load_plot_assessment,
            self,
        )
        if self._settings_store is not None and self.results_sidebar is not None:
            self.results_sidebar.risk_gauge.set_marker_settings(
                self._settings_store.load().gauge_markers
            )

    def load_plot_assessment(self, row: SummaryExportRow) -> bool:
        """Open the exact saved PLOT assignment/model through existing dirty policy.

        Source units and ownership come from persisted data, never display labels. The
        PLOT host closes itself only after a True result and its own edit consent.
        Foreign or no-longer-current rows fail before committing pending editor text.

        Args:
            row: Saved typed result row carrying exact source/assignment ownership and
                optional evidence.

        Returns:
            True after accepted exact saved-assignment activation, False after
            rejected/cancelled dirty intent.

        Raises:
            ValueError: PLOT assessment belongs to another project. PLOT assessment is
                no longer the saved current version.
        """
        workspace = self.presenter.workspace
        metadata = workspace.project_metadata
        if metadata is None or row.document.project_id != metadata.project_id:
            raise ValueError("PLOT assessment belongs to another project.")
        history = workspace.read_history().history
        if row.assignment_id is None:
            raise ValueError("PLOT requires an associated assessment.")
        entry = history.current_for(row.assignment_id, row.kind)
        if entry is None or entry.document_id != row.document.document_id:
            raise ValueError("PLOT assessment no longer matches the saved ownership.")
        active = workspace.active
        if active is not None and active.document == row.document:
            return True
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return False
        outcome = workspace.select_assignment(
            AssignmentSelection(metadata.project_id, row.assignment_id, row.kind),
            choice=self.browse_choice(),
        )
        if outcome.completed:
            self.presenter.evaluator.clear()
            self.duet_presenter.evaluator.clear()
            self.tst_presenter.evaluator.clear()
            self.refresh()
        return outcome.completed

    def open_saved_tool_data(self) -> None:
        """Browse saved data for the active worker/tool; Close preserves pending text.

        Acceptance resolves pending input and existing Save/Discard/Cancel intent before
        selecting the exact saved assignment. It never creates or promotes an
        assessment, nor infers ownership from displayed workplace labels.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        active = workspace.active
        if active is None or not workspace.supports_assignment_history:
            return
        history = workspace.read_history().history
        entry = next(
            (
                e
                for e in history.entries
                if e.document_id == active.document.document_id
            ),
            None,
        )
        if entry is None:
            return
        jobs = workspace.read_jobs().jobs
        options = saved_tool_options(jobs, history, entry.worker_id, self.active_kind())
        dialog = ToolDataDialog(options, language=self.language, parent=self)
        dialog.close_button.setIcon(self.icons["close"])
        dialog.load_button.setIcon(self.icons["open"])
        try:
            accepted = dialog.exec() == QDialog.Accepted
            selected = dialog.selected
        finally:
            dialog.close()
            dialog.deleteLater()
        if not accepted or selected is None:
            return
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return
        active = workspace.active
        choice = (
            self.browse_choice() if active is not None and active.is_dirty else None
        )
        outcome = workspace.select_assignment(
            AssignmentSelection(
                jobs.project_id,
                selected.assignment_id,
                selected.kind,
                entry.worker_id if selected.assignment_id is None else None,
            ),
            choice=choice,
        )
        if outcome.completed:
            self.presenter.evaluator.clear()
            self.duet_presenter.evaluator.clear()
            self.tst_presenter.evaluator.clear()
            self.refresh()

    def browse_choice(self) -> CloseChoice | None:
        """Retain accepted project drafts while navigating within an open project.

        Args:
            None.

        Returns:
            None for integrated private editing; diagnostics keep existing source
            Save/Discard/Cancel behavior. Project departure still uses dirty_choice.
        """
        if self.presenter.workspace.editing is not None:
            self.presenter.workspace.stage_assessments()
            return None
        return self.dirty_choice()

    def dirty_choice(self) -> CloseChoice | None:
        """Resolve edited inputs or an unpublished project before leaving it.

        Args:
            None.

        Returns:
            Save/Discard/Cancel disposition, or None for a clean permanent project.
            Cancelled first Save retains temporary backing.
        """
        if (
            not self.presenter.workspace.has_unsaved_changes
            and not self._is_unsaved_project()
        ):
            return None
        dialog = QMessageBox(self)
        dialog.setText(self.text("dirty"))
        save = dialog.addButton(self.text("save"), QMessageBox.AcceptRole)
        discard = dialog.addButton(
            self.text("discard_changes"), QMessageBox.DestructiveRole
        )
        dialog.addButton(self.text("cancel"), QMessageBox.RejectRole)
        dialog.exec()
        if dialog.clickedButton() is save:
            if self._is_unsaved_project():
                self.save_project_as()
                return (
                    CloseChoice.CANCEL
                    if self._is_unsaved_project()
                    else CloseChoice.DISCARD
                )
            return (
                CloseChoice.SAVE
                if self._approve_assessment_save()
                else CloseChoice.CANCEL
            )
        if dialog.clickedButton() is discard:
            return CloseChoice.DISCARD
        return CloseChoice.CANCEL

    def choose_file(self, saving: bool, *, title_key: str | None = None) -> str:
        """Use the standard platform file chooser with existing product file policy.

        Args:
            saving: True configures Save destination selection; False configures
                existing-file opening.
            title_key: Optional stable message key overriding the file chooser title.

        Returns:
            Selected destination/source path, or an empty string after cancellation.
        """
        key = "save" if saving else "open"
        dialog = QFileDialog(
            self, self.text(title_key or ("new" if saving else "open"))
        )
        if title_key is not None:
            # Snapshots are exclusive. Do not suggest that an existing file can
            # be overwritten by this command; the adapter also checks atomically.
            dialog.setOption(QFileDialog.DontConfirmOverwrite)
        if saving:
            dialog.setDefaultSuffix("csv" if title_key == "export_csv" else "ergprj")
        dialog.setAcceptMode(
            QFileDialog.AcceptSave if saving else QFileDialog.AcceptOpen
        )
        dialog.setFileMode(QFileDialog.AnyFile if saving else QFileDialog.ExistingFile)
        dialog.setNameFilter(
            "CSV (*.csv)"
            if title_key == "export_csv"
            else (
                "Proyectos ErgoTools (*.ergprj)"
                if self.language is Language.SPANISH
                else "ErgoTools projects (*.ergprj)"
            )
        )
        dialog.setLabelText(QFileDialog.Accept, self.text(key))
        dialog.setLabelText(QFileDialog.Reject, self.text("cancel"))
        dialog.setLabelText(QFileDialog.LookIn, self.text("look_in"))
        dialog.setLabelText(QFileDialog.FileName, self.text("file_name"))
        dialog.setLabelText(QFileDialog.FileType, self.text("file_type"))
        box = dialog.findChild(QDialogButtonBox)
        if box is not None:
            for button in box.buttons():
                icon = (
                    key
                    if box.buttonRole(button) == QDialogButtonBox.AcceptRole
                    else "cancel"
                )
                button.setIcon(self.icons[icon])
        return dialog.selectedFiles()[0] if dialog.exec() else ""

    def choose_item(self, title: str, label: str, items: list[str]) -> tuple[str, bool]:
        """Use translated selection actions with existing processed Apply/Cancel icons.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            label: Visible label/legend caption; None omits an optional chart series
                label.
            items: Selectable display captions in their presented order; caller maps the
                chosen caption to identity.

        Returns:
            Selected displayed caption and explicit acceptance flag; cancellation must
            not trigger the caller's action.
        """
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)
        combo = dialog.findChild(QComboBox)
        if combo is not None:
            # Match management/JROT popups; native delegates can paint white on white.
            combo.setItemDelegate(QStyledItemDelegate(combo))
        dialog.setOkButtonText(self.text("select"))
        dialog.setCancelButtonText(self.text("cancel"))
        box = dialog.findChild(QDialogButtonBox)
        if box is not None:
            for button in box.buttons():
                button.setIcon(
                    self.icons[
                        "cancel"
                        if box.buttonRole(button) == QDialogButtonBox.RejectRole
                        else "filter_apply"
                    ]
                )
        accepted = bool(dialog.exec())
        return dialog.textValue(), accepted

    def choose_project_details(
        self, metadata: ProjectMetadata | None = None
    ) -> tuple[str, str] | None:
        """Collect the original Name/Description form; Cancel has no side effects.

        Args:
            metadata: Saved or proposed project metadata; None uses the form's empty
                defaults.

        Returns:
            Literal project name/description pair after acceptance, or None on
            cancellation.
        """
        dialog = ProjectDetailsDialog(
            self.language,
            parent=self,
            name=metadata.title if metadata else "",
            description=(metadata.description or "") if metadata else "",
        )
        try:
            if dialog.exec_() != QDialog.Accepted:
                return None
            return dialog.name_input.text(), dialog.description_input.toPlainText()
        finally:
            dialog.close()
            dialog.deleteLater()

    def _is_unsaved_project(self) -> bool:
        """Identify only this window's owned temporary project backing.

        Args:
            None.

        Returns:
            True only while the workspace uses this window's owned temporary native
            backing.
        """
        return (
            self._unsaved_backing is not None
            and self.presenter.workspace.location
            == str(Path(self._unsaved_backing.name) / "unsaved.ergprj")
        )

    def _release_unsaved_backing(self) -> None:
        """Remove temporary backing after its repository has been released.

        Args:
            None.

        Returns:
            None.
        """
        if self._unsaved_backing is not None and not self._is_unsaved_project():
            self._unsaved_backing.cleanup()
            self._unsaved_backing = None

    def _new_unsaved_project(self) -> None:
        """Reset into editable unsaved state; defer destination/details to Save.

        Temporary SQLite backing supplies the existing editing/persistence ports. It is
        never a recent project. Failed creation or cancelled dirty consent retains the
        current owner; first Save publishes an exclusive whole copy.

        Args:
            None.

        Returns:
            None.
        """
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return
        choice = self.dirty_choice()
        if choice is CloseChoice.CANCEL:
            return
        backing = TemporaryDirectory(prefix="ergotools-unsaved-")
        adopted = False
        try:
            system = self.presenter.system
            outcome = self.presenter.workspace.create_empty(
                str(Path(backing.name) / "unsaved.ergprj"),
                ProjectMetadata(uuid4().hex, self.text("untitled_project"), system),
                choice=choice,
                remember=False,
            )
            if not outcome.completed:
                return
            self._release_unsaved_backing()
            self._unsaved_backing = backing
            adopted = True
            self.presenter.evaluator.clear()
            self.refresh()
        finally:
            if not adopted:
                backing.cleanup()

    def new_project(self) -> None:
        """Start unsaved integrated editing; retain the standalone harness workflow.

        Args:
            None.

        Returns:
            None.
        """
        if self.main_navigation is not None:
            self._new_unsaved_project()
            return
        location = self.choose_file(True)
        if not location:
            return
        description = None
        created_at = None
        language = None
        title = Path(location).stem
        units, ok = self.choose_item(
            self.text("new"),
            self.text("source_choice"),
            [self.text("imperial"), self.text("metric")],
        )
        if not ok:
            return
        system = (
            MeasurementSystem.IMPERIAL
            if units == self.text("imperial")
            else MeasurementSystem.METRIC
        )
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return
        outcome = self.presenter.workspace.create(
            str(Path(location).absolute()),
            ProjectMetadata(
                uuid4().hex, title, system, description, created_at, language
            ),
            "lifft",
            self.blank_lifft_source(system),
            choice=self.dirty_choice(),
        )
        if outcome.completed:
            self.presenter.evaluator.clear()
            self.refresh()
            if outcome.warning_keys:
                self.message.setText(
                    "\n".join(
                        Translator(self.language).text(key)
                        for key in outcome.warning_keys
                    )
                )

    def open_project(self) -> None:
        """Choose a project, converting original sources to a separate copy.

        Args:
            None.

        Returns:
            None.
        """
        location = self.choose_file(False)
        if location:
            self.open_project_location(location)

    def open_project_location(self, location: str) -> None:
        """Open native data or explain the optional external upgrade first.

        Args:
            location: Explicit native project path selected by CLI, menu or file
                chooser.

        Returns:
            None.

        Raises:
            OSError: Source/native file access fails.
            ValueError: Native validation fails after conversion or selection.
        """
        location = str(Path(location).absolute())
        conversion = self._project_conversion
        if conversion is not None and conversion.requires_conversion(location):
            self._open_migrated_project(location, conversion)
        else:
            self._open_native_project(location)

    def _open_migrated_project(
        self, source: str, conversion: ProjectConversion
    ) -> None:
        """Own temporary conversion, activation and cleanup without source writes.

        Args:
            source: English reference UI wording or earlier project path, as stated by
                this operation; user values are retained literally.
            conversion: External project-conversion port; optional tooling is never
                imported into the app.

        Returns:
            None.

        Raises:
            OSError: Temporary backing or native loading fails.
            ValueError: Converted native data cannot be validated.
        """
        backing = TemporaryDirectory(prefix="ergotools-migrated-")
        adopted = False
        destination = str(Path(backing.name) / "unsaved.ergprj")
        choice: CloseChoice | None = None

        def migrate() -> bool:
            """Resolve current edits before publishing the temporary native copy.

            Args:
                None.

            Returns:
                True after the external converter publishes the temporary native
                project; False after cancelled dirty consent.

            Raises:
                OSError: The external utility cannot be launched.
                ValueError: The source cannot be converted.
            """
            nonlocal choice
            choice = self.dirty_choice()
            if choice is CloseChoice.CANCEL:
                return False
            conversion.convert(source, destination)
            return True

        suggestion = str(Path(source).with_name(Path(source).stem + "_upgraded.ergprj"))
        dialog = ProjectMigrationDialog(
            self.language,
            conversion.command_line(source, suggestion),
            migrate,
            parent=self,
        )
        try:
            if dialog.exec() != QDialog.Accepted or choice is CloseChoice.CANCEL:
                return
            if not self._open_native_project(
                destination, choice=choice, remember=False
            ):
                return
            self._release_unsaved_backing()
            self._unsaved_backing = backing
            adopted = True
            self.refresh_navigation()
            self.message.setText(self.text("migration_saved_required"))
        finally:
            dialog.deleteLater()
            if not adopted:
                backing.cleanup()

    def _open_native_project(
        self,
        location: str,
        *,
        choice: CloseChoice | None = None,
        remember: bool = True,
    ) -> bool:
        """Open integrated projects automatically; retain the diagnostic picker.

        Args:
            location: Explicit native project path selected by CLI, menu or file
                chooser.
            choice: Previously collected dirty-source disposition, or None to let the
                existing policy ask.
            remember: True permits a successfully opened permanent project to enter
                recent settings.

        Returns:
            True after native activation; False after cancellation. Integrated projects
            choose a saved worker/tool context automatically, including unclassified
            readable data. Empty projects remain browsable without creating sources.

        Raises:
            OSError: Native input cannot be opened.
            ValueError: Native project or selected ownership is invalid.
        """
        documents = self.list_documents(location)
        if not documents:
            if self.main_navigation is None:
                self.message.setText(self.text("no_lifft"))
                return False
            outcome = self.presenter.workspace.switch(
                location,
                None,
                choice=choice if choice is not None else self.dirty_choice(),
                remember=remember,
            )
            if outcome.completed:
                metadata = self.presenter.workspace.project_metadata
                assert metadata is not None
                self.presenter.system = metadata.default_units
                self.units.blockSignals(True)
                self.units.setCurrentIndex(
                    list(MeasurementSystem).index(metadata.default_units)
                )
                self.units.blockSignals(False)
                self._empty_kind = AssessmentKind.LIFFT
                self.assessment_navigation.view = None
                if self.presenter.workspace.supports_assignment_history:
                    self._initial_assessment_view()
                self.presenter.evaluator.clear()
                self.duet_presenter.evaluator.clear()
                self.tst_presenter.evaluator.clear()
                self.refresh()
                self.message.setText(
                    "\n".join(
                        Translator(self.language).text(key)
                        for key in outcome.warning_keys
                    )
                )
            return outcome.completed
        options = (
            self.document_options(location, self.language)
            if self.document_options is not None
            else tuple((identity, identity) for identity in documents)
        )
        identities = {label: identity for identity, label in options}
        if self.main_navigation is not None:
            selected, ok = documents[0], True
        else:
            label, ok = self.choose_item(
                self.text("open"), self.text("pick"), list(identities)
            )
            selected = identities[label] if ok else ""
        if ok:
            outcome = self.presenter.workspace.switch(
                location,
                selected,
                choice=choice if choice is not None else self.dirty_choice(),
                remember=remember,
            )
            if outcome.completed:
                metadata = self.presenter.workspace.project_metadata
                assert metadata is not None
                self.presenter.system = metadata.default_units
                self.units.blockSignals(True)
                self.units.setCurrentIndex(
                    list(MeasurementSystem).index(metadata.default_units)
                )
                self.units.blockSignals(False)
                self.assessment_navigation.view = None
                if (
                    self.main_navigation is not None
                    and self.presenter.workspace.supports_assignment_history
                ):
                    self._initial_assessment_view()
                self.presenter.evaluator.clear()
                self.refresh()
                if outcome.warning_keys:
                    self.message.setText(
                        "\n".join(
                            Translator(self.language).text(key)
                            for key in outcome.warning_keys
                        )
                    )
            return outcome.completed
        return False

    def refresh_recent_projects(self) -> None:
        """Read only user settings when expanding the recent menu.

        Args:
            None.

        Returns:
            None.
        """
        if self._settings_store is not None and self._assessment_menu is not None:
            self._assessment_menu.set_recent(
                self._settings_store.load().recent_documents
            )

    def clear_recent_history(self) -> None:
        """Clear only saved locations; retain preferences, open project and edits.

        Args:
            None.

        Returns:
            None.
        """
        if self._settings_store is not None:
            self._settings_store.save(self._settings_store.load().clear_recent())
            self.refresh_recent_projects()

    def open_recent_project(self, location: str) -> None:
        """Open an explicit saved location, or offer to forget a missing file.

        Args:
            location: Explicit native project path selected by CLI, menu or file
                chooser.

        Returns:
            None.
        """
        if not Path(location).is_file():
            spanish = self.language is Language.SPANISH
            if (
                QMessageBox.question(
                    self,
                    "Proyecto no encontrado" if spanish else "Project not found",
                    (
                        "El archivo ya no está disponible. ¿Eliminarlo del historial?"
                        if spanish
                        else "The file is no longer available. "
                        "Remove it from recent history?"
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                == QMessageBox.Yes
                and self._settings_store is not None
            ):
                try:
                    self._settings_store.save(
                        self._settings_store.load().forget(location)
                    )
                    self.refresh_recent_projects()
                except (OSError, ValueError):
                    _LOG.exception("Removing recent project failed")
                    self.message.setText(self.text("error"))
            return
        self.run(lambda: self.open_project_location(location))

    def close_project(self) -> None:
        """Release the project after dirty disposition; keep the desktop adapter.

        Args:
            None.

        Returns:
            None.
        """
        outcome = self.presenter.workspace.close(choice=self.dirty_choice())
        if not outcome.completed:
            return
        self._empty_kind = AssessmentKind.LIFFT
        self.presenter.evaluator.clear()
        self.duet_presenter.evaluator.clear()
        self.tst_presenter.evaluator.clear()
        self.refresh()
        if outcome.warning_keys:
            self.message.setText(
                "\n".join(
                    Translator(self.language).text(key) for key in outcome.warning_keys
                )
            )

    def save_project_as(self) -> None:
        """Copy current validated edits and activate the copy, leaving the original.

        Args:
            None.

        Returns:
            None.

        Raises:
            OSError: Copy/publication fails; the current project remains owned.
            ValueError: Native snapshot or chosen metadata fails validation.
        """
        unsaved = self._is_unsaved_project()
        location = self.choose_file(True, title_key="save" if unsaved else "save_as")
        if not location:
            return
        path = Path(location).absolute()
        if path.exists():
            self.message.setText(self.text("snapshot_exists"))
            return
        workspace = self.presenter.workspace
        metadata = None
        if self.main_navigation is not None and workspace.supports_job_risk:
            original_metadata = workspace.project_metadata
            assert original_metadata is not None
            details = self.choose_project_details(
                original_metadata
                if not unsaved
                or original_metadata.title != self.text("untitled_project")
                else None
            )
            if details is None:
                return
            name, description = details
            metadata = replace(
                original_metadata,
                title=name.strip() or path.stem,
                description=description,
                created_at=(
                    original_metadata.created_at
                    if unsaved and original_metadata.created_at is not None
                    else datetime.now().replace(microsecond=0)
                ),
                language=(original_metadata.language or self.language)
                if unsaved
                else self.language,
                default_units=original_metadata.default_units
                if unsaved
                else self.presenter.system,
            )
        panel = self.secondary_panel() or self.task_panel
        if panel is not None and panel.commit_inputs():
            self.refresh()
        if not self.resolve_context_text():
            return
        if not self._approve_assessment_save():
            return
        outcome = workspace.save_as(
            str(path), metadata=metadata, result=self.current_result_snapshot()
        )
        self.presenter.evaluator.clear()
        self.duet_presenter.evaluator.clear()
        self.tst_presenter.evaluator.clear()
        self.refresh()
        self.message.setText(
            "\n".join(
                Translator(self.language).text(key) for key in outcome.warning_keys
            )
            if outcome.warning_keys
            else self.text("saved")
        )

    def backup_project(self) -> None:
        """Copy only saved data, retaining pending text and the current session.

        Args:
            None.

        Returns:
            None.
        """
        if self._is_unsaved_project():
            return
        location = self.choose_file(True, title_key="backup")
        if not location:
            return
        path = Path(location).absolute()
        if path.exists():
            self.message.setText(self.text("snapshot_exists"))
            return
        outcome = self.presenter.workspace.backup(str(path))
        self.message.setText(
            "\n".join(
                Translator(self.language).text(key) for key in outcome.warning_keys
            )
            if outcome.warning_keys
            else self.text("backup_saved")
        )

    def open_worker_transfer(self) -> None:
        """Open the original modal using the exact saved assignment of the source.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        active = workspace.active
        if active is None or not workspace.supports_assignment_history:
            return
        entry = next(
            (
                e
                for e in workspace.read_history().history.entries
                if e.document_id == active.document.document_id
            ),
            None,
        )
        if entry is None:
            return

        def resolve_move(request: TransferRequest) -> CloseChoice | None:
            """Resolve pending source input.

            Resolve pending source input and dirty consent only when the accepted move
            touches this window's active assignment.

            Args:
                request: Exact transfer intent used to decide whether the active source
                    needs dirty consent.

            Returns:
                Dirty-source disposition only for an affected active assignment, or None
                when the active source is unaffected.
            """
            selected = {
                e.document_id
                for e in dialog.history.history.entries
                if e.assignment_id == request.source_assignment_id
                and e.kind in request.kinds
            }
            if active.document.document_id not in selected:
                return None
            panel = self.secondary_panel() or self.task_panel
            if panel is not None and panel.commit_inputs():
                self.refresh()
            return self.browse_choice()

        if entry.assignment_id is None:
            self.message.setText(
                "Asocie la evaluación a un lugar de trabajo antes de transferirla."
                if self.language is Language.SPANISH
                else "Associate the assessment with a workplace before transferring it."
            )
            return
        dialog = WorkerTransferDialog(
            workspace,
            entry.assignment_id,
            self.icons,
            resolve_move,
            language=self.language,
            parent=self,
        )
        try:
            dialog.exec()
            if dialog.completed:
                if workspace.active is None:
                    self._empty_kind = entry.kind
                    self.refresh()
                else:
                    self.refresh_navigation()
                self.enable_controls()
        finally:
            dialog.close()
            dialog.deleteLater()

    def export_summary_csv(self) -> None:
        """Export saved current versions of the selected tool; retain pending edits.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if (
            workspace.location is None
            or self._summary_loader is None
            or self._csv_writer is None
        ):
            return
        kind = (
            AssessmentKind.TST
            if self.tst_active
            else AssessmentKind.DUET
            if self.duet_active
            else AssessmentKind.LIFFT
        )
        rows = self._summary_loader(workspace.location, kind)
        if not rows:
            self.message.setText(self.text("export_empty"))
            return
        location = self.choose_file(True, title_key="export_csv")
        if not location:
            return
        self._csv_writer(
            str(Path(location).absolute()),
            summary_csv_table(rows, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        self.message.setText(self.text("export_done"))

    def current_result_snapshot(self) -> HistoricalAssessmentResult | None:
        """Detach only a calculation that still belongs to the committed source.

        Args:
            None.

        Returns:
            Matching current calculation detached for native persistence, or None
            without a current applicable evaluation.
        """
        evaluator = (
            self.tst_presenter.evaluator
            if self.tst_active
            else self.duet_presenter.evaluator
            if self.duet_active
            else self.presenter.evaluator
        )
        evaluation = evaluator.current(self.presenter.workspace.active)
        result = (
            result_snapshot(
                evaluation,
                evaluation.preparation.source.system
                if isinstance(evaluation.preparation.source, (LifftDraft, TstDraft))
                else self.presenter.system,
            )
            if evaluation is not None
            else None
        )
        return result

    def save_project(self) -> None:
        """Publish first Save or atomically write the whole accepted open project.

        Args:
            None.

        Returns:
            None.
        """
        if self._is_unsaved_project():
            self.save_project_as()
            return
        if not self._approve_assessment_save():
            return
        if self.presenter.workspace.save(self.current_result_snapshot()):
            if self.assessment_navigation.view is not None:
                self.assessment_navigation.adopt_active()
            self.refresh()
            self.message.setText(self.text("saved"))

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 - Qt override
        """Preserve pending text and dirty source unless the user resolves them.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        if event is None:
            return
        self._release_unsaved_backing()
        secondary = self.secondary_panel()
        if secondary is not None:
            try:
                secondary.commit_inputs()
            except DraftError as error:
                self.message.setText(Translator(self.language).text(error.issue.code))
                event.ignore()
                return
        if self.secondary_panel() is None and self.task_panel is not None:
            try:
                if self.task_panel.commit_inputs():
                    self.refresh()
            except DraftError as error:
                self.message.setText(Translator(self.language).text(error.issue.code))
                event.ignore()
                return
        if self.pending:
            self.message.setText(self.text("pending"))
            event.ignore()
            return
        try:
            if (
                self.presenter.workspace.pending_release_count
                and self.presenter.workspace.retry_releases()
            ):
                self.message.setText(
                    Translator(self.language).text("project.cleanup_failed")
                )
                event.ignore()
                return
            outcome = self.presenter.workspace.close(choice=self.dirty_choice())
            if not outcome.completed or outcome.warning_keys:
                event.ignore()
                if outcome.warning_keys:
                    self.message.setText(
                        Translator(self.language).text(outcome.warning_keys[0])
                    )
                return
        except DraftError as error:
            self.message.setText(Translator(self.language).text(error.issue.code))
            event.ignore()
            return
        except Exception:
            _LOG.exception("Desktop close failed")
            self.message.setText(self.text("error"))
            event.ignore()
            return
        self._release_unsaved_backing()
        self.presenter.editor.clear()
        self.presenter.evaluator.clear()
        self.duet_presenter.context = None
        self.duet_presenter.evaluator.clear()
        self.tst_presenter.editor.clear()
        self.tst_presenter.evaluator.clear()
        if self._body_renderer is not None:
            self._body_renderer.close()
        event.accept()

    def _install_original_navigation(self) -> None:
        """Place reviewed shared controls around the existing task component.

        The existing lifecycle handlers are reused during incremental migration.
        Retained diagnostic controls remain hidden/owned in integrated mode; they do not
        define final layout or introduce alternative source state.

        Args:
            None.

        Returns:
            None.
        """
        # Apply the reference theme before Qt caches toolbar padding/spacing.
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        old_root = self.takeCentralWidget()
        assert old_root is not None and self.task_panel is not None
        root = QWidget()
        root.setObjectName("mainWorkspace")
        self.setCentralWidget(root)
        old_root.setParent(root)
        old_root.hide()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 10, 14, 8)
        layout.setSpacing(10)
        operations = {
            "new": self.new_project,
            "open": self.open_project,
            "save": self.save_project,
            "jobs": self.open_job_management,
            "plot": self.open_plot,
            "jrot": self.open_rotation,
            "settings": self.open_task_count,
            "export": self.export_summary_csv,
            "transfer": self.open_worker_transfer,
            "help": self.open_help,
            "workers": self.open_worker_management,
            "search": self.search_assessment,
            "refresh": self.refresh_navigation,
            "context": self.select_navigation_context,
            "associate": lambda: self._browse_context_picker(associate=True),
            "organization": self.open_organization,
            "follow_worker": lambda: self.set_context_mode(True),
            "keep_context": lambda: self.set_context_mode(False),
        }
        callbacks = {
            key: (lambda checked=False, action=action: self.navigation_action(action))
            for key, action in operations.items()
        }
        navigation = MainNavigation(
            self.icons, callbacks, self.navigate_worker, parent=root
        )
        self.main_navigation = navigation
        layout.addWidget(navigation)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        self.body_panel = BodyRegionPanel(self.icons, parent=root)
        content_layout.addWidget(self.body_panel)
        tool_frame = QFrame()
        tool_frame.setObjectName("workspacePanel")
        tool_frame.setMinimumWidth(0)
        tool_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        tool_layout = QVBoxLayout(tool_frame)
        tool_layout.setContentsMargins(6, 6, 6, 6)
        self.assessment_tabs = QTabWidget()
        self.assessment_tabs.setObjectName("assessmentTabs")
        self.assessment_tabs.setIconSize(QSize(36, 36))
        self.assessment_tabs.setMinimumWidth(0)
        self.assessment_tabs.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        tab_bar = self.assessment_tabs.tabBar()
        assert tab_bar is not None
        tab_bar.setElideMode(Qt.TextElideMode.ElideNone)
        tab_bar.setUsesScrollButtons(False)
        tab_bar.setExpanding(False)
        self.assessment_tabs.addTab(
            self.task_panel,
            self.icons["lifft"],
            "Lifting Fatigue Failure Tool (LiFFT)  ",
        )
        self.duet_panel = DuetTaskPanel(
            self.duet_presenter,
            self.icons,
            report_issue=lambda issue: self.message.setText(
                Translator(self.language).text(issue.code)
            ),
            changed=self.show_result,
            clear=lambda: self.run(self.clear_assessment),
            parent=self.assessment_tabs,
        )
        self.assessment_tabs.addTab(
            self.duet_panel, self.icons["duet"], "Distal Upper Extremity Tool (DUET)  "
        )
        self.tst_panel = TstTaskPanel(
            self.tst_presenter,
            self.icons,
            report_issue=lambda issue: self.message.setText(
                Translator(self.language).text(issue.code)
            ),
            changed=self.show_result,
            clear=lambda: self.run(self.clear_assessment),
            parent=self.assessment_tabs,
        )
        self.assessment_tabs.addTab(
            self.tst_panel, self.icons["shoulder"], "The Shoulder Tool (ST)  "
        )
        for panel in (self.duet_panel, self.tst_panel):
            panel.context_button.clicked.connect(
                lambda: self.run(self.open_saved_tool_data)
            )
        self.assessment_tabs.currentChanged.connect(self.select_tool)
        tool_layout.addWidget(self.assessment_tabs)
        content_layout.addWidget(tool_frame, 1)
        self.results_sidebar = ResultsSidebar(
            parent=root,
            icons=self.icons,
            gauge_markers=(
                self._settings_store.load().gauge_markers
                if self._settings_store is not None
                else GaugeMarkerSettings()
            ),
            change_gauge_markers=lambda settings: self.run(
                lambda: self.change_gauge_markers(settings)
            ),
        )
        content_layout.addWidget(self.results_sidebar)
        layout.addLayout(content_layout, 1)
        layout.addWidget(navigation.context_frame)
        layout.addWidget(navigation.footer)
        self.message.setParent(root)
        status_bar = self.statusBar()
        assert status_bar is not None
        status_bar.addWidget(self.message, 1)
        # The integrated status bar is a single line. Harness word wrapping can
        # increase its height and compress the adjacent fixed avatar captions.
        self.message.setWordWrap(False)
        self.message.setMinimumHeight(0)
        self.setWindowTitle("Fatigue Failure Risk Assessment Tools")
        # Retain reference geometry as the tested minimum, not a resize lock.
        self.setMinimumSize(1550, 1015)
        self.resize(1550, 1015)
        if self._renderer_factory is not None:
            widget, self._body_renderer = self._renderer_factory(
                self.body_panel.viewport
            )
            self.body_panel.attach_renderer(widget, self._body_renderer)
            selectable: object = self._body_renderer
            if isinstance(selectable, SelectableBodyRenderer):
                selectable.set_region_selected(self.select_body_region)
        self._assessment_menu = AssessmentMenu(
            self.buttons,
            self.enable_controls,
            language=self.language,
            open_preferences=lambda: self.run(self.open_preferences),
            open_recent=self.open_recent_project,
            refresh_recent=lambda: self.run(self.refresh_recent_projects),
            clear_recent=lambda: self.run(self.clear_recent_history),
            close_project=lambda: self.run(self.close_project),
            save_as=lambda: self.run(self.save_project_as),
            backup=lambda: self.run(self.backup_project),
            export_csv=lambda: self.run(self.export_summary_csv),
            open_guide=lambda: self.run(self.open_help),
            open_authors=lambda: self.run(self.open_authors),
            camera_animation=self.set_camera_animation,
            open_properties=self.open_project_properties,
            open_project_folder=self.open_project_folder,
            parent=self,
        )
        self._developer_menu = self._assessment_menu.addMenu("Developer Menu")
        assert self._developer_menu is not None
        preview = self._developer_menu.addAction(
            self.icons["jrot"], "JROT workflow prototype…"
        )
        assert preview is not None
        preview.setEnabled(self._developer_opener is not None)
        preview.triggered.connect(lambda: self.run(self.open_developer_preview))
        developer_action = self._developer_menu.menuAction()
        assert developer_action is not None
        developer_action.setVisible(False)
        renderer: object = self._body_renderer
        self._assessment_menu.camera_animation.setEnabled(
            isinstance(renderer, AnimatedBodyRenderer)
        )
        enabled = (
            self._settings_store.load().animated_body_region_focus
            if self._settings_store is not None
            else True
        )
        self._assessment_menu.camera_animation.blockSignals(True)
        self._assessment_menu.camera_animation.setChecked(enabled)
        self._assessment_menu.camera_animation.blockSignals(False)
        if isinstance(renderer, AnimatedBodyRenderer):
            renderer.set_animation_enabled(enabled)
        tab_bar = self.assessment_tabs.tabBar()
        assert tab_bar is not None
        self._tool_tab_focus = ToolTabFocus(tab_bar, self.begin_tool_focus)
        self.assessment_tabs.currentChanged.connect(lambda _: self.end_tool_focus())
        self._assessment_menu.export_csv.setIcon(self.icons["export"])
        for key, asset in (("new_assessment", "new"),):
            self._assessment_menu.actions_by_key[key].setIcon(self.icons[asset])
        for action, asset in (
            (self._assessment_menu.properties, "view"),
            (self._assessment_menu.close_project_action, "close"),
            (self._assessment_menu.preferences, "settings"),
            (self._assessment_menu.user_guide, "help"),
            (self._assessment_menu.about, "help"),
            (self._assessment_menu.camera_animation, "body_view"),
        ):
            action.setIcon(self.icons[asset])
        self.setMenuBar(self._assessment_menu)
        for panel in (self.task_panel, self.duet_panel, self.tst_panel):
            if panel is not None:
                panel.calculate_button.clicked.connect(
                    lambda: self.run(self.accept_calculated_result)
                )
        self.history_actions = AssessmentHistoryActions(self)
        for key in ("undo", "redo"):
            navigation.toolbar_actions[key].triggered.connect(
                self._assessment_menu.actions_by_key[key].trigger
            )
        self.enable_controls()
        self.refresh_navigation()
        self.show_result()

    def select_body_region(self, region: BodyRegion) -> None:
        """Route a colored anatomical click through ordinary tool-tab navigation.

        Args:
            region: Available body region selected by the optional rendering adapter.

        Returns:
            None; preserve current edits/context and reuse accepted-selection camera
            animation. Invalid pending input retains its tool, as for a tab click.
        """
        regions = (
            BodyRegion.LOW_BACK,
            BodyRegion.DISTAL_UPPER_EXTREMITIES,
            BodyRegion.SHOULDERS,
        )
        if region not in regions or self.assessment_tabs is None:
            return
        index = regions.index(region)
        if index == self.assessment_tabs.currentIndex():
            return
        self.begin_tool_focus()
        self.assessment_tabs.setCurrentIndex(index)

    def begin_tool_focus(self) -> None:
        """Capture original mouse selection before the existing source policy runs.

        Args:
            None.

        Returns:
            None.
        """
        renderer: object = self._body_renderer
        if isinstance(renderer, AnimatedBodyRenderer):
            renderer.begin_region_selection()

    def end_tool_focus(self) -> None:
        """Focus the actual resolved source, never an unaccepted clicked tab.

        Args:
            None.

        Returns:
            None.
        """
        renderer: object = self._body_renderer
        if isinstance(renderer, AnimatedBodyRenderer):
            renderer.end_region_selection()

    def set_camera_animation(self, enabled: bool) -> None:
        """Save view policy without committing input; restore the check on failure.

        Args:
            enabled: Whether the associated controls should accept user interaction.

        Returns:
            None.
        """
        renderer: object = self._body_renderer
        menu = self._assessment_menu
        store = self._settings_store
        if (
            menu is None
            or store is None
            or not isinstance(renderer, AnimatedBodyRenderer)
        ):
            return
        try:
            store.save(replace(store.load(), animated_body_region_focus=enabled))
        except Exception:
            _LOG.exception("Camera preference could not be saved")
            menu.camera_animation.blockSignals(True)
            menu.camera_animation.setChecked(not enabled)
            menu.camera_animation.blockSignals(False)
            self.message.setText(self.text("error"))
            return
        renderer.set_animation_enabled(enabled)

    def open_help(self) -> None:
        """Open current localized help without changing assessment input.

        Args:
            None.

        Returns:
            None.
        """
        try:
            if self._user_guides is not None:
                guide = self._user_guides.get(self.language)
                if guide is None:
                    raise OSError("The localized user guide is not configured.")
                open_user_guide(guide, language=self.language)
            elif self._user_guide is not None:
                open_user_guide(self._user_guide)
            else:
                raise OSError("The user guide is not configured.")
        except OSError:
            _LOG.exception("User guide could not be opened")
            spanish = self.language is Language.SPANISH
            QMessageBox.critical(
                self,
                "Ayuda no disponible" if spanish else "Help unavailable",
                "No se pudo abrir el manual de Ergo Tools."
                if spanish
                else "The Ergo Tools user manual could not be opened.",
            )

    def open_project_folder(self) -> None:
        """Delegate the saved project directory to the independent OS file manager.

        Args:
            None.

        Returns:
            None. No draft acceptance, Save, history or project transition occurs.
            No-project and temporary pre-save backing are ignored. A rejected desktop
            launch shows a localized error; the existing project stays open.
        """
        location = self.presenter.workspace.location
        if location is None or self._is_unsaved_project():
            return
        folder = Path(location).absolute().parent
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            spanish = self.language is Language.SPANISH
            QMessageBox.warning(
                self,
                "Carpeta del proyecto" if spanish else "Project folder",
                "No se pudo abrir la carpeta del proyecto en el explorador del sistema."
                if spanish
                else "The project folder could not be opened "
                "in the system file manager.",
            )

    def open_project_properties(self) -> None:
        """Show read-only project details without accepting pending assessment text.

        Args:
            None.

        Returns:
            None.
        """
        if self._is_unsaved_project():
            return
        workspace = self.presenter.workspace
        metadata = workspace.project_metadata
        location = workspace.location
        if metadata is None or location is None:
            return
        dialog = ProjectPropertiesDialog(
            metadata, location, self.language, parent=self, icons=self.icons
        )
        dialog.close_button.setIcon(self.icons["close"])
        try:
            dialog.exec_()
        finally:
            dialog.close()
            dialog.deleteLater()

    def open_authors(self) -> None:
        """Show a fresh owned original Authors form, preserving all pending input.

        Args:
            None.

        Returns:
            None.

        Raises:
            RuntimeError: The authors logo is not configured.
        """
        if self._authors_logo is None:
            raise RuntimeError("The authors logo is not configured.")
        dialog = AuthorsDialog(self.language, self._authors_logo, parent=self)
        try:
            dialog.exec_()
        finally:
            dialog.close()
            dialog.deleteLater()

    def navigation_action(self, action: Callable[[], None]) -> None:
        """Handle pending/dirty/error decisions, then update shared labels.

        Args:
            action: Host or local operation invoked once through the owning error
                boundary.

        Returns:
            None.
        """
        if action == self.save_project and self._is_unsaved_project():
            self.run(self.save_project_as)
            self.refresh_navigation()
            return
        if action in (
            self.open_task_count,
            self.export_summary_csv,
            self.open_plot,
            self.open_rotation,
            self.open_worker_transfer,
            self.open_help,
            self.search_assessment,
            self.open_authors,
            self.new_project,
        ):
            # Like Reset, Set Tasks can clear invalid pending text; Cancel retains it.
            self.run(action)
            self.refresh_navigation()
            return

        def perform() -> None:
            """Invoke accepted navigation once and update shared context labels.

            Invoke accepted navigation once and update shared context labels after it
            completes.

            Args:
                None.

            Returns:
                None.
            """
            before = self.presenter.workspace.active
            action()
            if (
                action != self.refresh_navigation
                and self.presenter.workspace.active is before
            ):
                self.refresh_navigation()

        self.run(perform)

    def refresh_navigation(self) -> None:
        """Read committed context without rebuilding or discarding task-grid text.

        Args:
            None.

        Returns:
            None.
        """
        navigation = self.main_navigation
        if navigation is None:
            return
        workspace = self.presenter.workspace
        active = workspace.active
        catalog = None
        worker_id = None
        workplace = None
        job_label = None
        if workspace.supports_assignment_history:
            self.assessment_navigation.adopt_active()
            catalog = workspace.read_hierarchy().hierarchy.work
            jobs = workspace.read_jobs().jobs
            entry = next(
                (
                    e
                    for e in workspace.read_history().history.entries
                    if active is not None
                    and e.document_id == active.document.document_id
                ),
                None,
            )
            if entry is not None:
                worker_id = entry.worker_id
            if entry is not None and entry.assignment_id is not None:
                assignment = next(
                    a
                    for a in jobs.assignments
                    if a.assignment_id == entry.assignment_id
                )
                worker_id = assignment.worker.worker_id
                workplace = assignment.worker.workplace
                if assignment.placement_id is not None:
                    placement = next(
                        p
                        for p in jobs.placements
                        if p.placement_id == assignment.placement_id
                    )
                    job = next(j for j in jobs.jobs if j.job_id == placement.job_id)
                    job_label = (job.job_id, job.name)
        view = self.assessment_navigation.view
        if (
            active is not None
            and view is not None
            and view.document_id == active.document.document_id
        ):
            worker_id, workplace, job_label = view.worker_id, view.workplace, view.job
        navigation.update_state(
            catalog,
            worker_id,
            workplace,
            job_label,
            workspace.project_metadata.title if workspace.project_metadata else None,
            self.presenter.system,
            self.language,
            project_loaded=not self._is_unsaved_project(),
        )
        metadata = workspace.project_metadata
        has_organization = (
            bool(workspace.read_hierarchy().hierarchy.plants)
            if workspace.supports_assignment_history
            else False
        )
        if workspace.editing is not None and workspace.has_unsaved_changes:
            modified = (
                "  •  Modificado"
                if self.language is Language.SPANISH
                else "  •  Modified"
            )
            navigation.project_label.setText(navigation.project_label.text() + modified)
        navigation.update_context_visibility(
            metadata.project_id if metadata else None, has_organization, self.language
        )
        navigation.associate_button.setVisible(
            view is not None and view.workplace is None and view.saved
        )
        navigation.associate_button.setEnabled(has_organization)
        for panel in (self.task_panel, self.duet_panel, self.tst_panel):
            if panel is not None:
                panel.setEnabled(
                    view is None
                    or view.workplace is None
                    or view.assignment_id is not None
                )
        self._show_context_status()
        navigation.follow_worker_button.setChecked(
            self.assessment_navigation.follow_worker
        )
        navigation.keep_context_button.setChecked(
            not self.assessment_navigation.follow_worker
        )
        can_browse = view is not None
        if active is not None and workspace.supports_assignment_history:
            can_browse = any(
                e.document_id == active.document.document_id
                for e in workspace.read_history().history.entries
            )
        for panel in (self.task_panel, self.duet_panel, self.tst_panel):
            if panel is not None:
                panel.context_button.setEnabled(can_browse)
                panel.clear_button.setEnabled(active is not None)
        navigation.toolbar_actions["save"].setEnabled(
            workspace.project_metadata is not None
            and (
                workspace.editing is not None
                or active is not None
                or self._is_unsaved_project()
            )
            and (
                workspace.editing is not None
                or view is None
                or view.workplace is None
                or view.assignment_id is not None
                or self._is_unsaved_project()
            )
        )
        self.refresh_save_controls()
        navigation.toolbar_actions["settings"].setEnabled(
            self._settings_store is not None
        )
        navigation.tool_label.setText(
            ("Herramienta" if self.language is Language.SPANISH else "Tool")
            + (
                ": ST"
                if self.tst_active
                else ": DUET"
                if self.duet_active
                else ": LiFFT"
            )
        )
        navigation.buttons["transfer"].setEnabled(can_browse)
        navigation.toolbar_actions["jobs"].setEnabled(workspace.supports_job_risk)
        navigation.toolbar_actions["plot"].setEnabled(
            workspace.supports_job_risk and self._plot_opener is not None
        )
        navigation.toolbar_actions["jrot"].setEnabled(
            workspace.supports_rotations and self._rotation_opener is not None
        )
        export_enabled = (
            workspace.supports_assignment_history
            and self._summary_loader is not None
            and self._csv_writer is not None
        )
        navigation.toolbar_actions["export"].setEnabled(export_enabled)
        if self._assessment_menu is not None:
            self._assessment_menu.export_csv.setEnabled(export_enabled)
        navigation.toolbar_actions["organization"].setEnabled(
            navigation.buttons["organization"].isEnabled()
            and not self._is_unsaved_project()
        )
        if self._is_unsaved_project():
            for key in ("jobs", "plot", "jrot", "export"):
                navigation.toolbar_actions[key].setEnabled(False)
            for key in ("workers", "organization", "context", "transfer"):
                navigation.buttons[key].setEnabled(False)
            if self._assessment_menu is not None:
                for action in (
                    self._assessment_menu.export_csv,
                    self._assessment_menu.backup,
                    self._assessment_menu.properties,
                ):
                    action.setEnabled(False)

        if self.history_actions is not None:
            self.history_actions.refresh()

    def search_assessment(self) -> None:
        """Open original cross-worker Search; resolve edits only after acceptance.

        Args:
            None.

        Returns:
            None.
        """
        workspace = self.presenter.workspace
        if not workspace.supports_assignment_history:
            return
        hierarchy = workspace.read_hierarchy().hierarchy
        kind = self.active_kind()
        rows = search_assessments(
            hierarchy,
            workspace.read_jobs().jobs,
            workspace.read_history().history,
            kind,
            year=date.today().year,
        )
        dialog = WorkerSearchDialog(
            rows, hierarchy, kind, self.icons, language=self.language, parent=self
        )
        try:
            if dialog.exec_() != QDialog.Accepted or dialog.selected is None:
                return
            panel = self.secondary_panel() or self.task_panel
            if panel is not None:
                panel.commit_inputs()
                if panel.pending:
                    return
            if not self.resolve_context_text():
                return
            outcome = workspace.select_assignment(
                dialog.selected, choice=self.browse_choice()
            )
            if outcome.completed:
                if self.main_navigation is not None:
                    self.main_navigation.alphabet_buttons["All"].setChecked(True)
                    self.main_navigation.filter_workers("All")
                self.presenter.evaluator.clear()
                self.duet_presenter.evaluator.clear()
                self.tst_presenter.evaluator.clear()
                self.refresh()
        finally:
            dialog.close()
            dialog.deleteLater()

    def select_navigation_context(self) -> None:
        """Open the owned context modal directly for the selected worker.

        Args:
            None.

        Returns:
            None.
        """
        navigation = self.main_navigation
        if navigation is None:
            return
        identity = navigation.workers.currentData()
        self.choose_assessment_context(
            worker_id=identity if isinstance(identity, str) else None
        )

    def navigate_worker(self, worker_id: str) -> None:
        """Activate saved worker data with the existing dirty-source decisions.

        Args:
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.

        Returns:
            None.
        """
        self.navigation_action(lambda: self._select_navigation_worker(worker_id))

    def _initial_assessment_view(self) -> None:
        """Open the first worker with saved data, preferring the visible LiFFT tab.

        Args:
            None.

        Returns:
            None; no modal choice, new assessment or project write is performed.
        """
        browser = self.assessment_navigation
        workers = worker_options(
            self.presenter.workspace.read_hierarchy().hierarchy.work, WorkerOrder.ID
        )
        for kind in (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST):
            for worker in workers:
                if browser.saved_contexts(worker.worker_id, kind):
                    browser.select(
                        worker.worker_id, kind, partial(self._blank_kind, kind)
                    )
                    return
        if workers:
            browser.select(
                workers[0].worker_id,
                AssessmentKind.LIFFT,
                lambda: self._blank_kind(AssessmentKind.LIFFT),
            )

    def _blank_kind(self, kind: AssessmentKind) -> AssessmentDraft:
        """Construct a reference blank grid without creating a database record.

        Args:
            kind: Requested tool; LiFFT/ST drafts use the current display unit system.

        Returns:
            Fresh 15-row typed draft with no copied inputs or calculated results.
        """
        if kind is AssessmentKind.TST:
            return self.blank_tst_source(self.presenter.system)
        if kind is AssessmentKind.DUET:
            return DuetDraft(tuple(DuetTask(uuid4().hex, 0) for _ in range(15)))
        return self.blank_lifft_source(self.presenter.system)

    def _select_navigation_worker(self, worker_id: str) -> None:
        """Navigate all workers, independently of saved tool-data availability.

        Args:
            worker_id: Exact selected worker identity; missing assessments remain
                browsable.

        Returns:
            None; cancellation retains all current tool drafts and the committed worker.
        """
        workspace = self.presenter.workspace
        browser = self.assessment_navigation
        kind = self.active_kind()
        workplace = browser.view.workplace if browser.view is not None else None
        if not workspace.resolve_browse(self.browse_choice()):
            return
        browser.select(
            worker_id,
            kind,
            lambda: self._blank_kind(kind),
            workplace=workplace,
            keep=not browser.follow_worker,
        )
        self.refresh()

    def set_context_mode(self, follow: bool) -> None:
        """Apply Follow worker/Keep context without reinterpreting source ownership.

        Args:
            follow: True restores this worker/tool's remembered or first saved context.

        Returns:
            None; a cancelled transition restores the previous checked mode.
        """
        browser = self.assessment_navigation
        old = browser.follow_worker
        browser.follow_worker = follow
        if follow and browser.view is not None:
            self._select_navigation_worker(browser.view.worker_id)
            if (
                self.presenter.workspace.editing is None
                and self.presenter.workspace.has_unsaved_changes
            ):
                browser.follow_worker = old
        self.refresh_navigation()

    def _browse_context_picker(
        self, worker_id: str | None = None, *, associate: bool = False
    ) -> None:
        """Open/create at the selected context, or associate a saved standalone source.

        Args:
            worker_id: Explicit selected worker, or None to use the navigation view.
            associate: Bind the saved standalone assessment to a chosen real workplace.
                Reuse an existing assignment or create the missing one atomically;
                ordinary opening never changes ownership. Explicit Create assessment
                creates one blank source only for the selected assignment/tool.

        Returns:
            None; cancelled picker/dirty consent preserves the current view and drafts.

        Raises:
            ValueError: Association was requested without a saved standalone source,
                or the chosen destination conflicts with existing assessment ownership.
        """
        workspace = self.presenter.workspace
        browser = self.assessment_navigation
        view = browser.view
        if worker_id is None:
            worker_id = view.worker_id if view is not None else None
        if worker_id is None:
            return
        if associate:
            if view is None or not view.saved or view.workplace is not None:
                raise ValueError("Select a saved standalone assessment first.")
            hierarchy = workspace.read_hierarchy().hierarchy
            jobs = workspace.read_jobs().jobs
            dialog = WorkplaceAssignmentDialog(
                hierarchy,
                jobs,
                worker_id,
                self.icons,
                language=self.language,
                reuse_existing=True,
                parent=self,
            )
            try:
                if (
                    dialog.exec_() != QDialog.Accepted
                    or dialog.selected_workplace is None
                ):
                    return
                if not workspace.resolve_browse(self.browse_choice()):
                    return
                entry = workspace.associate_assessment_at_workplace(
                    view.document_id,
                    dialog.selected_workplace,
                    dialog.selected_placement_id,
                    effective_date=date.today(),
                )
                if self.history_actions is not None:
                    self.history_actions.interactions.observe(None, None, None)
                browser.select(
                    worker_id,
                    self.active_kind(),
                    lambda: self._blank_kind(self.active_kind()),
                    workplace=dialog.selected_workplace,
                    explicit=True,
                    assignment_id=entry.assignment_id,
                )
                self.refresh()
            finally:
                dialog.close()
                dialog.deleteLater()
            return
        selector = AssignmentSelector(workspace)
        catalog = selector.refresh()
        kind = self.active_kind()
        dialog = AssessmentContextDialog(
            selector,
            catalog,
            worker_id,
            kind,
            (),
            self.icons,
            current=view.workplace if view is not None else None,
            shifts=workspace.read_hierarchy().hierarchy.work.shifts,
            saved_assignments=frozenset(
                e.assignment_id
                for e in workspace.read_history().history.entries
                if e.kind is kind and e.assignment_id is not None
            ),
            allow_standalone=not associate,
            language=self.language,
            parent=self,
        )
        try:
            if dialog.exec_() != QDialog.Accepted:
                return
            if dialog.selected_standalone:
                if workspace.resolve_browse(self.browse_choice()):
                    browser.select(
                        worker_id, kind, lambda: self._blank_kind(kind), explicit=True
                    )
                    self.refresh()
                return
            if dialog.selected_assignment is None:
                return
            workplace = dialog.selected_assignment.assignment.worker.workplace
            if (
                view is not None
                and view.worker_id == worker_id
                and view.kind is kind
                and view.assignment_id
                == dialog.selected_assignment.assignment.assignment_id
                and view.workplace == workplace
                and view.saved
            ):
                return
            assignment_id = dialog.selected_assignment.assignment.assignment_id
            exists = any(
                e.assignment_id == assignment_id and e.kind is kind
                for e in workspace.read_history().history.entries
            )
            entry = AssignmentAssessment(uuid4().hex, assignment_id, kind, worker_id)
            if not exists and not self._confirm_context_assessment_creation(entry):
                return
            if not workspace.resolve_browse(self.browse_choice()):
                return
            # Accepted draft staging can create this owner. Recheck before creation;
            # preparing after consent also avoids using an obsolete catalog/session.
            exists = any(
                e.assignment_id == assignment_id and e.kind is kind
                for e in workspace.read_history().history.entries
            )
            if not exists:
                catalog = selector.refresh()
                request = selector.prepare(catalog, worker_id, assignment_id, kind)
                if not selector.create(
                    request, entry.document_id, self._blank_kind(kind)
                ).completed:
                    return
            browser.select(
                worker_id,
                kind,
                lambda: self._blank_kind(kind),
                workplace=workplace,
                explicit=True,
                assignment_id=dialog.selected_assignment.assignment.assignment_id,
            )
            self.refresh()
        finally:
            dialog.close()
            dialog.deleteLater()

    def select_standalone_assessment(self) -> None:
        """View this worker/tool without assigning or moving saved assessment data.

        Args:
            None.

        Returns:
            None. Resolve normal Save/Discard/Cancel before selecting the standalone
            source or an editable first-Save preview. Cancellation retains the view.
        """
        browser = self.assessment_navigation
        view = browser.view
        if view is None or not self.resolve_context_text():
            return
        if not self.presenter.workspace.resolve_browse(self.browse_choice()):
            return
        browser.select(
            view.worker_id,
            view.kind,
            lambda: self._blank_kind(view.kind),
            explicit=True,
        )
        self.refresh()

    def _approve_assessment_save(self) -> bool:
        """Confirm same-Job creation elsewhere; standalone evidence needs no Job.

        Args:
            None.

        Returns:
            True only after every dirty preview's required confirmation; cancellation
            leaves all sources unsaved and no new database record is created.
        """
        for entry in self.presenter.workspace.pending_assessments:
            if not self._confirm_context_assessment_creation(entry):
                return False
            self.presenter.workspace.confirm_assessment_creation(entry.document_id)
        return True

    def _confirm_context_assessment_creation(self, entry: AssignmentAssessment) -> bool:
        """Preserve same-Job consent for explicit creation and first-Save previews.

        Args:
            entry: Proposed exact worker/tool/assignment ownership; standalone sources
                and workplaces without a Job do not need this additional warning.

        Returns:
            True when no same-Job assessment exists elsewhere or consent is Yes.
            No leaves ownership and active assessment unchanged; no writes occur here.
        """
        locations = self.assessment_navigation.duplicate_locations(entry)
        if not locations:
            return True
        jobs = self.presenter.workspace.read_jobs().jobs
        owner = next(
            a for a in jobs.assignments if a.assignment_id == entry.assignment_id
        )
        placement = next(
            p for p in jobs.placements if p.placement_id == owner.placement_id
        )
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[entry.kind]
        listing = "\n".join("- " + " > ".join(context_values(p)) for p in locations)
        spanish = self.language is Language.SPANISH
        question = (
            f"{owner.worker.worker_id} ya tiene una evaluación {tool} "
            f"para el trabajo {placement.job_id} "
            f"en otros lugares:\n\n{listing}\n\n¿Crear otra evaluación aquí?"
            if spanish
            else f"{owner.worker.worker_id} already has a {tool} assessment "
            f"for Job {placement.job_id} "
            f"at other locations:\n\n{listing}\n\n"
            "Create a separate assessment here?"
        )
        return bool(
            QMessageBox.question(
                self,
                "¿Crear otra evaluación?" if spanish else "Create another assessment?",
                question,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def _show_context_status(self) -> None:
        """Display exact navigation state rather than implying missing data is an error.

        Args:
            None.

        Returns:
            None; translate static text while keeping worker/tool identities literal.
        """
        view = self.assessment_navigation.view
        sidebar = self.results_sidebar
        active = self.presenter.workspace.active
        if sidebar is None:
            return
        spanish = self.language is Language.SPANISH
        if view is None:
            if active is None and self.presenter.workspace.project_metadata is not None:
                sidebar.assessment_status_label.setText(
                    "Seleccione trabajador" if spanish else "Select worker"
                )
                sidebar.assessment_status_detail.setText(
                    "Seleccione o cree un trabajador; la organización es opcional."
                    if spanish
                    else "Select or create a worker; organization is optional."
                )
                sidebar.assessment_status_label.setProperty("ready", False)
            return
        if active is None or view.document_id != active.document.document_id:
            return
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[view.kind]
        if view.workplace is None and not view.saved and not active.is_dirty:
            status = "Sin evaluación" if spanish else "No assessment"
            detail = (
                f"No existe una evaluación {tool} para {view.worker_id}."
                if spanish
                else f"No {tool} assessment exists for {view.worker_id}."
            )
        elif view.workplace is not None and view.assignment_id is None:
            status = "Asignación requerida" if spanish else "Assignment required"
            detail = (
                "Asigne el trabajador a este lugar y turno; el trabajo es opcional."
                if spanish
                else "Assign the worker to this workplace and shift; a Job is optional."
            )
        elif not view.saved:
            status = "Nueva evaluación" if spanish else "New assessment"
            detail = (
                "Guardar los datos introducidos creará una evaluación aquí."
                if spanish
                else "Saving entered data will create an assessment here."
            )
        else:
            # Navigation status must not hide a calculator's incomplete/review state.
            if sidebar.assessment_status_label.text() in (
                "Incomplete",
                "Incompleto",
                "Review required",
                "Revisión requerida",
            ):
                return
            status = "Listo" if spanish else "Ready"
            detail = (
                "Datos de evaluación disponibles."
                if spanish
                else "Assessment data is available."
            )
        sidebar.assessment_status_label.setText(status)
        sidebar.assessment_status_detail.setText(detail)
        sidebar.assessment_status_label.setProperty(
            "ready", status in ("Ready", "Listo")
        )
        style = sidebar.assessment_status_label.style()
        assert style is not None
        style.unpolish(sidebar.assessment_status_label)
        style.polish(sidebar.assessment_status_label)

    def blank_lifft_source(self, system: MeasurementSystem) -> LifftDraft:
        """Initialize original default rows only for explicitly created assessments.

        Existing files are never modified merely by opening or rendering them. The owned
        Set Number of Tasks dialog handles explicit row-count changes.

        Args:
            system: Measurement display policy; conversions preserve canonical
                source/body units.

        Returns:
            New 15-row LiFFT draft in the requested source system, with fresh identities
            and blank task inputs.
        """
        tasks = (
            tuple(LifftTask(uuid4().hex) for _ in range(15))
            if self.main_navigation is not None
            else ()
        )
        return LifftDraft(system, tasks)

    @property
    def duet_active(self) -> bool:
        """Identify the active source, independently of an unaccepted tab click.

        Args:
            None.

        Returns:
            True only when the committed active source is DUET, independent of a pending
            tab click.
        """
        return self.active_kind() is AssessmentKind.DUET

    @property
    def tst_active(self) -> bool:
        """Identify committed ST data independently of an unaccepted tab click.

        Args:
            None.

        Returns:
            True only when the committed active source is ST, independent of a pending
            tab click.
        """
        return self.active_kind() is AssessmentKind.TST

    def secondary_panel(self) -> DuetTaskPanel | TstTaskPanel | None:
        """Route shared actions to the actual active non-LiFFT task component.

        Args:
            None.

        Returns:
            Owned DUET/ST task panel for the committed tool, or None for LiFFT/no
            matching secondary component.
        """
        return (
            self.tst_panel
            if self.tst_active
            else self.duet_panel
            if self.duet_active
            else None
        )

    def active_source(self) -> AssessmentDraft | None:
        """Expose committed source without imposing a tool-specific presenter.

        Args:
            None.

        Returns:
            Current committed typed draft, or None when the workspace has no active
            assessment.
        """
        active = self.presenter.workspace.active
        return active.state if active is not None else None

    def active_kind(self) -> AssessmentKind:
        """Use the current model for worker/context selection and new versions.

        Args:
            None.

        Returns:
            Committed tool identity, or the selected empty-state tool when no draft is
            active.
        """
        source = self.active_source()
        return assessment_kind(source) if source is not None else self._empty_kind

    def blank_active_source(self) -> AssessmentDraft:
        """Create reference default rows only on explicit assessment creation.

        Args:
            None.

        Returns:
            New 15-row draft of the active tool with fresh task identities and original
            defaults.
        """
        if self.tst_active:
            return self.blank_tst_source(self.tst_presenter.system)
        if self.duet_active:
            return DuetDraft(tuple(DuetTask(uuid4().hex, 0) for _ in range(15)))
        source = self.active_source()
        return self.blank_lifft_source(
            source.system if isinstance(source, LifftDraft) else self.presenter.system
        )

    def blank_tst_source(self, system: MeasurementSystem) -> TstDraft:
        """Create original ST default rows only after explicit creation consent.

        Args:
            system: Measurement display policy; conversions preserve canonical
                source/body units.

        Returns:
            New 15-row ST draft in the requested source system with Handling Loads and
            fresh task identities.
        """
        return TstDraft(
            system,
            tuple(TstTask(uuid4().hex, TstDirection.HANDLING_LOADS) for _ in range(15)),
        )

    def _sync_tool_tab(self) -> None:
        """Project the actually committed tool into the tab bar under signal blocking.

        Project the actually committed tool into the tab bar under signal blocking,
        including rejected tab selections.

        Args:
            None.

        Returns:
            None.
        """
        tabs = getattr(self, "assessment_tabs", None)
        if tabs is not None:
            tabs.blockSignals(True)
            tabs.setCurrentIndex(2 if self.tst_active else 1 if self.duet_active else 0)
            tabs.blockSignals(False)

    def select_tool(self, index: int) -> None:
        """Switch tools at the selected workplace, retaining unsaved source sessions.

        Unbound projects select an explicit existing document or ask before creating a
        blank one. Integrated browsing preserves the workplace and every tool
        draft without writing or requesting creation consent merely for switching tabs.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        target = (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST)[index]
        browser = self.assessment_navigation
        if (
            self.main_navigation is not None
            and browser.view is not None
            and target is not self.active_kind()
        ):
            panel = self.secondary_panel() or self.task_panel
            if panel is not None:
                try:
                    panel.commit_inputs()
                except DraftError as error:
                    self.message.setText(
                        Translator(self.language).text(error.issue.code)
                    )
                    self._sync_tool_tab()
                    return
                if panel.pending:
                    self._sync_tool_tab()
                    return
            if self.history_actions is not None:
                self.history_actions.refresh()
            view = browser.view
            browser.select(
                view.worker_id,
                target,
                lambda: self._blank_kind(target),
                workplace=view.workplace,
                keep=True,
            )
            self.refresh()
            return
        if target is self.active_kind():
            return
        self._sync_tool_tab()

        def select() -> None:
            """Resolve dirty consent and activate the requested tool.

            Resolve dirty consent and activate the requested tool for the same
            assignment, asking before explicit blank creation when no saved version
            exists.

            Args:
                None.

            Returns:
                None.
            """
            workspace = self.presenter.workspace
            active = workspace.active
            if active is None:
                self._empty_kind = target
                self.refresh()
                return
            history = (
                workspace.read_history().history
                if workspace.supports_assignment_history
                else None
            )
            owner = (
                next(
                    (
                        e
                        for e in history.entries
                        if e.document_id == active.document.document_id
                    ),
                    None,
                )
                if history
                else None
            )
            matching = tuple(
                e for e in workspace.list_assessments() if e.kind is target
            )
            if owner is not None and history is not None:
                bound_ids = {
                    e.document_id
                    for e in history.entries
                    if e.assignment_id == owner.assignment_id and e.kind is target
                }
                matching = tuple(
                    e for e in matching if e.document.document_id in bound_ids
                )
            choice = self.browse_choice()
            if choice is CloseChoice.CANCEL:
                return
            if matching:
                ids = [e.document.document_id for e in matching]
                identity, accepted = (
                    (ids[0], True)
                    if len(ids) == 1
                    else self.choose_item(
                        self.text("assessment_context"), self.text("pick"), ids
                    )
                )
                if not accepted:
                    return
                outcome = workspace.switch(
                    str(workspace.location), identity, choice=choice
                )
            else:
                if (
                    QMessageBox.question(
                        self,
                        self.text("new_assessment"),
                        self.text("context_create_assessment"),
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    != QMessageBox.Yes
                ):
                    return
                source = (
                    self.blank_tst_source(self.presenter.system)
                    if target is AssessmentKind.TST
                    else DuetDraft(tuple(DuetTask(uuid4().hex, 0) for _ in range(15)))
                    if target is AssessmentKind.DUET
                    else self.blank_lifft_source(self.presenter.system)
                )
                identity = uuid4().hex
                if owner is not None:
                    assert history is not None
                    outcome = workspace.create_assignment_assessment(
                        AssignmentAssessment(
                            identity, owner.assignment_id, target, owner.worker_id
                        ),
                        source,
                        choice=choice,
                    )
                else:
                    outcome = workspace.create_assessment(
                        identity, source, choice=choice
                    )
            if outcome.completed:
                self.presenter.evaluator.clear()
                self.duet_presenter.evaluator.clear()
                self.tst_presenter.evaluator.clear()
                self.refresh()

        self.run(select)
