<div align="center">

# ElectronStore POS

**A point-of-sale desktop app for an electronics store.**

Tracks sales, stock, and profit in **Kenya Shillings (KES)**, with automatic
backups to **Google Drive**. Built with Python, Tkinter, and SQLite — no internet
required to operate the shop.

</div>

---

## Features

- **🛒 Point of Sale** — search products, add to cart, set quantities and
  per-line discounts, and charge. Choose payment method (cash / card / mobile).
  For cash, enter the amount tendered and get change computed. Stock is deducted
  automatically and a printable **receipt** is shown.
- **🧾 Sales history & voids** — review recent sales, re-print a receipt, and
  (as Manager) **void** a mistaken sale, which returns items to stock.
- **📦 Product management** — add products with a product code, category, price,
  and cost, then **edit**, **restock**, or **delete** them. Search stock and get
  low-stock alerts.
- **📊 Reports** — a dashboard with revenue, gross profit, and margin, plus a
  daily revenue chart, category breakdown, best sellers, **sales by staff**, and
  an **end-of-day** summary. Export to **CSV** or **PDF**.
- **☁️ Google Drive backups** — one-click (or scheduled) safe backups of your data
  to Google Drive, so you never lose sales records.
- **👥 Staff & roles** — Manager and Employee roles. Managers can add/edit/delete
  staff, change roles, and reset PINs; Employees can sell, manage products, and
  view reports.
- **🔒 PIN login** — simple staff access control.
- **🎨 Polished UI** — dark theme with animated buttons and charts.

## Screenshots

| New Sale | Products | Reports | Sales | Employees |
| :-: | :-: | :-: | :-: | :-: |
| *(add screenshots here)* | | | | |

---

## Requirements

