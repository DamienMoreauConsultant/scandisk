"""
Data models for the Disk Analyzer application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List


@dataclass
class FileEntry:
    """Represents a file or directory entry."""
    path: Path
    name: str
    parent_path: Path
    entry_type: str
    size: int = 0
    cumulative_size: int = 0
    creation_time: Optional[datetime] = None
    modification_time: Optional[datetime] = None
    extension: str = ""
    
    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)
        if isinstance(self.parent_path, str):
            self.parent_path = Path(self.parent_path)


@dataclass
class ScanResult:
    """Represents the result of a directory scan."""
    root_path: Path
    total_size: int = 0
    total_files: int = 0
    total_directories: int = 0
    entries: List[FileEntry] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.root_path, str):
            self.root_path = Path(self.root_path)


@dataclass
class DirectoryStats:
    """Statistics for a directory."""
    path: Path
    name: str
    size: int
    cumulative_size: int
    file_count: int = 0
    dir_count: int = 0
    
    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)
