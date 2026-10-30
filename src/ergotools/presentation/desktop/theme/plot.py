"""Reviewed original PLOT stylesheet for its ported components.

Presentation theme layer. PLOT menus, tool rail, filter/demographic controls, map and
outcome/detail panels, with selected/disabled/pending/saved states.

Comparison gauge headings share the 13-pixel section-heading rule; their risk
subtitles share the compact legend's 12-pixel rule.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Preserve exact stylesheet bytes during
documentation changes.
"""

# Original Qt stylesheet for pLOT menus, tool rail, filter/demographic controls, map and
# outcome/detail panels, with selected/disabled/pending/saved states.
PLOT_STYLE = """
            QMenuBar { background: #F4F7F9; color: #0B326C; }
            QMenuBar::item:selected { background: #EAF7F8; }
            QMenu { background: #FFFFFF; color: #1B2933; border: 1px solid #D5DEE5; }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background: #EAF7F8; color: #0B326C; }
            QMenu::item:disabled { color: #71828F; }
            QLabel#toolRailTitle {
                color: #FFFFFF;
                background: #073E68;
                font-weight: 700;
                border: 0;
            }
            QDialog#plotDialog {
                background: #F4F7F9;
                color: #1B2933;
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
            QLabel#dialogSubtitle { color: #5F6F7A; }
            QGroupBox {
                background: #FFFFFF;
                border: 1px solid #D5DEE5;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 6px;
                color: #0B326C;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QGroupBox::indicator {
                width: 15px;
                height: 15px;
            }
            QGroupBox#plotToolRail {
                background: #073E68;
                color: #FFFFFF;
                border: 1px solid #073E68;
                border-radius: 6px;
            }
            QGroupBox#plotToolRail::title { color: #FFFFFF; background: #073E68; }
            QGroupBox#workerSubgroup {
                background: #F8FBFC;
                border: 1px solid #D5DEE5;
                border-radius: 5px;
                margin-top: 10px;
                color: #0B326C;
                font-weight: 700;
            }
            QGroupBox QLabel, QGroupBox QCheckBox, QGroupBox QRadioButton {
                color: #1B2933;
                font-weight: 400;
            }
            QLabel#summarytitle_label, QLabel#outcometitle_label {
                color: #0B326C;
                font-weight: 700;
            }
            QLabel#workplaceFilterSummary { color: #304652; font-weight: 600; }
            QFrame#workplacePlantScope {
                background: #EAF7F8;
                border: 1px solid #08A9B5;
                border-radius: 4px;
            }
            QFrame#workplaceScopeBlock { background: transparent; border: 0; }
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
            QLabel#demographicFieldTitle {
                color: #1B2933;
                font-weight: 700;
            }
            QLabel#workerAssignmentContext {
                color: #304652;
                background: #F4F7F9;
                border: 1px solid #D5DEE5;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: 600;
            }
            QLabel#jobAssignmentContext {
                color: #304652;
                background: #F4F7F9;
                border: 1px solid #D5DEE5;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#jobPositionNote { color: #506273; }
            QLabel#jobPositionStatus {
                color: #506273;
                font-weight: 700;
            }
            QLabel#jobPositionStatus[pending="true"] { color: #A65A00; }
            QLabel#jobPositionStatus[saved="true"] { color: #168A38; }
            QPushButton#plotAlphabetButton {
                padding: 0;
                border: 0;
                background: transparent;
                color: #5F7180;
                font-size: 9px;
                font-weight: 600;
            }
            QPushButton#plotAlphabetButton:hover {
                color: #0B326C;
                background: #DDF3F5;
                font-size: 13px;
            }
            QPushButton#plotAlphabetButton:checked {
                color: #FFFFFF;
                background: #0B326C;
                border-radius: 3px;
            }
            QPushButton#plotAlphabetButton:disabled {
                color: #C7D0D7;
            }
            QPushButton#locateWorkerButton, QPushButton#locateJobButton {
                min-height: 24px;
                max-height: 24px;
                padding: 0 14px;
                background: #EAF7F8;
                border: 1px solid #08A9B5;
                color: #0B326C;
                font-weight: 700;
            }
            QLabel#rangeFieldLabel, QLabel#plotDescription {
                color: #506273;
                font-size: 12px;
                font-weight: 600;
            }
            QTabWidget#plotDetailsTabs QTabBar::tab {
                min-height: 30px;
                padding: 2px 9px;
                color: #405866;
                background: #EDF2F5;
                border: 1px solid #BCC9D3;
                border-bottom-color: #D5DEE5;
                font-size: 12px;
                font-weight: 400;
            }
            QTabWidget#plotDetailsTabs QTabBar::tab:selected {
                color: #087E91;
                background: #FFFFFF;
                border-bottom: 3px solid #08A9B5;
                font-weight: 500;
            }
            QTabWidget#plotDetailsTabs QTabBar::tab:hover:!selected {
                background: #EAF7F8;
            }
            QLabel#outcomeSectionHeading {
                color: #0B326C;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#outcomeGaugeCaption, QLabel#outcomeRiskLabel {
                color: #0B326C;
                font-weight: 700;
                font-size: 13px;
            }
            QLabel#comparisonRiskLabel {
                color: #0B326C;
                font-weight: 700;
            }
            QLabel#comparisonGaugeCaption {
                color: #405462;
                font-weight: 600;
                font-size: 11px;
            }
            QLabel#outcomeRangeLabel {
                color: #304652;
                font-weight: 600;
                font-size: 13px;
            }
            QLabel#outcomeRangeLabel[compact="true"],
            QLabel#comparisonRiskLabel { font-size: 12px; }
            QFrame#riskClusterDivider { background: #D5DEE5; border: 0; }
            QWidget#outcomeSummaryPanel, QFrame#outcomeRiskCluster {
                background: #F8FBFC;
                border: 1px solid #D5DEE5;
                border-radius: 5px;
            }
            QWidget#outcomeSummaryPanel QLabel, QFrame#outcomeRiskCluster QLabel {
                border: 0;
                background: transparent;
            }
            QFrame#mapScopeFooter {
                background: #F4F7F9;
                border: 1px solid #D5DEE5;
                border-radius: 4px;
            }
            QLabel#mapScopeLabel { color: #405462; font-weight: 600; }
            QWidget#plotCanvasPanel { background: #FFFFFF; }
            QGraphicsView, QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox {
                background: #FFFFFF;
                color: #1B2933;
                border: 1px solid #BCC9D3;
                border-radius: 5px;
                min-height: 30px;
                selection-background-color: #087E91;
                selection-color: #FFFFFF;
            }
            QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox { padding: 0 8px; }
            QComboBox:focus,
            QLineEdit:focus,
            QDoubleSpinBox:focus,
            QSpinBox:focus {
            border: 2px solid #08A9B5;
            }
            QTreeWidget {
                background: #FFFFFF;
                color: #1B2933;
                border: 1px solid #BCC9D3;
                border-radius: 5px;
                alternate-background-color: #F7FAFB;
            }
            QTreeWidget::item { min-height: 29px; padding: 2px 5px; }
            QTreeWidget::item:selected { background: #087E91; color: #FFFFFF; }
            QHeaderView::section {
                background: #EAF2F6;
                color: #0B326C;
                border: 0;
                border-bottom: 1px solid #BCC9D3;
                padding: 7px;
                font-weight: 700;
            }
            QPushButton {
                min-height: 34px;
                background: #FFFFFF;
                color: #0B326C;
                border: 1px solid #9EB0BE;
                border-radius: 5px;
                padding: 0 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #EAF7F8; border-color: #08A9B5; }
            QPushButton:pressed { background: #D6ECEF; }
            QPushButton#primaryButton {
                background: #087E91;
                color: #FFFFFF;
                border-color: #087E91;
            }
            QPushButton#primaryButton:hover { background: #096D7C; }
            QPushButton#applyfilter_button {
                background: #087E91;
                color: #FFFFFF;
                border-color: #087E91;
            }
            QPushButton#plotToolButton {
                min-width: 63px;
                max-width: 63px;
                min-height: 63px;
                max-height: 63px;
                padding: 0;
                border: 0;
                border-bottom: 1px solid #D5DEE5;
                border-radius: 0;
                background: #FFFFFF;
            }
            QPushButton#plotToolButton:hover { background: #EAF7F8; }
            QPushButton#plotToolButton:pressed { background: #D6ECEF; }
            QToolButton#plotFilterTool {
                min-height: 42px;
                padding: 2px 12px;
                color: #49606F;
                background: #FFFFFF;
                border: 1px solid #BCC9D3;
                font-weight: 600;
            }
            QToolButton#plotFilterTool:hover { background: #EAF7F8; }
            QToolButton#plotFilterTool:checked {
                color: #087E91;
                background: #DDF3F5;
                border-color: #08A9B5;
            }
            QToolButton#plotRiskViewButton {
                min-height: 25px;
                padding: 2px 8px;
                color: #304652;
                background: #FFFFFF;
                border: 1px solid #AFC0CB;
                border-radius: 0;
                font-weight: 600;
            }
            QToolButton#plotRiskViewButton:hover { background: #EAF7F8; }
            QToolButton#plotRiskViewButton:checked {
                color: #087E91;
                background: #DDF3F5;
                border-color: #08A9B5;
            }
            QCheckBox, QRadioButton { color: #304652; spacing: 6px; }
            QCheckBox:disabled,
            QRadioButton:disabled,
            QLabel:disabled {
            color: #98A7B2;
            }
            QSplitter::handle { background: #E4EBEF; }
            QSplitter::handle:horizontal { width: 5px; }
            QStatusBar { background: #F4F7F9; color: #506273; border: 0; }
            QToolTip {
            background: #1B2933;
            color: white;
            border: 1px solid #0B326C;
            padding: 6px;
            }
        
"""

# Result buttons open scoped trees; checked tools expose navigation mode.
PLOT_STYLE += """
QToolButton#plotSelectionButton { background: white; color: #0B326C;
 border: 1px solid #BCC9D3; border-radius: 4px; padding: 4px 7px; text-align: left; }
QToolButton#plotSelectionButton:hover { background: #EDF7F8; border-color: #08A9B5; }
QToolButton#plotSelectionButton:disabled { color: #89969E; background: #F4F7F9; }
QPushButton#plotToolButton[compactZoom="true"] { min-width: 31px; max-width: 31px; }
QPushButton#plotToolButton[compactZoom="true"][zoomOut="true"] {
 min-width: 32px; max-width: 32px; }
QPushButton#plotToolButton:checked { background: #DDF3F5;
 border-bottom: 1px solid #08A9B5; }
QTreeWidget#plotResultTree::item { min-height: 29px; padding: 2px; }
"""
