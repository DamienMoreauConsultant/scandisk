"""
Main entry point for the Disk Analyzer application.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Main function to launch the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Disk Analyzer")
    app.setOrganizationName("DamienMoreauConsultant")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
