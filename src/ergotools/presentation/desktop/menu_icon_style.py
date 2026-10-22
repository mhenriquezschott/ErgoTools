"""Enlarge popup menu icons without changing toolbar/button metrics or assets.

Presentation layer: wrap the existing Qt style with a popup small-icon metric. Qt owns
DPI scaling and painting; resource bytes, the application palette and all other style
metrics remain unchanged. Unbound small-icon queries also receive 25 because Qt5
stylesheet menu painting requests that metric without a widget. Explicit button small-
icon metrics remain delegated. QApplication owns the proxy and its base style.
"""

from typing import override

from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QProxyStyle,
    QStyle,
    QStyleOption,
    QWidget,
)


class MenuIconStyle(QProxyStyle):
    """Use the owner-selected 25 logical pixels for popup-menu icons."""

    @override
    def pixelMetric(
        self,
        metric: QStyle.PixelMetric,
        option: QStyleOption | None = None,
        widget: QWidget | None = None,
    ) -> int:
        """Override only popup menu small-icon sizing, delegating everything else.

        Args:
            metric: Qt style metric being requested by a control.
            option: Optional Qt painting/layout state, forwarded unchanged.
            widget: Requesting control; QMenu and unbound style queries receive 25.
                Qt5 stylesheet menu painting omits its widget for this metric.

        Returns:
            Exactly 25 logical pixels for popup-menu/unbound small-icon queries, or the
            unchanged base metric for toolbars, buttons, geometry and other controls.
        """
        value = super().pixelMetric(metric, option, widget)
        return (
            25
            if (
                metric == QStyle.PixelMetric.PM_SmallIconSize
                and (widget is None or isinstance(widget, QMenu))
            )
            else value
        )


def install_menu_icon_style(app: QApplication) -> None:
    """Install one owned menu-only style without wrapping it repeatedly.

    Args:
        app: Existing GUI-thread QApplication owning styles and all application views.

    Returns:
        None; repeated window construction is idempotent. Construct a fresh matching
        base by name, avoiding transfer/deletion of the application's existing style.
        The application flag also covers Qt's stylesheet wrapper around this proxy.
    """
    if app.property("ergotoolsMenuIconStyleInstalled") is True:
        return
    base = app.style()
    assert base is not None
    if not isinstance(base, MenuIconStyle):
        app.setStyle(MenuIconStyle(base.objectName()))
    app.setProperty("ergotoolsMenuIconStyleInstalled", True)
