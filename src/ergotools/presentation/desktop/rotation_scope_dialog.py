"""Original one-shift JROT scope tree over immutable saved catalog options.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_scope import RotationScopeOptions
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.language import Language
from ergotools.presentation.desktop.theme.jrot import JROT_STYLE


class RotationScopeDialog(QDialog):
    """Select exact eligible stations in one shift without saving project data.

    A caller owns the immutable catalog read and publishes the returned selection only
    after Accepted. Cancel/Escape leave its previously applied scope intact. Checkbox
    propagation is blocked for one batch; no SQL or global parent lookup occurs inside
    this dialog.
    """

    def __init__(
        self,
        options: RotationScopeOptions,
        icons: Mapping[str, QIcon],
        *,
        selected: tuple[WorkplaceContext, ...] = (),
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build the reviewed 680x560-minimum source tree and action row.

        Args:
            options: Immutable eligible saved selections; no storage access occurs while
                filtering the dialog.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            selected: Initially checked exact workplace contexts.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.options = options
        self.language = language
        self._icons = icons
        self._initial_selected = frozenset(selected)
        self._items: dict[tuple[str, ...], QTreeWidgetItem] = {}
        self._contexts: dict[tuple[str, ...], WorkplaceContext] = {}
        self.setObjectName("jrotScopeDialog")
        self.setWindowTitle(
            self.text("Select Rotation Scope", "Seleccionar ámbito de rotación")
        )
        self.setMinimumSize(680, 560)
        self.setStyleSheet(JROT_STYLE)
        font = QFont("Segoe UI")
        font.setPixelSize(12)
        self.setFont(font)
        layout = QVBoxLayout(self)
        self.heading = QLabel(
            self.text("Select workplace scope", "Seleccionar ámbito laboral")
        )
        self.heading.setObjectName("dialogTitle")
        layout.addWidget(self.heading)
        self.supporting = QLabel(
            self.text(
                "Choose one Shift and one or more Stations whose active Job placements "
                "and Worker assignments may participate in this rotation.",
                "Elija un turno y una o más estaciones cuyas ubicaciones de trabajo "
                "y asignaciones de trabajadores activas puedan participar "
                "en esta rotación.",
            )
        )
        self.supporting.setObjectName("supportingText")
        self.supporting.setWordWrap(True)
        layout.addWidget(self.supporting)
        shift_row = QHBoxLayout()
        self.shift_label = QLabel(self.text("Shift", "Turno"))
        shift_row.addWidget(self.shift_label)
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(list(options.shifts))
        if selected and selected[0].shift_id in options.shifts:
            self.shift_combo.setCurrentText(selected[0].shift_id)
        shift_row.addWidget(self.shift_combo, 1)
        layout.addLayout(shift_row)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            (
                self.text("Workplace hierarchy", "Jerarquía laboral"),
                self.text("Type", "Tipo"),
            )
        )
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(16, 16))
        header = self.tree.header()
        assert header is not None
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tree, 1)
        self.selection_label = QLabel()
        self.selection_label.setObjectName("supportingText")
        layout.addWidget(self.selection_label)
        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        self.use_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        assert self.use_button is not None and self.cancel_button is not None
        self.use_button.setText(self.text("Use scope", "Usar ámbito"))
        self.cancel_button.setText(self.text("Cancel", "Cancelar"))
        self.cancel_button.setIcon(icons["cancel"])
        self.use_button.setIcon(icons["filter_apply"])
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.shift_combo.currentTextChanged.connect(self.populate_tree)
        self.tree.itemChanged.connect(self.item_changed)
        self.populate_tree(self.shift_combo.currentText())

    def text(self, english: str, spanish: str) -> str:
        """Choose display text without changing stored identities or selections.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language == Language.SPANISH else english

    def populate_tree(self, shift_id: str) -> None:
        """Rebuild one shift without recursive signals or retaining deleted items.

        Args:
            shift_id: Exact saved shift whose eligible station nodes are displayed.

        Returns:
            None.
        """
        with QSignalBlocker(self.tree):
            self.tree.clear()
            self._items.clear()
            self._contexts.clear()
            for context in self.options.contexts:
                if context.shift_id != shift_id:
                    continue
                parent = self.tree.invisibleRootItem()
                assert parent is not None
                path: tuple[str, ...] = ()
                values = (
                    context.plant_name,
                    context.section_name,
                    context.line_name,
                    context.station_id,
                )
                for value, kind, caption in zip(
                    values,
                    ("plant", "section", "line", "station"),
                    (
                        self.text("Plant", "Planta"),
                        self.text("Section", "Sección"),
                        self.text("Line", "Línea"),
                        self.text("Station", "Estación"),
                    ),
                    strict=True,
                ):
                    path = (*path, value)
                    item = self._items.get(path)
                    if item is None:
                        item = QTreeWidgetItem(parent, (value, caption))
                        item.setIcon(0, self._icons[kind])
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Unchecked)
                        self._items[path] = item
                    parent = item
                self._contexts[path] = context
                parent.setCheckState(
                    0,
                    Qt.CheckState.Checked
                    if context in self._initial_selected
                    else Qt.CheckState.Unchecked,
                )
            self._update_parents()
            self.tree.expandAll()
        self._update_selection_label()

    def item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Propagate a group click and recompute mixed parents in one signal batch.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            None.
        """
        if column != 0:
            return
        state = item.checkState(0)
        with QSignalBlocker(self.tree):
            stack = [item]
            while stack:
                current = stack.pop()
                current.setCheckState(0, state)
                for index in range(current.childCount()):
                    child = current.child(index)
                    assert child is not None
                    stack.append(child)
            self._update_parents()
        self._update_selection_label()

    def _update_parents(self) -> None:
        """Project checked/mixed group state.

        Project checked/mixed group state from station leaves in bottom-up order within
        the caller's blocked signal batch.

        Args:
            None.

        Returns:
            None.
        """
        for path, item in reversed(tuple(self._items.items())):
            if path in self._contexts:
                continue
            states = set()
            for index in range(item.childCount()):
                child = item.child(index)
                assert child is not None
                states.add(child.checkState(0))
            state = (
                Qt.CheckState.Checked
                if states == {Qt.CheckState.Checked}
                else Qt.CheckState.Unchecked
                if states == {Qt.CheckState.Unchecked}
                else Qt.CheckState.PartiallyChecked
            )
            item.setCheckState(0, state)

    def selected_contexts(self) -> tuple[WorkplaceContext, ...]:
        """Return exact checked station identities in stable candidate order.

        Args:
            None.

        Returns:
            Checked eligible station contexts in stable catalog order, all within the
            displayed shift.
        """
        return tuple(
            context
            for path, context in self._contexts.items()
            if self._items[path].checkState(0) == Qt.CheckState.Checked
        )

    def _update_selection_label(self) -> None:
        """Display the exact checked station count without saving or accepting scope.

        Args:
            None.

        Returns:
            None.
        """
        count = len(self.selected_contexts())
        self.selection_label.setText(
            self.text(
                f"{count} Station{'s' if count != 1 else ''} selected",
                f"{count} {'estaciones' if count != 1 else 'estación'} "
                f"seleccionada{'s' if count != 1 else ''}",
            )
        )

    def accept(self) -> None:
        """Retain the original empty-selection prompt and keep the dialog open.

        Args:
            None.

        Returns:
            None.
        """
        if not self.selected_contexts():
            self.selection_label.setText(
                self.text(
                    "Select at least one Station.", "Seleccione al menos una estación."
                )
            )
            return
        super().accept()
