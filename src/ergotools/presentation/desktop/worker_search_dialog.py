"""Original Find Assessment form using immutable owned project snapshots.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.history_access import AssignmentSelection
from ergotools.domain.assessment_history import AssessmentHistory
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.language import Language
from ergotools.domain.risk import classify_probability
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.assessment_badges import AssessmentBadgeDelegate
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES

# Spanish Find Assessment captions for the original text/alphabet/workplace search
# workflow.
_TEXT_ES = {
    "Female": "Mujer",
    "Male": "Hombre",
    "Find Assessment": "Buscar evaluación",
    "Find a {tool} assessment": "Buscar evaluación de {tool}",
    (
        "Search saved assessments by worker, "
        "then narrow the results by last-name "
        "initial or workplace."
    ): (
        "Busque evaluaciones guardadas por "
        "trabajador y filtre por inicial del "
        "apellido o lugar de trabajo."
    ),
    "Assessment workplace scope": "Ámbito de trabajo de la evaluación",
    ("Filter workers by workplaces where they have saved {tool} assessments."): (
        "Filtrar por lugares con evaluaciones guardadas de {tool}."
    ),
    ("Select any level to include every saved assessment below it."): (
        "Seleccione un nivel para incluir las evaluaciones de sus niveles inferiores."
    ),
    "Workplace hierarchy": "Jerarquía de trabajo",
    "Type": "Tipo",
    ("Choose All workplaces, or filter saved {tool} assessments by location."): (
        "Elija todos los lugares o filtre las evaluaciones de {tool} por ubicación."
    ),
    "Saved assessments": "Evaluaciones guardadas",
    ("Search worker ID, first name, or last name"): "Buscar por ID, nombre o apellido",
    ("Results update as you type. Partial names and IDs are supported."): (
        "Los resultados se actualizan al escribir. Se admiten nombres e ID parciales."
    ),
    "Last name": "Apellido",
    ("Filter workers by the first letter of their last name."): (
        "Filtrar por la primera letra del apellido."
    ),
    "Show every last name": "Mostrar todos los apellidos",
    ("Show last names beginning with {letter}"): (
        "Mostrar apellidos que comienzan con {letter}"
    ),
    "Worker ID": "ID",
    "First name": "Nombre",
    "Sex": "Sexo",
    "Age": "Edad",
    "Workplace": "Lugar de trabajo",
    "Shift": "Turno",
    ("Exact workplace where this {tool} assessment is saved."): (
        "Lugar exacto donde se guarda esta evaluación de {tool}."
    ),
    ("Shift associated with this saved assessment."): (
        "Turno asociado con esta evaluación guardada."
    ),
    (
        "Select a saved assessment, then choose"
        " Use assessment. Double-clicking also "
        "opens it."
    ): (
        "Seleccione una evaluación y pulse Usar"
        " evaluación. También puede abrirla con"
        " doble clic."
    ),
    ("Close without changing the selected worker or assessment workplace."): (
        "Cerrar sin cambiar el trabajador ni el lugar de la evaluación."
    ),
    "Use assessment": "Usar evaluación",
    "Cancel": "Cancelar",
    "&Cancel": "&Cancelar",
    (
        "Show the selected worker and this "
        "exact assessment workplace in the main"
        " workspace."
    ): (
        "Mostrar el trabajador y el lugar "
        "exacto de esta evaluación en la "
        "ventana principal."
    ),
    "All": "Todos",
    "All workplaces": "Todos los lugares",
    "Plant": "Planta",
    "Section": "Sección",
    "Line": "Línea",
    "Station": "Estación",
    "Filter by {entity}: {text}": "Filtrar por {entity}: {text}",
    "{count} assessment": "{count} evaluación",
    "{count} assessments": "{count} evaluaciones",
}

# Original Find Assessment palette/object-name CSS scoped to this modal search form.
_SEARCH_STYLE = """

            QDialog#workerSearchDialog { background: #F4F7F9; color: #1B2933; }
            QFrame#searchPanel { background: white;
                border: 1px solid #D5DEE5;
                border-radius: 7px;
                }
            QLabel#sectionTitle { color: #0B326C; font-size: 14px; font-weight: 700; }
            QLabel#resultCount { color: #405462; font-weight: 600; }
            QTreeWidget, QTableWidget {
                background: white; color: #1B2933; border: 1px solid #BCC9D3;
                border-radius: 5px;
                alternate-background-color: #F7FAFB;
                gridline-color: #E3E9ED;
            }
            QTreeWidget::item { min-height: 30px; padding: 2px 5px; }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background: #087E91;
                color: white;
                }
            QHeaderView::section {
                background: #EAF2F6; color: #0B326C; border: 0;
                border-bottom: 1px solid #BCC9D3; padding: 8px 6px; font-weight: 700;
            }
            QPushButton#alphabetButton {
                min-width: 22px; max-width: 22px; min-height: 30px; max-height: 30px;
                padding: 0; border: 0; background: transparent; color: #5F6F7A;
                font-size: 11px; font-weight: 650;
            }
            QPushButton#alphabetButton:hover { background: #DDF3F5;
                color: #0B326C;
                font-size: 17px;
                }
            QPushButton#alphabetButton:checked { background: #0B326C;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                }
            QPushButton#alphabetButton:disabled { color: #C7D0D7; }
        
