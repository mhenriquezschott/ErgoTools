"""Reviewed original JROT stylesheet, composed with its original main theme.

Presentation theme layer. JROT menus, scope/tool segments, schedule and comparison tabs
layered over MAIN_WORKSPACE_STYLE.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Preserve exact stylesheet bytes during
documentation changes.
"""

from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE

# Original Qt stylesheet for jROT menus, scope/tool segments, schedule and comparison
# tabs layered over MAIN_WORKSPACE_STYLE.
JROT_STYLE = (
    MAIN_WORKSPACE_STYLE
    + """
QMenuBar { background: #F4F7F9; color: #0B326C; }
QMenuBar::item:selected { background: #EAF7F8; }
QMenu { background: #FFFFFF; color: #1B2933; border: 1px solid #D5DEE5; }
QMenu::item { padding: 6px 24px; }
QMenu::item:selected { background: #EAF7F8; color: #0B326C; }
QMenu::item:disabled { color: #71828F; }
QDialog#jrotWindow {
background: #F4F7F9;
color: #1B2933;
font: 12px "Segoe UI";
}
QGroupBox {
background: white;
border: 1px solid #D5DEE5;
border-radius: 7px;
margin-top: 9px;
padding-top: 5px;
color: #0B326C;
font-weight: 700;
}
QGroupBox::title {
subcontrol-origin: margin;
left: 10px;
padding: 0 5px;
}
QLabel#contextHeading {
color: #456071;
font-size: 11px;
font-weight: 650;
}
QLabel#contextValue {
color: #0B326C;
font-size: 14px;
font-weight: 750;
}
QFrame#workplacePlantScope {
background: #EAF7F8;
border: 1px solid #08A9B5;
border-radius: 4px;
}
QFrame#workplaceScopeBlock {
background: transparent;
border: 0;
}
QLabel#workplaceScopeType {
color: #405866;
font-size: 13px;
font-weight: 700;
}
QLabel#workplaceScopeValue {
color: #304652;
font-size: 14px;
font-weight: 600;
}
QLabel#workplacePlantValue {
color: #087E91;
font-size: 15px;
font-weight: 700;
}
QPushButton#toolSegment {
border-radius: 0;
min-height: 44px;
text-align: left;
padding: 2px 8px;
}
QPushButton#toolSegment:first {
border-top-left-radius: 5px;
border-bottom-left-radius: 5px;
}
QPushButton#toolSegment:checked {
background: #DDF3F5;
color: #087E91;
border: 2px solid #08A9B5;
}
QPushButton#scopeSegment {
border-radius: 0;
min-width: 74px;
min-height: 20px;
max-height: 20px;
padding: 2px 3px;
font-size: 12px;
}
QPushButton#scopeSegment:checked {
background: #DDF3F5;
color: #087E91;
border: 2px solid #08A9B5;
}
QPushButton#primaryButton {
background: #087E91;
color: white;
border-color: #087E91;
}
QPushButton#primaryButton:hover {
background: #096D7C;
}
QPushButton:disabled {
background: #F2F5F7;
color: #8998A3;
border-color: #D5DEE5;
}
QPushButton#primaryButton:disabled {
background: #E2E8EC;
color: #7B8993;
border-color: #CAD5DD;
}
QToolButton#jrotActionButton {
background: white;
color: #0B326C;
border: 1px solid #9FB4C4;
border-radius: 5px;
padding: 2px 4px 5px 4px;
font-weight: 700;
}
QToolButton#jrotActionButton:hover {
background: #EAF7F8;
border-color: #08A9B5;
}
QToolButton#jrotActionButton:pressed {
background: #DDF3F5;
}
QToolButton#jrotActionButton[primaryAction="true"] {
border: 2px solid #08A9B5;
}
QToolButton#jrotActionButton:disabled {
background: #F2F5F7;
color: #8998A3;
border-color: #D5DEE5;
}
QTableWidget {
background: white;
alternate-background-color: #F5F8FA;
border: 1px solid #CAD5DD;
gridline-color: #D5DEE5;
selection-background-color: #087E91;
selection-color: white;
}
QHeaderView::section {
background: #EAF1F5;
color: #0B326C;
border: 0;
border-right: 1px solid #CAD5DD;
border-bottom: 1px solid #CAD5DD;
padding: 7px;
font-weight: 700;
}
QTabWidget#comparisonTabs::pane {
border: 1px solid #D5DEE5;
background: white;
}
QTabWidget#comparisonTabs QTabBar::tab {
min-width: 130px;
min-height: 34px;
padding: 5px 14px;
color: #5F6F7A;
background: #EDF2F5;
border: 1px solid #D5DEE5;
}
QTabWidget#comparisonTabs QTabBar::tab:selected {
color: #087E91;
background: white;
border-bottom: 3px solid #08A9B5;
}
"""
)
