"""English-only scratch task grid and animated step drawer for the JROT prototype.

Presentation layer. These controls own temporary text, names and mouse animation only.
They have no preference/project writer and never alter the shared production widgets.
"""

from collections.abc import Callable
from dataclasses import replace
from functools import partial

from PyQt5.QtCore import (
    QEasingCurve,
    QEvent,
    QLocale,
    QPropertyAnimation,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import QCursor, QDoubleValidator
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.job_calculation import blank_job_source, resize_job_source
from ergotools.application.jrot_prototype import PrototypeJob
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem

# Local selectors follow the existing navy/teal theme without affecting other windows.
PROTOTYPE_STYLE = """
QDialog#jrotPrototype { background: #F4F7F9;
    }
QFrame#prototypeBrand { background: #073E68;
    border-radius: 8px;
    }
QFrame#prototypeBrand QLabel { color: white;
    }
QLabel#prototypeTitle { font-size: 22px;
    font-weight: 700;
    }
QLabel#pageTitle { color: #0B326C;
    font-size: 25px;
    font-weight: 700;
    }
QLabel#eyebrow { color: #087E91;
    font-weight: 700;
    font-size: 11px;
    }
QLabel#supporting { color: #526D7E;
    }
QFrame#prototypeCard { background: white;
    border: 1px solid #D5DEE5;
    border-radius: 7px;
    }
QLabel#cardTitle { color: #0B326C;
    font-size: 16px;
    font-weight: 700;
    }
QPushButton#primary { color: white;
    background: #087E91;
    border: 1px solid #087E91;
    font-weight: 700;
    }
QPushButton#primary:hover { background: #066D7E;
    }
QPushButton#primary:disabled { background: #DCE7EB;
    border-color: #DCE7EB;
    color: #788C98;
    }
QLabel#prototypeNotice { background: #EAF7F8;
    color: #0B5265;
    border: 1px solid #B5DFE4;
    border-radius: 5px;
    padding: 8px;
    }
QLabel#prototypeError { background: #FFF0ED;
    color: #982A1C;
    border: 1px solid #ECC4BB;
    border-radius: 5px;
    padding: 8px;
    }
QFrame#stepDrawer { background: #073E68;
    border-right: 1px solid #073E68;
    }
QFrame#stepDrawer QLabel { color: white; }
QFrame#stepDrawer QToolButton { color: white; background: #073E68;
    border: 1px solid #87A8BE; padding: 5px; }
QPushButton#drawerStep { text-align: left;
    color: white; background: #073E68;
    min-height: 40px;
    padding: 7px;
    border-color: transparent;
    font-weight: 600;
    }
QPushButton#drawerStep:hover { background: #14567E; }
QPushButton#drawerStep:checked { background: #087E91;
    color: white;
    border-left: 3px solid #08A9B5;
    }
QPushButton#rotationChoice { min-height: 72px; font-size: 16px;
    font-weight: 700; border: 2px solid #BCC9D3; border-radius: 6px;
    color: #0B326C; background: white; }
QPushButton#rotationChoice:checked { background: #087E91;
    border-color: #08A9B5; color: white; }
QToolButton#drawerNotch { color: white;
    background: #073E68;
    border: none;
    border-radius: 5px;
    min-height: 84px;
    }
QLabel#metricValue { color: #0B326C;
    font-size: 26px;
    font-weight: 700;
    }
QTableWidget { gridline-color: #E0E8EC;
    alternate-background-color: #F6FAFC;
    }
QHeaderView::section { background: #EAF2F6;
    color: #0B326C;
    font-weight: 700;
    border: 0;
    padding: 9px 7px;
    }
QTabBar::tab { background: #EAF2F6;
    color: #526D7E;
    padding: 10px 18px;
    min-width: 70px;
    }
QTabBar::tab:selected { background: white;
    color: #087E91;
    border-bottom: 3px solid #08A9B5;
    }
"""


def prototype_button(
    text: str, callback: Callable[[], None], *, primary: bool = False
) -> QPushButton:
    """Create one keyboard-safe action without default Enter activation.

    Args:
        text: English action caption.
        callback: Owned view operation; never an implicit save callback.
        primary: Use the existing teal primary-action appearance.

    Returns:
        Unparented button adopted by its containing layout.
    """
    button = QPushButton(text)
    button.setAutoDefault(False)
    if primary:
        button.setObjectName("primary")
    button.clicked.connect(callback)
    return button


def prototype_card(title: str, note: str = "") -> tuple[QFrame, QVBoxLayout]:
    """Create a white titled card with optional wrapping supporting text.

    Args:
        title: English content-group heading.
        note: Optional explanation, never used as an identity.

    Returns:
        Frame and its owned layout for caller-supplied controls.
    """
    frame = QFrame()
    frame.setObjectName("prototypeCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)
    heading = QLabel(title)
    heading.setObjectName("cardTitle")
    layout.addWidget(heading)
    if note:
        description = QLabel(note)
        description.setWordWrap(True)
        description.setObjectName("supporting")
        layout.addWidget(description)
    return frame, layout


class PrototypeDrawer(QWidget):
    """Window-local hover/pin navigation that reallocates real content width."""

    def __init__(self, steps: tuple[str, ...], select: Callable[[int], None]) -> None:
        """Own the notch, drawer and interruptible width animation.

        Args:
            steps: Ordered English page captions, including setup substeps.
            select: Host navigation callback; host validates departures.

        Returns:
            None; initially collapsed and unpinned, with no settings persistence.
        """
        super().__init__()
        self.setMouseTracking(True)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.notch = QToolButton()
        self.notch.setObjectName("drawerNotch")
        self.notch.setText("→")
        self.notch.setFixedWidth(28)
        self.notch.setToolTip("Show workflow steps. Pin the panel to keep it open.")
        root.addWidget(self.notch, 0, Qt.AlignmentFlag.AlignVCenter)
        self.panel = QFrame()
        self.panel.setObjectName("stepDrawer")
        self.panel.setMinimumWidth(0)
        self.panel.setMaximumWidth(0)
        panel = QVBoxLayout(self.panel)
        panel.setContentsMargins(12, 16, 12, 16)
        panel.setSpacing(5)
        title = QLabel("YOUR ROTATION")
        title.setObjectName("eyebrow")
        panel.addWidget(title)
        self.pin = QToolButton()
        self.pin.setText("Pin steps")
        self.pin.setCheckable(True)
        self.pin.setToolTip("Keep the steps visible for this window only.")
        self.pin.toggled.connect(self._pin_changed)
        panel.addWidget(self.pin)
        self.buttons = []
        for index, text in enumerate(steps):
            button = prototype_button(text, partial(select, index))
            button.setObjectName("drawerStep")
            button.setCheckable(True)
            panel.addWidget(button)
            self.buttons.append(button)
        panel.addStretch(1)
        hint = QLabel("Explore freely.\nAll changes stay in this preview.")
        hint.setWordWrap(True)
        hint.setObjectName("supporting")
        panel.addWidget(hint)
        root.addWidget(self.panel)
        self.animation = QPropertyAnimation(self.panel, b"maximumWidth", self)
        self.animation.setDuration(220)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(420)
        self.hide_timer.timeout.connect(self._hide_if_outside)
        self.notch.clicked.connect(lambda: self.reveal(self.panel.maximumWidth() < 100))
        self.notch.installEventFilter(self)
        self.panel.installEventFilter(self)

    def reveal(self, shown: bool = True) -> None:
        """Animate from current width; a pinned drawer cannot auto-collapse.

        Args:
            shown: Requested visibility; False is ignored while pinned.

        Returns:
            None; layouts resize the content instead of covering it.
        """
        if not shown and self.pin.isChecked():
            return
        self.hide_timer.stop()
        self.animation.stop()
        self.animation.setStartValue(self.panel.maximumWidth())
        self.animation.setEndValue(238 if shown else 0)
        self.animation.start()
        self.notch.setText("←" if shown else "→")

    def _pin_changed(self, checked: bool) -> None:
        """Keep local pin wording and drawer visibility synchronized.

        Args:
            checked: Current user-selected window-local pin state.

        Returns:
            None; no preference writer exists.
        """
        self.pin.setText("Unpin steps" if checked else "Pin steps")
        self.reveal(checked)

    def _hide_if_outside(self) -> None:
        """Collapse only after the cursor leaves the complete rail/drawer area.

        Args:
            None.

        Returns:
            None; movement between child buttons does not flicker the drawer.
        """
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.reveal(False)

    def eventFilter(self, watched: object, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Reveal on hover and defer collapsing until native child transitions settle.

        Args:
            watched: Owned notch/panel or an unrelated event source.
            event: Native hover transition, forwarded without consumption.

        Returns:
            False; standard control input remains available.
        """
        if watched in (self.notch, self.panel) and event is not None:
            if event.type() == QEvent.Type.Enter:
                self.reveal()
            elif event.type() == QEvent.Type.Leave:
                self.hide_timer.start()
        return False


class PrototypeTaskGrid(QTableWidget):
    """Metric scratch inputs plus names, using existing task DTOs unchanged."""

    changed = pyqtSignal()

    def __init__(self, kind: AssessmentKind) -> None:
        """Create one tool's grid without a Job, repository or history owner.

        Args:
            kind: Exact LiFFT/DUET/ST identity.

        Returns:
            None; parent dialog binds a temporary Job before editing. The compact
            minimum fits two demo rows while leaving space for prominent totals and
            Calculate; larger sources retain the table's native scrolling.
        """
        super().__init__()
        self.kind = kind
        self.job: PrototypeJob | None = None
        self.source: AssessmentDraft = blank_job_source(kind, MeasurementSystem.METRIC)
        self.controls: list[list[QLineEdit | QComboBox]] = []
        self.names: list[QLineEdit] = []
        self._dirty = False
        self.setMinimumHeight(170)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        vertical = self.verticalHeader()
        assert vertical is not None
        vertical.setDefaultSectionSize(42)

    def bind(self, job: PrototypeJob) -> None:
        """Load a detached Job/tool, preserving exact inputs and temporary task names.

        Args:
            job: Exclusive session Job copy; never an original project record.

        Returns:
            None; absent direct-entry tasks start as one blank scratch row.
        """
        self.job = job
        value = job.measurements.get(self.kind)
        self.source = (
            value.source
            if value and value.source
            else blank_job_source(self.kind, MeasurementSystem.METRIC)
        )
        self._dirty = False
        self._render()
        self.show_outputs(value)

    def _render(self) -> None:
        """Rebuild rows only after binding or explicit task-count operations.

        Args:
            None.

        Returns:
            None; input widgets retain ordinary keyboard editing within a row.
        """
        self.clear()
        self.controls = []
        self.names = []
        fields = (
            ["OMNI-RES", "Repetitions / day"]
            if self.kind is AssessmentKind.DUET
            else [
                *(["Task type"] if self.kind is AssessmentKind.TST else []),
                "Lever arm (cm)",
                "Load (N)",
                "Repetitions / day",
            ]
        )
        headers = ["Task name", *fields, "Damage", "Share (%)"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(self.source.tasks))
        assert self.job is not None
        for row, task in enumerate(self.source.tasks):
            assert isinstance(task, (LifftTask, DuetTask, TstTask))
            name = QLineEdit(self.job.task_names.get(task.task_id, ""))
            name.setPlaceholderText(f"Task {row + 1} — optional name")
            name.textEdited.connect(
                lambda text, key=task.task_id: self._name_changed(key, text)
            )
            self.names.append(name)
            self.setCellWidget(row, 0, name)
            widgets: list[QLineEdit | QComboBox] = []
            if isinstance(task, (DuetTask, TstTask)):
                combo = QComboBox()
                options = (
                    [(str(i), i) for i in range(11)]
                    if isinstance(task, DuetTask)
                    else [
                        ("Handling loads", "0"),
                        ("Push/pull downward", "1"),
                        ("Horizontal push/pull", "2"),
                    ]
                )
                for label, code in options:
                    combo.addItem(label, code)
                current = (
                    task.omni_res_scale
                    if isinstance(task, DuetTask)
                    else task.direction.value
                    if task.direction
                    else None
                )
                combo.setCurrentIndex(combo.findData(current))
                combo.currentIndexChanged.connect(self._input_changed)
                widgets.append(combo)
            values = (
                [task.repetitions]
                if isinstance(task, DuetTask)
                else [task.lever_arm, task.load, task.repetitions]
            )
            for value in values:
                edit = QLineEdit("" if value is None else format(value, ".15g"))
                edit.setPlaceholderText("—")
                validator = QDoubleValidator(0, 1e12, 12, edit)
                locale = QLocale("en_US")
                locale.setNumberOptions(QLocale.RejectGroupSeparator)
                validator.setLocale(locale)
                edit.setValidator(validator)
                edit.textEdited.connect(self._input_changed)
                widgets.append(edit)
            for column, widget in enumerate(widgets, 1):
                self.setCellWidget(row, column, widget)
            self.controls.append(widgets)
        header = self.horizontalHeader()
        assert header is not None
        header.setMinimumSectionSize(105)
        for column in range(len(headers)):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.setColumnWidth(0, 200)
        self.show_outputs(None)

    def _name_changed(self, key: str, text: str) -> None:
        """Retain optional names outside the scientific DTO/codec.

        Args:
            key: Stable source task ID.
            text: Literal temporary name; never a database key.

        Returns:
            None; names do not invalidate unchanged numerical results.
        """
        if self.job is not None:
            self.job.task_names[key] = text

    def _input_changed(self) -> None:
        """Invalidate stale totals immediately, even before a field is complete.

        Args:
            None.

        Returns:
            None; only the temporary Job/tool loses calculated outputs.
        """
        self._dirty = True
        if self.job is not None:
            self.job.measurements[self.kind] = JobRiskMeasurement(
                self.kind, source=self.source
            )
            self.job.skipped.discard(self.kind)
        self.show_outputs(None)
        self.changed.emit()

    def commit(self) -> None:
        """Accept all scratch text, distinguishing blanks from numeric zero.

        Args:
            None.

        Returns:
            None; incomplete inputs remain editable as None.

        Raises:
            ValueError: Visible numeric text or selector is invalid.
        """
        if not self._dirty or self.job is None:
            return
        lifft_tasks: list[LifftTask] = []
        duet_tasks: list[DuetTask] = []
        tst_tasks: list[TstTask] = []
        for task, controls in zip(self.source.tasks, self.controls, strict=True):
            assert isinstance(task, (LifftTask, DuetTask, TstTask))
            values = []
            for control in controls:
                if isinstance(control, QLineEdit):
                    if control.text().strip() and not control.hasAcceptableInput():
                        raise ValueError(
                            "Use nonnegative numbers with a decimal point."
                        )
                    values.append(
                        float(control.text()) if control.text().strip() else None
                    )
            if isinstance(task, DuetTask):
                combo = controls[0]
                assert isinstance(combo, QComboBox)
                duet_tasks.append(
                    replace(
                        task, omni_res_scale=combo.currentData(), repetitions=values[0]
                    )
                )
            elif isinstance(task, TstTask):
                direction = controls[0]
                assert isinstance(direction, QComboBox)
                tst_tasks.append(
                    replace(
                        task,
                        direction=TstDirection(direction.currentData()),
                        lever_arm=values[0],
                        load=values[1],
                        repetitions=values[2],
                    )
                )
            else:
                lifft_tasks.append(
                    replace(
                        task, lever_arm=values[0], load=values[1], repetitions=values[2]
                    )
                )
        if isinstance(self.source, DuetDraft):
            self.source = replace(self.source, tasks=tuple(duet_tasks))
        elif isinstance(self.source, LifftDraft):
            self.source = replace(self.source, tasks=tuple(lifft_tasks))
        else:
            self.source = replace(self.source, tasks=tuple(tst_tasks))
        self.job.measurements[self.kind] = JobRiskMeasurement(
            self.kind, source=self.source
        )
        self._dirty = False

    def resize_tasks(self, remove: bool = False) -> None:
        """Add one blank task or remove the selected row within the 1-100 bound.

        Args:
            remove: True removes the selected row; False appends one.

        Returns:
            None; this is scratch editing, without an Undo stack or durable mutation.

        Raises:
            ValueError: Invalid row selection/count or pending numeric input.
        """
        self.commit()
        index = self.currentRow()
        self.source = resize_job_source(self.source, remove=index if remove else None)
        self._dirty = True
        self._render()
        self._input_changed()

    def show_outputs(self, value: JobRiskMeasurement | None) -> None:
        """Project matching damage/contribution or unavailable placeholders.

        Args:
            value: Current calculated measurement; None clears stale output cells.

        Returns:
            None; read-only cells never manufacture a zero result.
        """
        for row in range(self.rowCount()):
            result = (
                value.task_results[row]
                if value and row < len(value.task_results)
                else None
            )
            for offset, number in enumerate(
                (
                    result.damage if result else None,
                    result.share_percent if result else None,
                )
            ):
                cell = QTableWidgetItem("—" if number is None else f"{number:.6g}")
                cell.setFlags(
                    Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
                    | Qt.ItemFlag.ItemIsSelectable
                )
                self.setItem(row, self.columnCount() - 2 + offset, cell)
