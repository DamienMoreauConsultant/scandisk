"""
Constants for the Disk Analyzer application.
"""

# File types
FILE_TYPE_FILE = "File"
FILE_TYPE_DIRECTORY = "Directory"
FILE_TYPE_SYMLINK = "Symbolic Link"
FILE_TYPE_OTHER = "Other"

# Size units
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]

# Colors for pie chart (rainbow palette, repeatable)
PIE_CHART_COLORS = [
    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
    "#FF9F40", "#8AC24A", "#607D8B", "#E91E63", "#00BCD4",
    "#FF5722", "#795548", "#9C27B0", "#2196F3", "#CDDC39",
    "#673AB7", "#F44336", "#009688", "#FFC107", "#3F51B5",
]

# Default database path
DEFAULT_DB_PATH = "scandisk.db"

# Scan settings
MAX_DEPTH = 100  # Prevent infinite recursion
SKIP_DIRS = [
    "node_modules", "__pycache__", ".git", ".svn", ".hg",
    "venv", "env", ".venv", "AppData", "Program Files",
    "Windows", "System Volume Information", "$RECYCLE.BIN"
]

# UI settings
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768
