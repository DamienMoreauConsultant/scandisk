"""
SQLite database management for the Disk Analyzer application.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from models import FileEntry, ScanResult
from utils.constants import DEFAULT_DB_PATH


class ScanDatabase:
    """Manages the SQLite database for scan results."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize the database.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
        
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create scans table (for storing scan metadata)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_path TEXT NOT NULL,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_size INTEGER DEFAULT 0,
                    total_files INTEGER DEFAULT 0,
                    total_directories INTEGER DEFAULT 0
                )
            """)
            
            # Create file_entries table (for storing individual file/directory info)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    parent_path TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    size INTEGER DEFAULT 0,
                    cumulative_size INTEGER DEFAULT 0,
                    creation_time TIMESTAMP,
                    modification_time TIMESTAMP,
                    extension TEXT DEFAULT '',
                    sha256 TEXT DEFAULT '',
                    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
                    UNIQUE(scan_id, path)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_entries_scan_id 
                ON file_entries(scan_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_entries_parent_path 
                ON file_entries(parent_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_entries_entry_type 
                ON file_entries(entry_type)
            """)
            
            conn.commit()
            
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
        
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            
    def save_scan_result(self, result: ScanResult) -> int:
        """
        Save a scan result to the database.
        
        Args:
            result: The ScanResult to save.
            
        Returns:
            The scan_id of the saved scan.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert scan metadata
            cursor.execute("""
                INSERT INTO scans (root_path, total_size, total_files, total_directories)
                VALUES (?, ?, ?, ?)
            """, (
                str(result.root_path),
                result.total_size,
                result.total_files,
                result.total_directories
            ))
            
            scan_id = cursor.lastrowid
            
            # Insert file entries
            for entry in result.entries:
                cursor.execute("""
                    INSERT INTO file_entries (
                        scan_id, path, name, parent_path, entry_type, 
                        size, cumulative_size, creation_time, modification_time, extension
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    str(entry.path),
                    entry.name,
                    str(entry.parent_path),
                    entry.entry_type,
                    entry.size,
                    entry.cumulative_size,
                    entry.creation_time.isoformat() if entry.creation_time else None,
                    entry.modification_time.isoformat() if entry.modification_time else None,
                    entry.extension
                ))
            
            conn.commit()
            return scan_id
            
    def load_scan_result(self, scan_id: int) -> Optional[ScanResult]:
        """
        Load a scan result from the database.
        
        Args:
            scan_id: The ID of the scan to load.
            
        Returns:
            ScanResult if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get scan metadata
            cursor.execute("""
                SELECT root_path, total_size, total_files, total_directories
                FROM scans WHERE id = ?
            """, (scan_id,))
            
            scan_row = cursor.fetchone()
            if not scan_row:
                return None
                
            result = ScanResult(
                root_path=Path(scan_row['root_path']),
                total_size=scan_row['total_size'],
                total_files=scan_row['total_files'],
                total_directories=scan_row['total_directories']
            )
            
            # Get file entries
            cursor.execute("""
                SELECT path, name, parent_path, entry_type, size, cumulative_size, 
                       creation_time, modification_time, extension
                FROM file_entries WHERE scan_id = ?
                ORDER BY path
            """, (scan_id,))
            
            for row in cursor.fetchall():
                entry = FileEntry(
                    path=Path(row['path']),
                    name=row['name'],
                    parent_path=Path(row['parent_path']),
                    entry_type=row['entry_type'],
                    size=row['size'],
                    cumulative_size=row['cumulative_size'],
                    creation_time=datetime.fromisoformat(row['creation_time']) if row['creation_time'] else None,
                    modification_time=datetime.fromisoformat(row['modification_time']) if row['modification_time'] else None,
                    extension=row['extension']
                )
                result.entries.append(entry)
                
            return result
            
    def get_scan_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all scans in the database.
        
        Returns:
            List of scan metadata dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, root_path, scan_time, total_size, total_files, total_directories
                FROM scans ORDER BY scan_time DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
            
    def delete_scan(self, scan_id: int):
        """
        Delete a scan and all its entries from the database.
        
        Args:
            scan_id: The ID of the scan to delete.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            conn.commit()
            
    def get_entries_by_parent(self, scan_id: int, parent_path: Path) -> List[FileEntry]:
        """
        Get all entries under a specific parent path.
        
        Args:
            scan_id: The scan ID.
            parent_path: The parent path to filter by.
            
        Returns:
            List of FileEntry objects.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT path, name, parent_path, entry_type, size, cumulative_size, 
                       creation_time, modification_time, extension
                FROM file_entries 
                WHERE scan_id = ? AND parent_path = ?
                ORDER BY entry_type DESC, name
            """, (scan_id, str(parent_path)))
            
            entries = []
            for row in cursor.fetchall():
                entry = FileEntry(
                    path=Path(row['path']),
                    name=row['name'],
                    parent_path=Path(row['parent_path']),
                    entry_type=row['entry_type'],
                    size=row['size'],
                    cumulative_size=row['cumulative_size'],
                    creation_time=datetime.fromisoformat(row['creation_time']) if row['creation_time'] else None,
                    modification_time=datetime.fromisoformat(row['modification_time']) if row['modification_time'] else None,
                    extension=row['extension']
                )
                entries.append(entry)
                
            return entries
            
    def get_entry_by_path(self, scan_id: int, path: Path) -> Optional[FileEntry]:
        """
        Get a specific entry by its path.
        
        Args:
            scan_id: The scan ID.
            path: The path of the entry.
            
        Returns:
            FileEntry if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT path, name, parent_path, entry_type, size, cumulative_size, 
                       creation_time, modification_time, extension
                FROM file_entries 
                WHERE scan_id = ? AND path = ?
            """, (scan_id, str(path)))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return FileEntry(
                path=Path(row['path']),
                name=row['name'],
                parent_path=Path(row['parent_path']),
                entry_type=row['entry_type'],
                size=row['size'],
                cumulative_size=row['cumulative_size'],
                creation_time=datetime.fromisoformat(row['creation_time']) if row['creation_time'] else None,
                modification_time=datetime.fromisoformat(row['modification_time']) if row['modification_time'] else None,
                extension=row['extension']
            )
            
    def update_sha256(self, scan_id: int, path: Path, sha256: str):
        """
        Update the SHA256 hash for a file entry.
        
        Args:
            scan_id: The scan ID.
            path: The path of the entry.
            sha256: The SHA256 hash value.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE file_entries 
                SET sha256 = ? 
                WHERE scan_id = ? AND path = ?
            """, (sha256, scan_id, str(path)))
            conn.commit()
            
    def find_duplicates_by_sha256(self, scan_id: int) -> Dict[str, List[Path]]:
        """
        Find duplicate files by SHA256 hash.
        
        Args:
            scan_id: The scan ID.
            
        Returns:
            Dictionary mapping SHA256 hash to list of file paths.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sha256, path 
                FROM file_entries 
                WHERE scan_id = ? AND sha256 != '' AND entry_type = 'File'
                ORDER BY sha256
            """, (scan_id,))
            
            duplicates = {}
            for row in cursor.fetchall():
                sha256 = row['sha256']
                path = Path(row['path'])
                if sha256 not in duplicates:
                    duplicates[sha256] = []
                duplicates[sha256].append(path)
                
            # Keep only hashes with multiple files
            return {k: v for k, v in duplicates.items() if len(v) > 1}
