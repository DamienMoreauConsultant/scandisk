"""
Recursive disk scanner for the Disk Analyzer application.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable
from models import FileEntry, ScanResult, DirectoryStats
from utils.file_utils import (
    get_file_type, get_file_extension, get_file_size,
    should_skip_dir, FILE_TYPE_DIRECTORY, FILE_TYPE_FILE
)
from utils.constants import MAX_DEPTH


class DiskScanner:
    """Scans directories recursively and collects file information."""
    
    def __init__(self):
        self._cancelled = False
        self._progress_callback: Optional[Callable[[int, int, Path], None]] = None
        self._current_entry: Optional[Path] = None
        
    def cancel(self):
        """Cancel the current scan."""
        self._cancelled = True
        
    def set_progress_callback(self, callback: Callable[[int, int, Path], None]):
        """Set a callback to report scan progress."""
        self._progress_callback = callback
        
    def scan(self, root_path: Path) -> ScanResult:
        """
        Scan a directory recursively and return scan results.
        
        Args:
            root_path: The root directory to scan.
            
        Returns:
            ScanResult containing all entries and statistics.
        """
        self._cancelled = False
        root_path = Path(root_path)
        
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        result = ScanResult(root_path=root_path)
        self._scan_directory(root_path, root_path, result, depth=0)
        
        return result
    
    def _scan_directory(
        self, 
        current_path: Path, 
        root_path: Path, 
        result: ScanResult, 
        depth: int = 0
    ):
        """
        Recursively scan a directory.
        
        Args:
            current_path: The current directory being scanned.
            root_path: The root directory of the scan.
            result: The ScanResult to populate.
            depth: Current recursion depth.
        """
        if self._cancelled:
            return
            
        if depth > MAX_DEPTH:
            return
            
        try:
            entries = list(current_path.iterdir())
        except (OSError, PermissionError):
            return
            
        dir_entries = []
        file_entries = []
        
        for entry in entries:
            if self._cancelled:
                return
                
            self._current_entry = entry
            
            # Skip hidden directories and excluded dirs
            if entry.is_dir() and should_skip_dir(entry):
                continue
                
            entry_type = get_file_type(entry)
            
            if entry_type == FILE_TYPE_DIRECTORY:
                dir_entries.append(entry)
            elif entry_type == FILE_TYPE_FILE:
                file_entries.append(entry)
            
            # Report progress
            if self._progress_callback:
                self._progress_callback(len(result.entries), len(result.entries) + len(entries), entry)
        
        # Process files first
        for entry in file_entries:
            file_entry = self._create_file_entry(entry, root_path)
            result.entries.append(file_entry)
            result.total_size += file_entry.size
            result.total_files += 1
        
        # Process directories recursively
        for entry in dir_entries:
            dir_entry = self._create_file_entry(entry, root_path)
            result.entries.append(dir_entry)
            result.total_directories += 1
            
            # Recursively scan subdirectory
            self._scan_directory(entry, root_path, result, depth + 1)
            
            # Update cumulative size for directory
            dir_entry.cumulative_size = self._calculate_cumulative_size(entry, result.entries)
        
        # Update cumulative size for root
        if current_path == root_path:
            root_entry = self._create_file_entry(root_path, root_path.parent)
            root_entry.cumulative_size = result.total_size
            result.entries.insert(0, root_entry)
    
    def _create_file_entry(self, path: Path, root_path: Path) -> FileEntry:
        """Create a FileEntry from a path."""
        try:
            stat = path.stat()
            creation_time = datetime.fromtimestamp(stat.st_ctime)
            modification_time = datetime.fromtimestamp(stat.st_mtime)
        except (OSError, PermissionError):
            creation_time = None
            modification_time = None
        
        return FileEntry(
            path=path,
            name=path.name,
            parent_path=path.parent,
            entry_type=get_file_type(path),
            size=get_file_size(path),
            cumulative_size=get_file_size(path),
            creation_time=creation_time,
            modification_time=modification_time,
            extension=get_file_extension(path)
        )
    
    def _calculate_cumulative_size(self, path: Path, entries: List[FileEntry]) -> int:
        """Calculate the cumulative size of a directory including all its contents."""
        total_size = 0
        for entry in entries:
            if str(entry.path).startswith(str(path)):
                total_size += entry.size
        return total_size
    
    def get_directory_stats(self, root_path: Path, entries: List[FileEntry]) -> List[DirectoryStats]:
        """
        Get statistics for each directory in the scan result.
        
        Args:
            root_path: The root directory.
            entries: List of FileEntry from scan result.
            
        Returns:
            List of DirectoryStats sorted by cumulative size (descending).
        """
        stats_dict = {}
        
        for entry in entries:
            if entry.entry_type == FILE_TYPE_DIRECTORY:
                if str(entry.path) not in stats_dict:
                    stats_dict[str(entry.path)] = DirectoryStats(
                        path=entry.path,
                        name=entry.name,
                        size=entry.size,
                        cumulative_size=entry.cumulative_size
                    )
                stats_dict[str(entry.path)].dir_count += 1
            elif entry.entry_type == FILE_TYPE_FILE:
                parent_path = entry.parent_path
                if str(parent_path) not in stats_dict:
                    stats_dict[str(parent_path)] = DirectoryStats(
                        path=parent_path,
                        name=parent_path.name,
                        size=0,
                        cumulative_size=0
                    )
                stats_dict[str(parent_path)].file_count += 1
                stats_dict[str(parent_path)].cumulative_size += entry.size
        
        # Convert to list and sort by cumulative size (descending)
        stats_list = list(stats_dict.values())
        stats_list.sort(key=lambda x: x.cumulative_size, reverse=True)
        
        return stats_list
