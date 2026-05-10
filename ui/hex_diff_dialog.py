"""
HexDiffDialog: Zeigt alle geänderten Bytes vor dem Speichern.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont


class HexDiffDialog(QDialog):
    """Zeigt alle geänderten Bytes in einer übersichtlichen Tabelle."""

    def __init__(self, diffs: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hex-Diff – Ausstehende Änderungen")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QVBoxLayout(self)

        header = QLabel(f"{len(diffs)} Byte{'s' if len(diffs) != 1 else ''} geändert")
        header.setObjectName("detailHeader")
        layout.addWidget(header)

        table = QTableWidget(len(diffs), 4)
        table.setObjectName("diffTable")
        table.setHorizontalHeaderLabels(["Adresse", "Original (HEX)", "Neu (HEX)", "Delta"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        mono = QFont("Courier New", 10)

        for row, (addr, orig, new) in enumerate(diffs):
            addr_item = QTableWidgetItem(f"0x{addr:08X}")
            addr_item.setFont(mono)
            addr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, addr_item)

            orig_item = QTableWidgetItem(f"{orig:02X}")
            orig_item.setFont(mono)
            orig_item.setForeground(QBrush(QColor("#F87171")))
            orig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, orig_item)

            new_item = QTableWidgetItem(f"{new:02X}")
            new_item.setFont(mono)
            new_item.setForeground(QBrush(QColor("#34D399")))
            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, new_item)

            delta = new - orig
            delta_item = QTableWidgetItem(f"{delta:+d}")
            delta_item.setFont(mono)
            delta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 3, delta_item)

        layout.addWidget(table)

        btn = QPushButton("Schließen")
        btn.setObjectName("applyBtn")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
