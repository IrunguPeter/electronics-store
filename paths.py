"""Central path resolution.

Ensures the database, backups, and exports live in a stable, writable folder:

- When frozen into a Windows .exe (PyInstaller), data goes to the current
  user's Local AppData folder (`%LOCALAPPDATA%\\ElectronStore`). This is always
  writable, even when the program itself is installed to Program Files — which
  Windows locks against writes for normal users.
- When run from source (`python main.py`), data stays in the project folder.

When frozen with --onefile, __file__ points into a temporary extraction folder,
so we must NOT anchor on it.
"""

import os
import sys
from pathlib import Path


def app_dir():
    """Return the folder the user-facing data should live in."""
    if getattr(sys, "frozen", False):
        # Packaged exe: use a per-user writable data folder.
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if not base:
            # Fallback: next to the executable (dev/no-UserProfile cases).
            return Path(sys.executable).resolve().parent
        return Path(base) / "ElectronStore"
    # Run from source: keep data in the project folder.
    return Path(__file__).resolve().parent


BASE_DIR = app_dir()

DB_PATH = BASE_DIR / "store.db"
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"
LOG_FILE = BASE_DIR / "electronstore.log"


def ensure_dirs():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
