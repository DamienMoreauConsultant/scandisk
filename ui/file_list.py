"""
File list widget for displaying files and directories.
"""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon, QAction
from models import FileEntry
from utils.file_utils import format_size, FILE_TYPE_DIRECTORY, FILE_TYPE_FILE
from utils.constants import FILE_TYPE_SYMLINK, FILE_TYPE_OTHER


class FileListWidget(QTreeWidget):
    """Widget for displaying a list of files and directories."""
    
    item_double_clicked = pyqtSignal(Path)
    
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Name", "Type", "Size", "Cumulative Size", "Modified"])
        self.setHeaderHidden(False)
        
        # Configure columns
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Icons
        self._icons = {
            FILE_TYPE_DIRECTORY: QIcon.fromTheme("folder"),
            FILE_TYPE_FILE: QIcon.fromTheme("text-x-generic"),
            FILE_TYPE_SYMLINK: QIcon.fromTheme("emblem-symbolic-link"),
            FILE_TYPE_OTHER: QIcon.fromTheme("file")
        }
        
        self._current_path: Optional[Path] = None
        
    def populate(self, entries: List[FileEntry], parent_path: Path):
        """
        Populate the list with file entries.
        
        Args:
            entries: List of FileEntry to display.
            parent_path: The parent directory path.
        """
        self.clear()
        self._current_path = parent_path
        
        # Sort entries: directories first (by cumulative size), then files (by size)
        dirs = [e for e in entries if e.entry_type == FILE_TYPE_DIRECTORY]
        files = [e for e in entries if e.entry_type != FILE_TYPE_DIRECTORY]
        
        dirs.sort(key=lambda x: x.cumulative_size, reverse=True)
        files.sort(key=lambda x: x.size, reverse=True)
        
        # Add directories
        for entry in dirs:
            self._add_entry(entry)
            
        # Add files
        for entry in files:
            self._add_entry(entry)
            
    def clear(self):
        """Clear the list."""
        super().clear()
        self._current_path = None
        
    def _add_entry(self, entry: FileEntry):
        """Add a single entry to the list."""
        item = QTreeWidgetItem()
        
        # Name
        item.setText(0, entry.name)
        
        # Type
        item.setText(1, entry.entry_type)
        
        # Size
        item.setText(2, format_size(entry.size))
        
        # Cumulative Size
        if entry.entry_type == FILE_TYPE_DIRECTORY:
            item.setText(3, format_size(entry.cumulative_size))
        else:
            item.setText(3, "")
            
        # Modified date
        if entry.modification_time:
            item.setText(4, entry.modification_time.strftime("%Y-%m-%d %H:%M"))
        else:
            item.setText(4, "Unknown")
            
        # Icon
        icon = self._icons.get(entry.entry_type, self._icons[FILE_TYPE_OTHER])
        if icon.isNull():
            icon = self._icons[FILE_TYPE_FILE]
        item.setIcon(0, icon)
        
        # Store path as data
        item.setData(0, Qt.ItemDataRole.UserRole, str(entry.path))
        
        # Set font for directories
        if entry.entry_type == FILE_TYPE_DIRECTORY:
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
            
        self.addTopLevelItem(item)
        
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click on an item."""
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str:
            self.item_double_clicked.emit(Path(path_str))
            
    def _show_context_menu(self, pos: QPoint):
        """Show context menu for the list."""
        item = self.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        
        # Open action
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._open_item(item))
        menu.addAction(open_action)
        
        # Properties action
        props_action = QAction("Properties", self)
        props_action.triggered.connect(lambda: self._show_properties(item))
        menu.addAction(props_action)
        
        menu.exec(self.viewport().mapToGlobal(pos))
        
    def _open_item(self, item: QTreeWidgetItem):
        """Open the selected item."""
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str:
            self.item_double_clicked.emit(Path(path_str))
            
    def _show_properties(self, item: QTreeWidgetItem):
        """Show properties for the selected item."""
        # TODO: Implement properties dialog
        pass
