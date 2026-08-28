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

| New Sale | Products | Reports | Employees |
| :-: | :-: | :-: | :-: |
| *(add screenshots here)* | | | |

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

> `store.db`, `backups/`, and `exports/` are git-ignored so your real shop data
> is never accidentally pushed to GitHub.

---

## Project Structure

```
electronics-store/
├── main.py          # Entry point — launches the GUI
├── gui.py           # Tkinter application (login, sale, products, reports, employees)
├── operations.py    # Database operations (sales, products, reports)
├── db.py            # Schema, connection and migrations
├── backup.py        # SQLite hot-backup + Google Drive upload (rclone)
├── export.py        # CSV and PDF report export
├── manual_backup.py # Standalone script for scheduled backups
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
void/restock, last-manager protection, and duplicate PIN rejection.

---

## Troubleshooting

- **"Tkinter not found"** — install it (see Requirements / Linux section).
- **Backup button says rclone not found** — install rclone and run
  `rclone config` to link your Google account.
- **PDF export fails** — make sure `reportlab` is installed
  (`pip install reportlab`); the app falls back to CSV otherwise.

## License

MIT
