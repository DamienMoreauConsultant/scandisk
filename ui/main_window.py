"""
Main window for the Disk Analyzer application.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QProgressBar,
    QStackedWidget, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from pie_chart import PieChartWidget
from file_list import FileListWidget
from navigation import NavigationBar
from scanner import DiskScanner
from database import ScanDatabase
from models import ScanResult, FileEntry
from utils.file_utils import format_size
from utils.constants import (
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    FILE_TYPE_DIRECTORY, FILE_TYPE_FILE
)


class ScanWorker(QThread):
    """Worker thread for performing disk scans."""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(ScanResult)
    error = pyqtSignal(str)
    
    def __init__(self, root_path: Path):
        super().__init__()
        self.root_path = root_path
        self.scanner = DiskScanner()
        
    def run(self):
        """Run the scan in a separate thread."""
        try:
            self.scanner.set_progress_callback(self._on_progress)
            result = self.scanner.scan(self.root_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
            
    def _on_progress(self, current: int, total: int, path: Path):
        """Handle progress updates."""
        self.progress.emit(current, total, str(path))
        
    def cancel(self):
        """Cancel the scan."""
        self.scanner.cancel()


class MainWindow(QMainWindow):
    """Main window of the Disk Analyzer application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Analyzer")
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        self.db = ScanDatabase()
        self.current_scan_result: Optional[ScanResult] = None
        self.current_path: Optional[Path] = None
        self.scan_worker: Optional[ScanWorker] = None
        
        self._init_ui()
        self._load_recent_scans()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header with scan controls
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scan_button = QPushButton("📁 Select Directory to Scan")
        self.scan_button.setFont(QFont("Segoe UI", 10))
        self.scan_button.clicked.connect(self._on_scan_clicked)
        header_layout.addWidget(self.scan_button)
        
        self.cancel_button = QPushButton("❌ Cancel Scan")
        self.cancel_button.setFont(QFont("Segoe UI", 10))
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.setEnabled(False)
        header_layout.addWidget(self.cancel_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(header_frame)
        
        # Navigation bar
        self.nav_bar = NavigationBar()
        self.nav_bar.navigation_requested.connect(self._on_navigation_requested)
        self.nav_bar.setVisible(False)
        main_layout.addWidget(self.nav_bar)
        
        # Info panel (top left and right)
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # Left info panel
        self.left_info = QLabel("Select a directory to scan")
        self.left_info.setFont(QFont("Segoe UI", 11))
        self.left_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.left_info.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.left_info.setMinimumWidth(250)
        info_layout.addWidget(self.left_info, stretch=1)
        
        # Right info panel (pie chart placeholder)
        self.pie_chart = PieChartWidget()
        self.pie_chart.setMinimumWidth(300)
        self.pie_chart.setMinimumHeight(250)
        info_layout.addWidget(self.pie_chart, stretch=1)
        
        main_layout.addWidget(info_frame)
        
        # File list
        self.file_list = FileListWidget()
        self.file_list.item_double_clicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.file_list, stretch=1)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def _load_recent_scans(self):
        """Load recent scans from the database."""
        scans = self.db.get_scan_list()
        if scans:
            self.status_bar.showMessage(f"Found {len(scans)} previous scan(s)")
            
    def _on_scan_clicked(self):
        """Handle the scan button click."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Directory to Scan")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_dir = dialog.selectedFiles()[0]
            self._start_scan(Path(selected_dir))
            
    def _start_scan(self, root_path: Path):
        """Start a new scan."""
        # Clean up previous scan
        self.current_scan_result = None
        self.current_path = None
        self.file_list.clear()
        self.pie_chart.clear()
        self.left_info.setText(f"Scanning: {root_path}")
        
        # Setup progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.scan_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status_bar.showMessage(f"Scanning {root_path}...")
        
        # Create and start worker
        self.scan_worker = ScanWorker(root_path)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()
        
    def _on_scan_progress(self, current: int, total: int, path: str):
        """Handle scan progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"Scanning: {path} ({current}/{total})")
        QApplication.processEvents()
        
    def _on_scan_finished(self, result: ScanResult):
        """Handle scan completion."""
        self.current_scan_result = result
        self.current_path = result.root_path
        
        # Save to database
        scan_id = self.db.save_scan_result(result)
        
        # Update UI
        self._update_ui_for_path(result.root_path)
        self.nav_bar.set_root_path(result.root_path)
        self.nav_bar.set_current_path(result.root_path)
        self.nav_bar.setVisible(True)
        
        # Cleanup
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_bar.showMessage(f"Scan completed: {format_size(result.total_size)}")
        
        # Show success message
        QMessageBox.information(
            self, "Scan Complete",
            f"Scan completed successfully!\n\n"
            f"Total size: {format_size(result.total_size)}\n"
            f"Files: {result.total_files}\n"
            f"Directories: {result.total_directories}"
        )
        
    def _on_scan_error(self, error: str):
        """Handle scan errors."""
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_bar.showMessage("Scan failed")
        QMessageBox.critical(self, "Scan Error", f"An error occurred: {error}")
        
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait()
            self.progress_bar.setVisible(False)
            self.scan_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status_bar.showMessage("Scan cancelled")
            
    def _on_navigation_requested(self, path: Path):
        """Handle navigation requests."""
        if self.current_scan_result:
            self._update_ui_for_path(path)
            self.nav_bar.set_current_path(path)
            
    def _on_item_double_clicked(self, path: Path):
        """Handle double click on a file/directory in the list."""
        if self.current_scan_result:
            entry = self._find_entry_by_path(path)
            if entry and entry.entry_type == FILE_TYPE_DIRECTORY:
                self._update_ui_for_path(path)
                self.nav_bar.set_current_path(path)
                
    def _update_ui_for_path(self, path: Path):
        """Update the UI to show contents of the specified path."""
        if not self.current_scan_result:
            return
            
        self.current_path = path
        
        # Find all entries under this path
        entries = []
        for entry in self.current_scan_result.entries:
            if str(entry.parent_path) == str(path):
                entries.append(entry)
        
        # Update info panel (left)
        root_entry = self._find_entry_by_path(path)
        if root_entry:
            info_text = f"""
            <b>Directory:</b> {root_entry.name}<br>
            <b>Type:</b> {root_entry.entry_type}<br>
            <b>Size:</b> {format_size(root_entry.cumulative_size)}<br>
            <b>Path:</b> {root_entry.path}
            """
            self.left_info.setText(info_text)
        else:
            self.left_info.setText(f"Path: {path}")
            
        # Update pie chart (right)
        self._update_pie_chart(entries, path)
        
        # Update file list
        self.file_list.populate(entries, path)
        
    def _update_pie_chart(self, entries: list, parent_path: Path):
        """Update the pie chart with directory sizes."""
        # Group files at the root level
        file_size = sum(e.size for e in entries if e.entry_type == FILE_TYPE_FILE)
        dir_sizes = []
        dir_names = []
        
        for entry in entries:
            if entry.entry_type == FILE_TYPE_DIRECTORY:
                dir_sizes.append(entry.cumulative_size)
                dir_names.append(entry.name)
        
        # Add files as a separate category
        if file_size > 0:
            dir_sizes.append(file_size)
            dir_names.append("Files")
            
        self.pie_chart.set_data(dir_names, dir_sizes, str(parent_path))
        
    def _find_entry_by_path(self, path: Path) -> Optional[FileEntry]:
        """Find a file entry by its path."""
        if not self.current_scan_result:
            return None
            
        for entry in self.current_scan_result.entries:
            if str(entry.path) == str(path):
                return entry
        return None
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.scan_worker and self.scan_worker.isRunning():
            reply = QMessageBox.question(
                self, "Scan in Progress",
                "A scan is currently in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                self.scan_worker.cancel()
                self.scan_worker.wait()
                
        self.db.close()
        event.accept()
