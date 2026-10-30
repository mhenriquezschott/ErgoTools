"""Apply injected personal animation choices to an explicitly owned widget subtree.

Presentation only. No global window lookup, settings I/O or result recalculation occurs;
new modal windows receive saved choices from their existing composition owner.
"""

from PyQt5.QtWidgets import QWidget

from ergotools.presentation.desktop.result_scales import DamageScale, RiskGauge


def apply_result_animations(root: QWidget, gauge: bool, damage: bool) -> None:
    """Update result-scale widgets belonging to one explicit host.

    Args:
        root: Main or modal window whose child scales are borrowed during this call.
        gauge: Animate risk gauges, including compact PLOT gauges.
        damage: Animate cumulative-damage bars.

    Returns:
        None; disabling settles current targets without modifying scientific values.
    """
    for widget in root.findChildren(RiskGauge):
        widget.set_animation_enabled(gauge)
    for bar in root.findChildren(DamageScale):
        bar.set_animation_enabled(damage)
