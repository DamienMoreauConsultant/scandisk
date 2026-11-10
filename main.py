"""
Main entry point for the Disk Analyzer application.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

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
