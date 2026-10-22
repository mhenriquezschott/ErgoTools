"""Original organization controls backed by project-owned hierarchy edits.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Iterator, Mapping

from PyQt5.QtCore import QLocale, QSignalBlocker, QSize, Qt
from PyQt5.QtGui import (
    QCloseEvent,
    QDoubleValidator,
    QIcon,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.organization_management import (
    delete_organization,
    organization_keys,
    save_organization,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.presentation.desktop.optional_date_edit import OptionalDateEdit
from ergotools.presentation.desktop.optional_duration_edit import OptionalDurationEdit
from ergotools.presentation.desktop.optional_time_edit import OptionalTimeEdit
from ergotools.presentation.desktop.organization_text import organization_text
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.theme.organization import ORGANIZATION_STYLE

# Module-scoped diagnostic logger; adapters log technical failures while views retain
# user input.
_LOG = logging.getLogger(__name__)
# Organization parent-to-child level order; independent shifts have no location child.
_NEXT = {
    OrganizationKind.PLANT: OrganizationKind.SECTION,
    OrganizationKind.SECTION: OrganizationKind.LINE,
    OrganizationKind.LINE: OrganizationKind.STATION,
}


# Original required/optional organization form fields and editor kinds by entity level.
ENTITY_FIELDS: dict[str, list[tuple[str, str, str]]] = {
    "Plant": [
        ("name", "Plant name", ("line")),
        (("description"), ("Description"), ("text")),
        (("location"), ("Location"), ("line")),
        (("type"), ("Plant type"), ("line")),
        (("area"), ("Area"), ("number")),
        (("start_time"), ("Start time (24 h, HH:mm)"), ("time")),
        (("end_time"), ("End time (24 h, HH:mm)"), ("time")),
        (("operational_hours"), ("Operational duration (hours/minutes)"), ("duration")),
        (("production_capacity"), ("Production capacity"), ("number")),
        (("opening_date"), ("Opening date"), ("date")),
        (("years_of_operation"), ("Years of operation"), ("number")),
    ],
    ("Section"): [
        (("name"), ("Section name"), ("line")),
        (("description"), ("Description"), ("text")),
        (("location"), ("Location"), ("line")),
        (("capacity"), ("Capacity"), ("number")),
        (("area"), ("Area"), ("number")),
        (("creation_date"), ("Creation date"), ("date")),
    ],
    ("Line"): [
        (("name"), ("Line name"), ("line")),
        (("description"), ("Description"), ("text")),
        (("location"), ("Location"), ("line")),
        (("products"), ("Products"), ("line")),
        (("creation_date"), ("Creation date"), ("date")),
    ],
    ("Station"): [
        (("id"), ("Station ID"), ("line")),
        (("location"), ("Location"), ("line")),
        (("cycle_time"), ("Cycle time (sec)"), ("number")),
        (("capacity"), ("Capacity"), ("number")),
        (("creation_date"), ("Creation date"), ("date")),
    ],
    ("Shift"): [
        (("id"), ("Shift ID"), ("line")),
        (("description"), ("Description"), ("text")),
        (("start_time"), ("Start time (24 h, HH:mm)"), ("time")),
        (("end_time"), ("End time (24 h, HH:mm)"), ("time")),
        (("shift_type"), ("Shift type"), ("line")),
        (("tasks_performed"), ("Tasks performed"), ("text")),
        (("product_output"), ("Product output"), ("number")),
        (("downtime"), ("Downtime (hrs)"), ("number")),
        (("notes"), ("Notes"), ("text")),
    ],
}


class OrganizationDialog(QDialog):
    """Edit location/shift records without SQL or parent-window global lookups."""

    add_child_button: QPushButton
    add_root_button: QPushButton
    breadcrumb: QLabel
    cancel_button: QPushButton
    delete_button: QPushButton
    directory_tabs: QTabWidget
    entity_title: QLabel
    form_container_layout: QVBoxLayout
    form_content: QWidget
    form_scroll: QScrollArea
    location_tree: QTreeWidget
    note: QLabel
    optional_content: QWidget
    optional_form: QFormLayout
    optional_toggle: QToolButton
    required_form: QFormLayout
    save_button: QPushButton
    shift_tree: QTreeWidget

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        initial_entity: OrganizationKind = OrganizationKind.PLANT,
        parent: QWidget | None = None,
    ) -> None:
        """Receive workspace/assets and build the original modal organization form.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            initial_entity: Organization level initially displayed by the management
                dialog.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self._accepting_entity = True
        self._form_baseline: tuple[str, ...] = ()
        self.project_history: ProjectHistoryActions | None = None
        self._workspace = workspace
        self._icons = icons
        self._language = language
        self._snapshot = workspace.read_hierarchy()
        self.current_entity: OrganizationKind | None = None
        self.current_keys: tuple[str, ...] | None = None
        self._parent_keys: tuple[str, ...] = ()
        # Dialog-only identities survive tree replacement/deletion for shared replay.
        self._location_expansion: dict[tuple[str, ...], bool] = {}
        self._view_selection: tuple[OrganizationKind, tuple[str, ...]] | None = None
        self.editors: dict[
            str,
            QLineEdit
            | QTextEdit
            | OptionalTimeEdit
            | OptionalDateEdit
            | OptionalDurationEdit,
        ] = {}
        self.ends_next_day: QCheckBox | None = None
        self.plant_shift_count: QLabel | None = None
        self.new_mode = False
        self._busy = False
        self.setWindowTitle(self._text("Organization Management"))
        self.setObjectName("organizationDialog")
        self.setWindowIcon(icons["plant"])
        self.setMinimumSize(1120, 740)
        self.resize(1180, 780)
        self.setStyleSheet(ORGANIZATION_STYLE)
        if language is Language.SPANISH:
            self.setLocale(QLocale("es_CL"))
        self._setup_ui()
        self._translate_controls()
        self.refresh_all()
        if initial_entity is OrganizationKind.SHIFT:
            self.directory_tabs.setCurrentIndex(1)
        keys = organization_keys(self._snapshot.hierarchy, initial_entity)
        if keys:
            self.select_keys(initial_entity, sorted(keys)[0])
            if initial_entity is not OrganizationKind.SHIFT:
                with QSignalBlocker(self.location_tree):
                    self.location_tree.setCurrentItem(None)
                    self.location_tree.clearSelection()
                    self.location_tree.collapseAll()
        else:
            self.start_new(initial_entity, [])

        self._accepting_entity = False
        if workspace.editing is not None:
            self.save_button.hide()
            self.project_history = ProjectHistoryActions(
                self,
                workspace.editing,
                icons,
                language,
                prepare=self.accept_pending_entity,
                restored=self.restore_project_entities,
                pending=self.pending_entity_action,
            )
            self.title_row.addStretch(1)
            for button in (
                self.project_history.undo_button,
                self.project_history.redo_button,
            ):
                # Mouse replay accepts the form; focused keyboard Undo stays native.
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                self.title_row.addWidget(button)

    def _form_values(self) -> tuple[str, ...]:
        """Read literal form tokens for navigation acceptance without data coercion.

        Args:
            None.

        Returns:
            Required/optional tokens in editor order, followed by Shift day intent
            when present. The day token participates only in draft acceptance; it
            is inferred from valid saved clock order and is never serialized.
        """
        values = tuple(self._editor_value(name) for name in self.editors)
        if self.ends_next_day is not None:
            values += ("next_day" if self.ends_next_day.isChecked() else "",)
        return values

    def pending_entity_action(self) -> str | None:
        """Expose a valid existing-record draft to the shared history controls.

        Args:
            None.

        Returns:
            The existing hierarchy-edit label when the form differs from its baseline;
            None during projection, new-record entry, or incomplete/invalid input.
            This inspection neither accepts the draft nor writes the project.
        """
        if self._accepting_entity or self.new_mode or self.current_keys is None:
            return None
        if self._form_values() == self._form_baseline:
            return None
        if self._shift_time_error() is not None:
            return None
        if any(
            (isinstance(editor, OptionalTimeEdit) and not editor.is_acceptable())
            or (
                isinstance(editor, QLineEdit)
                and editor.text().strip()
                and not editor.hasAcceptableInput()
            )
            for editor in self.editors.values()
        ):
            return None
        return "replace_hierarchy"

    def _refresh_pending_history(self) -> None:
        """Update shared Undo availability after a local editor changes.

        Args:
            None.

        Returns:
            None; acceptance still occurs at replay, navigation or closing, preserving
            native text Undo and the existing per-record project history boundary.
        """
        if self.project_history is not None:
            self.project_history.refresh()

    def _clock_value_changed(self) -> None:
        """Refresh overnight availability and shared pending Undo after clock entry.

        Args:
            None.

        Returns:
            None; absent clocks disable day choice without inventing stored values.
        """
        if self.ends_next_day is not None:
            self.ends_next_day.setEnabled(
                all(
                    isinstance(editor, OptionalTimeEdit)
                    and editor.is_acceptable()
                    and bool(editor.clock_text())
                    for name, editor in self.editors.items()
                    if name in ("start_time", "end_time")
                )
            )
        self._refresh_pending_history()

    def _shift_time_error(self) -> str | None:
        """Validate same-day/overnight intent for one complete Shift clock pair.

        Args:
            None.

        Returns:
            Localized correction guidance, or None for valid/incomplete optional
            pairs. Clock order encodes one daily shift: later end is same-day,
            earlier/equal end is next-day (equal with next-day means 24 hours).
            No additional day flag is serialized or inferred from unknown clocks.
        """
        if (
            self.current_entity is not OrganizationKind.SHIFT
            or self.ends_next_day is None
        ):
            return None
        start = self.editors.get("start_time")
        end = self.editors.get("end_time")
        if not isinstance(start, OptionalTimeEdit) or not isinstance(
            end, OptionalTimeEdit
        ):
            return None
        if not start.is_acceptable() or not end.is_acceptable():
            return None
        first, last = start.clock_text(), end.clock_text()
        if not first or not last:
            return None
        if not self.ends_next_day.isChecked() and last <= first:
            return self._text(
                "End time must be later than start time. "
                "Select Ends the following day for an overnight shift."
            )
        if self.ends_next_day.isChecked() and last > first:
            return self._text(
                "For an overnight shift, end time must be at or before start time. "
                "Otherwise clear Ends the following day."
            )
        return None

    def accept_pending_entity(self) -> bool:
        """Accept one changed organization record into private project state.

        Args:
            None.

        Returns:
            True when valid/unchanged; False retains missing identifiers or invalid
            numeric/time text for correction. No durable Save occurs.
        """
        if self._accepting_entity or self._workspace.editing is None:
            return True
        values = self._form_values()
        if values == self._form_baseline or not any(values):
            return True
        if not values[0]:
            self.note.setText(self._text("Note: An identifier is required."))
            return False
        self._accepting_entity = True
        try:
            self.save_entity()
            return True
        except (ValueError, RuntimeError) as error:
            self.note.setText(self._text(str(error)))
            return False
        except Exception:
            _LOG.exception("Unable to accept organization edits")
            self.note.setText(
                "No se pudieron aceptar los cambios; se conservaron los datos."
                if self._language is Language.SPANISH
                else "Changes could not be accepted; your entries are kept."
            )
            return False
        finally:
            self._accepting_entity = False

    def restore_project_entities(self) -> None:
        """Reload hierarchy controls after shared replay without accepting old fields.

        Args:
            None.

        Returns:
            None; surviving/restored records retain selection and optional details.
            A still-deleted identity leaves an empty form, not an invented record.
        """
        self._accepting_entity = True
        try:
            self._snapshot = self._workspace.read_hierarchy()
            selection = self._view_selection
            self.refresh_all()
            if selection is not None and selection[1] in organization_keys(
                self._snapshot.hierarchy, selection[0]
            ):
                self.select_keys(*selection, preserve_expansion=True)
            elif self.new_mode:
                self.start_new(
                    self.current_entity or OrganizationKind.PLANT,
                    list(self._parent_keys),
                )
            else:
                self._reset_form()
        finally:
            self._accepting_entity = False

    def accept(self) -> None:
        """Keep valid organization edits in the project when closing with Close.

        Args:
            None.

        Returns:
            None; invalid text keeps the dialog open.
        """
        if self.accept_pending_entity():
            super().accept()

    def reject(self) -> None:
        """Retain valid edits on Escape without publishing the project.

        Args:
            None.

        Returns:
            None; explicit Cancel still resets the pending form separately.
        """
        if self.accept_pending_entity():
            super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 — Qt override
        """Validate pending organization edits on native close.

        Args:
            event: Native close request, or None for a defensive direct call.

        Returns:
            None; validation failure leaves form text available.
        """
        if event is None:
            return
        if not self.accept_pending_entity():
            event.ignore()
            return
        super().closeEvent(event)

    def _text(self, source: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            source: English reference UI wording or earlier project path, as stated by
                this operation; user values are retained literally.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        return organization_text(source, self._language)

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
        except (ValueError, KeyError):
            self.note.setText(
                self._text(
                    "Note: Could not save. Check identifiers, numeric values "
                    "and referenced workplaces."
                )
            )
        except Exception:
            _LOG.exception("Organization operation failed")
            self.note.setText(
                self._text("Note: Unable to save changes. Please try again.")
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
        for tree in (self.location_tree, self.shift_tree):
            header = tree.headerItem()
            if header is not None:
                for column in range(tree.columnCount()):
                    header.setText(column, self._text(header.text(column)))
        for index in range(self.directory_tabs.count()):
            self.directory_tabs.setTabText(
                index, self._text(self.directory_tabs.tabText(index))
            )
            self.directory_tabs.setTabToolTip(
                index, self._text(self.directory_tabs.tabToolTip(index))
            )

    def _make_item(
        self, kind: OrganizationKind, keys: tuple[str, ...]
    ) -> QTreeWidgetItem:
        """Build an organization item with typed ancestry.

        Create one organization tree item carrying typed level/path data rather than
        parsing its caption.

        Args:
            kind: Organization hierarchy level whose typed identifier is selected or
                edited.
            keys: Exact ordered saved hierarchy ancestry for the selected organization
                level; display captions are not identifiers.

        Returns:
            Owned tree item carrying typed organization kind and exact saved ancestry.
        """
        item = QTreeWidgetItem([keys[-1], self._text(kind.value)])
        item.setData(0, Qt.ItemDataRole.UserRole, (kind, keys))
        item.setIcon(0, self._icons[kind.value.lower()])
        item.setToolTip(
            0, self._text("Select this item to view or edit its information.")
        )
        return item

    def _location_items(self) -> Iterator[QTreeWidgetItem]:
        """Walk current location items, including descendants of collapsed branches.

        Args:
            None.

        Yields:
            Dialog-owned items in ancestry traversal order. Consumers must finish
            before replacing tree contents; no Qt item is cached across refreshes.
        """
        root = self.location_tree.invisibleRootItem()
        assert root is not None
        stack = [root.child(index) for index in range(root.childCount())]
        while stack:
            item = stack.pop()
            if item is not None:
                yield item
                stack.extend(item.child(index) for index in range(item.childCount()))

    def _remember_location_expansion(self) -> None:
        """Remember exact branch flags before replacing owned tree items.

        Args:
            None.

        Returns:
            None; both expanded and collapsed flags use complete ancestry keys.
            Absent branches remain remembered until dialog close so deleting and
            undoing a subtree restores its prior expansion without storing Qt items
            or adding project history/settings/database state.
        """
        for item in self._location_items():
            _, keys = item.data(0, Qt.ItemDataRole.UserRole)
            self._location_expansion[keys] = item.isExpanded()

    def _restore_location_expansion(self) -> None:
        """Reapply remembered flags after model rebuild or automatic selection reveal.

        Args:
            None.

        Returns:
            None; replay/internal reselection must not let Qt's ancestor auto-expansion
            replace the user's explicitly collapsed branches. New unrelated branches
            start collapsed; deleted identities keep their dialog-local flags.
        """
        with QSignalBlocker(self.location_tree):
            for item in self._location_items():
                _, keys = item.data(0, Qt.ItemDataRole.UserRole)
                item.setExpanded(self._location_expansion.get(keys, False))

    def refresh_all(self) -> None:
        """Rebuild saved directories while retaining each location branch's state.

        Args:
            None.

        Returns:
            None.
        """
        hierarchy = self._snapshot.hierarchy
        self._remember_location_expansion()
        with QSignalBlocker(self.location_tree), QSignalBlocker(self.shift_tree):
            self.location_tree.clear()
            self.shift_tree.clear()
            items: dict[tuple[str, ...], QTreeWidgetItem] = {}
            for kind in (
                OrganizationKind.PLANT,
                OrganizationKind.SECTION,
                OrganizationKind.LINE,
                OrganizationKind.STATION,
            ):
                for keys in sorted(organization_keys(hierarchy, kind)):
                    item = self._make_item(kind, keys)
                    items[keys] = item
                    if len(keys) == 1:
                        self.location_tree.addTopLevelItem(item)
                    else:
                        items[keys[:-1]].addChild(item)
            self._restore_location_expansion()
            for keys in sorted(organization_keys(hierarchy, OrganizationKind.SHIFT)):
                self.shift_tree.addTopLevelItem(
                    self._make_item(OrganizationKind.SHIFT, keys)
                )

    def location_selected(self) -> None:
        """Load one exact tree identity rather than parsing its translated label.

        Args:
            None.

        Returns:
            None.
        """
        item = self.location_tree.currentItem()
        if item is not None:
            kind, keys = item.data(0, Qt.ItemDataRole.UserRole)
            self.load_entity(kind, keys)

    def shift_selected(self) -> None:
        """Load the selected independent shift without changing location ancestry.

        Args:
            None.

        Returns:
            None.
        """
        item = self.shift_tree.currentItem()
        if item is not None:
            kind, keys = item.data(0, Qt.ItemDataRole.UserRole)
            self.load_entity(kind, keys)

    def directory_tab_changed(self, index: int) -> None:
        """Change directory actions without duplicate signal reconnections.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        shift = index == 1
        self.add_root_button.setText(self._text("New shift" if shift else "New plant"))
        self.add_root_button.setIcon(self._icons["shift" if shift else "plant"])
        self.add_child_button.setVisible(not shift)
        (self.shift_selected if shift else self.location_selected)()

    def _new_root(self) -> None:
        """Begin a new plant or independent shift according.

        Begin a new plant or independent shift according to the selected directory tab.

        Args:
            None.

        Returns:
            None.
        """
        self.start_new(
            OrganizationKind.SHIFT
            if self.directory_tabs.currentIndex() == 1
            else OrganizationKind.PLANT,
            [],
        )

    def _clear_form(self) -> None:
        """Remove dynamic required/optional rows and release editor references.

        Remove dynamic required/optional rows and release editor references before
        changing entity scope.

        Args:
            None.

        Returns:
            None.
        """
        while self.required_form.rowCount():
            self.required_form.removeRow(0)
        while self.optional_form.rowCount():
            self.optional_form.removeRow(0)
        self.editors.clear()
        self.ends_next_day = None

    def set_optional_details_visible(self, expanded: bool) -> None:
        """Expand/collapse optional reference fields, preserving their text.

        Args:
            expanded: True reveals optional detail controls; False collapses them
                without clearing values.

        Returns:
            None.
        """
        self.optional_content.setVisible(expanded)
        self.optional_toggle.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )

    def load_entity(self, kind: OrganizationKind, keys: tuple[str, ...]) -> None:
        """Read metadata locally and lock the existing stable identifier.

        Args:
            kind: Organization hierarchy level whose typed identifier is selected or
                edited.
            keys: Exact ordered saved hierarchy ancestry for the selected organization
                level; display captions are not identifiers.

        Returns:
            None.
        """
        record = next(
            (
                r
                for r in self._snapshot.hierarchy.organization
                if r.kind is kind and r.keys == keys
            ),
            OrganizationRecord(kind, keys),
        )
        self._build_form(kind, keys[:-1], record=record)

    def _build_form(
        self,
        kind: OrganizationKind,
        parents: tuple[str, ...],
        *,
        record: OrganizationRecord | None = None,
    ) -> None:
        """Construct required identity and optional metadata editors.

        Construct required identity and optional metadata editors for an exact
        organization level/ancestry; saved identifiers remain locked. Rebuilding does
        not change the optional-details toggle; its dialog-local choice survives
        acceptance, navigation and replay. Saved record identities are remembered
        independently of retiring tree items for deletion/Undo selection recovery.

        Args:
            kind: Organization hierarchy level whose typed identifier is selected or
                edited.
            parents: Complete ordered saved ancestry for the new organization record.
            record: Saved organization details to load; None constructs an empty
                new-record form.

        Returns:
            None.
        """
        if not self.accept_pending_entity():
            return
        self._clear_form()
        self.current_entity = kind
        self.current_keys = record.keys if record else None
        self._parent_keys = parents
        self.new_mode = record is None
        if record is not None:
            self._view_selection = (kind, record.keys)
        self.entity_title.setText(
            self._text(("New " if self.new_mode else "Edit ") + kind.value.lower())
        )
        self.breadcrumb.setText(
            "  >  ".join(record.keys if record else parents)
            or self._text("Top-level record")
        )
        values = dict(record.attributes) if record else {}
        for index, (name, label, editor_type) in enumerate(ENTITY_FIELDS[kind.value]):
            editor: (
                QLineEdit
                | QTextEdit
                | OptionalTimeEdit
                | OptionalDateEdit
                | OptionalDurationEdit
            )
            if editor_type == "time":
                editor = OptionalTimeEdit(self._text("Not set"))
                # Match existing organization fields without restyling native arrows.
                editor.setMinimumHeight(36)
            elif editor_type == "date":
                editor = OptionalDateEdit(self._text("Not set"))
                editor.setMinimumHeight(36)
            elif editor_type == "duration":
                editor = OptionalDurationEdit(self._text("Not set"))
            else:
                editor = QTextEdit() if editor_type == "text" else QLineEdit()
            if isinstance(editor, QTextEdit):
                editor.setMaximumHeight(76)
            elif editor_type == "number":
                editor.setValidator(QDoubleValidator(editor))
            value = (
                (record.keys[-1] if record else "") if index == 0 else values.get(name)
            )
            text = "" if value is None else str(value)
            if isinstance(editor, OptionalDurationEdit):
                editor.set_value(float(text) if text else None)
            elif isinstance(editor, (OptionalTimeEdit, OptionalDateEdit)):
                editor.set_value(text)
            elif isinstance(editor, QTextEdit):
                editor.setPlainText(text)
            else:
                editor.setText(text)
            if index == 0 and not self.new_mode:
                editor.setEnabled(False)
                editor.setToolTip(
                    self._text(
                        "Identifiers cannot be renamed because related records may "
                        "depend on them."
                    )
                )
            else:
                editor.setToolTip(self._text(label) + " · " + self._text(kind.value))
            if editor_type == "time":
                editor.setToolTip(
                    self._text(
                        "24-hour time HH:mm (00:00-23:59). Type or use the arrows. "
                        "Ctrl+A, Delete clears this optional time."
                    )
                )
            if isinstance(editor, OptionalTimeEdit):
                editor.value_changed.connect(self._clock_value_changed)
            elif isinstance(editor, (OptionalDateEdit, OptionalDurationEdit)):
                editor.value_changed.connect(self._refresh_pending_history)
            else:
                editor.textChanged.connect(self._refresh_pending_history)
            target = self.required_form if index == 0 else self.optional_form
            target.addRow(self._text(label), editor)
            self.editors[name] = editor
            if kind is OrganizationKind.SHIFT and name == "end_time":
                self.ends_next_day = QCheckBox(self._text("Ends the following day"))
                self.ends_next_day.setObjectName("shiftEndsNextDay")
                self.ends_next_day.setToolTip(
                    self._text(
                        "Use for an overnight shift ending at or before its start time."
                    )
                )
                start = self.editors["start_time"]
                assert isinstance(start, OptionalTimeEdit)
                assert isinstance(editor, OptionalTimeEdit)
                self.ends_next_day.setChecked(
                    start.is_acceptable()
                    and editor.is_acceptable()
                    and bool(start.clock_text())
                    and bool(editor.clock_text())
                    and editor.clock_text() <= start.clock_text()
                )
                self.ends_next_day.toggled.connect(self._refresh_pending_history)
                self.optional_form.addRow("", self.ends_next_day)
        self.plant_shift_count = None
        if kind is OrganizationKind.PLANT:
            self.plant_shift_count = QLabel(
                str(self._workspace.plant_shift_count(record.keys[0]) if record else 0)
            )
            self.plant_shift_count.setObjectName("calculatedValue")
            self.plant_shift_count.setToolTip(
                self._text(
                    "Distinct shifts used by active Jobs or worker workplace "
                    "assignments in this plant."
                )
            )
            self.optional_form.insertRow(
                3, self._text("Shifts in use"), self.plant_shift_count
            )
        self._clock_value_changed()
        self._form_baseline = self._form_values()
        self._refresh_pending_history()
        self.delete_button.setEnabled(not self.new_mode)
        self.note.setText(
            self._text(
                "Note: Required identifiers must be unique within their "
                "parent location."
            )
        )

    def add_child(self) -> None:
        """Start the next hierarchy level beneath the selected saved parent.

        Args:
            None.

        Returns:
            None.
        """
        if not self.accept_pending_entity():
            return
        item = self.location_tree.currentItem()
        if item is not None:
            kind, keys = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            kind, keys = self.current_entity, self.current_keys
        if kind is None or keys is None:
            self.note.setText(
                self._text(
                    "Note: Select a plant, section, or line before adding a "
                    "child location."
                )
            )
        elif kind not in _NEXT:
            self.note.setText(
                self._text(
                    "Note: Stations are the final level of the location hierarchy."
                )
            )
        else:
            self.start_new(_NEXT[kind], list(keys))

    def start_new(self, entity: str | OrganizationKind, parents: list[str]) -> None:
        """Begin a new record under an explicit complete parent path.

        Args:
            entity: Organization level selected for explicit new-record creation.
            parents: Complete ordered saved ancestry for the new organization record.

        Returns:
            None.
        """
        kind = OrganizationKind(entity)
        expected = {
            OrganizationKind.PLANT: 0,
            OrganizationKind.SECTION: 1,
            OrganizationKind.LINE: 2,
            OrganizationKind.STATION: 3,
            OrganizationKind.SHIFT: 0,
        }[kind]
        if len(parents) != expected:
            self.note.setText(
                self._text(
                    "Note: Select the parent location before creating this record."
                )
            )
            return
        self._build_form(kind, tuple(parents))

    def _editor_value(self, name: str) -> str:
        """Read and trim the named line/multiline editor without mutating it.

        Args:
            name: Control object name used by the application stylesheet.

        Returns:
            Trimmed local editor text; absent fields are programming errors rather than
            invented values.
        """
        editor = self.editors[name]
        if isinstance(editor, OptionalTimeEdit):
            return editor.clock_text()
        if isinstance(editor, OptionalDateEdit):
            return editor.date_text()
        if isinstance(editor, OptionalDurationEdit):
            return editor.duration_text()
        return (
            editor.toPlainText() if isinstance(editor, QTextEdit) else editor.text()
        ).strip()

    def save_entity(self) -> None:
        """Save required identity and optional fields through one hierarchy commit.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: Organization identifiers cannot be renamed, numeric text is
                invalid, a clock is malformed, or the Shift day choice conflicts
                with its complete start/end clock order.
        """
        kind = self.current_entity
        if kind is None:
            return
        error = self._shift_time_error()
        if error is not None:
            raise ValueError(error)
        fields = ENTITY_FIELDS[kind.value]
        identity = self._editor_value(fields[0][0])
        if not identity:
            self.note.setText(self._text("Note: An identifier is required."))
            return
        keys = (*self._parent_keys, identity)
        if self.current_keys is not None and keys != self.current_keys:
            raise ValueError("Organization identifiers cannot be renamed.")
        attributes = []
        for name, _, editor_type in fields[1:]:
            value = self._editor_value(name)
            editor = self.editors[name]
            if (
                editor_type == "time"
                and value
                and isinstance(editor, OptionalTimeEdit)
                and not editor.is_acceptable()
            ):
                raise ValueError(
                    self._text(
                        "Use 24-hour time HH:mm (00:00-23:59), or clear the time."
                    )
                )
            typed: str | float | None = (
                (float(value.replace(",", ".")) if value else None)
                if editor_type in ("number", "duration")
                else (value or None)
            )
            attributes.append((name, typed))
        record = OrganizationRecord(kind, keys, tuple(attributes))
        replacement = save_organization(
            self._snapshot.hierarchy, record, creating=self.new_mode
        )
        self._snapshot = self._workspace.replace_hierarchy(self._snapshot, replacement)
        self._form_baseline = self._form_values()
        self.refresh_all()
        self.select_keys(kind, keys, preserve_expansion=not self.new_mode)
        self.note.setText(
            self._text(
                "Note: Changes accepted. Use the main Save to write the project."
                if self._workspace.editing is not None
                else "Note: Record saved successfully."
            )
        )

    def delete_entity(self) -> None:
        """Confirm subtree deletion, retaining view choices for shared restoration.

        Repository checks all saved references first. The remembered record identity
        and branch flags outlive deleted tree items only within this dialog, allowing
        Undo to reselect the restored record without collapsing the working tree.

        Args:
            None.

        Returns:
            None.
        """
        if self.current_entity is None or self.current_keys is None:
            return
        box = QMessageBox(
            QMessageBox.Question,
            self._text("Delete record"),
            self._text(
                "Delete this record and its child locations? Referenced "
                "workplaces cannot be deleted."
            ),
            QMessageBox.Yes | QMessageBox.No,
            self,
        )
        if self._language is Language.SPANISH:
            yes = box.button(QMessageBox.Yes)
            assert yes is not None
            yes.setText("Sí")
        try:
            if box.exec() != QMessageBox.Yes:
                return
        finally:
            box.deleteLater()
        replacement = delete_organization(
            self._snapshot.hierarchy, self.current_entity, self.current_keys
        )
        self._snapshot = self._workspace.replace_hierarchy(self._snapshot, replacement)
        self.refresh_all()
        self._reset_form()
        self.note.setText(self._text("Note: Deletion completed."))

    def _reset_form(self) -> None:
        """Return to the empty organization selection state and disable deletion.

        Args:
            None.

        Returns:
            None.
        """
        self._clear_form()
        self.current_entity = None
        self.current_keys = None
        self.delete_button.setEnabled(False)
        self.entity_title.setText(self._text("Select an item"))
        self.breadcrumb.setText(
            self._text("Choose a location or shift to view its details.")
        )

    def cancel_edit(self) -> None:
        """Reload saved fields or discard an unfinished new record.

        Args:
            None.

        Returns:
            None.
        """
        self._form_baseline = self._form_values()
        if self.current_entity is not None and self.current_keys is not None:
            self.load_entity(self.current_entity, self.current_keys)
        else:
            self._reset_form()

    def select_keys(
        self,
        kind: OrganizationKind,
        keys: tuple[str, ...],
        *,
        preserve_expansion: bool = False,
    ) -> None:
        """Select by typed identity; translated captions are display-only.

        Args:
            kind: Organization hierarchy level whose typed identifier is selected or
                edited.
            keys: Exact ordered saved hierarchy ancestry for the selected organization
                level; display captions are not identifiers.
            preserve_expansion: True for edit/replay reselection: reverse Qt's automatic
                ancestor reveal after selecting. Explicit navigation/new records keep
                the normal reveal behavior when False.

        Returns:
            None.
        """
        tree = self.shift_tree if kind is OrganizationKind.SHIFT else self.location_tree
        root = tree.invisibleRootItem()
        assert root is not None
        stack = [root.child(i) for i in range(root.childCount())]
        while stack:
            item = stack.pop(0)
            if item is None:
                continue
            if item.data(0, Qt.ItemDataRole.UserRole) == (kind, keys):
                tree.setCurrentItem(item)
                if preserve_expansion:
                    self._restore_location_expansion()
                return
            stack.extend(item.child(i) for i in range(item.childCount()))

    def _setup_ui(self) -> None:
        """Build the original organization form with processed icon dependencies.

        Args:
            None.

        Returns:
            None.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        title = QLabel("Organization Management")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("Manage the workplace hierarchy and independent work shifts.")
        subtitle.setObjectName("dialogSubtitle")
        self.title_row = QHBoxLayout()
        self.title_row.addWidget(title)
        layout.addLayout(self.title_row)
        layout.addWidget(subtitle)
        body = QHBoxLayout()
        body.setSpacing(16)
        directory = QFrame()
        directory.setObjectName("card")
        directory.setFixedWidth(410)
        directory_layout = QVBoxLayout(directory)
        directory_layout.setContentsMargins(15, 15, 15, 15)
        directory_heading = QLabel("Organization")
        directory_heading.setObjectName("sectionTitle")
        directory_layout.addWidget(directory_heading)
        self.directory_tabs = QTabWidget()
        self.directory_tabs.setIconSize(QSize(22, 22))
        self.location_tree = QTreeWidget()
        self.location_tree.setIconSize(QSize(22, 22))
        self.location_tree.setHeaderLabels(["Location hierarchy", "Type"])
        location_header = self.location_tree.header()
        assert location_header is not None
        location_header.setStretchLastSection(False)
        location_header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.location_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.location_tree.setToolTip(
            "Expand the hierarchy and select a plant, section, line, or"
            " station to view its details."
        )
        self.location_tree.itemSelectionChanged.connect(self.location_selected)
        self.shift_tree = QTreeWidget()
        self.shift_tree.setIconSize(QSize(22, 22))
        self.shift_tree.setHeaderLabels(["Shift", "Type"])
        shift_header = self.shift_tree.header()
        assert shift_header is not None
        shift_header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.shift_tree.setToolTip(
            "Select a shift to view or edit its independent schedule information."
        )
        self.shift_tree.itemSelectionChanged.connect(self.shift_selected)
        self.directory_tabs.addTab(
            self.location_tree,
            self._icons["plant.png".removesuffix(".png")],
            ("Locations"),
        )
        self.directory_tabs.addTab(
            self.shift_tree, self._icons["shift.png".removesuffix(".png")], ("Shifts")
        )
        self.directory_tabs.setTabToolTip(
            0, ("Manage the Plant > Section > Line > Station hierarchy.")
        )
        self.directory_tabs.setTabToolTip(
            1, ("Manage shifts, which are independent from the location hierarchy.")
        )
        self.directory_tabs.currentChanged.connect(self.directory_tab_changed)
        directory_layout.addWidget(self.directory_tabs, 1)
        tree_actions = QHBoxLayout()
        self.add_root_button = QPushButton("New plant")
        self.add_root_button.setIcon(self._icons["plant.png".removesuffix(".png")])
        self.add_root_button.setIconSize(QSize(26, 26))
        self.add_root_button.setToolTip(
            "Create a new top-level plant. On the Shifts tab, create a new shift."
        )
        self.add_root_button.clicked.connect(self._new_root)
        self.add_child_button = QPushButton("Add element")
        self.add_child_button.setIcon(self._icons["add_child.png".removesuffix(".png")])
        self.add_child_button.setIconSize(QSize(26, 26))
        self.add_child_button.setToolTip(
            "Add a new element at the next hierarchy level beneath the "
            "selected location."
        )
        self.add_child_button.setObjectName("primaryOutlineButton")
        self.add_child_button.clicked.connect(self.add_child)
        tree_actions.addWidget(self.add_root_button)
        tree_actions.addWidget(self.add_child_button)
        directory_layout.addLayout(tree_actions)
        body.addWidget(directory)
        details = QFrame()
        details.setObjectName("card")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(18, 16, 18, 16)
        header = QHBoxLayout()
        heading_box = QVBoxLayout()
        self.entity_title = QLabel("Select an item")
        self.entity_title.setObjectName("sectionTitle")
        self.breadcrumb = QLabel("Choose a location or shift to view its details.")
        self.breadcrumb.setObjectName("dialogSubtitle")
        self.breadcrumb.setWordWrap(True)
        heading_box.addWidget(self.entity_title)
        heading_box.addWidget(self.breadcrumb)
        header.addLayout(heading_box, 1)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setIcon(self._icons["delete.png".removesuffix(".png")])
        self.delete_button.setIconSize(QSize(26, 26))
        self.delete_button.setToolTip(
            "Delete the selected organization record after confirmation."
        )
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(lambda: self._run(self.delete_entity))
        header.addWidget(self.delete_button)
        details_layout.addLayout(header)
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setFrameShape(QFrame.NoFrame)
        self.form_content = QWidget()
        self.form_content.setObjectName("formContent")
        self.form_container_layout = QVBoxLayout(self.form_content)
        self.form_container_layout.setContentsMargins(0, 12, 8, 0)
        self.form_container_layout.setSpacing(10)
        required_label = QLabel("Required information")
        required_label.setObjectName("eyebrow")
        self.form_container_layout.addWidget(required_label)
        self.required_form = QFormLayout()
        self.required_form.setSpacing(10)
        self.required_form.setLabelAlignment(
            Qt.AlignmentFlag(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        )
        self.form_container_layout.addLayout(self.required_form)
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
            "Show or hide descriptive and operational fields."
        )
        self.optional_toggle.toggled.connect(self.set_optional_details_visible)
        self.form_container_layout.addWidget(self.optional_toggle)
        self.optional_content = QWidget()
        self.optional_content.setObjectName("optionalContent")
        self.optional_form = QFormLayout(self.optional_content)
        self.optional_form.setContentsMargins(0, 2, 0, 0)
        self.optional_form.setSpacing(10)
        self.optional_form.setLabelAlignment(
            Qt.AlignmentFlag(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        )
        self.optional_content.hide()
        self.form_container_layout.addWidget(self.optional_content)
        self.form_container_layout.addStretch()
        self.form_scroll.setWidget(self.form_content)
        details_layout.addWidget(self.form_scroll, 1)
        self.note = QLabel("Note: Select an item to begin.")
        self.note.setObjectName("notificationLabel")
        self.note.setWordWrap(True)
        self.note.setToolTip(
            "Validation, guidance, and save-result messages appear here."
        )
        details_layout.addWidget(self.note)
        body.addWidget(details, 1)
        layout.addLayout(body, 1)
        actions = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setIcon(self._icons["cancel.png".removesuffix(".png")])
        self.cancel_button.setIconSize(QSize(26, 26))
        self.cancel_button.setToolTip(
            "Discard unsaved field changes and reload the selected record."
        )
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.save_button = QPushButton("Save changes")
        self.save_button.setIcon(self._icons["save.png".removesuffix(".png")])
        self.save_button.setIconSize(QSize(26, 26))
        self.save_button.setToolTip(
            "Save the required identifier and any optional organization details."
        )
        self.save_button.setObjectName("primaryOutlineButton")
        self.save_button.clicked.connect(lambda: self._run(self.save_entity))
        close_button = QPushButton("Close")
        close_button.setIcon(self._icons["close.png".removesuffix(".png")])
        close_button.setIconSize(QSize(26, 26))
        close_button.setToolTip(
            "Close Organization Management and return to the assessment."
        )
        close_button.clicked.connect(self.accept)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)
        actions.addWidget(close_button)
        layout.addLayout(actions)
