"""Central path resolution.

Ensures the database, backups, and exports live in a stable folder whether the
app is run from source (python main.py) or frozen into a Windows .exe with
PyInstaller. When frozen with --onefile, __file__ points into a temporary
extraction folder, so we anchor on the directory containing the executable
instead.
"""

import sys
from pathlib import Path


def app_dir():
    """Return the folder the user-facing data should live in."""
    if getattr(sys, "frozen", False):
        # Packaged exe: use the directory that holds the .exe.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = app_dir()

DB_PATH = BASE_DIR / "store.db"
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"


def ensure_dirs():
    BACKUP_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)