"""


@dataclass(frozen=True, slots=True)
class SearchAssessment:
    """Display metadata plus exact ownership; labels never resolve a selection.

    Exact document identity, optional Job ID and historical ownership accompany the
    visible row; selection never parses these captions.

    Age follows the original current-year minus birth-year convention. Context contains
    plant, section, line, station and shift, without translated keys.
    """

    selection: AssignmentSelection
    worker_id: str
    last_name: str
    first_name: str
    sex: str
    age: str
    context: tuple[str, ...]
    document_id: str = ""
    job: str = ""
    historical: bool = False


def search_assessments(
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    history: AssessmentHistory,
    kind: AssessmentKind,
    *,
    year: int,
) -> tuple[SearchAssessment, ...]:
    """Project saved standalone and assigned sources, including closed owners.

    Project/ownership mismatches raise ValueError. Different assignments at one
    workplace remain separately addressable, as required by historical ownership. No
    assessment input, result or unit is recalculated or changed.

    Args:
        hierarchy: Immutable saved workplace/shift catalog used to build the local
            selection tree.
        jobs: Immutable job/placement/assignment catalog used to resolve marker
            ownership.
        history: Immutable saved ownership catalog, one source per owner/tool.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.
        year: Explicit year used for worker age projections; no current date is inferred
            here.

    Returns:
        Immutable saved assessment search rows with exact
        worker/assignment/workplace ownership and literal captions.

    Raises:
        ValueError: Search catalogs belong to different projects.
    """
    history.validate_jobs(jobs)
    if hierarchy.work.project_id != jobs.project_id:
        raise ValueError("Search catalogs belong to different projects.")
    workers = {worker.worker_id: worker for worker in hierarchy.work.workers}
    owners = {owner.assignment_id: owner for owner in jobs.assignments}
    rows = []
    for entry in history.entries:
        if entry.kind is not kind:
            continue
        owner = (
            owners.get(entry.assignment_id) if entry.assignment_id is not None else None
        )
        worker = workers[entry.worker_id]
        details = worker.details
        birth = details.birth_date if details else None
        place = owner.worker.workplace if owner is not None else None
        rows.append(
            SearchAssessment(
                AssignmentSelection(
                    jobs.project_id,
                    entry.assignment_id,
                    kind,
                    entry.worker_id if entry.assignment_id is None else None,
                ),
                worker.worker_id,
                worker.last_name or "",
                worker.first_name or "",
                (details.sex if details else None) or "-",
                str(max(0, year - int(birth[:4]))) if birth else "-",
                (
                    place.plant_name if place is not None else "",
                    place.section_name if place is not None else "",
                    place.line_name if place is not None else "",
                    place.station_id if place is not None else "",
                    place.shift_id if place is not None else "",
                ),
                entry.document_id,
                (
                    next(
                        (
                            p.job_id
                            for p in jobs.placements
                            if p.placement_id == owner.placement_id
                        ),
                        "",
                    )
                    if owner is not None
                    else ""
                ),
                owner is not None and not owner.active,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.last_name.casefold(),
                row.first_name.casefold(),
                row.worker_id,
                row.context,
                row.selection.assignment_id
                if row.selection.assignment_id is not None
                else -1,
            ),
        )
    )


class WorkerSearchDialog(QDialog):
    """Filter a saved snapshot; acceptance returns an exact assignment/model.

    The owning main window resolves pending edits and Save/Discard/Cancel only after
    acceptance. Closing this modal never mutates project or editor state.
    """

    use_button: QPushButton

    def __init__(
        self,
        rows: Sequence[SearchAssessment],
        hierarchy: WorkHierarchy,
        kind: AssessmentKind,
        icons: Mapping[str, QIcon] | None = None,
        *,
        language: Language = Language.ENGLISH,
        probabilities: Mapping[str, float | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Retain original size/layout and snapshot supplied rows/assets.

        Args:
            rows: Immutable saved result/search rows retaining exact assignment
                ownership.
            hierarchy: Immutable saved workplace/shift catalog used to build the local
                selection tree.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            probabilities: Saved percentages by document ID; supplied maps
                enable the colored result column without calculating or writing data.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.rows = tuple(rows)
        self.probabilities = probabilities
        self.hierarchy = hierarchy
        self.icons = icons or {}
        self.language = language
        self.tool_name = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "Shoulder",
        }[kind]
        if language is Language.SPANISH and kind is AssessmentKind.TST:
            self.tool_name = "Hombro"
        self.active_letter: str | None = None
        self.active_workplace: tuple[str, ...] = ()
        self.selected: AssignmentSelection | None = None
        self.alphabet_buttons: dict[str, QPushButton] = {}
        self.setObjectName("workerSearchDialog")
        self.setWindowTitle(self.text("Find Assessment"))
        self.resize(1080, 650)
        self.setMinimumSize(900, 560)
        self.setStyleSheet(MAIN_WORKSPACE_STYLE + _SEARCH_STYLE)
        if language is Language.SPANISH:
            self.setStyleSheet(
                self.styleSheet() + "QPushButton#alphabetButton { min-width: 12px; }"
            )
        if probabilities is not None:
            self.resize(1380, 720)
            self.setMinimumSize(1120, 600)
        self.build_ui()
        self.populate_workplace_tree()
        available = {row.last_name[0].upper() for row in self.rows if row.last_name}
        for letter, button in self.alphabet_buttons.items():
            button.setEnabled(letter == "All" or letter in available)
        self.apply_filters()

    def text(self, source: str, **values: str | int) -> str:
        """Translate authored text only; database names remain literal.

        Args:
            source: English reference UI wording or earlier project path, as stated by
                this operation; user values are retained literally.
            values: Named literal substitutions for the localized message template; not
                saved identities or numeric parsing policy.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return (
            _TEXT_ES.get(source, source)
            if self.language is Language.SPANISH
            else source
        ).format(**values)

    def icon(self, name: str) -> QIcon:
        """Reuse the processed application icon mapping.

        Args:
            name: Control object name used by the application stylesheet.

        Returns:
            Packaged icon for the requested identity, or a null QIcon when optional
            assets are unavailable.
        """
        return self.icons.get(name, QIcon())

    def build_ui(self) -> None:
        """Build search/filter controls and optional colored saved-risk results.

        Args:
            None.

        Returns:
            None.
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        title = QLabel(self.text("Find a {tool} assessment", tool=self.tool_name))
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            self.text(
                "Search saved assessments by worker, then narrow the "
                "results by last-name initial or workplace."
            )
        )
        subtitle.setObjectName("supportingText")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        content = QHBoxLayout()
        content.setSpacing(12)
        workplace_panel = QFrame()
        workplace_panel.setObjectName("searchPanel")
        workplace_panel.setFixedWidth(360)
        workplace_layout = QVBoxLayout(workplace_panel)
        workplace_layout.setContentsMargins(12, 12, 12, 12)
        workplace_title = QLabel(self.text("Assessment workplace scope"))
        workplace_title.setObjectName("sectionTitle")
        workplace_title.setToolTip(
            self.text(
                (
                    "Filter workers by workplaces where they have saved "
                    "{tool} assessments."
                ),
                tool=self.tool_name,
            )
        )
        workplace_layout.addWidget(workplace_title)
        workplace_help = QLabel(
            self.text("Select any level to include every saved assessment below it.")
        )
        workplace_help.setObjectName("supportingText")
        workplace_help.setWordWrap(True)
        workplace_layout.addWidget(workplace_help)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderLabels(
            [self.text("Workplace hierarchy"), self.text("Type")]
        )
        tree_header = self.workplace_tree.header()
        assert tree_header is not None
        tree_header.setSectionResizeMode(0, QHeaderView.Fixed)
        tree_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.workplace_tree.setColumnWidth(0, 245)
        self.workplace_tree.setColumnWidth(1, 82)
        self.workplace_tree.setAlternatingRowColors(True)
        self.workplace_tree.setToolTip(
            self.text(
                (
                    "Choose All workplaces, or filter saved {tool} "
                    "assessments by location."
                ),
                tool=self.tool_name,
            )
        )
        self.workplace_tree.currentItemChanged.connect(self.workplace_changed)
        workplace_layout.addWidget(self.workplace_tree, 1)
        content.addWidget(workplace_panel)
        directory_panel = QFrame()
        directory_panel.setObjectName("searchPanel")
        directory_layout = QVBoxLayout(directory_panel)
        directory_layout.setContentsMargins(12, 12, 12, 12)
        directory_layout.setSpacing(8)
        search_row = QHBoxLayout()
        directory_title = QLabel(self.text("Saved assessments"))
        directory_title.setObjectName("sectionTitle")
        search_row.addWidget(directory_title)
        search_row.addStretch(1)
        self.result_count = QLabel()
        self.result_count.setObjectName("resultCount")
        search_row.addWidget(self.result_count)
        directory_layout.addLayout(search_row)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.text("Search worker ID, first name, or last name")
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(self.icon("search"), QLineEdit.LeadingPosition)
        self.search_input.setToolTip(
            self.text(
                "Results update as you type. Partial names and IDs are supported."
            )
        )
        self.search_input.textChanged.connect(self.apply_filters)
        directory_layout.addWidget(self.search_input)
        alphabet_row = QHBoxLayout()
        alphabet_row.setSpacing(1)
        alphabet_label = QLabel(self.text("Last name"))
        alphabet_label.setObjectName("supportingText")
        alphabet_label.setToolTip(
            self.text("Filter workers by the first letter of their last name.")
        )
        if self.language is Language.SPANISH:
            alphabet_label.setMinimumWidth(
                alphabet_label.fontMetrics().horizontalAdvance(alphabet_label.text())
            )
        alphabet_row.addWidget(alphabet_label)
        alphabet_row.addSpacing(5)
        self.alphabet_group = QButtonGroup(self)
        self.alphabet_group.setExclusive(True)
        for value in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(self.text(value))
            button.setObjectName("alphabetButton")
            if self.language is Language.SPANISH and value == "All":
                button.setStyleSheet("min-width: 40px; max-width: 40px;")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.setToolTip(
                self.text("Show every last name")
                if value == "All"
                else self.text("Show last names beginning with {letter}", letter=value)
            )
            button.clicked.connect(
                lambda checked, letter=value: self.set_alphabet(letter)
            )
            self.alphabet_group.addButton(button)
            self.alphabet_buttons[value] = button
            alphabet_row.addWidget(button)
        alphabet_row.addStretch(1)
        directory_layout.addLayout(alphabet_row)
        self.table = QTableWidget(0, 8 if self.probabilities is not None else 7)
        self.table.setHorizontalHeaderLabels(
            [
                self.text("Worker ID"),
                self.text("Last name"),
                self.text("First name"),
                self.text("Sex"),
                self.text("Age"),
                self.text("Workplace"),
                self.text("Shift"),
            ]
            + (
                ["Riesgo (%)" if self.language is Language.SPANISH else "Risk (%)"]
                if self.probabilities is not None
                else []
            )
        )
        workplace_header = self.table.horizontalHeaderItem(5)
        shift_header = self.table.horizontalHeaderItem(6)
        assert workplace_header is not None and shift_header is not None
        workplace_header.setToolTip(
            self.text(
                "Exact workplace where this {tool} assessment is saved.",
                tool=self.tool_name,
            )
        )
        shift_header.setToolTip(
            self.text("Shift associated with this saved assessment.")
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        vertical_header = self.table.verticalHeader()
        assert vertical_header is not None
        vertical_header.hide()
        vertical_header.setDefaultSectionSize(35)
        header = self.table.horizontalHeader()
        assert header is not None
        section_widths = (105, 108, 108, 74, 50)
        for column, width in enumerate(section_widths):
            header.setSectionResizeMode(column, QHeaderView.Fixed)
            self.table.setColumnWidth(column, width)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 58)
        if self.probabilities is not None:
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
            self.table.setItemDelegateForColumn(7, AssessmentBadgeDelegate(self.table))
        header.setSortIndicator(1, Qt.SortOrder.AscendingOrder)
        self.table.setToolTip(
            self.text(
                "Select a saved assessment, then choose Use assessment. "
                "Double-clicking also opens it."
            )
        )
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.table.itemDoubleClicked.connect(lambda *_: self.accept_selection())
        directory_layout.addWidget(self.table, 1)
        content.addWidget(directory_panel, 1)
        root.addLayout(content, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        assert cancel_button is not None
        cancel_button.setText(self.text("&Cancel"))
        cancel_button.setIcon(self.icon("cancel"))
        cancel_button.setIconSize(QSize(22, 22))
        cancel_button.setToolTip(
            self.text(
                "Close without changing the selected worker or assessment workplace."
            )
        )
        use_button = buttons.button(QDialogButtonBox.Ok)
        assert use_button is not None
        self.use_button = use_button
        self.use_button.setText(self.text("Use assessment"))
        self.use_button.setObjectName("primaryOutlineButton")
        self.use_button.setIcon(self.icon("worker"))
        self.use_button.setIconSize(QSize(24, 24))
        self.use_button.setToolTip(
            self.text(
                "Show the selected worker and this exact assessment "
                "workplace in the main workspace."
            )
        )
        self.use_button.setEnabled(False)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def populate_workplace_tree(self) -> None:
        """Include only saved-source paths and an explicit standalone root.

        Args:
            None.

        Returns:
            None.
        """
        if any(not row.context[0] for row in self.rows):
            label = (
                "Evaluaciones independientes"
                if self.language is Language.SPANISH
                else "Standalone assessments"
            )
            standalone = self.add_workplace_item(None, label, "All", ("", "", "", ""))
            standalone.setIcon(0, self.icon("worker"))
        all_item = self.add_workplace_item(None, self.text("All workplaces"), "All", ())
        all_item.setIcon(0, self.icon("plant"))
        relevant = {
            row.context[:depth]
            for row in self.rows
            for depth in range(1, 5)
            if row.context[0]
        }
        hierarchy = self.hierarchy
        for plant in sorted(hierarchy.plants, key=str.casefold):
            if (plant,) not in relevant:
                continue
            p = self.add_workplace_item(None, plant, "Plant", (plant,))
            for section in sorted(
                hierarchy.sections_in(plant), key=lambda s: s.section_name.casefold()
            ):
                if (plant, section.section_name) not in relevant:
                    continue
                s = self.add_workplace_item(
                    p, section.section_name, "Section", (plant, section.section_name)
                )
                for line in sorted(
                    hierarchy.lines_in(section), key=lambda x: x.line_name.casefold()
                ):
                    path = (plant, section.section_name, line.line_name)
                    if path not in relevant:
                        continue
                    child = self.add_workplace_item(s, line.line_name, "Line", path)
                    for station in sorted(
                        hierarchy.stations_in(line),
                        key=lambda x: x.station_id.casefold(),
                    ):
                        if (*path, station.station_id) not in relevant:
                            continue
                        self.add_workplace_item(
                            child,
                            station.station_id,
                            "Station",
                            (*path, station.station_id),
                        )
        self.workplace_tree.collapseAll()
        self.workplace_tree.setCurrentItem(all_item)

    def add_workplace_item(
        self,
        parent: QTreeWidgetItem | None,
        label: str,
        entity: str,
        path: tuple[str, ...],
    ) -> QTreeWidgetItem:
        """Store full ancestry separately from translated display text.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.
            label: Visible label/legend caption; None omits an optional chart series
                label.
            entity: Organization level selected for explicit new-record creation.
            path: Exact ordered workplace ancestry prefix used for local tree filtering.

        Returns:
            New owned tree item carrying the complete exact path prefix in item data.
        """
        item = QTreeWidgetItem([label, self.text(entity)])
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        item.setIcon(0, self.icon(entity.lower()))
        item.setToolTip(
            0,
            self.text(
                "Filter by {entity}: {text}",
                entity=self.text(entity).lower(),
                text=label,
            ),
        )
        if parent is None:
            self.workplace_tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        return item

    def set_alphabet(self, letter: str) -> None:
        """Apply the original surname-initial filter.

        Args:
            letter: Surname initial filter, or the reference All sentinel to remove that
                filter.

        Returns:
            None.
        """
        self.active_letter = None if letter == "All" else letter
        self.apply_filters()

    def workplace_changed(
        self, item: QTreeWidgetItem | None, previous: QTreeWidgetItem | None = None
    ) -> None:
        """Filter descendants using full raw ancestry, never a displayed label.

        Args:
            item: Borrowed live tree/graphics item carrying typed owner data; None
                denotes no selection.
            previous: Previously selected Qt tree item; ignored when deriving the new
                exact context.

        Returns:
            None.
        """
        self.active_workplace = (
            tuple(item.data(0, Qt.ItemDataRole.UserRole) or ()) if item else ()
        )
        self.apply_filters()

    def apply_filters(self, *_args: object) -> None:
        """Intersect casefolded worker text, surname initial and workplace prefix.

        Args:
            _args: Unused Qt signal payloads; filter intent is read from the complete
                controls.

        Returns:
            None.
        """
        query = self.search_input.text().strip().casefold()
        rows = tuple(
            row
            for row in self.rows
            if (
                not query
                or query
                in " ".join((row.worker_id, row.first_name, row.last_name)).casefold()
            )
            and (
                not self.active_letter
                or row.last_name.upper().startswith(self.active_letter)
            )
            and row.context[: len(self.active_workplace)] == self.active_workplace
        )
        self.render_rows(rows)

    def render_rows(self, rows: Sequence[SearchAssessment]) -> None:
        """Rebuild filtered rows and clear selection without accumulating signals.

        Args:
            rows: Immutable saved result/search rows retaining exact assignment
                ownership.

        Returns:
            None.
        """
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = (
                row.worker_id,
                row.last_name or "-",
                row.first_name or "-",
                self.text(row.sex),
                row.age,
                (
                    " > ".join(row.context[:4])
                    if row.context[0]
                    else (
                        "Evaluación independiente"
                        if self.language is Language.SPANISH
                        else "Standalone assessment"
                    )
                )
                + (
                    (
                        " · Histórica"
                        if self.language is Language.SPANISH
                        else " · Historical"
                    )
                    if row.historical
                    else ""
                ),
                row.context[4],
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.selection)
                item.setToolTip(
                    value + (("\nJob: " + row.job) if row.job and column == 5 else "")
                )
                self.table.setItem(index, column, item)
            if self.probabilities is not None:
                probability = self.probabilities.get(row.document_id)
                caption = (
                    f"{probability:.1f}%"
                    if probability is not None
                    else (
                        "Sin calcular"
                        if self.language is Language.SPANISH
                        else "Not calculated"
                    )
                )
                badge = QTableWidgetItem(caption)
                color = (
                    RISK_APPEARANCES[classify_probability(probability)].color_hex
                    if probability is not None
                    else "#F0F4F7"
                )
                badge.setBackground(QBrush(QColor(color)))
                badge.setToolTip(caption)
                self.table.setItem(index, 7, badge)
        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.SortOrder.AscendingOrder)
        self.table.clearSelection()
        self.selected = None
        self.use_button.setEnabled(False)
        self.result_count.setText(
            self.text(
                "{count} assessment" if len(rows) == 1 else "{count} assessments",
                count=len(rows),
            )
        )

    def selection_changed(self) -> None:
        """Read exact identity from the selected sorted row and update interlock.

        Args:
            None.

        Returns:
            None.
        """
        model = self.table.selectionModel()
        assert model is not None
        selected = model.selectedRows()
        item = self.table.item(selected[0].row(), 0) if selected else None
        self.selected = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.use_button.setEnabled(self.selected is not None)

    def accept_selection(self) -> None:
        """Accept only an explicitly selected saved assignment.

        Args:
            None.

        Returns:
            None.
        """
        if self.selected is not None:
            self.accept()
