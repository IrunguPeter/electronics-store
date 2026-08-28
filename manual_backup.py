"""CLI entry point for automated backups (cron-friendly)."""
from backup import run_backup

if __name__ == "__main__":
    path, msg = run_backup()
    print(f"Local: {path}")
    print(msg)
