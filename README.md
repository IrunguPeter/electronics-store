# Electronics Store POS

A desktop POS (point-of-sale) for an electronics store. Tracks sales, stock, and
profit, with automatic backup to Google Drive via rclone. Currency is **Kenya
Shillings (KES)**. Works on **Windows**, macOS, and Linux.

## Requirements
- Python 3.8+
- [rclone](https://rclone.org/downloads/) (for Google Drive backup) — optional but recommended
- `matplotlib` and `reportlab` (`pip install -r requirements.txt`)
- Tkinter (bundled with Python on Windows; on Linux install `python3-tk`)

## Setup

### 1. Install rclone (Windows)

Two easy ways:

```powershell
# Option A: winget (fastest)
winget install rclone

# Option B: manual
# - Download the Windows .zip from https://rclone.org/downloads/
# - Extract rclone.exe to C:\rclone\ (or anywhere)
# - Add that folder to your PATH
```

### 2. Link rclone to Google Drive (one-time)

```powershell
rclone config
```
- Select **n** to make a **new remote**
- Name it exactly **`gdrive`**
- Choose **drive** for the storage type
- Follow the prompts — it opens your browser to log in to Google and grant access
- Accept all defaults after that

Create the backup folder:
```powershell
rclone mkdir gdrive:store-backups
```

### 3. Run the app

```powershell
pip install -r requirements.txt
python main.py
```

The GUI has three screens:
- **New Sale** — search/pick products, set quantity, charge (auto-deducts stock)
- **Products** — add products (name, category, product code, price, cost), search, low-stock alerts
- **Reports** — daily revenue chart, category share, top sellers, profit & margin; export to CSV or PDF

Back up to your Drive any time with the **Backup** button.

## Automatic daily backups (Windows Task Scheduler)

1. Open **Task Scheduler** → **Create Basic Task**
2. Name it `Store Backup`
3. Trigger: **Daily** at your preferred time
4. Action: **Start a program**
   - Program: `python`
   - Add arguments: `C:\path\to\electronics-store\manual_backup.py`
5. Finish. It now backs up to Drive every day.

> The first staff member to run the app logs in with PIN 1234 (change this and
> add real staff via the Employees menu).

## How backups work
- Uses SQLite's hot-backup API — never touches the live DB in a way that could
  corrupt it.
- Local copies go in `./backups/`
- A copy is uploaded to `gdrive:store-backups/` in your Google Drive.

## Data
Stored in `store.db` (SQLite). Tables: `products` (with `code`, price, cost, stock),
`employees`, `sales`, `sale_items`. Stock is decremented automatically on each sale.
All prices are in Kenya Shillings (KES).
