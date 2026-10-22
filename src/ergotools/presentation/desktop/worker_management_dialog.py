"""Original Worker Management controls over typed project services.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date

from PyQt5.QtCore import (
    QDate,
    QEvent,
    QLocale,
    QObject,
    QRegExp,
    QRegularExpression,
    QSignalBlocker,
    QSize,
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QCloseEvent,
    QDoubleValidator,
    QIcon,
    QRegExpValidator,
    QRegularExpressionValidator,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.job_assignment import assign_worker, change_worker_assignment
from ergotools.application.job_classification import (
    ClassificationRequest,
    classify_assignments,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.worker_details import (
    WorkerDetails,
    display_body_measurement,
    store_body_measurement,
)
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.theme.worker_management import (
    WORKER_MANAGEMENT_STYLE,
)
from ergotools.presentation.desktop.worker_countries import COUNTRIES
from ergotools.presentation.desktop.worker_text import worker_text
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)

# Module-scoped diagnostic logger; adapters log technical failures while views retain
# user input.
_LOG = logging.getLogger(__name__)


class WorkerManagementDialog(QDialog):
    """Own optional form text; persist through workspace commands, never SQL.

    Integrated editing accepts one worker/classification action into the private
    project session. New/navigation/Close retain valid form edits; Cancel discards
    pending text. One main Save publishes the project. Diagnostic workspaces retain
    explicit local commits. Closing never selects or creates an assessment; the main
    context picker owns those explicit actions.
    """

    add_assignment_button: QPushButton
    address_input: QLineEdit
    age_label: QLabel
    assignment_status_label: QLabel
    assignment_table: QTableWidget
    assignments_tab: QWidget
    cancel_button: QPushButton
    city_input: QLineEdit
    close_button: QPushButton
    country_combo: QComboBox
    date_of_hiring_input: QDateEdit
    delete_button: QPushButton
    details_scroll: QScrollArea
    dob_input: QDateEdit
    email_input: QLineEdit
    first_button: QPushButton
    first_name_input: QLineEdit
    first_page_button: QPushButton
    gender_combo: QComboBox
    general_tab: QWidget
    height_input: QLineEdit
    last_button: QPushButton
    last_name_input: QLineEdit
    last_page_button: QPushButton
    new_button: QPushButton
    next_button: QPushButton
    next_page_button: QPushButton
    notification_area: QFrame
    notification_label: QLabel
    optional_details: QWidget
    optional_toggle: QToolButton
    page_label: QLabel
    previous_button: QPushButton
    previous_page_button: QPushButton
    save_button: QPushButton
    search_button: QPushButton
    state_combo: QComboBox
    tabs: QTabWidget
    weight_input: QLineEdit
    worker_count_label: QLabel
    worker_id_combo: QComboBox
    worker_search_input: QLineEdit
    worker_table: QTableWidget
    year_of_birth_input: QSpinBox
    zipcode_input: QLineEdit

    worker_page_size: int

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        system: MeasurementSystem,
        *,
        language: Language = Language.ENGLISH,
        selected_worker: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Load one project snapshot and construct the original visible form.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            selected_worker: Saved worker ID to initially select; None uses the original
                default selection.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self._loaded_worker: WorkerEntry | None = None
        self._accepting_worker = False
        self.project_history: ProjectHistoryActions | None = None
        self._workspace = workspace
        self._icons = icons
        self._system = system
        self._language = language
        self._hierarchy = workspace.read_hierarchy()
        self._jobs = workspace.read_jobs()
        self._filtered: list[WorkerEntry] = []
        self.alphabet_buttons: dict[str, QPushButton] = {}
        self._busy = False
        self._fitting_assignment_columns = False
        self._assignment_viewport: QWidget | None = None
        self._assignment_fit_timer = QTimer(self)
        self._assignment_fit_timer.setSingleShot(True)
        self._assignment_fit_timer.timeout.connect(self._fit_assignment_columns)
        self.setWindowTitle(self._text("Worker Management"))
        self.setWindowIcon(icons["worker_management"])
        self.setMinimumSize(1360, 760)
        self.resize(1400, 800)
        if language is Language.SPANISH:
            self.setLocale(QLocale("es_CL"))
        self._setup_ui()
        viewport = self.worker_table.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)
        self.worker_id_combo.setItemDelegate(QStyledItemDelegate(self.worker_id_combo))
        self.save_button.clicked.disconnect()
        self.delete_button.clicked.disconnect()
        self.add_assignment_button.clicked.disconnect()
        self.save_button.clicked.connect(lambda: self._run(self.save_worker))
        self.delete_button.clicked.connect(lambda: self._run(self.delete_worker))
        self.add_assignment_button.clicked.connect(
            lambda: self._run(self.add_worker_assignment)
        )
        self._translate_controls()
        if language is Language.SPANISH:
            self.alphabet_buttons["All"].setFixedWidth(44)
            directory = self.worker_table.parentWidget()
            assert directory is not None
            directory.setMinimumWidth(565)
        self._reload_workers(selected_worker)
        if workspace.editing is not None:
            self.save_button.setDefault(False)
            self.save_button.hide()
            self.worker_id_combo.editTextChanged.connect(
                lambda text: self.add_assignment_button.setEnabled(bool(text.strip()))
            )
            self.new_button.clicked.disconnect()
            self.new_button.clicked.connect(lambda: self._run(self.add_next_worker))
            self.new_button.setText(self._text("Add worker"))
            self.new_button.setToolTip(
                self._text("Accept this worker and start another.")
            )
            self.project_history = ProjectHistoryActions(
                self,
                workspace.editing,
                icons,
                language,
                prepare=self.accept_pending_worker,
                restored=self.restore_project_workers,
                pending=self.pending_worker_action,
            )
            self.title_row.addStretch(1)
            for button in (
                self.project_history.undo_button,
                self.project_history.redo_button,
            ):
                # Mouse replay completes the form edit; keyboard typing Undo stays
                # with the focused field, as before.
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                self.title_row.addWidget(button)
            for field in (
                self.first_name_input,
                self.last_name_input,
                self.height_input,
                self.weight_input,
                self.address_input,
                self.city_input,
                self.zipcode_input,
                self.email_input,
            ):
                field.textChanged.connect(self.project_history.refresh)
            for combo in (self.gender_combo, self.country_combo, self.state_combo):
                combo.currentIndexChanged.connect(self.project_history.refresh)
                if combo.isEditable():
                    editor = combo.lineEdit()
                    assert editor is not None
                    editor.textChanged.connect(self.project_history.refresh)
            for date_edit in (self.dob_input, self.date_of_hiring_input):
                date_edit.dateChanged.connect(self.project_history.refresh)

    def _text(self, source: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            source: English reference UI wording or earlier project path, as stated by
                this operation; user values are retained literally.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        if self._workspace.editing is not None:
            source = {
                "Enter a Worker ID and save the new worker.": (
                    "Enter a Worker ID; Add worker or Close accepts the record."
                ),
                "Select a Worker before editing workplace assignments.": (
                    "Enter a Worker ID before adding assignments."
                ),
                "Select a Worker before assigning a workplace.": (
                    "Enter a Worker ID before adding assignments."
                ),
                "Permanently delete the selected worker after confirmation.": (
                    "Delete the selected worker after confirmation. "
                    "Undo can restore it."
                ),
                "Unable to save worker changes. Please try again.": (
                    "Changes could not be accepted. Your entries are kept for retry."
                ),
            }.get(source, source)
        return worker_text(source, self._language)

    def _run(self, action: Callable[[], None]) -> None:
        """Invoke one explicit operation and display expected failures.

        Invoke one explicit operation and display expected failures while retaining the
        current form for correction or retry.

        Args:
            action: Host or local operation invoked once through the owning error
                boundary.

        Returns:
            None.
        """
        if self._busy:
            return
        self._busy = True
        try:
            action()
        except ValueError as error:
            message = self._text(str(error))
            if self._language is Language.SPANISH and message == str(error):
                message = "Revise los valores del formulario e inténtelo de nuevo."
            self.set_notification(message, "error")
        except Exception:
            _LOG.exception("Worker Management operation failed")
            self.set_notification(
                self._text("Unable to save worker changes. Please try again."), "error"
            )
        finally:
            self._busy = False

    def _translate_controls(self) -> None:
        """Translate owned captions, tooltips and placeholders.

        Translate owned captions, tooltips and placeholders without rebuilding controls
        or changing saved field values.

        Args:
            None.

        Returns:
            None.
        """
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QLabel, QPushButton, QToolButton)):
                widget.setText(self._text(widget.text()))
            if widget.toolTip():
                widget.setToolTip(self._text(widget.toolTip()))
            if isinstance(widget, QLineEdit):
                widget.setPlaceholderText(self._text(widget.placeholderText()))
        for index in range(self.tabs.count()):
            self.tabs.setTabText(index, self._text(self.tabs.tabText(index)))
        for table in (self.worker_table, self.assignment_table):
            for column in range(table.columnCount()):
                item = table.horizontalHeaderItem(column)
                if item is not None:
                    item.setText(self._text(item.text()))
        self.dob_input.setSpecialValueText(self._text("Not provided"))
        for index, source in enumerate(("Not provided", "Female", "Male")):
            self.gender_combo.setItemText(index, self._text(source))

    def set_notification(self, message: str, severity: str = "info") -> None:
        """Show one scoped notification without changing form values.

        Args:
            message: Literal user-facing notification/error content.
            severity: Notification style identity (info/error/success) consumed by the
                established stylesheet.

        Returns:
            None.
        """
        self.notification_label.setText(
            self._text("Note: {message}").format(message=self._text(message))
        )
        self.notification_area.setProperty("severity", severity)
        style = self.notification_area.style()
        if style is not None:
            style.unpolish(self.notification_area)
            style.polish(self.notification_area)

    @property
    def selected_worker_id(self) -> str | None:
        """Return a saved worker identity rather than an unsaved typed identifier.

        Args:
            None.

        Returns:
            Exact saved worker ID selected in the combo, or None for unsaved/unknown
            text.
        """
        identity = self.worker_id_combo.currentText().strip()
        return (
            identity
            if any(
                w.worker_id == identity for w in self._hierarchy.hierarchy.work.workers
            )
            else None
        )

    def no_action(self) -> None:
        """Retain the reference's hidden search button; directory search is visible.

        Args:
            None.

        Returns:
            None.
        """

    def pending_worker_action(self) -> str | None:
        """Expose a valid existing-worker form edit before its acceptance boundary.

        Args:
            None.

        Returns:
            Stable worker-edit label when details/classification differ from the
            loaded form; None during projection, unchanged/invalid input or new
            worker entry. This inspection never accepts data or writes the file.
        """
        if self._accepting_worker or self._loaded_worker is None:
            return None
        if self.selected_worker_id != self._loaded_worker.worker_id:
            return None
        try:
            changed = self._form_worker() != self._loaded_worker
        except ValueError:
            return None
        return (
            "replace_worker_catalogs"
            if changed or self._classification_changed()
            else None
        )

    def accept_pending_worker(self) -> bool:
        """Accept one valid worker into the project session, preserving failed text.

        Args:
            None.

        Returns:
            True for an unchanged/blank form or a successful accepted worker; False
            when validation fails. No project file is written in integrated mode.
        """
        if self._accepting_worker or self._workspace.editing is None:
            return True
        if (
            not self.worker_id_combo.currentText().strip()
            and self._loaded_worker is None
            and not any(
                field.text().strip()
                for field in (
                    self.first_name_input,
                    self.last_name_input,
                    self.height_input,
                    self.weight_input,
                )
            )
        ):
            return True
        self._accepting_worker = True
        try:
            candidate = self._form_worker()
            if candidate != self._loaded_worker or self._classification_changed():
                self.save_worker()
            return True
        except ValueError as error:
            self.set_notification(self._text(str(error)), "error")
            return False
        except Exception:
            _LOG.exception("Unable to accept worker changes into the project")
            self.set_notification(
                self._text("Unable to save worker changes. Please try again."), "error"
            )
            return False
        finally:
            self._accepting_worker = False

    def _classification_changed(self) -> bool:
        """Detect accepted assignment dropdown changes without persisting them.

        Args:
            None.

        Returns:
            True if any displayed classification differs from its current assignment.
        """
        for row in range(self.assignment_table.rowCount()):
            combo = self.assignment_table.cellWidget(row, 5)
            if isinstance(combo, QComboBox):
                assignment = next(
                    (
                        a
                        for a in self._jobs.jobs.assignments
                        if a.assignment_id == combo.property("assignmentId")
                    ),
                    None,
                )
                if (
                    assignment is not None
                    and combo.currentData() != assignment.placement_id
                ):
                    return True
        return False

    def add_next_worker(self) -> None:
        """Accept the current worker as one Undo step, then prepare a blank form.

        Args:
            None.

        Returns:
            None; invalid data stays visible and does not clear the current form.
        """
        if self.accept_pending_worker():
            self.new_worker()

    def restore_project_workers(self) -> None:
        """Rebind directory and details after shared Undo/Redo without accepting text.

        Args:
            None.

        Returns:
            None; removed selections fall back to an existing worker or a blank form.
        """
        self._accepting_worker = True
        try:
            selected = self.selected_worker_id
            self._loaded_worker = None
            self._hierarchy = self._workspace.read_hierarchy()
            self._jobs = self._workspace.read_jobs()
            self._reload_workers(selected)
        finally:
            self._accepting_worker = False

    def reject(self) -> None:
        """Retain valid worker edits on Escape, without writing the project file.

        Args:
            None.

        Returns:
            None; invalid forms remain open for correction or explicit Cancel.
        """
        if self.accept_pending_worker():
            super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 — Qt override
        """Accept valid worker edits before closing the window.

        Args:
            event: Native close request; None is ignored defensively.

        Returns:
            None; rejected validation leaves the window and typed data available.
        """
        if event is None:
            return
        if not self.accept_pending_worker():
            event.ignore()
            return
        super().closeEvent(event)

    def close_worker(self) -> None:
        """Close through validation, retaining accepted integrated worker edits.

        Args:
            None.

        Returns:
            None.
        """
        self.close()

    def set_optional_details_visible(self, expanded: bool) -> None:
        """Expand the original details section while retaining all entered values.

        Args:
            expanded: True reveals optional detail controls; False collapses them
                without clearing values.

        Returns:
            None.
        """
        self.optional_details.setVisible(expanded)
        self.optional_toggle.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )

    def date_of_birth_changed(self) -> None:
        """Update age from the date widget without creating an edit or SQL query.

        Args:
            None.

        Returns:
            None.
        """
        birthday = self.dob_input.date()
        today = QDate.currentDate()
        if birthday == self.dob_input.minimumDate():
            self.age_label.setText(self._text("Not available"))
        else:
            age = (
                today.year()
                - birthday.year()
                - ((today.month(), today.day()) < (birthday.month(), birthday.day()))
            )
            self.age_label.setText(self._text("{age} years").format(age=max(0, age)))

    def populate_states_for_usa(self) -> None:
        """Keep editable region suggestions separate from stored country identity.

        Args:
            None.

        Returns:
            None.
        """
        with QSignalBlocker(self.state_combo):
            self.state_combo.clear()
            if self.country_combo.currentText() == "United States":
                self.state_combo.addItems(US_STATES)
            else:
                self.state_combo.addItem(self._text("Outside US"))

    def _reload_workers(self, selected: str | None = None) -> None:
        """Rebuild saved worker IDs under signal blocking.

        Rebuild saved worker IDs under signal blocking, retain the requested worker when
        available and refresh the local directory/details.

        Args:
            selected: Saved profile/worker identity to reselect, or None for the local
                default.

        Returns:
            None.
        """
        previous = self._accepting_worker
        self._accepting_worker = True
        try:
            self._rebuild_workers(selected)
        finally:
            self._accepting_worker = previous

    def _rebuild_workers(self, selected: str | None) -> None:
        """Project accepted workers without accepting the form being replaced.

        Args:
            selected: Preferred worker identity, or None for the first worker.

        Returns:
            None; Cancel, deletion, replay and accepted commits use this guarded path.
        """
        workers = sorted(
            self._hierarchy.hierarchy.work.workers, key=lambda w: w.worker_id
        )
        with QSignalBlocker(self.worker_id_combo):
            self.worker_id_combo.clear()
            self.worker_id_combo.addItems([w.worker_id for w in workers])
            index = self.worker_id_combo.findText(selected or "")
            self.worker_id_combo.setCurrentIndex(index if index >= 0 else 0)
        self.filter_worker_table(self.worker_search_input.text())
        if workers:
            self.load_worker_details()
        else:
            self.new_worker()

    def filter_worker_table(self, text: str) -> None:
        """Filter by ID/name and alphabet locally, preserving a visible selection.

        Args:
            text: Literal control text or user input; interpretation follows this
                method's stated policy.

        Returns:
            None.
        """
        query = text.strip().casefold()
        self._filtered = sorted(
            (
                w
                for w in self._hierarchy.hierarchy.work.workers
                if query
                in f"{w.worker_id} {w.last_name or ''}, {w.first_name or ''}".casefold()
                and (
                    self.active_alphabet_letter is None
                    or any(
                        (n or "").upper().startswith(self.active_alphabet_letter)
                        for n in (w.first_name, w.last_name)
                    )
                )
            ),
            key=lambda w: w.worker_id,
        )
        index = next(
            (
                i
                for i, w in enumerate(self._filtered)
                if w.worker_id == self.selected_worker_id
            ),
            0,
        )
        self.worker_page = index // self.worker_page_size
        self._render_page()
        if self._filtered and self.selected_worker_id not in {
            w.worker_id for w in self._filtered
        }:
            self.select_filtered_worker(0)
        count = len(self._filtered)
        self.worker_count_label.setText(
            self._text("{count} workers").format(count=count)
        )

    def set_alphabet_filter(self, letter: str) -> None:
        """Filter name prefixes locally without reloading storage.

        Args:
            letter: Surname initial filter, or the reference All sentinel to remove that
                filter.

        Returns:
            None.
        """
        self.active_alphabet_letter = None if letter == "All" else letter
        for value, button in self.alphabet_buttons.items():
            with QSignalBlocker(button):
                button.setChecked(value == letter)
        self.filter_worker_table(self.worker_search_input.text())

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 — Qt override
        """Refit resized worker/assignment viewports and position the birth calendar.

        Opening an unspecified birth date browses eighteen years before today
        without selecting or persisting a birthday. Existing dates retain Qt's
        normal calendar selection and navigation.

        Args:
            watched: QObject receiving the event; may be None in direct defensive calls.
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            True only when this filter explicitly consumes the event; otherwise the
            normal Qt base-filter result.
        """
        if (
            watched is not None
            and watched is self._assignment_viewport
            and event is not None
            and event.type() in (QEvent.Type.Resize, QEvent.Type.Show)
            and not self._fitting_assignment_columns
        ):
            self._assignment_fit_timer.start(0)
        if (
            watched is self.worker_table.viewport()
            and event is not None
            and event.type() == QEvent.Type.Resize
        ):
            QTimer.singleShot(0, self._resize_page)
        if (
            event is not None
            and event.type() == QEvent.Type.Show
            and watched is self.dob_input.calendarWidget()
            and self.dob_input.date() == self.dob_input.minimumDate()
        ):
            calendar = self.dob_input.calendarWidget()
            assert calendar is not None
            initial_date = QDate.currentDate().addYears(-18)
            calendar.setCurrentPage(initial_date.year(), initial_date.month())
        return super().eventFilter(watched, event)

    def _resize_page(self) -> None:
        """Fit directory page capacity to the actual viewport.

        Fit directory page capacity to the actual viewport while keeping the selected
        saved worker on its page.

        Args:
            None.

        Returns:
            None.
        """
        viewport = self.worker_table.viewport()
        assert viewport is not None
        capacity = max(1, viewport.height() // 38)
        if capacity != self.worker_page_size:
            self.worker_page_size = capacity
            index = next(
                (
                    i
                    for i, w in enumerate(self._filtered)
                    if w.worker_id == self.selected_worker_id
                ),
                0,
            )
            self.worker_page = index // capacity
            self._render_page()

    def _render_page(self) -> None:
        """Render one bounded worker-directory page from the local filtered snapshot.

        Render one bounded worker-directory page from the local filtered snapshot with
        blocked selection signals.

        Args:
            None.

        Returns:
            None.
        """
        page_count = max(
            1,
            (len(self._filtered) + self.worker_page_size - 1) // self.worker_page_size,
        )
        self.worker_page = min(self.worker_page, page_count - 1)
        rows = self._filtered[
            self.worker_page * self.worker_page_size : (self.worker_page + 1)
            * self.worker_page_size
        ]
        with QSignalBlocker(self.worker_table):
            self.worker_table.setRowCount(len(rows))
            for row, worker in enumerate(rows):
                details = worker.details or WorkerDetails()
                age = ""
                if details.birth_date:
                    birthday = date.fromisoformat(details.birth_date)
                    today = date.today()
                    age = str(
                        today.year
                        - birthday.year
                        - ((today.month, today.day) < (birthday.month, birthday.day))
                    )
                values = (
                    worker.worker_id,
                    ", ".join(n for n in (worker.last_name, worker.first_name) if n),
                    self._text(details.sex or ""),
                    age,
                )
                for column, value in enumerate(values):
                    self.worker_table.setItem(row, column, QTableWidgetItem(value))
                self.worker_table.setRowHeight(row, 38)
                if worker.worker_id == self.selected_worker_id:
                    self.worker_table.selectRow(row)
        self.page_label.setText(
            self._text("Page {page} of {total}").format(
                page=self.worker_page + 1, total=page_count
            )
        )
        for button, enabled in (
            (self.first_page_button, self.worker_page > 0),
            (self.previous_page_button, self.worker_page > 0),
            (self.next_page_button, self.worker_page < page_count - 1),
            (self.last_page_button, self.worker_page < page_count - 1),
        ):
            button.setEnabled(enabled)

    def worker_table_selection_changed(self) -> None:
        """Load a clicked worker once; blocked rendering prevents signal recursion.

        Args:
            None.

        Returns:
            None.
        """
        item = self.worker_table.item(self.worker_table.currentRow(), 0)
        if item is not None:
            self.worker_id_combo.setCurrentIndex(
                self.worker_id_combo.findText(item.text())
            )

    def select_filtered_worker(self, index: int) -> None:
        """Select one bounded worker in the filtered directory.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        if self._filtered:
            worker = self._filtered[min(max(0, index), len(self._filtered) - 1)]
            self.worker_id_combo.setCurrentIndex(
                self.worker_id_combo.findText(worker.worker_id)
            )
            self.worker_page = self._filtered.index(worker) // self.worker_page_size
            self._render_page()

    def _move_worker(self, offset: int) -> None:
        """Move a bounded offset through the filtered saved worker sequence.

        Args:
            offset: Signed number of positions to move in the filtered worker sequence.

        Returns:
            None.
        """
        index = next(
            (
                i
                for i, w in enumerate(self._filtered)
                if w.worker_id == self.selected_worker_id
            ),
            0,
        )
        self.select_filtered_worker(index + offset)

    def first_worker(self) -> None:
        """Select the first filtered worker.

        Args:
            None.

        Returns:
            None.
        """
        self.select_filtered_worker(0)

    def previous_worker(self) -> None:
        """Select the preceding filtered worker.

        Args:
            None.

        Returns:
            None.
        """
        self._move_worker(-1)

    def next_worker(self) -> None:
        """Select the next filtered worker.

        Args:
            None.

        Returns:
            None.
        """
        self._move_worker(1)

    def last_worker(self) -> None:
        """Select the last filtered worker.

        Args:
            None.

        Returns:
            None.
        """
        self.select_filtered_worker(len(self._filtered) - 1)

    def _show_page(self, page: int) -> None:
        """Select the first worker on a requested zero-based directory page.

        Args:
            page: Zero-based requested worker-directory page.

        Returns:
            None.
        """
        self.select_filtered_worker(page * self.worker_page_size)

    def first_worker_page(self) -> None:
        """Show the first directory page.

        Args:
            None.

        Returns:
            None.
        """
        self._show_page(0)

    def previous_worker_page(self) -> None:
        """Show the preceding directory page.

        Args:
            None.

        Returns:
            None.
        """
        self._show_page(max(0, self.worker_page - 1))

    def next_worker_page(self) -> None:
        """Show the following directory page.

        Args:
            None.

        Returns:
            None.
        """
        self._show_page(self.worker_page + 1)

    def last_worker_page(self) -> None:
        """Show the final directory page.

        Args:
            None.

        Returns:
            None.
        """
        self.select_filtered_worker(len(self._filtered) - 1)

    def load_worker_details(self) -> None:
        """Load names/details locally; saved body units never depend on UI labels.

        Args:
            None.

        Returns:
            None.
        """
        target = self.selected_worker_id
        if (
            self._workspace.editing is not None
            and not self._accepting_worker
            and self._loaded_worker is not None
            and target != self._loaded_worker.worker_id
        ):
            original_id = self._loaded_worker.worker_id
            with QSignalBlocker(self.worker_id_combo):
                self.worker_id_combo.setEditText(original_id)
            if not self.accept_pending_worker():
                return
            with QSignalBlocker(self.worker_id_combo):
                self.worker_id_combo.setCurrentIndex(
                    self.worker_id_combo.findText(target or "")
                )
        worker = next(
            (
                w
                for w in self._hierarchy.hierarchy.work.workers
                if w.worker_id == target
            ),
            None,
        )
        if worker is None:
            return
        details = worker.details or WorkerDetails()
        self.first_name_input.setText(worker.first_name or "")
        self.last_name_input.setText(worker.last_name or "")
        self.dob_input.setDate(
            QDate.fromString(details.birth_date, "yyyy-MM-dd")
            if details.birth_date
            else self.dob_input.minimumDate()
        )
        self.date_of_birth_changed()
        self.gender_combo.setCurrentIndex((None, "Female", "Male").index(details.sex))
        for field, value, mass in (
            (self.height_input, details.height_cm, False),
            (self.weight_input, details.weight_kg, True),
        ):
            projected = display_body_measurement(value, self._system, mass=mass)
            field.setText("" if projected is None else format(projected, ".15g"))
        for field, text_value in (
            (self.address_input, details.address),
            (self.city_input, details.city),
            (self.zipcode_input, details.postal_code),
            (self.email_input, details.email),
        ):
            field.setText(text_value or "")
        self.country_combo.setCurrentText(details.country or "")
        self.populate_states_for_usa()
        self.state_combo.setCurrentText(details.region or "")
        self.date_of_hiring_input.setDate(
            QDate.fromString(details.hiring_date, "yyyy-MM-dd")
            if details.hiring_date
            else QDate.currentDate()
        )
        self._load_assignments()
        for control in (
            self.worker_table,
            self.worker_search_input,
            self.delete_button,
            self.first_button,
            self.previous_button,
            self.next_button,
            self.last_button,
        ):
            control.setEnabled(True)
        for button in (
            self.first_button,
            self.previous_button,
            self.next_button,
            self.last_button,
        ):
            button.setEnabled(True)
        self._loaded_worker = self._form_worker()
        self.set_notification("Worker record loaded and ready to edit.")
        self._render_page()

    def new_worker(self) -> None:
        """Start a blank record with the original optional-details defaults.

        Args:
            None.

        Returns:
            None.
        """
        self._loaded_worker = None
        with QSignalBlocker(self.worker_id_combo):
            self.worker_id_combo.setCurrentIndex(-1)
            self.worker_id_combo.setEditText("")
        for field in (
            self.first_name_input,
            self.last_name_input,
            self.height_input,
            self.weight_input,
            self.address_input,
            self.city_input,
            self.zipcode_input,
            self.email_input,
        ):
            field.clear()
        self.dob_input.setDate(self.dob_input.minimumDate())
        self.date_of_birth_changed()
        self.gender_combo.setCurrentIndex(0)
        self.country_combo.setCurrentIndex(-1)
        self.state_combo.setCurrentIndex(-1)
        self.date_of_hiring_input.setDate(QDate.currentDate())
        self.assignment_table.setRowCount(0)
        self._fit_assignment_columns()
        self.assignment_status_label.setText(
            self._text("Select a Worker before editing workplace assignments.")
        )
        if self.project_history is not None:
            self.project_history.refresh()
        for control in (
            self.worker_table,
            self.worker_search_input,
            self.delete_button,
        ):
            control.setEnabled(False)
        for button in (
            self.first_button,
            self.previous_button,
            self.next_button,
            self.last_button,
        ):
            button.setEnabled(False)
        self.set_notification("Enter a Worker ID and save the new worker.")
        self.worker_id_combo.setFocus()

    def cancel_worker(self) -> None:
        """Discard visible edits and restore the first saved worker, as originally.

        Args:
            None.

        Returns:
            None.
        """
        self._reload_workers()

    def _form_worker(self) -> WorkerEntry:
        """Validate local worker fields and construct canonical cm/kg details.

        Validate local worker fields and construct canonical cm/kg details without
        writing; unchanged display strings retain exact saved body values.

        Args:
            None.

        Returns:
            Validated worker entry with optional canonical centimeter/kilogram details;
            storage is unchanged until the host command.

        Raises:
            ValueError: Worker ID is required. Worker ID cannot contain spaces.
        """
        identity = self.worker_id_combo.currentText().strip()
        if not identity:
            raise ValueError("Worker ID is required.")
        if any(c.isspace() for c in identity):
            raise ValueError("Worker ID cannot contain spaces.")
        prior = next(
            (
                w
                for w in self._hierarchy.hierarchy.work.workers
                if w.worker_id == identity
            ),
            None,
        )
        existing = prior.details if prior and prior.details else WorkerDetails()

        # Keep unedited canonical values exactly; display rounding must not drift.
        def body(field: QLineEdit, old: float | None, mass: bool) -> float | None:
            """Parse one optional body measurement.

            Parse one optional body measurement, preserving its canonical saved value
            when display text is unchanged; convert changed values from the selected
            cm/kg or in/lb display.

            Args:
                field: Typed input field identity to commit, or the line editor being
                    inspected.
                old: Previously saved canonical body measurement; None denotes an absent
                    value.
                mass: True interprets body weight in kg/lb; False interprets body height
                    in cm/in.

            Returns:
                Canonical optional cm/kg measurement, preserving old precision for
                unchanged display text; None for a cleared optional field.
            """
            projected = display_body_measurement(old, self._system, mass=mass)
            if field.text() == ("" if projected is None else format(projected, ".15g")):
                return old
            return store_body_measurement(
                float(field.text().replace(",", ".")) if field.text().strip() else None,
                self._system,
                mass=mass,
            )

        details = WorkerDetails(
            birth_date=None
            if self.dob_input.date() == self.dob_input.minimumDate()
            else self.dob_input.date().toString("yyyy-MM-dd"),
            sex=(None, "Female", "Male")[self.gender_combo.currentIndex()],
            height_cm=body(self.height_input, existing.height_cm, False),
            weight_kg=body(self.weight_input, existing.weight_kg, True),
            hiring_date=self.date_of_hiring_input.date().toString("yyyy-MM-dd"),
            address=self.address_input.text().strip() or None,
            city=self.city_input.text().strip() or None,
            region=self.state_combo.currentText().strip() or None,
            country=self.country_combo.currentText().strip() or None,
            postal_code=self.zipcode_input.text().strip() or None,
            email=self.email_input.text().strip() or None,
        )
        return WorkerEntry(
            identity,
            self.first_name_input.text().strip() or None,
            self.last_name_input.text().strip() or None,
            details,
        )

    def save_worker(self) -> None:
        """Commit details and all visible classification changes atomically.

        Args:
            None.

        Returns:
            None.
        """
        worker = self._form_worker()
        hierarchy = self._hierarchy.hierarchy
        found = any(w.worker_id == worker.worker_id for w in hierarchy.work.workers)
        workers = (
            tuple(
                worker if w.worker_id == worker.worker_id else w
                for w in hierarchy.work.workers
            )
            if found
            else (*hierarchy.work.workers, worker)
        )
        jobs = self._jobs.jobs
        requests = []
        next_id = max((a.assignment_id for a in jobs.assignments), default=0) + 1
        for row in range(self.assignment_table.rowCount()):
            combo = self.assignment_table.cellWidget(row, 5)
            if (
                isinstance(combo, QComboBox)
                and combo.property("workerId") == worker.worker_id
            ):
                requests.append(
                    ClassificationRequest(
                        combo.property("assignmentId"), combo.currentData(), next_id
                    )
                )
                next_id += 1
        changed = classify_assignments(
            jobs, worker.worker_id, tuple(requests), effective_date=date.today()
        )
        replacement = replace(hierarchy, work=replace(hierarchy.work, workers=workers))
        self._hierarchy, self._jobs = self._workspace.save_worker_catalogs(
            self._hierarchy, replacement, self._jobs, changed
        )
        self._reload_workers(worker.worker_id)
        self.set_notification(
            "Worker changes accepted. Use the main Save to write the project."
            if self._workspace.editing is not None
            else "Worker changes saved."
        )

    def delete_worker(self) -> None:
        """Delete an unreferenced worker; preserve saved assignment/history owners.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: Workers with saved assignments cannot be deleted.
        """
        identity = self.selected_worker_id
        if identity is None:
            return
        if any(a.worker.worker_id == identity for a in self._jobs.jobs.assignments):
            raise ValueError("Workers with saved assignments cannot be deleted.")
        box = QMessageBox(
            QMessageBox.Question,
            self._text("Confirm Deletion"),
            self._text("Are you sure you want to delete this worker?"),
            QMessageBox.Yes | QMessageBox.No,
            self,
        )
        if self._language is Language.SPANISH:
            yes = box.button(QMessageBox.Yes)
            no = box.button(QMessageBox.No)
            assert yes is not None and no is not None
            yes.setText("Sí")
            no.setText("No")
        try:
            if box.exec() != QMessageBox.Yes:
                return
        finally:
            box.deleteLater()
        hierarchy = self._hierarchy.hierarchy
        replacement = replace(
            hierarchy,
            work=replace(
                hierarchy.work,
                workers=tuple(
                    w for w in hierarchy.work.workers if w.worker_id != identity
                ),
            ),
        )
        self._hierarchy, self._jobs = self._workspace.save_worker_catalogs(
            self._hierarchy, replacement, self._jobs, self._jobs.jobs
        )
        self._reload_workers()
        self.set_notification("Worker deleted.")

    def _load_assignments(self) -> None:
        """Rebuild this worker's saved assignment rows and exact job choices.

        Rebuild this worker's saved assignment rows and exact job choices, connecting
        classification notifications once after initial values are set.

        Args:
            None.

        Returns:
            None.
        """
        worker = self.selected_worker_id
        rows = [
            a
            for a in self._jobs.jobs.assignments
            if a.active and a.worker.worker_id == worker
        ]
        self.assignment_table.setRowCount(len(rows))
        for row, assignment in enumerate(rows):
            p = assignment.worker.workplace
            for column, value in enumerate(
                (p.plant_name, p.section_name, p.line_name, p.station_id, p.shift_id)
            ):
                item = QTableWidgetItem(value)
                heading = self.assignment_table.horizontalHeaderItem(column)
                assert heading is not None
                item.setToolTip(f"{heading.text()}: {value}")
                self.assignment_table.setItem(row, column, item)
            combo = QComboBox()
            combo.setItemDelegate(QStyledItemDelegate(combo))
            combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            combo.addItem(self._text("No Job"), None)
            for placement in self._jobs.jobs.placements:
                job = next(
                    j for j in self._jobs.jobs.jobs if j.job_id == placement.job_id
                )
                if placement.active and job.active and placement.workplace == p:
                    combo.addItem(f"{job.job_id} | {job.name}", placement.placement_id)
            if combo.findData(assignment.placement_id) < 0:
                combo.addItem(
                    self._text("Placement unavailable"), assignment.placement_id
                )
            for index in range(combo.count()):
                combo.setItemData(
                    index, combo.itemText(index), Qt.ItemDataRole.ToolTipRole
                )
            combo.setCurrentIndex(max(0, combo.findData(assignment.placement_id)))
            combo.setProperty("assignmentId", assignment.assignment_id)
            combo.setProperty("workerId", worker)
            combo.currentIndexChanged.connect(self._assignment_status)
            self.assignment_table.setCellWidget(row, 5, combo)
            actions = QWidget()
            actions.setToolTip(
                self._text("Change or remove this workplace assignment.")
            )
            buttons = QHBoxLayout(actions)
            buttons.setContentsMargins(2, 2, 2, 2)
            buttons.setSpacing(4)
            for remove, icon, caption in (
                (False, "job_management", "Change assignment"),
                (True, "delete", "Remove assignment"),
            ):
                button = QPushButton(actions)
                button.setObjectName("assignmentAction")
                button.setStyleSheet(
                    "QPushButton#assignmentAction {padding: 0; min-height: 0;}"
                )
                button.setIcon(self._icons[icon])
                button.setIconSize(QSize(24, 24))
                button.setFixedSize(34, 34)
                button.setToolTip(self._text(caption))
                button.setAccessibleName(self._text(caption))
                identity = assignment.assignment_id
                button.clicked.connect(
                    lambda _checked=False, identity=identity, delete=remove: self._run(
                        lambda: self.edit_worker_assignment(identity, remove=delete)
                    )
                )
                buttons.addWidget(button)
            self.assignment_table.setCellWidget(row, 6, actions)

        self._fit_assignment_columns()
        self.add_assignment_button.setEnabled(worker is not None)
        self._assignment_status()

    def _assignment_cell_insets(self, row: int, column: int) -> QSize:
        """Measure native padding reserved around an embedded assignment control.

        Args:
            row: Existing assignment row, regardless of its current scroll position.
            column: Job or Actions column containing a QWidget editor.

        Returns:
            Horizontal/vertical logical pixels outside the delegate's content area.
            Native style geometry includes cell padding; the grid line is separate.
        """
        table = self.assignment_table
        cell = QStyleOptionViewItem()
        cell.initFrom(table)
        cell.widget = table
        # This matches the native delegate's full padded editor geometry.
        cell.showDecorationSelected = True
        model, style = table.model(), table.style()
        assert model is not None and style is not None
        cell.rect = table.visualRect(model.index(row, column))
        contents = style.subElementRect(
            QStyle.SubElement.SE_ItemViewItemText, cell, table
        )
        return QSize(
            cell.rect.width() - contents.width(),
            cell.rect.height() - contents.height(),
        )

    def _fit_assignment_columns(self) -> None:
        """Fit complete values/controls, then give spare viewport width to Job.

        Args:
            None.

        Returns:
            None. Every column retains its intrinsic header/content minimum. Job
            absorbs positive spare width and its selectors fill the padded cells;
            overflow retains those minima and uses conditional scrollbars. Actions
            reserve their complete layout, padding and grid in both dimensions.
            Resize/rebuild/clear affects presentation only, never project history.
        """
        if self._fitting_assignment_columns:
            return
        self._assignment_fit_timer.stop()
        self._fitting_assignment_columns = True
        table = self.assignment_table
        updates_enabled = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            # Drop the previous viewport's filled width before measuring intrinsic
            # options again; a narrower window must not retain an old wide column.
            for row in range(table.rowCount()):
                combo = table.cellWidget(row, 5)
                assert isinstance(combo, QComboBox)
                combo.setMinimumWidth(0)
            table.resizeColumnsToContents()
            widths = [table.columnWidth(column) for column in range(7)]
            widths[5] = max(160, widths[5])
            job_insets: list[int] = []
            for row in range(table.rowCount()):
                combo, actions = table.cellWidget(row, 5), table.cellWidget(row, 6)
                assert isinstance(combo, QComboBox) and actions is not None
                combo.ensurePolished()
                option = QStyleOptionComboBox()
                combo.initStyleOption(option)
                option.rect.setWidth(combo.sizeHint().width())
                style = combo.style()
                assert style is not None
                field = style.subControlRect(
                    QStyle.ComplexControl.CC_ComboBox,
                    option,
                    QStyle.SubControl.SC_ComboBoxEditField,
                    combo,
                )
                text_width = max(
                    combo.fontMetrics().horizontalAdvance(combo.itemText(index))
                    for index in range(combo.count())
                )
                margin = style.pixelMetric(
                    QStyle.PixelMetric.PM_FocusFrameHMargin, option, combo
                )
                selector_width = max(
                    combo.sizeHint().width(),
                    option.rect.width() - field.width() + text_width + 2 * margin,
                )
                job_padding = self._assignment_cell_insets(row, 5)
                job_insets.append(job_padding.width())
                widths[5] = max(widths[5], selector_width + job_padding.width() + 1)
                actions.ensurePolished()
                actions_size = actions.sizeHint().expandedTo(actions.minimumSizeHint())
                actions.setMinimumSize(actions_size)
                action_padding = self._assignment_cell_insets(row, 6)
                widths[6] = max(
                    widths[6], actions_size.width() + action_padding.width() + 1
                )
                table.setRowHeight(
                    row,
                    max(
                        46,
                        combo.sizeHint().height() + job_padding.height() + 1,
                        actions_size.height() + action_padding.height() + 1,
                    ),
                )
            viewport = table.viewport()
            assert viewport is not None
            widths[5] += max(0, viewport.width() - sum(widths))
            for column, width in enumerate(widths):
                table.setColumnWidth(column, width)
            for row, padding in enumerate(job_insets):
                combo = table.cellWidget(row, 5)
                assert isinstance(combo, QComboBox)
                # The declared minimum also avoids Qt's smaller cached first-show
                # editor hint and makes all selectors fill the same Job column.
                combo.setMinimumWidth(widths[5] - padding - 1)
        finally:
            table.setUpdatesEnabled(updates_enabled)
            self._fitting_assignment_columns = False

    def edit_worker_assignment(
        self, assignment_id: int, *, remove: bool = False
    ) -> None:
        """Change an exact assignment through the placement picker or confirm removal.

        Actions commit immediately, like Add assignment; unsaved worker details stay
        intact. Pending dropdown classifications must be saved first to avoid losing
        them when the assignment grid refreshes. Removal preserves historical owners.

        Args:
            assignment_id: Identity captured by the row action, not a mutable row index.
            remove: True asks confirmation to end; False opens eligible placements.

        Returns:
            None; cancellation does not write and failures retain the current form.

        Raises:
            ValueError: Pending classifications need saving, worker/assignment is
                invalid, or destination eligibility/history protections reject change.
            RuntimeError: The workspace cannot commit the proposed catalog.
        """
        previous = next(
            (
                a
                for a in self._jobs.jobs.assignments
                if a.assignment_id == assignment_id
            ),
            None,
        )
        if not self.accept_pending_worker():
            return
        if previous is not None and self._workspace.editing is not None:
            assignment_id = next(
                (
                    a.assignment_id
                    for a in self._jobs.jobs.assignments
                    if a.active and a.worker == previous.worker
                ),
                assignment_id,
            )
        worker_id = self.selected_worker_id
        if worker_id is None:
            raise ValueError("Select a Worker before assigning a workplace.")
        catalog = self._jobs.jobs
        for row in range(self.assignment_table.rowCount()):
            combo = self.assignment_table.cellWidget(row, 5)
            if isinstance(combo, QComboBox):
                saved = next(
                    a
                    for a in catalog.assignments
                    if a.assignment_id == combo.property("assignmentId")
                )
                if saved.placement_id != combo.currentData():
                    raise ValueError(
                        "Save dropdown changes before changing "
                        "or removing an assignment."
                    )
        placement_id = None
        workplace = None
        if remove:
            box = QMessageBox(
                QMessageBox.Question,
                self._text("Remove assignment"),
                self._text(
                    "Remove this active assignment? Existing assessments will be kept."
                ),
                QMessageBox.Yes | QMessageBox.No,
                self,
            )
            box.setStyleSheet(WORKER_MANAGEMENT_STYLE)
            box.setIconPixmap(self._icons["delete"].pixmap(32, 32))
            yes_button, no_button = (
                box.button(QMessageBox.Yes),
                box.button(QMessageBox.No),
            )
            assert yes_button is not None and no_button is not None
            yes_button.setIcon(self._icons["delete"])
            no_button.setIcon(self._icons["cancel"])
            box.setDefaultButton(QMessageBox.No)
            if self._language is Language.SPANISH:
                yes, no = box.button(QMessageBox.Yes), box.button(QMessageBox.No)
                assert yes is not None and no is not None
                yes.setText("Sí")
                no.setText("No")
            try:
                if box.exec() != QMessageBox.Yes:
                    return
            finally:
                box.deleteLater()
        else:
            placements = tuple(
                p
                for p in catalog.placements
                if p.active
                and next(j.active for j in catalog.jobs if j.job_id == p.job_id)
            )
            dialog = WorkplaceAssignmentDialog(
                self._hierarchy.hierarchy,
                catalog,
                worker_id,
                self._icons,
                language=self._language,
                current=previous.worker.workplace if previous is not None else None,
                placement_id=previous.placement_id if previous is not None else None,
                parent=self,
            )
            dialog.setWindowTitle(self._text("Change assignment"))
            dialog.heading.setText(self._text("Change assignment"))
            dialog.accept_button.setText(self._text("Change assignment"))
            try:
                if dialog.exec() != QDialog.Accepted:
                    return
                placement_id = dialog.selected_placement_id
                placement = next(
                    (p for p in placements if p.placement_id == placement_id), None
                )
                workplace = (
                    placement.workplace
                    if placement is not None
                    else dialog.selected_workplace
                )
                if workplace is None:
                    return
            finally:
                dialog.close()
                dialog.deleteLater()
        change = change_worker_assignment(
            catalog,
            worker_id,
            assignment_id,
            placement_id,
            workplace=workplace,
            effective_date=date.today(),
            new_assignment_id=max(
                (a.assignment_id for a in catalog.assignments), default=0
            )
            + 1,
        )
        if change.jobs is catalog:
            return
        self._jobs = self._workspace.replace_jobs(self._jobs, change.jobs)
        self._load_assignments()
        self.set_notification(
            "Assignment removed; existing assessments kept."
            if remove
            else "Workplace assignment changed; existing assessments kept."
        )

    def _assignment_status(self) -> None:
        """Summarize valid workplaces and optional Jobs without a completeness warning.

        Count locally selected Job choices separately from valid workplace assignments;
        changing the caption never saves or alters an assignment.

        Args:
            None.

        Returns:
            None.
        """
        total = self.assignment_table.rowCount()
        count = sum(
            isinstance(c := self.assignment_table.cellWidget(row, 5), QComboBox)
            and c.currentData() is not None
            for row in range(total)
        )
        for row in range(total):
            combo = self.assignment_table.cellWidget(row, 5)
            assert isinstance(combo, QComboBox)
            combo.setToolTip(
                f"{self._text('Job (optional)')}: {combo.currentText()}\n"
                + self._text(
                    "A Job is optional. Only Jobs available at this workplace "
                    "and shift are shown."
                )
            )
        self.assignment_status_label.setText(
            self._text(
                "{total} workplace assignment · {count} with a Job"
                if total == 1
                else "{total} workplace assignments · {count} with a Job"
            ).format(count=count, total=total)
        )

    def add_worker_assignment(self) -> None:
        """Commit a selected workplace/shift with an optional Job and return its intent.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: Select a Worker before assigning a workplace.
        """
        if not self.accept_pending_worker():
            return
        worker_id = self.selected_worker_id
        if worker_id is None:
            raise ValueError("Select a Worker before assigning a workplace.")
        placements = tuple(
            p
            for p in self._jobs.jobs.placements
            if p.active
            and next(j.active for j in self._jobs.jobs.jobs if j.job_id == p.job_id)
        )
        dialog = WorkplaceAssignmentDialog(
            self._hierarchy.hierarchy,
            self._jobs.jobs,
            worker_id,
            self._icons,
            language=self._language,
            parent=self,
        )
        try:
            if dialog.exec() != QDialog.Accepted:
                return
            placement = next(
                (
                    p
                    for p in placements
                    if p.placement_id == dialog.selected_placement_id
                ),
                None,
            )
            workplace = (
                placement.workplace
                if placement is not None
                else dialog.selected_workplace
            )
            if workplace is None:
                return
            worker = self._hierarchy.hierarchy.work.worker_context(worker_id, workplace)
            change = assign_worker(
                self._jobs.jobs,
                worker,
                placement.placement_id if placement is not None else None,
                effective_date=date.today(),
                new_assignment_id=max(
                    (a.assignment_id for a in self._jobs.jobs.assignments), default=0
                )
                + 1,
            )
            self._jobs = self._workspace.replace_jobs(self._jobs, change.jobs)
            self._load_assignments()
            self.set_notification(
                "Workplace assigned. Assessments are unchanged; select an assessment"
                " context in the main window to open or create one."
            )
        finally:
            dialog.close()
            dialog.deleteLater()

    def _setup_ui(self) -> None:
        """Build the reviewed original worker controls with injected services/assets.

        Args:
            None.

        Returns:
            None.
        """
        self.setObjectName("workerManagementDialog")
        self.setStyleSheet(WORKER_MANAGEMENT_STYLE)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(16)
        title = QLabel("Worker Management")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Find a worker or create a new record. Worker ID is "
            "required; all other details are optional."
        )
        subtitle.setObjectName("dialogSubtitle")
        self.title_row = QHBoxLayout()
        self.title_row.addWidget(title)
        main_layout.addLayout(self.title_row)
        main_layout.addWidget(subtitle)
        workspace = QHBoxLayout()
        workspace.setSpacing(16)
        directory_card = QFrame()
        directory_card.setObjectName("card")
        directory_card.setMinimumWidth(535)
        directory_card.setMaximumWidth(575)
        directory_layout = QVBoxLayout(directory_card)
        directory_layout.setContentsMargins(16, 16, 16, 14)
        directory_layout.setSpacing(12)
        directory_heading = QLabel("Workers")
        directory_heading.setObjectName("sectionTitle")
        directory_layout.addWidget(directory_heading)
        self.worker_search_input = QLineEdit()
        self.worker_search_input.setPlaceholderText("Search by ID or name")
        self.worker_search_input.setClearButtonEnabled(True)
        self.worker_search_input.setToolTip(
            "Filter the worker list by Worker ID, first name, or last name."
        )
        self.worker_search_input.textChanged.connect(self.filter_worker_table)
        directory_layout.addWidget(self.worker_search_input)
        self.worker_table = QTableWidget(0, 4)
        self.worker_table.setHorizontalHeaderLabels(["Worker ID", "Name", "Sex", "Age"])
        self.worker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.worker_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.worker_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.worker_table.setAlternatingRowColors(True)
        vertical = self.worker_table.verticalHeader()
        assert vertical is not None
        vertical.setVisible(False)
        self.worker_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        header = self.worker_table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.worker_table.setToolTip(
            "Select a row to view or edit that worker's details."
        )
        self.worker_table.itemSelectionChanged.connect(
            self.worker_table_selection_changed
        )

        self.worker_page = 0
        self.worker_page_size = 10
        directory_layout.addWidget(self.worker_table, 1)
        alphabet_layout = QHBoxLayout()
        alphabet_layout.setSpacing(0)
        alphabet_label = QLabel("Name")
        alphabet_label.setObjectName("alphabetLabel")
        alphabet_label.setToolTip(
            "Filter workers by the first letter of their first or last name."
        )
        alphabet_layout.addWidget(alphabet_label)

        self.active_alphabet_letter = None
        for letter in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(letter)
            button.setObjectName("alphabetButton")
            button.setCheckable(True)
            button.setFixedSize(32 if letter == "All" else 17, 32)
            button.setToolTip(
                "Show all workers."
                if letter == "All"
                else f"Show workers whose first or last name begins with {letter}."
            )
            button.clicked.connect(
                lambda checked, value=letter: self.set_alphabet_filter(value)
            )
            self.alphabet_buttons[letter] = button
            alphabet_layout.addWidget(button)
        self.alphabet_buttons["All"].setChecked(True)
        directory_layout.addLayout(alphabet_layout)
        list_footer = QHBoxLayout()
        self.worker_count_label = QLabel("0 workers")
        self.worker_count_label.setObjectName("supportingText")
        list_footer.addWidget(self.worker_count_label)
        list_footer.addStretch()
        record_navigation_label = QLabel("Worker")
        record_navigation_label.setObjectName("recordNavigationLabel")
        record_navigation_label.setToolTip(
            "The arrow buttons move one worker at a time."
        )
        list_footer.addWidget(record_navigation_label)
        self.first_button = QPushButton("|<")
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.last_button = QPushButton(">|")
        for button, icon_name, tooltip, callback in (
            (
                self.first_button,
                "first.png",
                "Go to the first worker.",
                self.first_worker,
            ),
            (
                self.previous_button,
                "previous.png",
                "Go to the previous worker.",
                self.previous_worker,
            ),
            (self.next_button, "next.png", "Go to the next worker.", self.next_worker),
            (self.last_button, "last.png", "Go to the last worker.", self.last_worker),
        ):
            button.setObjectName("navButton")
            button.setFixedWidth(42)
            button.setText("")
            button.setIcon(self._icons[icon_name.removesuffix(".png")])
            button.setIconSize(QSize(24, 24))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            list_footer.addWidget(button)
        directory_layout.addLayout(list_footer)
        page_footer = QHBoxLayout()
        self.first_page_button = QPushButton("First")
        self.first_page_button.setObjectName("pageButton")
        self.first_page_button.setToolTip("Show the first page of workers.")
        self.first_page_button.clicked.connect(self.first_worker_page)
        self.previous_page_button = QPushButton("Prev")
        self.previous_page_button.setObjectName("pageButton")
        self.previous_page_button.setToolTip("Show the previous page of workers.")
        self.previous_page_button.clicked.connect(self.previous_worker_page)
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setObjectName("pageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setToolTip(
            "Current worker-list page and total number of pages."
        )
        self.next_page_button = QPushButton("Next")
        self.next_page_button.setObjectName("pageButton")
        self.next_page_button.setToolTip("Show the next page of workers.")
        self.next_page_button.clicked.connect(self.next_worker_page)
        self.last_page_button = QPushButton("Last")
        self.last_page_button.setObjectName("pageButton")
        self.last_page_button.setToolTip("Show the last page of workers.")
        self.last_page_button.clicked.connect(self.last_worker_page)
        for button, icon_name in (
            (self.first_page_button, "first.png"),
            (self.previous_page_button, "previous.png"),
            (self.next_page_button, "next.png"),
            (self.last_page_button, "last.png"),
        ):
            button.setIcon(self._icons[icon_name.removesuffix(".png")])
            button.setIconSize(QSize(18, 18))
        page_footer.addWidget(self.first_page_button)
        page_footer.addWidget(self.previous_page_button)
        page_footer.addWidget(self.page_label, 1)
        page_footer.addWidget(self.next_page_button)
        page_footer.addWidget(self.last_page_button)
        directory_layout.addLayout(page_footer)
        workspace.addWidget(directory_card)
        details_card = QFrame()
        details_card.setObjectName("card")
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(18, 16, 18, 16)
        details_layout.setSpacing(10)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("detailsTabs")

        self.general_tab = QWidget()
        self._setup_general_tab()
        self.tabs.addTab(self.general_tab, "Worker details")
        self.assignments_tab = QWidget()
        self._setup_assignments_tab()
        self.tabs.addTab(self.assignments_tab, "Workplace assignments")
        details_layout.addWidget(self.tabs, 1)
        self.notification_area = QFrame()
        self.notification_area.setObjectName("notificationArea")
        self.notification_area.setProperty("severity", "info")
        notification_layout = QHBoxLayout(self.notification_area)
        notification_layout.setContentsMargins(12, 9, 12, 9)
        self.notification_label = QLabel()
        self.notification_label.setObjectName("notificationLabel")
        self.notification_label.setWordWrap(True)
        notification_layout.addWidget(self.notification_label)
        details_layout.addWidget(self.notification_area)
        self.set_notification(
            "Select a worker to review or edit its information.", "info"
        )
        workspace.addWidget(details_card, 1)
        main_layout.addLayout(workspace, 1)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)
        self.new_button = QPushButton("New worker")
        self.save_button = QPushButton("Save changes")
        self.delete_button = QPushButton("Delete")
        self.search_button = QPushButton("Search")
        self.cancel_button = QPushButton("Cancel")
        self.close_button = QPushButton("Close")
        self.new_button.setIcon(self._icons["new.png".removesuffix(".png")])
        self.save_button.setIcon(self._icons["save.png".removesuffix(".png")])
        self.new_button.setIconSize(QSize(26, 26))
        self.save_button.setIconSize(QSize(26, 26))
        self.delete_button.setIcon(self._icons["delete.png".removesuffix(".png")])
        self.delete_button.setIconSize(QSize(26, 26))
        self.search_button.setIcon(self._icons["search.png".removesuffix(".png")])
        self.search_button.setIconSize(QSize(26, 26))
        self.cancel_button.setIcon(self._icons["cancel.png".removesuffix(".png")])
        self.cancel_button.setIconSize(QSize(26, 26))
        self.close_button.setIcon(self._icons["close.png".removesuffix(".png")])
        self.close_button.setIconSize(QSize(26, 26))
        self.save_button.setObjectName("primaryOutlineButton")
        self.delete_button.setObjectName("dangerButton")
        self.search_button.hide()
        actions = (
            (
                self.new_button,
                "Start a blank worker record. Unsaved edits in the form are cleared.",
                self.new_worker,
            ),
            (
                self.save_button,
                "Save this worker and all entered optional details to the project.",
                self.save_worker,
            ),
            (
                self.delete_button,
                "Permanently delete the selected worker after confirmation.",
                self.delete_worker,
            ),
            (
                self.search_button,
                "Open the legacy worker search dialog.",
                self.no_action,
            ),
            (
                self.cancel_button,
                "Discard the current new-record form and return to the first worker.",
                self.cancel_worker,
            ),
            (
                self.close_button,
                "Close Worker Management and return to the assessment window.",
                self.close_worker,
            ),
        )
        for button, tooltip, callback in actions:
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
        action_bar.addWidget(self.new_button)
        action_bar.addWidget(self.save_button)
        action_bar.addWidget(self.delete_button)
        action_bar.addStretch()
        action_bar.addWidget(self.cancel_button)
        action_bar.addWidget(self.close_button)
        main_layout.addLayout(action_bar)

    def _setup_general_tab(self) -> None:
        """Build the reviewed original worker controls with injected services/assets.

        Args:
            None.

        Returns:
            None.
        """
        tab_layout = QVBoxLayout(self.general_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        self.details_scroll = QScrollArea()
        self.details_scroll.setObjectName("detailsScroll")
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QFrame.NoFrame)
        self.details_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        details_content = QWidget()
        details_content.setObjectName("detailsContent")
        page_layout = QVBoxLayout(details_content)
        page_layout.setContentsMargins(0, 0, 8, 0)
        page_layout.setSpacing(12)
        heading = QLabel("Worker details")
        heading.setObjectName("sectionTitle")
        page_layout.addWidget(heading)
        required_note = QLabel("Required information")
        required_note.setObjectName("eyebrow")
        page_layout.addWidget(required_note)
        required_grid = QGridLayout()
        required_grid.setHorizontalSpacing(14)
        required_grid.setVerticalSpacing(10)
        required_grid.setColumnStretch(1, 1)
        required_grid.setColumnStretch(3, 1)
        self.worker_id_combo = QComboBox()
        self.worker_id_combo.setEditable(True)
        self.worker_id_combo.currentIndexChanged.connect(self.load_worker_details)

        self.worker_id_combo.setToolTip(
            "Required. Enter a unique Worker ID without spaces."
        )
        self.first_name_input = QLineEdit()
        self.first_name_input.setToolTip("Optional worker first name.")
        self.last_name_input = QLineEdit()
        self.last_name_input.setToolTip("Optional worker last name.")
        self.year_of_birth_input = QSpinBox()
        self.year_of_birth_input.setRange(1900, QDate.currentDate().year())
        self.year_of_birth_input.setValue(QDate.currentDate().year())
        self.year_of_birth_input.setToolTip(
            "Worker's year of birth. Age is calculated automatically."
        )

        self.year_of_birth_input.hide()
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("dd MMM yyyy")
        self.dob_input.setMinimumDate(QDate(1899, 12, 31))
        self.dob_input.setMaximumDate(QDate.currentDate())
        self.dob_input.setSpecialValueText("Not provided")
        self.dob_input.setDate(self.dob_input.minimumDate())
        birth_calendar = self.dob_input.calendarWidget()
        assert birth_calendar is not None
        birth_calendar.installEventFilter(self)
        self.dob_input.setToolTip(
            "Optional complete date of birth. Age is calculated "
            "automatically when provided."
        )
        self.dob_input.dateChanged.connect(self.date_of_birth_changed)
        self.age_label = QLabel("Not available")
        self.age_label.setObjectName("calculatedValue")
        self.age_label.setToolTip(
            "Calculated automatically when a date of birth is provided."
        )
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Not provided", "Female", "Male"])
        self.gender_combo.setToolTip(
            "Optional worker sex used for filtering and the PLOT marker shape."
        )
        required_fields = ((0, 0, "Worker ID", self.worker_id_combo),)
        for row, column, label_text, field in required_fields:
            label = QLabel(label_text)
            label.setProperty("fieldLabel", True)
            required_grid.addWidget(label, row, column)
            required_grid.addWidget(field, row, column + 1)
        page_layout.addLayout(required_grid)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("divider")
        page_layout.addWidget(divider)
        self.optional_toggle = QToolButton()
        self.optional_toggle.setObjectName("optionalToggle")
        self.optional_toggle.setText("Optional details")
        self.optional_toggle.setCheckable(True)
        self.optional_toggle.setChecked(False)
        self.optional_toggle.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.optional_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.optional_toggle.setToolTip(
            "Show or hide optional identity, employment, and body measurement fields."
        )
        self.optional_toggle.toggled.connect(self.set_optional_details_visible)
        page_layout.addWidget(self.optional_toggle)
        self.optional_details = QWidget()
        optional_grid = QGridLayout(self.optional_details)
        optional_grid.setContentsMargins(0, 4, 0, 0)
        optional_grid.setHorizontalSpacing(14)
        optional_grid.setVerticalSpacing(10)
        optional_grid.setColumnStretch(1, 1)
        optional_grid.setColumnStretch(3, 1)
        self.height_input = QLineEdit()
        self.height_input.setValidator(QDoubleValidator(0.0, 300.0, 2))
        self.height_input.setToolTip(
            "Optional worker height. Values use the project's "
            "configured measurement system."
        )
        self.weight_input = QLineEdit()
        self.weight_input.setValidator(QDoubleValidator(0.0, 500.0, 2))
        self.weight_input.setToolTip(
            "Optional worker weight. Values use the project's "
            "configured measurement system."
        )
        self.address_input = QLineEdit()
        self.address_input.setToolTip("Optional street or workplace address.")
        self.city_input = QLineEdit()
        self.city_input.setToolTip("Optional city.")
        self.state_combo = QComboBox()
        self.state_combo.setEditable(True)
        self.state_combo.addItem("Outside US")
        self.state_combo.setToolTip(
            "Optional state or region. US states are listed when United"
            " States is selected."
        )
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.addItems(COUNTRIES)
        self.country_combo.setCurrentIndex(-1)
        self.country_combo.setToolTip("Optional country.")
        self.country_combo.currentIndexChanged.connect(self.populate_states_for_usa)
        self.zipcode_input = QLineEdit()
        self.zipcode_input.setValidator(
            QRegExpValidator(QRegExp("^[A-Za-z0-9\\- ]{3,10}$"))
        )
        self.zipcode_input.setToolTip("Optional postal or ZIP code.")
        self.email_input = QLineEdit()
        self.email_input.setValidator(
            QRegularExpressionValidator(
                QRegularExpression("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"),
                self.email_input,
            )
        )
        self.email_input.setToolTip("Optional email address.")
        self.state_combo.setCurrentIndex(-1)
        self.date_of_hiring_input = QDateEdit()
        self.date_of_hiring_input.setCalendarPopup(True)
        self.date_of_hiring_input.setDisplayFormat("dd MMM yyyy")
        self.date_of_hiring_input.setDate(QDate.currentDate())
        self.date_of_hiring_input.setMinimumDate(QDate(1950, 1, 1))
        self.date_of_hiring_input.setMaximumDate(QDate.currentDate())
        self.date_of_hiring_input.setToolTip("Optional employment start date.")
        for date_edit in (self.dob_input, self.date_of_hiring_input):
            calendar = date_edit.calendarWidget()
            assert calendar is not None
            previous_button = calendar.findChild(QToolButton, "qt_calendar_prevmonth")
            next_button = calendar.findChild(QToolButton, "qt_calendar_nextmonth")
            if previous_button:
                previous_button.setIcon(
                    self._icons["previous.png".removesuffix(".png")]
                )
                previous_button.setIconSize(QSize(18, 18))
                previous_button.setToolTip("Previous month")
            if next_button:
                next_button.setIcon(self._icons["next.png".removesuffix(".png")])
                next_button.setIconSize(QSize(18, 18))
                next_button.setToolTip("Next month")
        metric_units = self._system is MeasurementSystem.METRIC
        height_label = "Height (cm)" if metric_units else "Height (in)"
        weight_label = "Weight (kg)" if metric_units else "Weight (lb)"
        optional_fields = (
            (0, 0, "First name", self.first_name_input),
            (0, 2, "Last name", self.last_name_input),
            (1, 0, "Sex", self.gender_combo),
            (1, 2, "Date of birth", self.dob_input),
            (2, 0, "Calculated age", self.age_label),
            (2, 2, "Date of hiring", self.date_of_hiring_input),
            (3, 0, height_label, self.height_input),
            (3, 2, weight_label, self.weight_input),
        )
        for row, column, label_text, field in optional_fields:
            label = QLabel(label_text)
            label.setProperty("fieldLabel", True)
            optional_grid.addWidget(label, row, column)
            optional_grid.addWidget(field, row, column + 1)
        self.optional_details.hide()
        page_layout.addWidget(self.optional_details)
        page_layout.addStretch()
        self.details_scroll.setWidget(details_content)
        tab_layout.addWidget(self.details_scroll)

    def _setup_assignments_tab(self) -> None:
        """Build the reviewed original worker controls with injected services/assets.

        Args:
            None.

        Returns:
            None.
        """
        layout = QVBoxLayout(self.assignments_tab)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)
        heading = QLabel("Assigned workplaces")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        self.assignment_status_label = QLabel()
        self.assignment_status_label.setObjectName("supportingText")
        self.assignment_status_label.setWordWrap(True)
        assignment_header = QHBoxLayout()
        assignment_header.addWidget(self.assignment_status_label, 1)
        self.add_assignment_button = QPushButton("Assign workplace…")
        self.add_assignment_button.setIcon(self._icons["station"])
        self.add_assignment_button.setIconSize(QSize(24, 24))
        self.add_assignment_button.setObjectName("primaryOutlineButton")
        self.add_assignment_button.setToolTip(
            "Assign this Worker to a workplace and shift; a Job is optional."
        )
        self.add_assignment_button.clicked.connect(self.add_worker_assignment)
        assignment_header.addWidget(self.add_assignment_button)
        layout.addLayout(assignment_header)
        self.assignment_table = QTableWidget(0, 7)

        self.assignment_table.setHorizontalHeaderLabels(
            [
                "Plant",
                "Section",
                "Line",
                "Station",
                "Shift",
                "Job (optional)",
                "Actions",
            ]
        )
        self.assignment_table.setAlternatingRowColors(True)
        self.assignment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assignment_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.assignment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        vertical = self.assignment_table.verticalHeader()
        assert vertical is not None
        vertical.setVisible(False)
        vertical.setDefaultSectionSize(46)
        header = self.assignment_table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setResizeContentsPrecision(-1)
        header.setStretchLastSection(False)
        # Job widgets need a useful empty width as well as their full option hints.
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.assignment_table.setWordWrap(False)
        self.assignment_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.assignment_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        help_text = (
            "Plant for this workplace assignment.",
            "Section within the selected Plant.",
            "Line within the selected Section.",
            "Station where this worker is assigned.",
            "Shift for this workplace assignment.",
            "Choose an optional Job for each workplace assignment using a "
            "compatible Job Placement.",
            "Change or remove this workplace assignment.",
        )
        for column, description in enumerate(help_text):
            header_item = self.assignment_table.horizontalHeaderItem(column)
            assert header_item is not None
            header_item.setToolTip(self._text(description))
        viewport = self.assignment_table.viewport()
        assert viewport is not None
        self._assignment_viewport = viewport
        viewport.installEventFilter(self)
        layout.addWidget(self.assignment_table, 1)


# Frozen original US region suggestions; never interpreted as stored worker identity.
US_STATES: tuple[str, ...] = (
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
)
