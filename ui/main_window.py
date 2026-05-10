"""
MED9.1 Konfigurationstool - Hauptfenster
Industrielles Dark-Theme, strukturiert nach Sensoren / Aktoren / Programmablauf
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QLabel,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QPushButton, QFrame, QProgressBar, QToolBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QPixmap

from core.a2l_parser import A2LParser, CharType
from core.binary_handler import BinaryHandler, CharacteristicIO
from ui.characteristic_editor import CharacteristicEditor
from ui.hex_diff_dialog import HexDiffDialog
from ui.styles import DARK_STYLE, CATEGORY_ICONS


class LoadWorker(QThread):
    """Lädt A2L + BIN in einem separaten Thread."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, a2l_path, bin_path, base_addr):
        super().__init__()
        self.a2l_path = a2l_path
        self.bin_path = bin_path
        self.base_addr = base_addr
        self.parser = A2LParser()
        self.binary = BinaryHandler()

    def run(self):
        self.progress.emit("Lade A2L Beschreibungsdatei...")
        if not self.parser.parse_file(self.a2l_path):
            self.finished.emit(False, "A2L-Datei konnte nicht gelesen werden.")
            return

        stats = self.parser.stats()
        self.progress.emit(
            f"A2L OK: {stats['characteristics']} Characteristics, "
            f"{stats['measurements']} Measurements"
        )

        self.progress.emit("Lade Binary...")
        if not self.binary.load(self.bin_path, self.base_addr):
            self.finished.emit(False, "Binary konnte nicht geladen werden.")
            return

        self.progress.emit("Verknüpfe Daten...")
        self.finished.emit(True, "OK")


