"""
Industrielles Dark Theme für den MED9.1 ECU Konfigurator.
Farb-Konzept: Anthrazit / Navy / Bernstein-Akzente – professionell, klar, gut lesbar.
"""

CATEGORY_ICONS = {
    "Sensoren": "📡",
    "Aktoren": "⚙",
    "Programmablauf": "🔄",
    "Sonstiges": "📋",
}

DARK_STYLE = """
/* ─── Basis ─────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0F1117;
    color: #E2E8F0;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

/* ─── Menüleiste ─────────────────────────────────────────── */
QMenuBar {
    background-color: #1A1F2E;
    color: #CBD5E1;
    border-bottom: 1px solid #2D3748;
    padding: 2px 8px;
}
QMenuBar::item:selected {
    background-color: #2D3748;
    border-radius: 4px;
}
QMenu {
    background-color: #1A1F2E;
    border: 1px solid #2D3748;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #1E3A5F;
    color: #60A5FA;
}
QMenu::separator {
    height: 1px;
    background-color: #2D3748;
    margin: 4px 8px;
}

/* ─── Toolbar ────────────────────────────────────────────── */
QToolBar {
    background-color: #1A1F2E;
    border-bottom: 1px solid #2D3748;
    padding: 4px 8px;
    spacing: 6px;
}
QToolBar::separator {
    background-color: #2D3748;
    width: 1px;
    margin: 4px 4px;
}

/* ─── Buttons ────────────────────────────────────────────── */
QPushButton#toolbarBtn {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton#toolbarBtn:hover {
    background-color: #1E3A5F;
    color: #60A5FA;
    border-color: #3B82F6;
}
QPushButton#toolbarBtnDanger {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton#toolbarBtnDanger:hover {
    background-color: #3B1212;
    color: #F87171;
    border-color: #EF4444;
}
QPushButton#applyBtn {
    background-color: #1E4D3C;
    color: #34D399;
    border: 1px solid #10B981;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
}
QPushButton#applyBtn:hover {
    background-color: #10B981;
    color: #0F1117;
}
QPushButton#welcomeBtn {
    background-color: #1E3A5F;
    color: #60A5FA;
    border: 1px solid #3B82F6;
    border-radius: 8px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#welcomeBtn:hover {
    background-color: #3B82F6;
    color: #FFFFFF;
}

/* ─── Banner ─────────────────────────────────────────────── */
QFrame#banner {
    background-color: #1A1F2E;
    border-bottom: 1px solid #2D3748;
}
QLabel#fileLabel {
    color: #94A3B8;
    font-size: 12px;
}
QLabel#changeLabel {
    font-size: 12px;
    padding-right: 8px;
}

/* ─── Navigation ──────────────────────────────────────────── */
QFrame#navFrame {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}
QLabel#navHeader {
    background-color: #1A1F2E;
    color: #64748B;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-bottom: 1px solid #2D3748;
    padding-left: 8px;
}
QTreeWidget#navTree {
    background-color: #111827;
    border: none;
    color: #CBD5E1;
    font-size: 13px;
}
QTreeWidget#navTree::item {
    padding: 6px 4px;
    border-radius: 4px;
}
QTreeWidget#navTree::item:hover {
    background-color: #1E293B;
    color: #93C5FD;
}
QTreeWidget#navTree::item:selected {
    background-color: #1E3A5F;
    color: #60A5FA;
}
QTreeWidget#navTree::branch {
    background-color: #111827;
}

/* ─── Tabs ───────────────────────────────────────────────── */
QTabWidget#mainTabs::pane {
    background-color: #0F1117;
    border: 1px solid #1F2937;
    border-top: none;
}
QTabBar::tab {
    background-color: #1A1F2E;
    color: #64748B;
    border: 1px solid #1F2937;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #0F1117;
    color: #60A5FA;
    border-color: #2D3748;
    border-bottom: 1px solid #0F1117;
}
QTabBar::tab:hover:!selected {
    background-color: #1E293B;
    color: #93C5FD;
}
QTabBar::close-button {
    subcontrol-position: right;
}

/* ─── Editor ─────────────────────────────────────────────── */
QFrame#editorLeft {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}
QLineEdit#searchBar {
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    margin-bottom: 4px;
}
QLineEdit#searchBar:focus {
    border-color: #3B82F6;
}

/* ─── Tabellen ───────────────────────────────────────────── */
QTableWidget#charList, QTableWidget#curveTable, QTableWidget#mapTable, QTableWidget#diffTable {
    background-color: #111827;
    color: #CBD5E1;
    border: none;
    gridline-color: #1F2937;
    selection-background-color: #1E3A5F;
    selection-color: #60A5FA;
    font-size: 12px;
}
QTableWidget#charList::item:hover {
    background-color: #1E293B;
}
QHeaderView::section {
    background-color: #1A1F2E;
    color: #64748B;
    border: none;
    border-bottom: 1px solid #2D3748;
    padding: 6px 8px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

/* ─── Detail ─────────────────────────────────────────────── */
QLabel#detailHeader {
    color: #60A5FA;
    font-size: 16px;
    font-weight: bold;
    padding: 4px 0;
}
QLabel#detailMeta {
    color: #64748B;
    font-size: 11px;
    line-height: 1.6;
}
QLabel#rawLabel {
    color: #475569;
    font-size: 11px;
    font-family: "Courier New", monospace;
}
QLabel#errorLabel {
    color: #F87171;
    font-size: 12px;
    background-color: #1F0A0A;
    padding: 8px;
    border-radius: 6px;
    border: 1px solid #7F1D1D;
}
QFrame#separator {
    color: #1F2937;
}
QScrollArea#detailScroll {
    border: none;
    background-color: transparent;
}

/* ─── Editor Cards ───────────────────────────────────────── */
QFrame#editorCard {
    background-color: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 12px;
}

/* ─── SpinBox ────────────────────────────────────────────── */
QDoubleSpinBox#valueSpin {
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}
QDoubleSpinBox#valueSpin:focus {
    border-color: #3B82F6;
}

/* ─── Statusbar ──────────────────────────────────────────── */
QStatusBar#statusBar {
    background-color: #1A1F2E;
    color: #64748B;
    border-top: 1px solid #2D3748;
    font-size: 11px;
}

/* ─── Scrollbars ─────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #0F1117;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background-color: #0F1117;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background-color: #334155;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ─── Welcome ─────────────────────────────────────────────── */
QLabel#welcomeTitle {
    color: #60A5FA;
    font-size: 28px;
    font-weight: bold;
    letter-spacing: -0.5px;
}
QLabel#welcomeSubtitle {
    color: #64748B;
    font-size: 14px;
    line-height: 1.6;
}
QLabel#welcomeCats {
    color: #334155;
    font-size: 13px;
    letter-spacing: 2px;
}
QLabel#welcomeWarning {
    color: #78350F;
    font-size: 11px;
    background-color: #1C1507;
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid #451A03;
}

/* ─── Splitter ───────────────────────────────────────────── */
QSplitter::handle {
    background-color: #1F2937;
    width: 1px;
}

/* ─── Dialoge ────────────────────────────────────────────── */
QDialog {
    background-color: #0F1117;
}
QMessageBox {
    background-color: #1A1F2E;
    color: #E2E8F0;
}
QMessageBox QPushButton {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 20px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background-color: #1E3A5F;
    color: #60A5FA;
}

/* ─── Progress ───────────────────────────────────────────── */
QProgressBar {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 4px;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 4px;
}
"""
