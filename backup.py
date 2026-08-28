import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

import paths
from db import init_db

UPLOAD_REMOTE = "gdrive:store-backups"  # rclone remote:folder


def create_local_backup():
    """Hot-backup SQLite to a timestamped local file."""
    paths.BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = paths.BACKUP_DIR / f"store_{ts}.db"
    n = 1
    while dest.exists():  # two backups in the same second -> unique suffix
        dest = paths.BACKUP_DIR / f"store_{ts}_{n}.db"
        n += 1

    src_conn = sqlite3.connect(paths.DB_PATH)
    dest_conn = sqlite3.connect(dest)
    src_conn.backup(dest_conn)
    dest_conn.close()
    src_conn.close()
    return dest


def _find_rclone():
    """Locate rclone on Windows (rclone.exe) or Linux/macOS."""
    exe = shutil.which("rclone")
    if exe:
        return exe
    for cand in [
        r"C:\Program Files\rclone\rclone.exe",
        r"C:\rclone\rclone.exe",
        str(Path.home() / "rclone" / "rclone.exe"),
    ]:
        if Path(cand).exists():
            return cand
    return None


def upload_to_drive(backup_path):
    """Upload a backup file to Google Drive via rclone."""
    rclone = _find_rclone()
    if not rclone:
        return (
            False,
            "rclone not found. See README for Windows install instructions.",
        )
    try:
        result = subprocess.run(
            [rclone, "copy", str(backup_path), UPLOAD_REMOTE],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return False, result.stderr.strip() or "rclone failed"
        return True, "Uploaded to Google Drive"
    except subprocess.TimeoutExpired:
        return False, "Upload timed out"
    except Exception as e:
        return False, str(e)


def run_backup():
    """Local backup + optional Drive upload."""
    backup_path = create_local_backup()
    _, drive_msg = upload_to_drive(backup_path)
    return str(backup_path), drive_msg


def list_backups():
    """Existing local backups, newest first."""
    if not paths.BACKUP_DIR.exists():
        return []
    return sorted(
        paths.BACKUP_DIR.glob("store_*.db"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )


def _is_sqlite(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def _backup_has_manager(backup_path):
    """Return (manager_count, usable) for a backup file."""
    try:
        conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM employees WHERE role='Manager'"
            ).fetchone()[0]
        finally:
            conn.close()
        return count, count > 0
    except Exception:
        return 0, False


def restore_backup(backup_path):
    """Replace the live database with a chosen backup.

    1. validates the file is a real backup with a Manager account,
    2. keeps a safety snapshot of the current database first,
    3. copies the backup over store.db and re-runs migrations.

    Returns (ok, message).
    """
    backup_path = Path(backup_path)
    if not backup_path.exists():
        return False, "Backup file not found."
    if not _is_sqlite(backup_path):
        return False, "Selected file is not a valid database."
    managers, usable = _backup_has_manager(backup_path)
    if not usable:
        return False, "Backup has no Manager account - refusing to restore."

    safety = create_local_backup()  # undo-able restore
    try:
        shutil.copyfile(backup_path, paths.DB_PATH)
    except OSError as e:
        return False, f"Could not write database: {e}"

    init_db()  # idempotent; applies migrations to the restored file

    return True, (
        f"Restored from {backup_path.name} ({managers} manager). "
        f"Previous database kept as {safety.name}."
    )