- **Python 3.8 or newer**
- **Tkinter** — bundled with Python on Windows/macOS; on Linux install `python3-tk`
- **matplotlib** and **reportlab** — `pip install -r requirements.txt`
- **[rclone](https://rclone.org/downloads/)** — optional, only needed for
  Google Drive backups

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/IrunguPeter/electronics-store.git
cd electronics-store

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

> **First run:** if no staff account exists, the app creates a default
> **Manager** with PIN **`1234`**. Log in with that to get started.

### On Linux

```bash
sudo apt install python3-tk      # or: sudo dnf install python3-tkinter
```

### Google Drive backups (optional)

1. Install rclone:
   - **Windows:** `winget install rclone` (or download from
     [rclone.org](https://rclone.org/downloads/))
   - **Linux/macOS:** `sudo apt install rclone`
2. Link your Google account (one-time):
   ```bash
   rclone config          # name the remote exactly "gdrive"
   rclone mkdir gdrive:store-backups
   ```
3. Back up any time with the **Backup** button in the app.

---

## Build a Windows .exe (PyInstaller)

Give the customer a single double-clickable file with no Python install needed.

> PyInstaller does **not** cross-compile: the `.exe` must be built **on a Windows
> computer**. Any Windows PC with Python works for the build.

1. On a Windows machine, open the project folder.
2. **Double-click `build_windows.bat`** (or run it from a terminal). It installs
   the dependencies plus PyInstaller, then builds the exe.
3. When it finishes, the program is at
   **`dist\ElectronStore.exe`**. The icon is baked in from `icon.ico`, so the
   exe and its window/taskbar icon look right with no extra files to copy.
4. Copy that **one file** to the shop PC. Place it in its own folder (e.g.
   `C:\ElectronStore\`).

**How data is stored when running the exe:**
- The database (`store.db`), `backups/`, and `exports/` are created **next to the
  `.exe`**, so they survive as long as the folder does. Don't run it from a
  folder you can't write to.
- Always keep a recent backup (the **Backup** button / Google Drive) in case the
  folder is ever moved or deleted.

To build manually instead of the `.bat`:

```bash
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller electronstore.spec --noconfirm
```

---

## Online installer (Start Menu setup)

If you'd rather hand the shop a single small *installer* that downloads the app
and adds a **Start Menu** shortcut:

1. **Publish the app**: create a GitHub **Release** for this repo and attach
   `dist\ElectronStore.exe` as an asset named **exactly** `ElectronStore.exe`.
   The installer downloads it from
   `/releases/latest/download/ElectronStore.exe`.
2. **Build the installer** (on Windows): run `build_setup.bat`. It builds both
   the app exe and `dist\ElectronStoreSetup.exe`.
3. **Give the shop `ElectronStoreSetup.exe`**. Running it downloads the app,
   installs it to `%LOCALAPPDATA%\Programs\ElectronStore`, adds **Start Menu**
   and desktop shortcuts, registers it under **Settings → Apps** (uninstallable),
   and offers to launch it right away.

Notes:

- **Dependencies**: Python, Tkinter, matplotlib, and reportlab are already
  inside the app exe, so the setup file only downloads that one file.
- **Updates**: publish a new Release (same asset name) and re-run the installer
  to update. Sales data is never touched — it lives separately in
  `%LOCALAPPDATA%\ElectronStore`.
- **No admin needed** (per-user install), and no internet is needed afterwards —
  only while the installer downloads.
- **Custom download URL**: build/ship with `ELECTRONSTORE_DOWNLOAD_URL=...` set
  or run the installer with `--url <address>` (e.g. a private mirror).

### Publishing a release (so the installer can download)

**Easiest: let GitHub Actions do it.** Tag a commit with `v*` and push — the
`.github/workflows/release.yml` workflow builds both exes on a Windows runner,
runs the test suite, and creates the GitHub Release automatically:

```bash
git tag v1.0 && git push origin v1.0
```

The release ships with `ElectronStore.exe` (the asset the installer downloads)
**and** `ElectronStoreSetup.exe` as a bonus. No Windows PC or local build needed.

**Or build it yourself.** From the project folder (on the build PC), after
`build_setup.bat` has produced `dist\ElectronStore.exe`:

```bash
gh release create v1.0 "dist/ElectronStore.exe" --title "ElectronStore 1.0" --notes "First release"
```

- The asset must keep the name **`ElectronStore.exe`** (that's exactly what the
  build outputs), otherwise `/releases/latest/download/...` won't resolve it.
- Every time you want the shop to update, create a **new** release with a new
  tag (e.g. `v1.1`, `v1.2`, …) — `latest` always points at the most recent
  non-draft release, and the shop just runs `ElectronStoreSetup.exe` again.
- Draft, or replace an uploaded asset by deleting the old one in the GitHub
  web UI and re-attaching — or simply make a new release instead.

---

## Usage

### Logging in
Enter your PIN on the login screen. (Default: `1234`.) You can log out with the
**Logout** link in the top-right of the main window.

### Recording a sale
1. In the **New Sale** tab, search or click a product.
2. Set the **Qty** and click **Add to Cart** (or double-click a product).
3. To discount a line, select it in the cart, enter a **Line discount** and
   click **Apply**.
4. Choose a **payment method**.
   - For **cash**, enter the amount received — the app works out the change.
5. Click **Charge**. Stock is updated, a success toast appears, and a printable
   **receipt** is shown.

### Voiding a sale
1. Open the **Sales** tab to see recent sales.
2. Double-click a sale to view its receipt.
3. As **Manager**, select a sale and click **Void Selected Sale**.
   Items are returned to stock and the sale is marked VOIDED. Voided sales are
   excluded from the revenue and profit reports.

### Managing products
In the **Products** tab, fill in the details and click **Add Product**:
name, category, product code, selling price, cost price, and stock quantity.
Click any product in the list to load it for editing, then **Save Changes**,
**Restock** (adjust stock), or **Delete** it. Rows turn **amber** when stock is
low and **red** when out of stock.

### Viewing reports
The **Reports** tab shows revenue, gross profit, and margin for the current data,
a daily revenue chart, a category breakdown, and your best-selling products.
Use **By Staff** to see each cashier's sales, or **End of Day** for a daily
summary of payment methods, units, and voids. Use **Export CSV** or **Export PDF**
to save a report.

### Managing staff
The **Employees** tab lists everyone with a PIN. **Managers** can add new staff,
promote/demote between Manager and Employee, reset PINs, and delete accounts.
**Employees** can view the list but cannot change it. The app protects against
deleting or demoting the very last manager.

---

## Backups

- Uses SQLite's hot-backup API, so the live database is never locked or corrupted.
- A manual **Backup** button saves to `./backups/` and uploads a copy to
  `gdrive:store-backups/` in Google Drive.
- For fully automatic backups, schedule `manual_backup.py`:
  - **Windows:** use Task Scheduler (see below)
  - **Linux/macOS:** add a cron job
    ```
    0 23 * * * python3 /path/to/electronics-store/manual_backup.py
    ```

### Restoring from a backup

If the machine ever needs replacing, use the **Restore** button in the app
(Managers only, next to **Backup**):

1. Choose a backup from the list (`store_YYYYMMDD_HHMMSS.db`). You can also
   drop a `store_*.db` file you downloaded from Google Drive into the `backups/`
   folder first — it will appear in the list.
2. The app keeps a **safety copy** of the current database in `backups/`
   before restoring, then restores the chosen one and logs out.
3. Log back in with the manager PIN from the restored backup.

**Guard rail:** a backup with no Manager account is refused, so you can't
restore an empty or corrupted file and lock yourself out.

### Automatic backups on Windows (Task Scheduler)

1. Open **Task Scheduler** → **Create Basic Task**.
2. Name it `Store Backup`, trigger **Daily**.
3. Action **Start a program**: program `python`, argument `C:\path\to\electronics-store\manual_backup.py`.
4. Finish.

---

## Data & Storage

Everything is stored in a single SQLite file, **`store.db`**, in the app folder.
Tables:

| Table | Purpose |
| ----- | ------- |
| `products` | product code, name, category, price, cost, stock |
| `employees` | staff names, roles, and PINs |
| `sales` | each sale: date, cashier, total, payment method, tendered/change |
| `sale_items` | line items, quantities, unit prices, discounts |

All prices are stored as **whole Kenya Shillings (KES)** (integer values), so
money stays exact — no floating-point drift.

Staff PINs are stored as **PBKDF2 hashes** with a per-PIN salt — never in
plaintext. Unhandled errors are written to a rotating `electronstore.log`
(next to `store.db`) for diagnosis.

> `store.db`, `backups/`, and `exports/` are git-ignored so your real shop data
> is never accidentally pushed to GitHub.

---

## Project Structure

```
electronics-store/
├── main.py          # Entry point — launches the GUI
├── gui.py           # Tkinter application (login, sale, products, reports, sales, employees)
├── operations.py    # Database operations (sales, products, reports)
├── db.py            # Schema, connection and migrations
├── security.py      # PBKDF2-SHA256 PIN hashing (no plaintext PINs stored)
├── logutil.py       # Rotating exception log (electronstore.log)
├── backup.py        # SQLite hot-backup + Google Drive upload (rclone)
├── export.py        # CSV and PDF report export
├── paths.py         # Central path resolution (runs from source or .exe)
├── manual_backup.py # Standalone script for scheduled backups
├── electronstore.spec   # PyInstaller build config
├── build_windows.bat   # One-click Windows .exe builder
├── tests/           # pytest suite for the data layer
└── requirements.txt
```

---

## Testing

The data layer has a pytest suite in `tests/`:

```bash
pip install -r requirements.txt   # includes pytest
python -m pytest tests/
```

Tests cover integer money handling, sale totals and change, stock deduction,
void/restock, product editing and payment validation, per-staff and end-of-day
reports, last-manager protection, and duplicate PIN rejection.

---

## Troubleshooting

- **"Tkinter not found"** — install it (see Requirements / Linux section).
- **Backup button says rclone not found** — install rclone and run
  `rclone config` to link your Google account.
- **PDF export fails** — make sure `reportlab` is installed
  (`pip install reportlab`); the app falls back to CSV otherwise.

## License

MIT
