"""
CharacteristicEditor: Zeigt und editiert Skalare, Kennlinien und Kennfelder.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QSplitter, QFrame, QComboBox, QDoubleSpinBox, QPushButton,
    QHeaderView, QAbstractItemView, QScrollArea, QGridLayout, QSizePolicy,
    QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush

from core.a2l_parser import Characteristic, CharType
from core.binary_handler import CharacteristicIO


class CharacteristicEditor(QWidget):
    """Haupt-Editor für eine Gruppe von Characteristics."""

    value_changed = pyqtSignal()

    def __init__(self, characteristics: list, char_io: CharacteristicIO, on_change=None):
        super().__init__()
        self.chars = sorted(characteristics, key=lambda c: c.name)
        self.char_io = char_io
        self._on_change = on_change
        self._current_char: Characteristic | None = None
        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Linke Seite: Charakteristik-Liste
        left = QFrame()
        left.setObjectName("editorLeft")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)

        search_bar = QLineEdit()
        search_bar.setObjectName("searchBar")
        search_bar.setPlaceholderText("🔍  Suchen...")
        search_bar.textChanged.connect(self._filter_list)
        left_layout.addWidget(search_bar)

        self._list = QTableWidget()
        self._list.setObjectName("charList")
        self._list.setColumnCount(3)
        self._list.setHorizontalHeaderLabels(["Name", "Typ", "Einheit"])
        self._list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._list.setColumnWidth(1, 60)
        self._list.setColumnWidth(2, 60)
        self._list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.verticalHeader().setVisible(False)
        self._list.itemSelectionChanged.connect(self._on_list_selection)
        left_layout.addWidget(self._list)

        left.setFixedWidth(320)

        # Rechte Seite: Detailansicht
        self._detail = DetailPanel(self.char_io, self._on_change)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self._detail)
        layout.addWidget(splitter)

    def _populate_list(self, filter_text=""):
        self._list.setRowCount(0)
        ft = filter_text.lower()
        for char in self.chars:
            if ft and ft not in char.name.lower() and ft not in char.long_id.lower():
                continue
            row = self._list.rowCount()
            self._list.insertRow(row)

            name_item = QTableWidgetItem(char.name)
            name_item.setData(Qt.ItemDataRole.UserRole, char)
            name_item.setToolTip(char.long_id)
            self._list.setItem(row, 0, name_item)

            type_colors = {
                CharType.VALUE: "#60A5FA",
                CharType.CURVE: "#34D399",
                CharType.MAP: "#F59E0B",
                CharType.VAL_BLK: "#A78BFA",
            }
            type_item = QTableWidgetItem(char.char_type.value[:3])
            type_item.setForeground(QBrush(QColor(type_colors.get(char.char_type, "#9CA3AF"))))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.setItem(row, 1, type_item)

            unit_item = QTableWidgetItem(char.unit or "-")
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.setItem(row, 2, unit_item)

    def _filter_list(self, text):
        self._populate_list(text)

    def _on_list_selection(self):
        rows = self._list.selectedItems()
        if not rows:
            return
        char = self._list.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if char:
            self._current_char = char
            self._detail.show_characteristic(char)

    def reload_values(self):
        if self._current_char:
            self._detail.show_characteristic(self._current_char)


class DetailPanel(QWidget):
    """Zeigt Details und Editor für eine einzelne Characteristic."""

    def __init__(self, char_io: CharacteristicIO, on_change=None):
        super().__init__()
        self.char_io = char_io
        self._on_change = on_change
        self._current_char: Characteristic | None = None
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        # Header
        self._header = QLabel("Wähle eine Characteristic aus der Liste")
        self._header.setObjectName("detailHeader")
        self._layout.addWidget(self._header)

        self._meta = QLabel("")
        self._meta.setObjectName("detailMeta")
        self._meta.setWordWrap(True)
        self._layout.addWidget(self._meta)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        self._layout.addWidget(sep)

        # Scroll-Bereich für den eigentlichen Editor
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("detailScroll")
        self._editor_container = QWidget()
        self._editor_layout = QVBoxLayout(self._editor_container)
        self._editor_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._editor_container)
        self._layout.addWidget(scroll)

    def show_characteristic(self, char: Characteristic):
        self._current_char = char

        # Header aktualisieren
        self._header.setText(char.name)
        self._meta.setText(
            f"{char.long_id}\n"
            f"Adresse: 0x{char.address:08X}  │  "
            f"Typ: {char.char_type.value}  │  "
            f"Einheit: {char.unit or '–'}  │  "
            f"Bereich: [{char.lower_limit} … {char.upper_limit}]"
        )

        # Alten Editor entfernen
        for i in reversed(range(self._editor_layout.count())):
            w = self._editor_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Passenden Editor anzeigen
        if char.char_type == CharType.VALUE:
            self._show_scalar_editor(char)
        elif char.char_type == CharType.CURVE:
            self._show_curve_editor(char)
        elif char.char_type == CharType.MAP:
            self._show_map_editor(char)
        else:
            lbl = QLabel(f"Typ '{char.char_type.value}' wird derzeit nicht unterstützt.")
            lbl.setObjectName("detailMeta")
            self._editor_layout.addWidget(lbl)

    # ── Scalar ───────────────────────────────────────────────────────────────

    def _show_scalar_editor(self, char: Characteristic):
        rv = self.char_io.read_scalar(char)

        frame = QFrame()
        frame.setObjectName("editorCard")
        layout = QGridLayout(frame)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Physikalischer Wert:"), 0, 0)

        spin = QDoubleSpinBox()
        spin.setObjectName("valueSpin")
        spin.setDecimals(4)
        spin.setRange(char.lower_limit, char.upper_limit)
        spin.setSuffix(f"  {char.unit}" if char.unit else "")
        if rv:
            spin.setValue(rv.phys)
        spin.setFixedWidth(200)
        layout.addWidget(spin, 0, 1)

        if rv:
            raw_lbl = QLabel(f"RAW: {int(rv.raw) if isinstance(rv.raw, float) and rv.raw == int(rv.raw) else rv.raw}")
            raw_lbl.setObjectName("rawLabel")
            layout.addWidget(raw_lbl, 0, 2)

        btn = QPushButton("✔  Übernehmen")
        btn.setObjectName("applyBtn")
        btn.clicked.connect(lambda: self._write_scalar(char, spin, raw_lbl if rv else None))
        layout.addWidget(btn, 1, 0, 1, 2)

        self._editor_layout.addWidget(frame)

    def _write_scalar(self, char, spin, raw_lbl):
        val = spin.value()
        if self.char_io.write_scalar(char, val):
            # Rohen Wert aktualisieren
            rv = self.char_io.read_scalar(char)
            if rv and raw_lbl:
                raw_lbl.setText(f"RAW: {int(rv.raw)}")
            if self._on_change:
                self._on_change()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Fehler", f"Schreiben fehlgeschlagen für {char.name}.\nAdresse 0x{char.address:08X} außerhalb der Binary?")

    # ── Curve ─────────────────────────────────────────────────────────────────

    def _show_curve_editor(self, char: Characteristic):
        data = self.char_io.read_curve(char)

        if data is None:
            lbl = QLabel(f"Kennlinie konnte nicht gelesen werden.\n(Adresse: 0x{char.address:08X})")
            lbl.setObjectName("errorLabel")
            self._editor_layout.addWidget(lbl)
            return

        frame = QFrame()
        frame.setObjectName("editorCard")
        layout = QVBoxLayout(frame)

        info = QLabel(f"Kennlinie: {data['n']} Stützstellen")
        info.setObjectName("rawLabel")
        layout.addWidget(info)

        table = QTableWidget(2, data["n"])
        table.setObjectName("curveTable")
        table.setVerticalHeaderLabels(["X (Achse)", "Y (Wert)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setFixedHeight(100)

        for j in range(data["n"]):
            x_item = QTableWidgetItem(f"{data['x_phys'][j]:.3f}")
            x_item.setFlags(x_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            x_item.setBackground(QColor("#1E3A5F"))
            table.setItem(0, j, x_item)

            y_item = QTableWidgetItem(f"{data['y_phys'][j]:.3f}")
            table.setItem(1, j, y_item)

        layout.addWidget(table)

        unit_lbl = QLabel(f"Einheit Y: {char.unit or '–'}")
        unit_lbl.setObjectName("rawLabel")
        layout.addWidget(unit_lbl)

        btn = QPushButton("✔  Werte übernehmen")
        btn.setObjectName("applyBtn")
        btn.clicked.connect(lambda: self._write_curve(char, table, data["n"]))
        layout.addWidget(btn)

        self._editor_layout.addWidget(frame)

    def _write_curve(self, char, table, n):
        y_phys = []
        try:
            for j in range(n):
                item = table.item(1, j)
                y_phys.append(float(item.text()))
        except ValueError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Fehler", "Ungültige Zahlenwerte in der Tabelle.")
            return

        if self.char_io.write_curve_y(char, y_phys):
            if self._on_change:
                self._on_change()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Fehler", "Schreiben fehlgeschlagen.")

    # ── Map ───────────────────────────────────────────────────────────────────

    def _show_map_editor(self, char: Characteristic):
        data = self.char_io.read_map(char)

        if data is None:
            lbl = QLabel(f"Kennfeld konnte nicht gelesen werden.\n(Adresse: 0x{char.address:08X})")
            lbl.setObjectName("errorLabel")
            self._editor_layout.addWidget(lbl)
            return

        nx, ny = data["nx"], data["ny"]
        frame = QFrame()
        frame.setObjectName("editorCard")
        layout = QVBoxLayout(frame)

        info = QLabel(f"Kennfeld: {nx} × {ny}  (Einheit: {char.unit or '–'})")
        info.setObjectName("rawLabel")
        layout.addWidget(info)

        # Tabelle: Zeilen = X-Achse, Spalten = Y-Achse
        table = QTableWidget(nx, ny)
        table.setObjectName("mapTable")

        # Spaltenköpfe = Y-Achse
        y_headers = [f"{v:.2f}" for v in data["y_phys"]]
        x_headers = [f"{v:.2f}" for v in data["x_phys"]]
        table.setHorizontalHeaderLabels(y_headers)
        table.setVerticalHeaderLabels(x_headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        z = data["z_phys"]
        zmin = min(min(row) for row in z)
        zmax = max(max(row) for row in z)
        zrange = zmax - zmin if zmax != zmin else 1

        for i in range(nx):
            for j in range(ny):
                val = z[i][j]
                item = QTableWidgetItem(f"{val:.3f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Heat-Map-Färbung
                ratio = (val - zmin) / zrange
                r = int(30 + ratio * 180)
                b = int(210 - ratio * 180)
                item.setBackground(QColor(r, 50, b))
                table.setItem(i, j, item)

        layout.addWidget(table)

        btn = QPushButton("✔  Kennfeld übernehmen")
        btn.setObjectName("applyBtn")
        btn.clicked.connect(lambda: self._write_map(char, table, nx, ny))
        layout.addWidget(btn)

        self._editor_layout.addWidget(frame)

    def _write_map(self, char, table, nx, ny):
        from core.binary_handler import CharacteristicIO
        from core.a2l_parser import DataType

        z_phys = []
        try:
            for i in range(nx):
                for j in range(ny):
                    item = table.item(i, j)
                    z_phys.append(float(item.text()))
        except (ValueError, AttributeError):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Fehler", "Ungültige Werte im Kennfeld.")
            return

        dtype = self.char_io._get_dtype(char)
        compu = self.char_io._get_compu(char)
        from core.a2l_parser import DataType
        ax_dtype = DataType.UWORD
        rl = self.char_io.record_layouts.get(char.record_layout)
        if rl and rl.axis_pts_x:
            ax_dtype = rl.axis_pts_x[1]
        ay_dtype = DataType.UWORD
        if rl and rl.axis_pts_y:
            ay_dtype = rl.axis_pts_y[1]

        nx_s = char.axis_x.max_axis_points if char.axis_x else nx
        ny_s = char.axis_y.max_axis_points if char.axis_y else ny
        addr = char.address + ax_dtype.size * nx_s + ay_dtype.size * ny_s

        z_raw = [compu.inverse(v) if compu else v for v in z_phys]
        if self.char_io.binary.write_array(addr, dtype, z_raw):
            if self._on_change:
                self._on_change()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Fehler", "Schreiben fehlgeschlagen.")
