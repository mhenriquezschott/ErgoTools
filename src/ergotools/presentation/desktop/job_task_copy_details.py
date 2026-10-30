"""Read-only task rows and copy selection embedded beneath one source tree entry.

Presentation layer. Checkboxes choose identities only; inputs/results remain unchanged.
The parent picker owns source revalidation and explicit subset calculation on Copy.
"""

from dataclasses import replace

from PyQt5.QtCore import QEvent, QObject, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from ergotools.domain.assessments.document import AssessmentDraft, task_has_data
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.language import Language
from ergotools.presentation.desktop.job_task_editor import JobTaskEditor


class JobTaskCopyDetails(QWidget):
    """Embed read-only rows and copy-checkbox controls beneath one tree source.

    Attributes:
        selection_changed: Emits selected stable task IDs, never source mutations.
        activated: Selects this source when its embedded controls receive interaction.
        grid: Compact populated rows; task values/results are always read-only.
        preferred_height: Bounded row-dependent height requested by the source tree.
    """

    selection_changed = pyqtSignal(object)
    activated = pyqtSignal()

    def __init__(
        self,
        item: JobRiskMeasurement,
        language: Language,
        convention: DecimalConvention,
        selected: tuple[str, ...],
    ) -> None:
        """Build read-only controls for one source with independent copy checkboxes.

        Args:
            item: Existing source and matching output, never edited by this component.
            language: English/Spanish view captions.
            convention: Numeric display separator only.
            selected: Previously checked stable source-task identities.

        Returns:
            None; no calculator, workspace or repository is used.
        """
        super().__init__()
        self.setMinimumWidth(0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(0)
        source = item.source
        tasks: tuple[LifftTask | DuetTask | TstTask, ...] = (
            tuple(t for t in source.tasks if task_has_data(t)) if source else ()
        )
        if isinstance(source, LifftDraft):
            preview: AssessmentDraft | None = replace(
                source, tasks=tuple(t for t in source.tasks if task_has_data(t))
            )
        elif isinstance(source, DuetDraft):
            preview = replace(
                source, tasks=tuple(t for t in source.tasks if task_has_data(t))
            )
        elif source is not None:
            assert isinstance(source, TstDraft)
            preview = replace(
                source, tasks=tuple(t for t in source.tasks if task_has_data(t))
            )
        else:
            preview = None
        task_ids = {t.task_id for t in tasks}
        self.grid = JobTaskEditor(
            language,
            convention,
            kind=item.kind,
            read_only=True,
            selectable=True,
            compact=True,
        )
        original_tasks: tuple[LifftTask | DuetTask | TstTask, ...] = (
            source.tasks if source else ()
        )
        self.grid.load_source(
            preview,
            tuple(
                r
                for t, r in zip(original_tasks, item.task_results, strict=False)
                if t.task_id in task_ids
            ),
        )
        for number, task in enumerate(original_tasks, 1):
            if task.task_id in self.grid.task_checks:
                check = self.grid.task_checks[task.task_id]
                check.setText(str(number))
                check.setToolTip(
                    ("Copy task " if language is Language.ENGLISH else "Copiar tarea ")
                    + str(number)
                )
        self.grid.set_task_selection(selected)
        first_header = self.grid.headers[0]
        self.grid.header_grid.removeWidget(first_header)
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        first_header.setFixedHeight(22)
        header_layout.addWidget(first_header)
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(2)
        self.all_button = QToolButton()
        self.all_button.setText("All" if language is Language.ENGLISH else "Todas")
        self.none_button = QToolButton()
        self.none_button.setText("None" if language is Language.ENGLISH else "Ninguna")
        self.all_button.setToolTip(
            "Select all populated tasks"
            if language is Language.ENGLISH
            else "Seleccionar todas las tareas con datos"
        )
        self.none_button.setToolTip(
            "Clear task selection"
            if language is Language.ENGLISH
            else "Vaciar la selección de tareas"
        )
        for button in (self.all_button, self.none_button):
            button.setFixedHeight(18)
            button.setStyleSheet(
                "QToolButton { font-size: 10px; color: #0B326C; padding: 0 2px; "
                "border: 0; border-radius: 2px; } "
                "QToolButton:hover { background: #DDF3F5; }"
            )
            actions.addWidget(button)
        header_layout.addLayout(actions)
        self.grid.header_grid.addWidget(header, 0, 0)
        self.preferred_height = 64 + min(len(tasks), 6) * 24
        self.setFixedHeight(self.preferred_height)
        self.grid.task_selection_changed.connect(self.selection_changed)
        self.all_button.clicked.connect(
            lambda: self.grid.set_task_selection(tuple(t.task_id for t in tasks))
        )
        self.none_button.clicked.connect(lambda: self.grid.set_task_selection(()))
        layout.addWidget(self.grid, 1)
        if not tasks:
            empty = QLabel(
                "No populated tasks"
                if language is Language.ENGLISH
                else "No hay tareas con datos"
            )
            layout.addWidget(empty)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Select this source when its embedded read-only controls receive interaction.

        Args:
            watched: Owned preview/control widget.
            event: Native focus/click event, passed through without modification.

        Returns:
            False; source activation never consumes checkbox or native copy events.
        """
        if event is not None and event.type() in (
            QEvent.Type.FocusIn,
            QEvent.Type.MouseButtonPress,
        ):
            self.activated.emit()
        return False
