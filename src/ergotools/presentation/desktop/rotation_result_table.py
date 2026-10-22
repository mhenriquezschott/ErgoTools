"""Original read-only optimized JROT table, using frozen links rather than text.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import QSignalBlocker, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

from ergotools.application.rotation_pool import RotationPool
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.presentation.desktop.rotation_display import (
    measurement_color,
    rotation_text,
    target_labels,
    target_measurement,
)


def render_rotation_result(
    table: QTableWidget,
    scheme: RotationScheme,
    pool: RotationPool,
    kind: AssessmentKind,
    language: Language,
) -> None:
    """Render original 50px rows, 70px worker and 100px block columns.

    Keep the source 700px column budget and one-decimal probability/average text. Values
    use recorded percent values and units. No calculation,
    storage read, editable result or missing-risk default occurs.

    Args:
        table: Owned Qt table to populate or delegate edits for; identity lives in item
            data.
        scheme: Immutable complete saved or proposed rotation scheme with exact evidence
            links.
        pool: Immutable worker/target/current Job values against which grid choices and
            schedules are validated.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        None.
    """
    labels = target_labels(pool.targets, language)
    choices = {choice.target.key: choice for choice in pool.targets}
    blocks = len(scheme.current[0].target_keys)
    with QSignalBlocker(table):
        table.clear()
        table.setRowCount(len(scheme.current))
        table.setColumnCount(blocks + 2)
        table.setHorizontalHeaderLabels(
            [
                rotation_text("Worker", "Trab.", language),
                *(
                    rotation_text(f"Time-Block\n{i + 1}", f"Bloque\n{i + 1}", language)
                    for i in range(blocks)
                ),
                rotation_text("Avg.", "Prom.", language),
            ]
        )
        header = table.horizontalHeader()
        vertical = table.verticalHeader()
        assert header is not None and vertical is not None
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        vertical.setDefaultSectionSize(50)
        table.setColumnWidth(0, 70)
        for column in range(1, blocks + 1):
            table.setColumnWidth(column, 100)
        table.setColumnWidth(blocks + 1, max(100, 700 - 70 - blocks * 100))
        for row, rotation in enumerate(scheme.current):
            worker = QTableWidgetItem(rotation.worker_id)
            worker.setData(Qt.ItemDataRole.UserRole, rotation.worker_id)
            table.setItem(row, 0, worker)
            probabilities = []
            colors = []
            for column, key in enumerate(rotation.target_keys, 1):
                choice = choices[key]
                measurement = target_measurement(choice, kind)
                assert (
                    measurement is not None
                    and measurement.probability_percent is not None
                )
                probability = measurement.probability_percent
                color = QColor(measurement_color(kind, measurement.cumulative_damage))
                cell = QTableWidgetItem(f"{labels[key]}\n{probability:.1f}%")
                cell.setData(Qt.ItemDataRole.UserRole, key)
                cell.setBackground(color)
                cell.setToolTip(
                    f"{choice.job_name} ({measurement.cumulative_damage})\n"
                    + rotation_text("Units", "Unidades", language)
                    + f": {measurement.unit or 'Metric'}"
                )
                table.setItem(row, column, cell)
                probabilities.append(probability)
                colors.append(color)
            average = QTableWidgetItem(f"{sum(probabilities) / blocks:.1f}%")
            average.setBackground(
                QColor(
                    sum(color.red() for color in colors) // blocks,
                    sum(color.green() for color in colors) // blocks,
                    sum(color.blue() for color in colors) // blocks,
                )
            )
            table.setItem(row, blocks + 1, average)
            for column in range(blocks + 2):
                item = table.item(row, column)
                assert item is not None
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(
                    Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
                    | Qt.ItemFlag.ItemIsSelectable
                )
