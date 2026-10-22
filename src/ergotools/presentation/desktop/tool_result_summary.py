"""Original inline assessment summaries, independent of models and storage.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGridLayout, QLabel, QWidget


class ToolResultSummary(QGridLayout):
    """Two reference summary rows aligned with the task damage column.

    The owning panel supplies already formatted values and palette colors. This
    component never calculates risk, loads data, or installs refresh callbacks.
    """

    def __init__(self) -> None:
        """Create the original labels, spacing and foreground treatment.

        Args:
            None.

        Returns:
            None.
        """
        super().__init__()
        self.setContentsMargins(0, 5, 0, 5)
        self.total_title = QLabel()
        self.total_value = QLabel()
        self.probability_title = QLabel()
        self.probability_value = QLabel()
        for row, (title, value) in enumerate(self.rows):
            title.setObjectName("toolResultName")
            title.setStyleSheet(
                "color: #0B326C; font-size: 13px; font-weight: 700; padding-right: 8px;"
            )
            title.setAlignment(
                Qt.AlignmentFlag(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
            )
            value.setObjectName("toolResultValue")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setMinimumHeight(30)
            self.setRowMinimumHeight(row, 30)
            self.addWidget(title, row, 0)
            self.addWidget(value, row, 1)
        self.setColumnStretch(2, 1)
        self.show_values("0.0", "0.0", None)

    @property
    def rows(self) -> tuple[tuple[QLabel, QLabel], ...]:
        """Return the damage and probability label pairs in reference order.

        Args:
            None.

        Returns:
            Current saved worker-result rows in reference binary ID/surname order, or an
            empty tuple without results.
        """
        return (
            (self.total_title, self.total_value),
            (self.probability_title, self.probability_value),
        )

    def show_values(self, damage: str, probability: str, color: str | None) -> None:
        """Replace all output state, clearing stale color for unavailable results.

        Args:
            damage: Already formatted cumulative-damage text, not a calculation operand.
            probability: Already formatted probability text; this component does not
                evaluate risk.
            color: Original CSS/Qt palette color, or None to clear unavailable-result
                styling.

        Returns:
            None.
        """
        foreground = "#10212B"
        background = "transparent"
        if color is not None:
            rgb = QColor(color)
            background = rgb.name()
            luminance = 0.299 * rgb.red() + 0.587 * rgb.green() + 0.114 * rgb.blue()
            foreground = "#10212B" if luminance > 145 else "#FFFFFF"
        style = (
            f"background: {background}; color: {foreground}; border-radius: 4px; "
            "font-size: 15px; font-weight: 800; padding: 5px 12px;"
        )
        for (_, value), text in zip(self.rows, (damage, probability), strict=True):
            value.setText(text)
            value.setStyleSheet(style)

    def align_to(self, target: QWidget | None, panel: QWidget) -> None:
        """Align after layout or translation changes; constrain to panel bounds.

        Args:
            target: Damage-column widget to align the summaries against; None uses
                available panel bounds.
            panel: Owning task panel used for coordinate mapping and horizontal clipping
                bounds.

        Returns:
            None.
        """
        width = max(title.sizeHint().width() for title, _ in self.rows)
        for title, _ in self.rows:
            title.setFixedWidth(width)
        if target is None:
            return
        outer = panel.layout()
        assert outer is not None
        left = outer.contentsMargins().left()
        target_x = target.mapTo(panel, target.rect().topLeft()).x() - left
        available = panel.width() - left - outer.contentsMargins().right()
        margin = max(
            0,
            min(
                target_x - width - self.horizontalSpacing(),
                available - width - target.width() - self.horizontalSpacing(),
            ),
        )
        self.setContentsMargins(margin, 5, 0, 5)
        for _, value in self.rows:
            value.setFixedWidth(target.width())
