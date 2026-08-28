import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from paths import BACKUP_DIR, DB_PATH

UPLOAD_REMOTE = "gdrive:store-backups"  # rclone remote:folder


def create_local_backup():
    """Hot-backup SQLite to a timestamped local file."""
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"store_{ts}.db"

    src_conn = sqlite3.connect(DB_PATH)
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
