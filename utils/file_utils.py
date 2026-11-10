"""
Utility functions for file operations.
"""

import os
import hashlib
from pathlib import Path
from .constants import FILE_TYPE_FILE, FILE_TYPE_DIRECTORY, FILE_TYPE_SYMLINK, FILE_TYPE_OTHER, SKIP_DIRS


def get_file_type(path: Path) -> str:
    """Determine the type of a file system entry."""
    try:
        if path.is_symlink():
            return FILE_TYPE_SYMLINK
        elif path.is_dir():
            return FILE_TYPE_DIRECTORY
        elif path.is_file():
            return FILE_TYPE_FILE
        else:
            return FILE_TYPE_OTHER
    except (OSError, PermissionError):
        return FILE_TYPE_OTHER


def get_file_extension(path: Path) -> str:
    """Get the file extension (including the dot)."""
    if path.is_dir():
        return ""
    return path.suffix.lower()


def get_file_size(path: Path) -> int:
    """Get the actual file size in bytes (not disk usage)."""
    try:
        if path.is_file():
            return path.stat().st_size
        return 0
    except (OSError, PermissionError):
        return 0


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def should_skip_dir(path: Path) -> bool:
    """Check if a directory should be skipped during scan."""
    return path.name in SKIP_DIRS or path.name.startswith('.')


def get_sha256(path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, PermissionError):
        return ""
