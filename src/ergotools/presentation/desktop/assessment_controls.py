"""Shared native assessment inputs used by worker panels and Job task views.

Presentation layer. Construct precision-preserving numeric fields and the established
OMNI-Res/direction selectors. Callers own signals, parsing, source edits and lifetime;
these factories perform no calculations, history operations or persistence.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QSizePolicy, QStyledItemDelegate

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit

# Original bilingual scale descriptors; intermediate ratings intentionally have no name.
OMNI_RATINGS = (
    ("Extremely Easy", "Extremadamente fácil"),
    ("", ""),
    ("Easy", "Fácil"),
    ("", ""),
    ("Somewhat Easy", "Algo fácil"),
    ("", ""),
    ("Somewhat Hard", "Algo difícil"),
    ("", ""),
    ("Hard", "Difícil"),
    ("", ""),
    ("Extremely Hard", "Extremadamente difícil"),
)
# Original selector order and model identities; no formula convention is inferred here.
TASK_DIRECTIONS = (
    (TstDirection.HANDLING_LOADS, "Handling Loads", "Manipulación de cargas"),
    (TstDirection.DOWNWARD, "Push or Pull Downward", "Empujar o Tirar hacia abajo"),
    (TstDirection.HORIZONTAL, "Horizontal Push or Pull", "Empuje o Tirón Horizontal"),
)


def assessment_number(
    value: float | None, convention: DecimalConvention, decimals: int
) -> PrecisionLineEdit:
    """Construct the common centered input while retaining exact unchanged values.

    Args:
        value: Source quantity or None for an empty input.
        convention: Explicit decimal separator, independent of UI language.
        decimals: Display precision only; zero for repetitions.

    Returns:
        Unparented native editor; caller installs parsing/history callbacks.
    """
    editor = PrecisionLineEdit(value, convention, decimals)
    editor.setCursorPosition(0)
    editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return editor


def assessment_selector(
    kind: AssessmentKind,
    value: int | TstDirection | None,
    language: Language = Language.ENGLISH,
) -> QComboBox:
    """Construct the original descriptive DUET or ST selector with typed item data.

    Args:
        kind: DUET scale or ST direction; LiFFT has no selector.
        value: Exact selected scale/direction, or None for an unselected input.
        language: Labels only; identities and original order remain unchanged.

    Returns:
        Unparented selector, with the existing popup style and sizing policy.

    Raises:
        ValueError: LiFFT was requested, since it has no selector input.
    """
    if kind is AssessmentKind.LIFFT:
        raise ValueError("LiFFT has no assessment selector.")
    combo = QComboBox()
    combo.setItemDelegate(QStyledItemDelegate(combo))
    view = combo.view()
    assert view is not None
    view.setStyleSheet(
        "QAbstractItemView { background: white; color: #1B2933; outline: 0; }"
        "QAbstractItemView::item { min-height: 28px; padding: 2px 7px; }"
        "QAbstractItemView::item:selected, QAbstractItemView::item:hover "
        "{ background: #087E91; color: white; }"
    )
    spanish = language is Language.SPANISH
    if kind is AssessmentKind.DUET:
        combo.setMinimumWidth(250)
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        combo.setMinimumContentsLength(19)
        for index, captions in enumerate(OMNI_RATINGS):
            combo.addItem(f"{index}: {captions[int(spanish)]}", index)
        combo.setCurrentIndex(combo.findData(value))
    else:
        combo.setMinimumWidth(0)
        combo.setMaximumWidth(220)
        combo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        for direction, english, translated in TASK_DIRECTIONS:
            combo.addItem(translated if spanish else english, direction.value)
        combo.setCurrentIndex(
            combo.findData(value.value if isinstance(value, TstDirection) else None)
        )
    return combo
