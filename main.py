#!/usr/bin/env python3
"""
MED9.1 ECU Konfigurator
Einstiegspunkt der Applikation.

Starten mit:
    python main.py
"""

import sys
import os

# Sicherstellen dass das Projektverzeichnis im Pfad ist
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # High-DPI Support
    app.setApplicationName("MED9.1 ECU Konfigurator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ECU Tools")

    # Basis-Font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
