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
- **First time using the app?** The default PIN is **`1234`**. Ask the owner to
  add real staff accounts (see section 8) and set a PIN you will remember.
- When you are done, click **Logout** (top-right) so the next person logs in
  with their own PIN.

---

## 2. The main screen

After logging in you will see the main window with five tabs at the top:

- **New Sale** — where you ring up customers.
- **Products** — where you add and check your stock.
- **Reports** — where you see your sales and profit.
- **Sales** — a list of recent sales, where you can view a receipt or void a
  mistake (managers only).
- **Employees** — where staff accounts are managed (managers only).

There is also a green **Backup** button at the top right, and a **Logout** link.

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
5. *(Optional)* To give a discount on a line: select that item in the cart,
   type the discount in the **Line discount** box, and click **Apply**.
6. Choose the **payment method**: Cash, Card, or Mobile.
   - If **Cash**, a small window asks how much money you received — type the
     amount and the app works out and shows the **change**.
7. Click **Charge**.

> A green **"Sale successful"** message appears, and a **receipt** pops up so you
> can review or save/print it. The stock for those products is reduced
> automatically.

**To remove a wrong item:** select it in the cart list and press the **Delete**
key on your keyboard.

---

## 3.5 Fixing a mistake — voiding a sale (Sales tab)

If you ring up a sale by mistake, you can undo it.

1. Go to the **Sales** tab to see the list of recent sales.
2. Double-click any sale to open its **receipt**.
3. **(Manager only)** Select the wrong sale in the list and click
   **Void Selected Sale**, then confirm.
4. The items are **returned to stock** and the sale is marked **VOIDED**.
   Voided sales are left out of the revenue and profit reports.

> Only **Managers** can void sales. If you are not a manager and a sale needs
> correcting, ask your manager.

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

**Editing, restocking, or deleting a product:**
1. **Click the product** in the list at the bottom (above the low-stock
   colouring). Its details load into the form at the top.
2. To change details (name, category, code, price, or cost), edit the fields and
   click **Save Changes**.
3. To add or remove stock, click **Restock** and type how many to add (a
   positive number) or remove (a negative number).
4. To remove a product you no longer sell, click **Delete** and confirm.

> Deleting a product also removes its sales history. Use **Void** in the Sales
> tab instead if you only want to correct a mistaken sale.

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

### Sales by staff
- Click **By Staff** (next to Refresh) to see a table of each staff member's
  sales, items sold, and revenue. This is useful for end-of-day cash matching.

### End of day
- Click **End of Day** to see a summary for a specific date (leave blank for
  today): totals by payment method (cash/card/mobile), items sold, and any
  voided sales.
- Each report window has a **Save CSV** button to keep a copy.

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

## 8. Managing staff (Employees tab)

The **Employees** tab is where you manage staff accounts. It is available to
everyone, but only **Managers** can make changes.

### Roles
- **Manager** — can do everything, including managing staff.
- **Employee** — can record sales, add products, and view reports, but **cannot**
  add, edit, or delete staff.

### Adding a new staff member (Manager only)
1. Go to the **Employees** tab.
2. In the **Add staff** row, type their **name**, choose a **role**
   (Manager or Employee), and set a **PIN** (a secret number they will log in with).
3. Click **Add**.

> Each PIN must be unique. If you see "that PIN is already in use", pick another.

### Changing a role (Manager only)
1. Click a staff member in the list.
2. Click **Set Manager** or **Set Employee**.
3. You cannot change your own role, and you cannot demote the last manager.

### Resetting a forgotten PIN (Manager only)
1. Click the staff member in the list.
2. Click **Reset PIN** and type a new PIN.

### Removing a staff member (Manager only)
1. Click the staff member in the list.
2. Click **Delete** and confirm.

> The app will not let you delete or demote the **only** manager, so you can
> never lock yourself out completely.

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
| Discount a line | New Sale | select cart item → Line discount → Apply |
| Remove cart item | New Sale | select item → press Delete |
| Add stock | Products | fill form → Add Product |
| Edit product | Products | click product → Save Changes |
| Restock | Products | click product → Restock |
| Check stock alerts | Products | amber = low, red = none |
| See profit | Reports | Revenue / Profit / Margin cards |
| Sales by staff | Reports | By Staff button |
| End-of-day report | Reports | End of Day button |
| Export report | Reports | Export CSV or Export PDF |
| View a receipt | Sales | double-click a sale |
| Void a sale (Manager) | Sales | select sale → Void Selected Sale |
| Back up | Backup button (top right) | click it |
| Add staff | Employees (Manager) | name + role + PIN → Add |
| Reset a PIN | Employees (Manager) | select → Reset PIN |
| Log out | Logout link (top right) | click it |

---

*Thank you for using ElectronStore POS. Keep your backups running and the shop
healthy!*
