"""Workplace scope selector for JROT."""

from __future__ import annotations

import os
import sqlite3

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from database import connect_database
from rotation_repository import available_scope_contexts


class RotationScopeDialog(QDialog):
    def __init__(self, database_path, selected_context_ids=(), parent=None):
        super().__init__(parent)
        self.database_path = database_path
        self.selected_context_ids = set(selected_context_ids)
        self.setWindowTitle("Select Rotation Scope")
        self.setMinimumSize(680, 560)

        layout = QVBoxLayout(self)
        heading = QLabel("Select workplace scope")
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)
        supporting = QLabel(
            "Choose one Shift and one or more Stations whose active Job placements "
            "and Worker assignments may participate in this rotation."
        )
        supporting.setObjectName("supportingText")
        supporting.setWordWrap(True)
        layout.addWidget(supporting)

        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel("Shift"))
        self.shift_combo = QComboBox()
        shift_row.addWidget(self.shift_combo, 1)
        layout.addLayout(shift_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(("Workplace hierarchy", "Type"))
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, self.tree.header().Stretch)
        self.tree.header().setSectionResizeMode(1, self.tree.header().ResizeToContents)
        layout.addWidget(self.tree, 1)

        self.selection_label = QLabel()
        self.selection_label.setObjectName("supportingText")
        layout.addWidget(self.selection_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Use scope")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._icon_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons")
        )
        self._load_shifts()
        self.shift_combo.currentTextChanged.connect(self._populate_tree)
        self.tree.itemChanged.connect(self._tree_item_changed)
        self._select_initial_shift()

    def _load_shifts(self):
        connection = connect_database(self.database_path, read_only=True)
        try:
            shifts = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT DISTINCT context.shift_id
                    FROM WorkplaceContext AS context
                    JOIN JobPlacement AS placement
                      ON placement.workplace_context_id = context.id
                     AND placement.active = 1
                    ORDER BY context.shift_id COLLATE NOCASE
                    """
                )
            ]
        finally:
            connection.close()
        self.shift_combo.addItems(shifts)

    def _select_initial_shift(self):
        if self.selected_context_ids:
            placeholders = ", ".join("?" for _ in self.selected_context_ids)
            connection = connect_database(self.database_path, read_only=True)
            try:
                row = connection.execute(
                    f"""
                    SELECT shift_id FROM WorkplaceContext
                    WHERE id IN ({placeholders})
                    ORDER BY id LIMIT 1
                    """,
                    tuple(self.selected_context_ids),
                ).fetchone()
            finally:
                connection.close()
            if row:
                self.shift_combo.setCurrentText(row[0])
        self._populate_tree(self.shift_combo.currentText())

    def _populate_tree(self, shift_id):
        self.tree.blockSignals(True)
        self.tree.clear()
        connection = connect_database(self.database_path, read_only=True)
        try:
            contexts = available_scope_contexts(connection, shift_id=shift_id)
        finally:
            connection.close()

        parents = {}
        icon_names = {
            "Plant": "plant.png",
            "Section": "section.png",
            "Line": "line.png",
            "Station": "station.png",
        }
        for context in contexts:
            parent = self.tree.invisibleRootItem()
            path = ()
            for entity_type, value in (
                ("Plant", context["plant_name"]),
                ("Section", context["section_name"]),
                ("Line", context["line_name"]),
                ("Station", context["station_id"]),
            ):
                path += (value,)
                item = parents.get(path)
                if item is None:
                    item = QTreeWidgetItem(parent, (value, entity_type))
                    item.setIcon(0, QIcon(os.path.join(self._icon_root, icon_names[entity_type])))
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.Unchecked)
                    parents[path] = item
                parent = item
            item.setData(0, Qt.UserRole, context["id"])
            item.setCheckState(
                0,
                Qt.Checked if context["id"] in self.selected_context_ids else Qt.Unchecked,
            )
        self.tree.expandAll()
        self.tree.blockSignals(False)
        self._update_selection_label()

    def _tree_item_changed(self, item, column):
        if column != 0:
            return
        self.tree.blockSignals(True)
        self._set_children_checked(item, item.checkState(0))
        self.tree.blockSignals(False)
        self._update_parent_states(item.parent())
        self._update_selection_label()

    def _set_children_checked(self, item, state):
        for index in range(item.childCount()):
            child = item.child(index)
            child.setCheckState(0, state)
            self._set_children_checked(child, state)

    def _update_parent_states(self, item):
        while item is not None:
            states = {item.child(index).checkState(0) for index in range(item.childCount())}
            self.tree.blockSignals(True)
            if states == {Qt.Checked}:
                item.setCheckState(0, Qt.Checked)
            elif states == {Qt.Unchecked}:
                item.setCheckState(0, Qt.Unchecked)
            else:
                item.setCheckState(0, Qt.PartiallyChecked)
            self.tree.blockSignals(False)
            item = item.parent()

    def selected_ids(self):
        selected = []
        iterator = self.tree.invisibleRootItem()
        stack = [iterator.child(index) for index in range(iterator.childCount())]
        while stack:
            item = stack.pop()
            context_id = item.data(0, Qt.UserRole)
            if context_id is not None and item.checkState(0) == Qt.Checked:
                selected.append(int(context_id))
            stack.extend(item.child(index) for index in range(item.childCount()))
        return sorted(selected)

    def _update_selection_label(self):
        count = len(self.selected_ids())
        self.selection_label.setText(f"{count} Station{'s' if count != 1 else ''} selected")

    def accept(self):
        if not self.selected_ids():
            self.selection_label.setText("Select at least one Station.")
            return
        super().accept()
