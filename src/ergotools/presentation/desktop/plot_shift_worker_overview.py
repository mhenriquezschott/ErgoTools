"""Read-only searchable worker details for PLOT rotation playback.

Presentation layer. Reuses the application's adaptive alphabet and packaged navigation
icons; selection/Locate publish local intent, never worker or map edits.
"""

from typing import TYPE_CHECKING
from unicodedata import normalize

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.worker_details import display_body_measurement
from ergotools.presentation.desktop.alphabet_navigation import AlphabetNavigation
from ergotools.presentation.desktop.plot_shift_graphics import contrast_ink, shift_color

if TYPE_CHECKING:
    from ergotools.presentation.desktop.plot_shift_player import PlotShiftPlayer


class ShiftWorkerOverview(QScrollArea):
    """Show demographic, workplace and current/ending index data for one worker."""

    def __init__(self, player: "PlotShiftPlayer") -> None:
        """Compose local navigation without acquiring a project mutation capability.

        Args:
            player: Existing transient playback owner.

        Returns:
            None.
        """
        super().__init__()
        self.player = player
        self.letter = "All"
        self.ids: tuple[str, ...] = ()
        text = player.host.text
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        panel = QWidget()
        self.setWidget(panel)
        layout = QVBoxLayout(panel)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            text("Search worker ID or name", "Buscar ID o nombre")
        )
        self.search.setToolTip(
            text(
                "Find a worker in the filtered rotation.",
                "Buscar un trabajador de la rotación filtrada.",
            )
        )
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)
        self.selector = QComboBox()
        self.selector.setMinimumWidth(0)
        self.selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.selector.setToolTip(
            text(
                "Select a worker; the map and exposure table follow.",
                "Seleccionar trabajador; el mapa y la tabla siguen la selección.",
            )
        )
        self.selector.currentIndexChanged.connect(self.selected)
        layout.addWidget(self.selector)
        self.alphabet = AlphabetNavigation(text("All", "Todos"), self.set_letter)
        layout.addWidget(self.alphabet)
        navigation = QHBoxLayout()
        for delta, asset, caption in (
            (-10000, "first", text("First", "Primero")),
            (-1, "previous", text("Previous", "Anterior")),
            (1, "next", text("Next", "Siguiente")),
            (10000, "last", text("Last", "Último")),
        ):
            button = QPushButton()
            button.setIcon(player.host.workers.icons[asset])
            button.setIconSize(QSize(22, 22))
            button.setToolTip(caption)
            button.clicked.connect(lambda _checked, d=delta: self.navigate(d))
            navigation.addWidget(button, 1)
        layout.addLayout(navigation)
        box = QGroupBox(text("Worker details", "Datos del trabajador"))
        fields = QGridLayout(box)
        self.values: dict[str, QLabel] = {}
        for row, (key, title) in enumerate(
            (
                ("identity", text("Worker", "Trabajador")),
                ("age", text("Age", "Edad")),
                ("sex", text("Sex", "Sexo")),
                ("body", text("Height / weight", "Estatura / peso")),
                ("place", text("Workplace", "Lugar de trabajo")),
                ("job", text("Current Job", "Trabajo actual")),
                ("now", text("Accumulated index", "Índice acumulado")),
                ("final", text("Final index", "Índice final")),
            )
        ):
            caption = QLabel(title)
            value = QLabel("—")
            value.setWordWrap(True)
            value.setTextFormat(Qt.TextFormat.PlainText)
            self.values[key] = value
            fields.addWidget(caption, row, 0)
            fields.addWidget(value, row, 1)
        fields.setColumnStretch(1, 1)
        layout.addWidget(box)
        self.locate = QPushButton(text("Locate worker", "Localizar trabajador"))
        self.locate.setIcon(player.host.workers.icons["locate"])
        self.locate.setIconSize(QSize(24, 24))
        self.locate.setToolTip(
            text(
                "Center the selected moving worker and highlight its blue frame.",
                "Centrar el trabajador y destacar su marco azul.",
            )
        )
        self.locate.clicked.connect(player.locate_worker)
        layout.addWidget(self.locate)
        layout.addStretch(1)
        note = QLabel(
            text(
                "Read-only rotation view. Assessments and map settings stay unchanged.",
                "Vista de solo lectura. No cambia evaluaciones ni ajustes del mapa.",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)

    def initial(self, name: str) -> str:
        """Normalize accented surname initials for the shared alphabet.

        Args:
            name: Literal surname or display name.

        Returns:
            Uppercase ASCII-compatible initial, or empty text.
        """
        return normalize("NFKD", name).strip()[:1].upper()

    def set_letter(self, letter: str) -> None:
        """Filter local navigation while leaving the map's shared filters intact.

        Args:
            letter: Shared alphabet token, including All.

        Returns:
            None.
        """
        self.letter = letter
        self.refresh()

    def refresh(self) -> None:
        """Rebuild choices from currently visible workers, preserving selection.

        Args:
            None.

        Returns:
            None; no map or project edits occur.
        """
        player = self.player
        people = {w.worker_id: w for w in player.catalog_people.values()}
        offered = sorted(
            player.visible_ids,
            key=lambda key: ((people[key].last_name or "").casefold(), key),
        )
        initials = frozenset(
            self.initial(people[key].last_name or "") for key in offered
        )
        if self.letter != "All" and self.letter not in initials:
            self.letter = "All"
        self.alphabet.set_available(initials, self.letter)
        query = self.search.text().casefold().strip()
        self.selector.blockSignals(True)
        self.selector.clear()
        for key in offered:
            person = people[key]
            title = f"{key} · {person.first_name or ''} {person.last_name or ''}"
            if (
                self.letter == "All"
                or self.initial(person.last_name or "") == self.letter
            ) and (not query or query in title.casefold()):
                self.selector.addItem(title, key)
        self.selector.setCurrentIndex(self.selector.findData(player.selected_worker))
        self.selector.blockSignals(False)
        self.locate.setEnabled(player.selected_worker in player.visible_ids)
        self.show_details()

    def selected(self) -> None:
        """Publish a selection to the player's linked map and exposure table.

        Args:
            None.

        Returns:
            None.
        """
        key = self.selector.currentData()
        if isinstance(key, str):
            self.player.select_worker(key)

    def navigate(self, delta: int) -> None:
        """Clamp First/Previous/Next/Last to the visible search results.

        Args:
            delta: Relative step or large first/last sentinel.

        Returns:
            None.
        """
        if self.selector.count():
            self.selector.setCurrentIndex(
                max(
                    0,
                    min(
                        self.selector.count() - 1, self.selector.currentIndex() + delta
                    ),
                )
            )

    def show_details(self) -> None:
        """Project selected person metadata and the player's current Job/index values.

        Args:
            None.

        Returns:
            None; blank/incomplete data stays explicitly absent.
        """
        player, data = self.player, self.player.data
        for value in self.values.values():
            value.setText("—")
            value.setStyleSheet("")
        if player.selected_worker not in player.catalog_people:
            return
        index = (
            next(
                (
                    i
                    for i, row in enumerate(data.rows)
                    if row.worker_id == player.selected_worker
                ),
                None,
            )
            if data
            else None
        )
        worker = next(
            w
            for w in player.catalog_people.values()
            if w.worker_id == player.selected_worker
        )
        details = worker.details
        self.values["identity"].setText(
            f"{worker.worker_id} · {worker.first_name or ''} {worker.last_name or ''}"
        )
        self.values["age"].setText(
            str(player.host.current_year - int(details.birth_date[:4]))
            if details and details.birth_date
            else "—"
        )
        self.values["sex"].setText(details.sex if details and details.sex else "—")
        metric = player.host.system is MeasurementSystem.METRIC
        height = display_body_measurement(
            details.height_cm if details else None, player.host.system, mass=False
        )
        weight = display_body_measurement(
            details.weight_kg if details else None, player.host.system, mass=True
        )
        height_text = f"{height:g}" if height is not None else "—"
        weight_text = f"{weight:g}" if weight is not None else "—"
        self.values["body"].setText(
            f"{height_text} {'cm' if metric else 'in'} / "
            f"{weight_text} {'kg' if metric else 'lb'}"
        )
        assignment = player.assignment_for_worker(worker.worker_id)
        if assignment is not None:
            place = assignment.worker.workplace
            self.values["place"].setText(
                " / ".join(
                    (
                        place.plant_name,
                        place.section_name,
                        place.line_name,
                        place.station_id,
                        place.shift_id,
                    )
                )
            )
        if data is None or index is None:
            return
        a, b, fraction = data.phase(player.elapsed)
        target = data.rows[index].target_keys[b if fraction > 0.5 else a]
        destination = next((d for d in data.destinations if d.key == target), None)
        current_place = player.target_places.get(target)
        if current_place is not None:
            self.values["place"].setText(
                " / ".join(
                    (
                        current_place.plant_name,
                        current_place.section_name,
                        current_place.line_name,
                        current_place.station_id,
                        current_place.shift_id,
                    )
                )
            )
        if destination:
            self.values["job"].setText(f"{destination.job_id} · {destination.name}")
        if not data.issues:
            for key, minute in (
                ("now", player.elapsed),
                ("final", data.timing.shift_minutes),
            ):
                score = data.index(index, minute)
                self.values[key].setText(f"{score:.2f}")
                color = shift_color(score)
                self.values[key].setStyleSheet(
                    f"background:{color.name()};color:{contrast_ink(color).name()};font-weight:bold;padding:5px;border-radius:3px;"
                )
