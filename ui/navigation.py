"""
Navigation bar for browsing through directories.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class NavigationBar(QWidget):
    """Navigation bar for browsing directories."""
    
    navigation_requested = pyqtSignal(Path)
    
    def __init__(self):
        super().__init__()
        self._root_path: Optional[Path] = None
        self._current_path: Optional[Path] = None
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setIcon(QIcon.fromTheme("go-previous"))
        self.back_button.setFont(QFont("Segoe UI", 9))
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setEnabled(False)
        layout.addWidget(self.back_button)
        
        # Forward button (placeholder for future use)
        # self.forward_button = QPushButton("→ Forward")
        # self.forward_button.setIcon(QIcon.fromTheme("go-next"))
        # self.forward_button.setFont(QFont("Segoe UI", 9))
        # self.forward_button.setEnabled(False)
        # layout.addWidget(self.forward_button)
        
        # Path label
        self.path_label = QLabel("")
        self.path_label.setFont(QFont("Segoe UI", 10))
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.path_label, stretch=1)
        
        # Home button
        self.home_button = QPushButton("🏠 Home")
        self.home_button.setFont(QFont("Segoe UI", 9))
        self.home_button.clicked.connect(self._on_home_clicked)
        self.home_button.setEnabled(False)
        layout.addWidget(self.home_button)
        
    def set_root_path(self, path: Path):
        """Set the root path of the scan."""
        self._root_path = path
        self._current_path = path
        self._update_buttons()
        
    def set_current_path(self, path: Path):
        """Set the current path."""
        self._current_path = path
        self.path_label.setText(str(path))
        self._update_buttons()
        
    def _update_buttons(self):
        """Update button states based on current path."""
        if not self._root_path or not self._current_path:
            self.back_button.setEnabled(False)
            self.home_button.setEnabled(False)
            return
            
        self.back_button.setEnabled(self._current_path != self._root_path)
        self.home_button.setEnabled(True)
        
    def _on_back_clicked(self):
        """Handle back button click."""
        if self._current_path and self._current_path != self._root_path:
            new_path = self._current_path.parent
            self.navigation_requested.emit(new_path)
            
    def _on_home_clicked(self):
        """Handle home button click."""
        if self._root_path:
            self.navigation_requested.emit(self._root_path)
