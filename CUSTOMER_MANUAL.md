# ElectronStore POS — User Manual

*For the shop owner and staff. This guide explains how to run the app, record
sales, add products, check reports, and keep your data backed up.*

---

## 1. Starting the app

1. Make sure the computer is on.
2. Open the folder where the program is saved.
3. Run the program:
   - **Windows:** double-click the `main.py` file, or open a terminal in the
     folder and type `python main.py`.
   - The program was set up to open with a small **login window**.

### Logging in (PIN)
- A login screen appears asking for your **PIN** (a personal number).
- Type your PIN and press **Enter** or click **Login**.
- **First time using the app?** The default PIN is **`1234`**. You should change
  it as soon as convenient (see section 8).

---

## 2. The main screen

After logging in you will see the main window with three tabs at the top:

- **New Sale** — where you ring up customers.
- **Products** — where you add and check your stock.
- **Reports** — where you see your sales and profit.

There is also a green **Backup** button at the top right.

---

## 3. Recording a sale (New Sale tab)

This is the screen you will use most.

1. **Find the product:**
   - Type part of the name in the **search box**, **or**
   - Click the product in the list on the left.
2. **Set the quantity** in the **Qty** box (it starts at `1`).
3. Click **Add to Cart** (or double-click the product).
   The item appears in the cart on the right, and the **total** updates.
4. Repeat for every item the customer is buying.
5. Choose the **payment method**: Cash, Card, or Mobile.
6. Click **Charge**.

> A green **"Sale successful"** message appears, and the money is recorded.
> The stock for those products is reduced automatically.

**To remove a wrong item:** select it in the cart list and press the **Delete**
key on your keyboard.

---

## 4. Adding a product (Products tab)

When you get new stock, add it here so you can sell it.

1. Go to the **Products** tab.
2. Fill in the fields:
   - **Name** — e.g. "4K TV 55-inch"
   - **Category** — e.g. "TV", "Laptop", "Phone", "Accessory"
   - **Product Code** — a short code you make up, e.g. "TV-55". Each product
     needs its own code (same code twice is not allowed).
   - **Price** — how much you sell it for (in KES).
   - **Cost** — how much you paid for it (in KES). This is used to calculate
     your profit.
   - **Stock** — how many you have.
3. Click **Add Product**.

**Low-stock alerts:**
- **Amber** row = only a few left (5 or fewer).
- **Red** row = out of stock.

---

## 5. Reports (Reports tab)

This tab shows how the shop is doing:

- **Revenue** — total money taken in.
- **Profit** — revenue minus what the goods cost you.
- **Margin** — your profit as a percentage.
- **Daily Revenue chart** — a graph of sales per day. Use the **Days** box to
  choose 7/14/30/90 days.
- **Top Sellers** — your best-selling products.
- **By Category** — a pie chart of sales by category.

### Exporting a report
- Click **Export CSV** to save a spreadsheet you can open in Excel.
- Click **Export PDF** to save a printable report.
- Choose where to save the file when the window appears.

---

## 6. Backing up your data (very important!)

Your records are stored in a file called `store.db`. To avoid losing everything,
back it up regularly to your **Google Drive**.

- Click the green **Backup** button (top right of the main window).
- The app saves a copy locally *and* uploads it to Google Drive.
- You should see a message confirming the backup.

> **Tip:** Back up at least once a day, especially before closing the shop.

> **For the owner:** If you want backups to happen *automatically* every day
> (so nobody has to remember), see section 9.

---

## 7. What to do if something goes wrong

- **App won't open / says Tkinter missing:** Contact whoever installed the
  program — the Python "Tk" package needs to be installed.
- **Backup says "rclone not found":** rclone (the Google Drive tool) is not set
  up. Ask your installer to set it up with your Google account.
- **PDF export fails:** reportlab is not installed. Ask your installer to run
  `pip install reportlab`.
- **Forgotten PIN:** If you lose access, ask your installer. The PIN is stored
  in a file called `store.db`, and an administrator can reset it.

---

## 8. Changing staff details / PINs

> **Note:** Currently staff accounts are managed by whoever administers the
> program (the database file). The app includes one default manager.

To add a new staff member or change a PIN, an administrator needs to use the
database. The simplest safe way is to ask the person who set up the program, or
a developer, to update the `employees` table. *(A staff-management screen is a
planned improvement.)*

---

## 9. Automatic daily backups (for the owner)

### On Windows
1. Open the **Task Scheduler** (search for it in the Start menu).
2. Choose **Create Basic Task**.
3. Name: `Store Backup` → **Next**.
4. Trigger: **Daily**, choose a time (e.g. 8 PM) → **Next**.
5. Action: **Start a program** → **Next**.
6. Program/script: type `python`
   Arguments: the full path to `manual_backup.py`
   (e.g. `C:\Users\You\electronics-store\manual_backup.py`) → **Next** → **Finish**.

### On Linux/macOS (cron)
- Ask your technical person to add this line to the cron jobs:
  ```
  0 20 * * * python3 /path/to/electronics-store/manual_backup.py
  ```

---

## Quick reference

| Task | Where | How |
| ---- | ----- | --- |
| Ring up a sale | New Sale | search → qty → Add to Cart → Charge |
| Remove cart item | New Sale | select item → press Delete |
| Add stock | Products | fill form → Add Product |
| Check stock alerts | Products | amber = low, red = none |
| See profit | Reports | Revenue / Profit / Margin cards |
| Export report | Reports | Export CSV or Export PDF |
| Back up | Backup button (top right) | click it |
| Change PIN | ask administrator | *(planned feature)* |

---

*Thank you for using ElectronStore POS. Keep your backups running and the shop
healthy!*