class MainWindow(QMainWindow):
    """Hauptfenster des MED9.1 Konfigurationstools."""

    APP_TITLE = "MED9.1 ECU Konfigurator"
    VERSION = "1.0.0"

    # Standardkategorien mit Reihenfolge
    CATEGORY_ORDER = ["Sensoren", "Aktoren", "Programmablauf", "Sonstiges"]

    def __init__(self):
        super().__init__()
        self.parser: A2LParser | None = None
        self.binary: BinaryHandler | None = None
        self.char_io: CharacteristicIO | None = None
        self._worker: LoadWorker | None = None

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self.setStyleSheet(DARK_STYLE)
        self.setWindowTitle(self.APP_TITLE)
        self.resize(1400, 900)
        self._show_welcome()

    # ── UI Setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Info-Banner
        self._banner = QFrame()
        self._banner.setObjectName("banner")
        self._banner.setFixedHeight(48)
        banner_layout = QHBoxLayout(self._banner)
        banner_layout.setContentsMargins(16, 0, 16, 0)

        self._file_label = QLabel("Keine Datei geöffnet")
        self._file_label.setObjectName("fileLabel")
        banner_layout.addWidget(self._file_label)

        banner_layout.addStretch()

        self._change_label = QLabel("")
        self._change_label.setObjectName("changeLabel")
        banner_layout.addWidget(self._change_label)

        layout.addWidget(self._banner)

        # Hauptbereich: Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")

        # Linke Seite: Navigationsbaum
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_frame.setFixedWidth(280)
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        nav_header = QLabel("  Navigation")
        nav_header.setObjectName("navHeader")
        nav_header.setFixedHeight(36)
        nav_layout.addWidget(nav_header)

        self._tree = QTreeWidget()
        self._tree.setObjectName("navTree")
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        nav_layout.addWidget(self._tree)

        splitter.addWidget(nav_frame)

        # Rechte Seite: Tabs
        right_frame = QFrame()
        right_frame.setObjectName("rightFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("mainTabs")
        self._tab_widget.setTabsClosable(False)
        right_layout.addWidget(self._tab_widget)

        splitter.addWidget(right_frame)
        splitter.setSizes([280, 1120])

        layout.addWidget(splitter)

        # Statusbar
        self._status = QStatusBar()
        self._status.setObjectName("statusBar")
        self.setStatusBar(self._status)
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setFixedWidth(200)
        self._status.addPermanentWidget(self._progress)

    def _setup_menu(self):
        menu = self.menuBar()
        menu.setObjectName("menuBar")

        # Datei-Menü
        file_menu = menu.addMenu("&Datei")

        open_act = QAction("&Öffnen (A2L + BIN)...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_files)
        file_menu.addAction(open_act)

        file_menu.addSeparator()

        self._save_act = QAction("&Speichern", self)
        self._save_act.setShortcut("Ctrl+S")
        self._save_act.setEnabled(False)
        self._save_act.triggered.connect(self._save_binary)
        file_menu.addAction(self._save_act)

        self._save_as_act = QAction("Speichern &als...", self)
        self._save_as_act.setEnabled(False)
        self._save_as_act.triggered.connect(self._save_binary_as)
        file_menu.addAction(self._save_as_act)

        file_menu.addSeparator()

        self._discard_act = QAction("Änderungen &verwerfen", self)
        self._discard_act.setEnabled(False)
        self._discard_act.triggered.connect(self._discard_changes)
        file_menu.addAction(self._discard_act)

        file_menu.addSeparator()
        quit_act = QAction("&Beenden", self)
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Ansicht-Menü
        view_menu = menu.addMenu("&Ansicht")

        diff_act = QAction("&Hex-Diff anzeigen...", self)
        diff_act.triggered.connect(self._show_diff)
        view_menu.addAction(diff_act)

        # Info-Menü
        info_menu = menu.addMenu("&Info")
        about_act = QAction("&Über...", self)
        about_act.triggered.connect(self._show_about)
        info_menu.addAction(about_act)

    def _setup_toolbar(self):
        tb = QToolBar("Hauptwerkzeuge")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))

        open_btn = QPushButton("📂  Öffnen")
        open_btn.setObjectName("toolbarBtn")
        open_btn.clicked.connect(self._open_files)
        tb.addWidget(open_btn)

        tb.addSeparator()

        self._save_btn = QPushButton("💾  Speichern")
        self._save_btn.setObjectName("toolbarBtn")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_binary)
        tb.addWidget(self._save_btn)

        self._diff_btn = QPushButton("🔍  Hex-Diff")
        self._diff_btn.setObjectName("toolbarBtn")
        self._diff_btn.setEnabled(False)
        self._diff_btn.clicked.connect(self._show_diff)
        tb.addWidget(self._diff_btn)

        tb.addSeparator()

        self._discard_btn = QPushButton("↩  Verwerfen")
        self._discard_btn.setObjectName("toolbarBtnDanger")
        self._discard_btn.setEnabled(False)
        self._discard_btn.clicked.connect(self._discard_changes)
        tb.addWidget(self._discard_btn)

        self.addToolBar(tb)

    # ── Datei laden ──────────────────────────────────────────────────────────

    def _open_files(self):
        """Dialog zum Öffnen von A2L + BIN."""
        a2l_path, _ = QFileDialog.getOpenFileName(
            self, "A2L Beschreibungsdatei öffnen",
            "", "A2L Dateien (*.a2l *.A2L);;Alle Dateien (*)"
        )
        if not a2l_path:
            return

        bin_path, _ = QFileDialog.getOpenFileName(
            self, "Binary öffnen",
            os.path.dirname(a2l_path),
            "Binary Dateien (*.bin *.BIN *.hex *.mot);;Alle Dateien (*)"
        )
        if not bin_path:
            return

        # Basisadresse ermitteln (aus A2L oder Standard MED9.x)
        base_addr = 0x80000000  # Typisch für Bosch MED9.x

        self._load_files(a2l_path, bin_path, base_addr)

    def _load_files(self, a2l_path, bin_path, base_addr):
        self._status.showMessage("Lade Dateien...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        self._worker = LoadWorker(a2l_path, bin_path, base_addr)
        self._worker.progress.connect(self._on_load_progress)
        self._worker.finished.connect(
            lambda ok, msg: self._on_load_finished(ok, msg, self._worker)
        )
        self._worker.start()

    def _on_load_progress(self, msg: str):
        self._status.showMessage(msg)

    def _on_load_finished(self, ok: bool, msg: str, worker: LoadWorker):
        self._progress.setVisible(False)
        if not ok:
            QMessageBox.critical(self, "Ladefehler", msg)
            self._status.showMessage(f"Fehler: {msg}")
            return

        self.parser = worker.parser
        self.binary = worker.binary
        self.char_io = CharacteristicIO(
            self.binary,
            self.parser.compu_methods,
            self.parser.record_layouts
        )

        stats = self.parser.stats()
        self._file_label.setText(
            f"  📄 {os.path.basename(worker.a2l_path)}  +  "
            f"🔧 {os.path.basename(worker.bin_path)}  │  "
            f"{stats['characteristics']:,} Characteristics  │  "
            f"{stats['measurements']:,} Measurements"
        )

        self._build_navigation()
        self._save_act.setEnabled(True)
        self._save_as_act.setEnabled(True)
        self._discard_act.setEnabled(True)
        self._save_btn.setEnabled(True)
        self._diff_btn.setEnabled(True)
        self._discard_btn.setEnabled(True)

        self._status.showMessage(
            f"Geladen: {stats['characteristics']} Characteristics in "
            f"{len(self.parser.get_categories())} Kategorien"
        )

    # ── Navigation aufbauen ──────────────────────────────────────────────────

    def _build_navigation(self):
        self._tree.clear()
        self._tab_widget.clear()
        categories = self.parser.get_categories()

        for cat in self.CATEGORY_ORDER:
            if cat not in categories:
                continue

            icon = CATEGORY_ICONS.get(cat, "📋")
            cat_item = QTreeWidgetItem(self._tree, [f"{icon}  {cat}"])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "name": cat})
            font = cat_item.font(0)
            font.setBold(True)
            font.setPointSize(10)
            cat_item.setFont(0, font)

            for sub, chars in sorted(categories[cat].items()):
                sub_item = QTreeWidgetItem(cat_item, [f"  {sub}  ({len(chars)})"])
                sub_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "subcategory",
                    "category": cat,
                    "subcategory": sub,
                    "chars": chars
                })

        self._tree.expandAll()

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data["type"] == "subcategory":
            self._open_subcategory_tab(
                data["category"], data["subcategory"], data["chars"]
            )

    def _open_subcategory_tab(self, category: str, subcategory: str, chars: list):
        """Öffnet einen Tab für eine Subkategorie."""
        tab_title = f"{subcategory}"

        # Prüfen ob Tab bereits offen
        for i in range(self._tab_widget.count()):
            if self._tab_widget.tabText(i) == tab_title:
                self._tab_widget.setCurrentIndex(i)
                return

        # Neuen Tab erstellen
        editor = CharacteristicEditor(
            characteristics=chars,
            char_io=self.char_io,
            on_change=self._on_value_changed
        )
        idx = self._tab_widget.addTab(editor, tab_title)
        self._tab_widget.setCurrentIndex(idx)
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._tab_widget.removeTab)

    # ── Änderungen verwalten ─────────────────────────────────────────────────

    def _on_value_changed(self):
        """Wird aufgerufen wenn ein Wert geändert wurde."""
        if self.binary:
            n = self.binary.change_count
            self._change_label.setText(f"⚡ {n} Byte{'s' if n != 1 else ''} geändert")
            self._change_label.setStyleSheet("color: #F59E0B; font-weight: bold;")

    def _save_binary(self):
        if not self.binary:
            return
        if self.binary.save():
            n = self.binary.change_count
            self._change_label.setText("")
            self._status.showMessage("Binary gespeichert.")
            QMessageBox.information(self, "Gespeichert",
                "Binary wurde erfolgreich gespeichert.\n"
                "Ein Backup (.bak) wurde angelegt.")
        else:
            QMessageBox.critical(self, "Fehler", "Speichern fehlgeschlagen.")

    def _save_binary_as(self):
        if not self.binary:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Binary speichern als",
            "", "Binary Dateien (*.bin);;Alle Dateien (*)"
        )
        if path:
            if self.binary.save_as(path):
                self._status.showMessage(f"Gespeichert als: {path}")
            else:
                QMessageBox.critical(self, "Fehler", "Speichern fehlgeschlagen.")

    def _discard_changes(self):
        if not self.binary:
            return
        n = self.binary.change_count
        if n == 0:
            return
        reply = QMessageBox.question(
            self, "Änderungen verwerfen",
            f"Alle {n} geänderten Bytes zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.binary.discard_changes()
            self._change_label.setText("")
            self._status.showMessage("Änderungen verworfen.")
            # Alle offenen Tabs neu laden
            for i in range(self._tab_widget.count()):
                widget = self._tab_widget.widget(i)
                if isinstance(widget, CharacteristicEditor):
                    widget.reload_values()

    def _show_diff(self):
        if not self.binary:
            return
        diffs = self.binary.get_diff()
        dlg = HexDiffDialog(diffs, self)
        dlg.exec()

    # ── Sonstiges ────────────────────────────────────────────────────────────

    def _show_welcome(self):
        welcome = WelcomeWidget()
        welcome.open_requested.connect(self._open_files)
        self._tab_widget.addTab(welcome, "Start")

    def _show_about(self):
        QMessageBox.about(
            self, f"Über {self.APP_TITLE}",
            f"<b>{self.APP_TITLE}</b><br>"
            f"Version {self.VERSION}<br><br>"
            "ECU-Konfigurationstool für Bosch MED9.1<br>"
            "Unterstützt: Skalare, Kennlinien, Kennfelder<br><br>"
            "Format: ASAP2 (A2L) + Binary<br>"
            "<small>Verwendung auf eigene Gefahr.</small>"
        )

    def closeEvent(self, event):
        if self.binary and self.binary.has_changes:
            reply = QMessageBox.question(
                self, "Ungespeicherte Änderungen",
                "Es gibt ungespeicherte Änderungen. Wirklich beenden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()


class WelcomeWidget(QWidget):
    """Willkommensbildschirm."""
    open_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        title = QLabel("MED9.1 ECU Konfigurator")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Öffne eine A2L-Beschreibungsdatei zusammen mit der zugehörigen Binary,\n"
            "um Steuergeräteparameter zu konfigurieren."
        )
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        cats = QLabel("Sensoren  ·  Aktoren  ·  Programmablauf")
        cats.setObjectName("welcomeCats")
        cats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cats)

        btn = QPushButton("📂  A2L + Binary öffnen")
        btn.setObjectName("welcomeBtn")
        btn.setFixedWidth(260)
        btn.setFixedHeight(48)
        btn.clicked.connect(self.open_requested)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        warning = QLabel(
            "⚠  Vor dem Flashen: Backup der Original-Binary erstellen.\n"
            "Dieses Tool ist für erfahrene Anwender gedacht."
        )
        warning.setObjectName("welcomeWarning")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning)
