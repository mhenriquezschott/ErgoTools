"""Lightweight draft-only Settings demonstrations using the shared result widgets.

Presentation layer. Avatar playback is a packaged recording, not another VTK scene.
Sample values are illustrative, never calculations or project writes. Playback stops
when hidden/closed; controls only edit the owning PreferencesDialog's ordinary drafts.
"""

from pathlib import Path

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices, QHideEvent, QMovie, QShowEvent
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.domain.language import Language
from ergotools.presentation.desktop.result_scales import DamageScale, RiskGauge


class AnimationPreviews(QGroupBox):
    """Three coordinated examples with independent draft animation switches."""

    def __init__(
        self,
        focus: QCheckBox,
        gauge: QCheckBox,
        damage: QCheckBox,
        avatar: bytes,
        language: Language,
    ) -> None:
        """Arrange visual samples without renderer or project capabilities.

        Args:
            focus: Existing avatar-animation checkbox; reparented into its own card.
            gauge: Existing risk-animation checkbox, with host-owned Apply semantics.
            damage: Existing damage-animation checkbox, with host-owned Apply semantics.
            avatar: Recorded packaged GIF bytes; empty supports diagnostic hosts.
            language: Current translated labels; sample quantities are unchanged.

        Returns:
            None; only visible samples animate, never the active assessment.
        """
        self.spanish = language is Language.SPANISH
        super().__init__(self.text("Live examples", "Ejemplos en vivo"))
        self.focus, self.gauge_choice, self.damage_choice = focus, gauge, damage
        row = QHBoxLayout(self)
        row.setSpacing(12)
        self.avatar_card = QGroupBox(self.text("Avatar focus", "Enfoque del avatar"))
        self.gauge_card = QGroupBox(self.text("Risk gauge", "Indicador de riesgo"))
        self.damage_card = QGroupBox(self.text("Cumulative damage", "Daño acumulado"))
        for card in (self.avatar_card, self.gauge_card, self.damage_card):
            card.setMinimumWidth(220)
            row.addWidget(card, 1)
        avatar_layout = QVBoxLayout(self.avatar_card)
        avatar_layout.addWidget(focus)
        self.avatar_label = QLabel()
        self.avatar_label.setMinimumHeight(220)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet(
            "background:#092D45;color:white;border-radius:6px;"
        )
        self.avatar_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.buffer = QBuffer(self)
        self.buffer.setData(QByteArray(avatar))
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.movie = QMovie(self.buffer, QByteArray(b"gif"), self)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.movie.setScaledSize(QSize(240, 226))
        self.avatar_label.setMovie(self.movie)
        if not self.movie.isValid():
            self.avatar_label.setText(
                self.text("Preview unavailable", "Vista no disponible")
            )
        avatar_layout.addWidget(self.avatar_label, 1)
        self.avatar_state = QLabel()
        self.avatar_state.setWordWrap(True)
        avatar_layout.addWidget(self.avatar_state)
        gauge_layout = QVBoxLayout(self.gauge_card)
        gauge_layout.addWidget(gauge)
        self.gauge = RiskGauge()
        self.gauge.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.gauge.marker_language = language
        self.gauge.outcome_text = self.text(
            "Sample probability (%)", "Probabilidad de ejemplo (%)"
        )
        gauge_layout.addWidget(self.gauge)
        gauge_layout.addStretch(1)
        self.gauge_state = QLabel()
        self.gauge_state.setWordWrap(True)
        gauge_layout.addWidget(self.gauge_state)
        damage_layout = QVBoxLayout(self.damage_card)
        damage_layout.addWidget(damage)
        damage_layout.addStretch(1)
        self.damage_value = QLabel()
        self.damage_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.damage_value.setStyleSheet("font-size:22px;font-weight:700;color:#0B326C;")
        damage_layout.addWidget(self.damage_value)
        self.damage = DamageScale()
        damage_layout.addWidget(self.damage)
        damage_layout.addStretch(1)
        self.damage_state = QLabel()
        self.damage_state.setWordWrap(True)
        damage_layout.addWidget(self.damage_state)
        for label in (self.avatar_state, self.gauge_state, self.damage_state):
            label.setFixedHeight(46)
            label.setAlignment(
                Qt.AlignmentFlag(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            )
        self.index = 0
        self.timer = QTimer(self)
        self.timer.setInterval(2200)
        self.timer.timeout.connect(self.advance)
        focus.toggled.connect(self.refresh_choices)
        gauge.toggled.connect(self.refresh_choices)
        damage.toggled.connect(self.refresh_choices)
        self.refresh_choices()
        self.show_sample()

    def text(self, english: str, spanish: str) -> str:
        """Resolve descriptive captions without translating any sample data.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Caption matching the owning Settings language.
        """
        return spanish if self.spanish else english

    def refresh_choices(self) -> None:
        """Show immediately what each tentative switch does, without applying it.

        Args:
            None.

        Returns:
            None; disabled avatar focus shows full body, matching the production policy.
        """
        self.gauge.set_animation_enabled(self.gauge_choice.isChecked())
        self.damage.set_animation_enabled(self.damage_choice.isChecked())
        self.avatar_state.setText(
            self.text(
                "Smooth focus on the active body region."
                if self.focus.isChecked()
                else "Full body remains in view; region focus is off.",
                "Enfoque suave en la región activa."
                if self.focus.isChecked()
                else "Se mantiene el cuerpo completo; enfoque de región desactivado.",
            )
        )
        for checkbox, label in (
            (self.gauge_choice, self.gauge_state),
            (self.damage_choice, self.damage_state),
        ):
            label.setText(
                self.text(
                    "Smooth transitions between sample values."
                    if checkbox.isChecked()
                    else "Values change immediately, without movement.",
                    "Transiciones suaves entre valores de ejemplo."
                    if checkbox.isChecked()
                    else "Los valores cambian de inmediato, sin movimiento.",
                )
            )
        if self.focus.isChecked() and self.isVisible():
            self.movie.start()
        else:
            self.movie.stop()
            self.movie.jumpToFrame(0)

    def show_sample(self) -> None:
        """Project a fixed illustrative pair through the actual gauge and bar controls.

        Args:
            None.

        Returns:
            None; samples represent display behavior, without source-bound calculations.
        """
        probability, damage, color = (
            (18, 0.15, "#19B83F"),
            (33, 0.65, "#F5C400"),
            (44, 1.2, "#FF8A19"),
            (70, 1.8, "#FF3B30"),
        )[self.index]
        self.gauge.set_probability(probability)
        self.damage.set_value(damage, color)
        self.damage_value.setText(f"{damage:.2f}")

    def advance(self) -> None:
        """Change only the local demonstration target at a readable cadence.

        Args:
            None.

        Returns:
            None; checkbox choices determine interpolation versus immediate changes.
        """
        self.index = (self.index + 1) % 4
        self.show_sample()

    def showEvent(self, event: QShowEvent | None) -> None:  # noqa: N802 — Qt override
        """Resume samples only while this Settings page is visible.

        Args:
            event: Original native show event, forwarded unchanged.

        Returns:
            None; reopening a page does not alter any preference draft.
        """
        super().showEvent(event)
        self.refresh_choices()
        self.timer.start()

    def hideEvent(self, event: QHideEvent | None) -> None:  # noqa: N802 — Qt override
        """Stop background movie/timer work when navigating away or closing Settings.

        Args:
            event: Original native hide event, forwarded unchanged.

        Returns:
            None; no animation survives a hidden or closed settings page.
        """
        self.timer.stop()
        self.movie.setPaused(True)
        self.gauge.animation.stop()
        self.damage.animation.stop()
        super().hideEvent(event)


class GaugeAppearancePreview(QGroupBox):
    """Immediate preview of draft ticks/labels/spacing with a sample-value slider."""

    def __init__(self, language: Language) -> None:
        """Show shared gauge geometry rather than a separate illustrative drawing.

        Args:
            language: Explicit owned interface caption language.

        Returns:
            None; controls are local samples and expose no result-save operation.
        """
        spanish = language is Language.SPANISH
        super().__init__("Vista previa" if spanish else "Live preview")
        layout = QVBoxLayout(self)
        self.gauge = RiskGauge()
        self.gauge.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.gauge.setMaximumWidth(380)
        self.gauge.set_animation_enabled(False)
        self.gauge.marker_language = language
        self.gauge.outcome_text = (
            "Probabilidad de ejemplo (%)" if spanish else "Sample probability (%)"
        )
        layout.addWidget(self.gauge, 0, Qt.AlignmentFlag.AlignHCenter)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(42)
        self.slider.setToolTip(
            "Mover para probar distintos valores"
            if spanish
            else "Move to preview different values"
        )
        self.slider.valueChanged.connect(self.gauge.set_probability)
        layout.addWidget(self.slider)
        self.gauge.set_probability(42)

    def apply_markers(self, settings: GaugeMarkerSettings) -> None:
        """Project only marker appearance without writing the host's preferences.

        Args:
            settings: Validated current tentative checkbox/spacing choices.

        Returns:
            None; current sample value and scientific sources are unaffected.
        """
        self.gauge.set_marker_settings(settings)


class DiagnosticReportInfo(QGroupBox):
    """Show report location and folder access without editing logging policy."""

    def __init__(self, path: str | None, language: Language) -> None:
        """Explain the current launch's reporting state and where to find its file.

        Args:
            path: Current report filename from bootstrap, or None when disabled.
            language: Owned caption language.

        Returns:
            None; the native file browser is independent of ErgoTools' lifetime.
        """
        spanish = language is Language.SPANISH
        super().__init__(
            "Diagnóstico de pantalla" if spanish else "Display diagnostics"
        )
        layout = QVBoxLayout(self)
        label = QLabel(
            ("Informe de esta sesión: " if spanish else "This session's report: ")
            + Path(path).name
            if path
            else (
                "Desactivado. Use --startup-diagnostics al iniciar "
                "para registrar un informe."
                if spanish
                else "Off. Launch with --startup-diagnostics to record a report."
            )
        )
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setToolTip(path or "")
        layout.addWidget(label)
        if path:
            row = QHBoxLayout()
            copy = QPushButton("Copiar ruta" if spanish else "Copy report path")
            folder = QPushButton("Abrir carpeta" if spanish else "Open report folder")
            copy.setAutoDefault(False)
            folder.setAutoDefault(False)
            copy.setToolTip(path)
            folder.setToolTip(str(Path(path).parent))

            def copy_path() -> None:
                """Copy only the current report filename to the system clipboard.

                Args:
                    None.

                Returns:
                    None; no file or setting is changed.
                """
                clipboard = QApplication.clipboard()
                if clipboard is not None:
                    clipboard.setText(path)

            def open_folder() -> None:
                """Open the report folder through the independent system browser.

                Args:
                    None.

                Returns:
                    None; this window never owns the file browser's lifetime.
                """
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))

            copy.clicked.connect(copy_path)
            folder.clicked.connect(open_folder)
            row.addWidget(copy)
            row.addWidget(folder)
            row.addStretch(1)
            layout.addLayout(row)
