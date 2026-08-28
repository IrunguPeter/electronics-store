import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, simpledialog, ttk

import backup
import operations as ops
from db import init_db
from paths import ICON_PATH

# Palette
BG = "#0f172a"        # slate-900
PANEL = "#1e293b"     # slate-800
PANEL2 = "#334155"    # slate-700
ACCENT = "#38bdf8"    # sky-500
ACCENT2 = "#2563eb"   # blue-600
SUCCESS = "#22c55e"   # green-500
WARN = "#f59e0b"      # amber-500
TEXT = "#e2e8f0"      # slate-200
MUTED = "#94a3b8"     # slate-400
DANGER = "#ef4444"    # red-500

# Currency — Kenya Shillings
CURRENCY = "KES"
CURRENCY_SYMBOL = "KSh"


def _lighten(color, amount):
    """Return a lighter version of a hex color (amount 0..1)."""
    h = color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    rgb = [min(255, int(c + (255 - c) * amount)) for c in rgb]
    return "#%02x%02x%02x" % tuple(rgb)


def fmt_money(amount):
    """Format an amount as whole Kenyan Shillings, e.g. 12,345 KSh."""
    return f"{CURRENCY_SYMBOL} {int(round(float(amount))):,}"


def _rounded_points(x1, y1, x2, y2, r):
    """Return polygon points for a rounded rectangle."""
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


def _empty_row(tree, message):
    """Insert a muted 'nothing here yet' row when a list is empty."""
    cols = list(tree["columns"])
    values = [""] * len(cols)
    if values:
        values[len(cols) // 2] = message
    tree.delete(*tree.get_children())
    tree.insert("", "end", iid="_empty_", values=tuple(values),
                tags=("empty",))


class AccentButton(tk.Canvas):
    """Rounded pill button drawn on a canvas, with hover/press animations."""

    def __init__(self, master, text="", command=None, bg=ACCENT2, fg="white",
                 font=("Segoe UI", 11, "bold"), radius=16, padx=18, pady=9,
                 **kw):
        super().__init__(
            master, bg=master.cget("bg"), highlightthickness=0, bd=0, **kw
        )
        self.base_color = bg
        self.hover_color = _lighten(bg, 0.18)
        self.text = text
        self.fg = fg
        self.font = font
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.command = command
        self._enabled = True

        # Pre-measure text so the pill fits its label
        fnt = tkfont.Font(root=self, font=font)
        tw = fnt.measure(text)
        th = fnt.metrics("linespace")
        w = tw + padx * 2 + radius
        h = th + pady * 2
        self.configure(width=w, height=h)
        self._tw, self._th = tw, th

        self.shape = self.create_polygon(
            _rounded_points(2, 2, w - 2, h - 2, radius),
            fill=bg, outline="", smooth=True,
        )
        self.label = self.create_text(
            w // 2, h // 2, text=text, fill=fg, font=font
        )

        self.bind("<Enter>", lambda e: self._tween(bg, self.hover_color))
        self.bind("<Leave>", lambda e: self._tween(self.hover_color, bg))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _tween(self, a, b, steps=8):
        def to_hex(t):
            return "#%02x%02x%02x" % tuple(
                max(0, min(255, int(v))) for v in t)

        def rgb(c):
            c = c[1:] if c.startswith("#") else c
            return tuple(int(c[j:j + 2], 16) for j in (0, 2, 4))

        a, b = rgb(a), rgb(b)

        def step(i):
            if i > steps:
                self.itemconfigure(self.shape, fill=to_hex(b))
                return
            mixed = tuple(int(a[j] + (b[j] - a[j]) * (i / steps)) for j in range(3))
            self.itemconfigure(self.shape, fill=to_hex(mixed))
            self.after(12, lambda: step(i + 1))

        step(0)

    def _on_press(self, _):
        # Shrink the pill slightly for a press effect
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        self.coords(
            self.shape, *_rounded_points(4, 4, w - 4, h - 4, self.radius)
        )

    def _on_release(self, _):
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        self.coords(
            self.shape, *_rounded_points(2, 2, w - 2, h - 2, self.radius)
        )
        if self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        self.itemconfigure(self.label, text=text)
        fnt = tkfont.Font(root=self, font=self.font)
        tw = fnt.measure(text)
        th = fnt.metrics("linespace")
        w = tw + self.padx * 2 + self.radius
        h = th + self.pady * 2
        self.configure(width=w, height=h)
        self.coords(self.shape, *_rounded_points(2, 2, w - 2, h - 2, self.radius))
        self.coords(self.label, w // 2, h // 2)


class RoundedEntry(tk.Canvas):
    """Rounded pill container wrapping a real tk.Entry."""

    def __init__(self, master, textvariable=None, fg=TEXT, bg=PANEL,
                 font=("Segoe UI", 12), radius=14, width_chars=10,
                 justify="left", insertbackground=None, show=None, **kw):
        fnt = tkfont.Font(root=master, font=font)
        ch = fnt.measure("0")
        w = max(ch * width_chars + radius * 2 + 12, 60)
        h = fnt.metrics("linespace") + 16
        super().__init__(master, bg=master.cget("bg"), highlightthickness=0,
                         bd=0, width=w, height=h, **kw)
        self.bg = bg
        self.radius = radius
        self.shape = self.create_polygon(
            _rounded_points(2, 2, w - 2, h - 2, radius),
            fill=bg, outline="", smooth=True,
        )
        self.entry = tk.Entry(
            self, textvariable=textvariable, bg=bg, fg=fg, show=show,
            insertbackground=(insertbackground or fg), relief="flat", bd=0,
            font=font, justify=justify, highlightthickness=0,
        )
        self._entry_window = self.create_window(
            w // 2, h // 2, window=self.entry, width=w - radius - 16
        )
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, _):
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 4 and h > 4:
            self.coords(
                self.shape, *_rounded_points(2, 2, w - 2, h - 2, self.radius)
            )
            self.coords(self._entry_window, w // 2, h // 2)
            self.itemconfigure(self._entry_window, width=w - self.radius - 12)

    def get(self):
        return self.entry.get()


class NumberButton(tk.Button):
    """Big on-screen numpad button."""

    def __init__(self, master, text, command):
        super().__init__(
            master,
            text=text,
            command=command,
            bg=PANEL2,
            fg=TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 18, "bold"),
            activebackground=ACCENT2,
            activeforeground="white",
        )
        self.bind("<Enter>", lambda e: self.configure(bg=ACCENT2, fg="white"))
        self.bind("<Leave>", lambda e: self.configure(bg=PANEL2, fg=TEXT))


class Toplevel(tk.Frame):
    """Main dashboard with a top nav bar, animated tab switching, and status bar."""

    def __init__(self, master, cashier_id, cashier_name, cashier_role):
        super().__init__(master, bg=BG)
        master.title("ElectronStore POS")
        master.geometry("1100x700")
        master.configure(bg=BG)
        master.minsize(950, 620)

        self.cashier_id = cashier_id
        self.cashier_name = cashier_name
        self.cashier_role = cashier_role
        self.is_manager = cashier_role == "Manager"
        self.current_tab = None

        self._build_nav()
        self._build_statusbar()

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.tabs = {
            "sale": SaleView,
            "products": ProductsView,
            "reports": ReportsView,
            "sales": SalesView,
            "employees": EmployeesView,
        }
        self.show("sale")

        self.after(2000, self._flash_status, f"Welcome, {cashier_name}!")

    def _build_nav(self):
        nav = tk.Frame(self, bg=PANEL, height=60)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        title = tk.Label(
            nav, text="ElectronStore", bg=PANEL, fg=ACCENT,
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(side="left", padx=20)

        self.nav_btns = {}
        for key, label in [
            ("sale", "New Sale"),
            ("products", "Products"),
            ("reports", "Reports"),
            ("sales", "Sales"),
            ("employees", "Employees"),
        ]:
            b = tk.Label(
                nav, text="  " + label + "  ", bg=PANEL, fg=MUTED,
                font=("Segoe UI", 12, "bold"), cursor="hand2",
            )
            b.pack(side="left", padx=6, pady=12)
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            b.bind("<Enter>", lambda e, b=b: b.configure(fg=TEXT))
            b.bind("<Leave>", lambda e, b=b: b.configure(fg=MUTED))
            self.nav_btns[key] = b
            self.nav_btns[key].name = key

        # Logout on right
        logout = tk.Label(
            nav, text="  Logout  ", bg=PANEL, fg=DANGER,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
        )
        logout.pack(side="right", padx=(0, 16), pady=14)
        logout.bind("<Button-1>", lambda _: self._logout())

        # Restore (Managers only) + Backup on right
        if self.is_manager:
            self.restore_btn = AccentButton(
                nav, text="Restore", command=self.do_restore, bg=DANGER,
            )
            self.restore_btn.pack(side="right", padx=8)

        # Backup button on right
        self.backup_btn = AccentButton(
            nav, text="Backup", command=self.do_backup, bg=SUCCESS,
        )
        self.backup_btn.pack(side="right", padx=8)

        # Separator line under nav
        line = tk.Frame(self, bg=ACCENT2, height=2)
        line.pack(fill="x")

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=PANEL, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status = tk.Label(
            bar, text="Ready", bg=PANEL, fg=MUTED, anchor="w",
            font=("Segoe UI", 10),
        )
        self.status.pack(side="left", padx=12)
        tk.Label(
            bar, text=f"{self.cashier_name}  ({self.cashier_role})",
            bg=PANEL, fg=ACCENT, font=("Segoe UI", 10, "bold"),
        ).pack(side="right", padx=12)

    def _flash_status(self, msg):
        self._status_colour = ACCENT
        self._status_msg = msg
        self._status_step = 0
        self._animate_status()

    def _animate_status(self):
        # Fade accent -> muted over ~1.5s
        self._status_step += 1
        if self._status_step > 18:
            self.status.configure(text=self._status_msg or "Ready", fg=MUTED)
            return
        self.status.configure(text=self._status_msg, fg=ACCENT)
        self.after(40, self._animate_status)

    def show(self, key):
        for f in self.container.winfo_children():
            f.destroy()
        self.current_tab = self.tabs[key](self.container, self)
        self.current_tab.pack(fill="both", expand=True)
        self._highlight_nav(key)

    def _highlight_nav(self, key):
        for k, b in self.nav_btns.items():
            if k == key:
                b.configure(bg=ACCENT2, fg="white")
            else:
                b.configure(bg=PANEL, fg=MUTED)

    def do_backup(self):
        self.status.configure(text="Backing up…", fg=ACCENT)

        def work():
            ok_local = False
            try:
                path, msg = backup.run_backup()
                ok_local = True
            except Exception as e:
                self._flash_status(f"Backup failed: {e}")
                return
            self.after(0, self._flash_status, f"Backup saved: {path} — {msg}")

        threading.Thread(target=work, daemon=True).start()

    def do_restore(self):
        if not self.is_manager:
            messagebox.showerror("Restore", "Only Managers can restore a backup.")
            return
        backups = backup.list_backups()
        if not backups:
            messagebox.showinfo(
                "Restore",
                "No backups found yet. Use Backup first, or copy a "
                "'store_*.db' file into the backups folder.",
            )
            return

        win = tk.Toplevel(self)
        win.title("Restore from backup")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        _set_window_icon(win)

        tk.Label(
            win, text="Choose a backup to restore", bg=BG, fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(padx=20, pady=(16, 4))
        tk.Label(
            win, text="The current database is replaced and you will log in again.", bg=BG, fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(padx=20)

        box = tk.Listbox(
            win, bg=PANEL2, fg=TEXT, relief="flat", highlightthickness=0,
            selectmode="single", width=58, height=min(10, len(backups)),
            font=("Consolas", 10),
        )
        box.pack(padx=20, pady=(10, 4))
        for p in backups:
            try:
                stamp = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                size = f"{p.stat().st_size:,} B"
            except OSError:
                stamp, size = "?", "?"
            box.insert("end", f"  {p.name}   {size}   {stamp}")
        if backups:
            box.selection_set(0)

        btns = tk.Frame(win, bg=BG)
        btns.pack(pady=(2, 14))

        def restore_sel():
            sel = box.curselection()
            if not sel:
                self._flash_status("Select a backup first")
                return
            chosen = backups[sel[0]]
            if not messagebox.askyesno(
                "Restore backup",
                f"Replace current data with {chosen.name}?\n\n"
                "A safety copy of the current database is kept in backups/ "
                "before restoring, so this can be undone.\n\n"
                "The app will log out so you can log back in.",
            ):
                return
            ok, msg = backup.restore_backup(chosen)
            if not ok:
                messagebox.showerror("Restore", msg)
                return
            messagebox.showinfo(
                "Restore", msg + "\n\nLogging out - please log in again."
            )
            win.destroy()
            self._logout()

        AccentButton(
            btns, text="Restore Selected", command=restore_sel, bg=DANGER,
        ).pack(side="left", padx=6)
        AccentButton(
            btns, text="Cancel", command=win.destroy, bg=PANEL2,
        ).pack(side="left", padx=6)

    def _logout(self):
        self.master.destroy()
        root = tk.Tk()
        root.report_callback_exception = LoginWindow._error_hook
        _set_window_icon(root)
        LoginWindow(root)
        root.mainloop()


# --------------------------------------------------------------------------
# SALE VIEW
# --------------------------------------------------------------------------
class SaleView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.cart = []  # list of dicts
        self.total = 0.0
        self.barcode = ""

        # Cashier identity banner (keeps who is ringing up in view)
        hdr = tk.Frame(self, bg=PANEL)
        hdr.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(hdr, text="On duty:", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 11)).pack(side="left", padx=(12, 4), pady=8)
        tk.Label(hdr, text=self.app.cashier_name, bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(side="left", pady=5)
        role_bg = SUCCESS if self.app.is_manager else ACCENT2
        tk.Label(hdr, text=self.app.cashier_role, bg=role_bg, fg="white",
                 font=("Segoe UI", 10, "bold"), padx=12, pady=3).pack(
            side="left", padx=10)
        tk.Label(hdr, text="Ring up a sale below", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="right", padx=12)

        # Left: product picker
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left, text="Scan / pick products", bg=BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")

        srch = tk.Frame(left, bg=BG)
        srch.pack(fill="x", pady=6)
        self.search_var = tk.StringVar()
        e = RoundedEntry(srch, textvariable=self.search_var, bg=PANEL, fg=TEXT,
                         font=("Segoe UI", 12), width_chars=14)
        e.pack(side="left", fill="x", expand=True, padx=(0, 6))
        e.entry.bind("<Return>", lambda _: self._search())
        e.entry.bind("<KeyRelease>", lambda _: self._search())
        AccentButton(srch, text="Search", command=self._search).pack(side="right")

        # Product list
        cols = ("id", "name", "price", "stock")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("price", text="Price")
        self.tree.heading("stock", text="Stock")
        for c in ("id", "price", "stock"):
            self.tree.column(c, width=70, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background=PANEL, fieldbackground=PANEL,
            foreground=TEXT, rowheight=28, borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background=PANEL2, foreground=TEXT,
            relief="flat", font=("Segoe UI", 10, "bold"),
        )
        self.tree.pack(fill="both", expand=True, pady=8)
        self.tree.tag_configure("empty", foreground=MUTED)
        self.tree.bind("<Double-Button-1>", lambda _: self._add_selected())
        self.tree.bind("<Return>", lambda _: self._add_selected())

        # Add button + qty
        bottom = tk.Frame(left, bg=BG)
        bottom.pack(fill="x")
        tk.Label(bottom, text="Qty:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 11)).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        RoundedEntry(bottom, textvariable=self.qty_var, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 12), width_chars=4).pack(
            side="left", padx=6
        )
        AccentButton(bottom, text="Add to Cart", command=self._add_selected).pack(
            side="left", padx=6
        )

        self._search()

        # Right: cart + checkout
        right = tk.Frame(self, bg=PANEL)
        right.pack(side="right", fill="y", padx=10, pady=10, ipadx=6)

        tk.Label(right, text="Cart", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=4)

        self.cart_list = tk.Listbox(right, bg=PANEL2, fg=TEXT, relief="flat",
                                    highlightthickness=0, height=14,
                                    font=("Consolas", 10))
        self.cart_list.pack(fill="both", expand=True)
        self.cart_list.bind("<Delete>", lambda _: self._remove_selected())

        self.total_lbl = tk.Label(
            right, text=fmt_money(0), bg=PANEL, fg=SUCCESS,
            font=("Segoe UI", 20, "bold"),
        )
        self.total_lbl.pack(anchor="e", pady=6)

        # Per-line discount (applies to the selected cart line)
        disc = tk.Frame(right, bg=PANEL)
        disc.pack(fill="x", pady=2)
        tk.Label(disc, text="Line discount KSh:", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="left")
        self.disc_var = tk.StringVar(value="0")
        RoundedEntry(disc, textvariable=self.disc_var, bg=PANEL2, fg=TEXT,
                     font=("Segoe UI", 11), width_chars=6).pack(
            side="left", padx=4)
        AccentButton(disc, text="Apply", command=self._apply_discount,
                     bg=PANEL2).pack(side="left")

        pm = tk.Frame(right, bg=PANEL)
        pm.pack(fill="x", pady=4)
        self.pmethod = tk.StringVar(value="cash")
        for i, m in enumerate(["cash", "card", "mobile"]):
            tk.Radiobutton(
                pm, text=m.title(), variable=self.pmethod, value=m,
                bg=PANEL, fg=TEXT, selectcolor=PANEL2, activebackground=PANEL,
                activeforeground=TEXT, font=("Segoe UI", 10),
            ).grid(row=0, column=i, padx=4)

        AccentButton(right, text="Charge  ✓", command=self._checkout,
                     bg=SUCCESS).pack(fill="x", pady=6)

        self._render_cart()

    def _search(self):
        term = self.search_var.get().strip()
        rows = ops.list_products(term)
        self.tree.delete(*self.tree.get_children())
        if not rows:
            hint = "No products found"
            if term:
                hint += f" for '{term}'"
            else:
                hint += " — add some in the Products tab"
            _empty_row(self.tree, hint)
            return
        for p in rows:
            self.tree.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["name"], fmt_money(p["price"]), p["stock_qty"],
            ))

    def _add_selected(self):
        try:
            pid = int(self.tree.selection()[0])
        except (IndexError, ValueError):
            self.app._flash_status("Select a product to add")
            return
        try:
            qty = int(self.qty_var.get()) or 1
        except ValueError:
            qty = 1
        prod = ops.get_product(pid)
        if not prod:
            return
        if qty > prod["stock_qty"]:
            self.app._flash_status(f"Only {prod['stock_qty']} in stock")
            return
        for item in self.cart:
            if item["id"] == pid:
                item["qty"] += qty
                break
        else:
            self.cart.append({"id": pid, "name": prod["name"], "qty": qty,
                              "price": prod["price"], "discount": 0})
        self._render_cart()
        self._count_up()

    def _remove_selected(self):
        sel = self.cart_list.curselection()
        if not sel:
            return
        del self.cart[sel[0]]
        self._render_cart()

    def _apply_discount(self):
        """Apply the discount field to the currently selected cart line."""
        sel = self.cart_list.curselection()
        if not sel:
            self.app._flash_status("Select a cart line to discount")
            return
        try:
            d = int(self.disc_var.get().strip().replace(",", "").replace("KSh", ""))
        except ValueError:
            messagebox.showerror("Discount", "Enter a whole number of shillings")
            return
        item = self.cart[sel[0]]
        if d < 0:
            messagebox.showerror("Discount", "Discount cannot be negative")
            return
        if d > item["price"]:
            messagebox.showerror(
                "Discount", "Discount cannot exceed the unit price")
            return
        item["discount"] = d
        self.disc_var.set("0")
        self._render_cart()
        self.app._flash_status(f"Discount applied to {item['name']}")

    def _render_cart(self):
        self.cart_list.delete(0, "end")
        self.total = 0
        for idx, item in enumerate(self.cart):
            line = (item["price"] - item["discount"]) * item["qty"]
            self.total += line
            name = item["name"]
            if item["discount"]:
                name += f" (-{item['discount']})"
            self.cart_list.insert(
                "end",
                f"{item['qty']:>3} x {name:<30} {fmt_money(line):>13}",
            )
        self.total_lbl.configure(text=fmt_money(self.total))

    def _count_up(self):
        # animate total from 0 to target over ~0.3s
        target = self.total
        start = 0
        steps = 12

        def step(i):
            if i > steps:
                self.total_lbl.configure(text=fmt_money(target))
                return
            frac = i / steps
            eased = 1 - (1 - frac) ** 2
            self.total_lbl.configure(
                text=fmt_money(round(start + (target - start) * eased)))
            self.after(18, lambda: step(i + 1))

        step(0)

    def _checkout(self):
        if not self.cart:
            self.app._flash_status("Cart is empty")
            return
        method = self.pmethod.get()
        tendered = 0
        if method == "cash":
            tendered = self._prompt_tendered()
            if tendered is None:
                return
        items = [(i["id"], i["qty"], i["discount"]) for i in self.cart]
        ok, result = ops.create_sale(
            self.app.cashier_id, method, items, tendered=tendered)
        if not ok:
            messagebox.showerror("Checkout", result)
            self._search()
            return
        self._celebrate(result)
        self._show_receipt(result, tendered)
        self.cart.clear()
        self._render_cart()
        self._search()

    def _prompt_tendered(self):
        """Ask for the cash amount tendered. Returns int or None if cancelled."""
        dialog = tk.Toplevel(self)
        dialog.title("Cash Tendered")
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        result = {"value": None}

        tk.Label(
            dialog, text=f"Total: {fmt_money(self.total)}", bg=BG, fg=TEXT,
            font=("Segoe UI", 14, "bold"), padx=20, pady=(14, 4),
        ).pack()
        tk.Label(
            dialog, text="Amount received:", bg=BG, fg=MUTED,
            font=("Segoe UI", 11),
        ).pack()
        var = tk.StringVar()
        entry = RoundedEntry(dialog, textvariable=var, bg=PANEL, fg=TEXT,
                             font=("Segoe UI", 14), width_chars=12)
        entry.pack(padx=20, pady=8)
        entry.entry.focus_set()

        def confirm():
            try:
                amt = int(var.get().strip().replace(",", "").replace("KSh", ""))
            except ValueError:
                messagebox.showerror("Cash", "Enter a whole number of shillings")
                return
            if amt < self.total:
                messagebox.showerror("Cash", "Amount tendered is less than the total")
                return
            result["value"] = amt
            dialog.destroy()

        entry.entry.bind("<Return>", lambda _: confirm())
        btns = tk.Frame(dialog, bg=BG)
        btns.pack(pady=(4, 14))
        AccentButton(btns, text="OK", command=confirm).pack(side="left", padx=6)
        AccentButton(
            btns, text="Cancel", command=dialog.destroy, bg=PANEL2).pack(
            side="left", padx=6)

        dialog.wait_window()
        return result["value"]

    def _celebrate(self, sale_id):
        overlay = tk.Toplevel(self)
        overlay.overrideredirect(True)
        overlay.configure(bg=SUCCESS)
        overlay.attributes("-topmost", True)
        # center over window
        self.update_idletasks()
        x = self.winfo_rootx() + 120
        y = self.winfo_rooty() + 150
        overlay.geometry(f"+{x}+{y}")
        tk.Label(
            overlay, text=f"✓ Sale #{sale_id}\nSuccessful!",
            bg=SUCCESS, fg="white", font=("Segoe UI", 20, "bold"),
            padx=30, pady=20,
        ).pack()
        for _, size in enumerate(range(1, 12)):
            overlay.after(size * 12, lambda s=size: overlay.tk.call(
                "wm", "geometry", overlay,
                f"{300 + s*4}x{180 + s*3}+{x - s*2}+{y - s*2}",
            ))
        overlay.after(1100, overlay.destroy)

    def _show_receipt(self, sale_id, tendered):
        """Show an on-screen printable receipt for the completed sale."""
        win = tk.Toplevel(self)
        win.title(f"Receipt - Sale #{sale_id}")
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()

        text = tk.Text(win, bg="white", fg="black", font=("Consolas", 11),
                       padx=14, pady=10, wrap="none", relief="flat",
                       width=40, height=24)
        text.pack(padx=10, pady=10)

        cashier = self.app.cashier_name
        lines = [
            "        ELECTRONSTORE POS        ",
            "---------------------------------",
            f"Sale #: {sale_id:>22}",
            f"Date: {datetime.now():%Y-%m-%d %H:%M}",
            f"Cashier: {cashier}",
            "---------------------------------",
        ]
        for it in self.cart:
            unit = it["price"]
            if it["discount"]:
                unit -= it["discount"]
            line_total = unit * it["qty"]
            lines.append(f"{it['name']}")
            lines.append(
                f"  {it['qty']} x {fmt_money(unit)}  {fmt_money(line_total):>14}")
        lines += [
            "---------------------------------",
            f"TOTAL{fmt_money(self.total):>31}",
        ]
        if tendered:
            lines += [
                f"Tendered{fmt_money(tendered):>28}",
                f"Change{fmt_money(tendered - self.total):>30}",
            ]
        lines += [
            "---------------------------------",
            "      THANK YOU - COME AGAIN      ",
        ]
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

        def print_receipt():
            from paths import EXPORT_DIR, ensure_dirs
            try:
                text.configure(state="normal")
                text.update_idletasks()
                ensure_dirs()
                text.postscript(file=str(EXPORT_DIR / f"receipt_{sale_id}.ps"))
                text.configure(state="disabled")
            except Exception:
                messagebox.showinfo(
                    "Print", "Open the receipt screen and use your system "
                    "print dialog / screenshot to print.")
            backup = EXPORT_DIR / f"receipt_{sale_id}.txt"
            with open(backup, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            self.app._flash_status(f"Receipt saved to {backup}")

        btns = tk.Frame(win, bg=BG)
        btns.pack(pady=(0, 10))
        AccentButton(btns, text="Save / Print", command=print_receipt).pack(
            side="left", padx=6)
        AccentButton(btns, text="Close", command=win.destroy, bg=PANEL2).pack(
            side="left", padx=6)


# --------------------------------------------------------------------------
# SALES VIEW (recent sales, view receipt, void)
# --------------------------------------------------------------------------
class SalesView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=10)
        tk.Label(top, text="Recent Sales", bg=BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        AccentButton(top, text="Refresh", command=self._refresh).pack(
            side="right", padx=6)
        AccentButton(top, text="Void Selected Sale",
                     command=self._void_sale, bg=DANGER).pack(
            side="right", padx=6
        )

        cols = ("id", "datetime", "total", "method", "cashier", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("id", text="#")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("total", text="Total")
        self.tree.heading("method", text="Method")
        self.tree.heading("cashier", text="Cashier")
        self.tree.heading("status", text="Status")
        self.tree.column("id", width=70, anchor="center")
        self.tree.column("datetime", width=180, anchor="center")
        self.tree.column("total", width=120, anchor="center")
        self.tree.column("method", width=90, anchor="center")
        self.tree.column("cashier", width=140, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        style = ttk.Style()
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                        relief="flat", font=("Segoe UI", 10, "bold"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.tag_configure("voided", foreground=MUTED)
        self.tree.tag_configure("empty", foreground=MUTED)
        self.tree.bind("<Double-Button-1>", lambda _: self._view_receipt())

        info = tk.Label(
            self, text="Double-click a sale to view its receipt. Only Managers "
                       "can void a sale (restocks items).",
            bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w",
        )
        info.pack(fill="x", padx=12, pady=(0, 10))

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = ops.recent_sales(50)
        if not rows:
            _empty_row(self.tree, "No sales yet — ring one up in New Sale")
            return
        for s in rows:
            status = "VOIDED" if s["voided"] else "OK"
            tag = "voided" if s["voided"] else ""
            self.tree.insert("", "end", iid=str(s["id"]), values=(
                s["id"], s["datetime"], fmt_money(s["total"]),
                s["payment_method"].title(), s["cashier"] or "-", status,
            ), tags=(tag,))

    def _selected_id(self):
        try:
            return int(self.tree.selection()[0])
        except (IndexError, ValueError):
            return None

    def _view_receipt(self):
        sale_id = self._selected_id()
        if not sale_id:
            return
        sale, items = ops.get_sale(sale_id)
        if not sale:
            messagebox.showerror("Receipt", "Sale not found")
            return
        win = tk.Toplevel(self)
        win.title(f"Receipt - Sale #{sale_id}")
        win.configure(bg=BG)
        win.transient(self)
        text = tk.Text(win, bg="white", fg="black", font=("Consolas", 11),
                       padx=14, pady=10, wrap="none", relief="flat",
                       width=40, height=24)
        text.pack(padx=10, pady=10)
        lines = [
            "        ELECTRONSTORE POS        ",
            "---------------------------------",
            f"Sale #: {sale['id']:>21}",
            f"Date: {sale['datetime']}",
            "---------------------------------",
        ]
        for it in items:
            unit = it["unit_price"] - it["discount"]
            lines.append(f"{it['name']}")
            lines.append(
                f"  {it['quantity']} x {fmt_money(unit)}  "
                f"{fmt_money(unit * it['quantity']):>14}")
        lines += [
            "---------------------------------",
            f"TOTAL{fmt_money(sale['total']):>31}",
        ]
        if sale["payment_method"] == "cash" and sale["tendered"]:
            lines += [
                f"Tendered{fmt_money(sale['tendered']):>28}",
                f"Change{fmt_money(sale['change']):>30}",
            ]
        if sale["voided"]:
            lines += [
                "---------------------------------",
                f"   ** VOIDED ** {sale['void_reason'] or ''}",
            ]
        lines += [
            "---------------------------------",
            "      THANK YOU - COME AGAIN      ",
        ]
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")
        AccentButton(win, text="Close", command=win.destroy, bg=PANEL2).pack(
            pady=(0, 10))

    def _void_sale(self):
        if not self.app.is_manager:
            messagebox.showerror("Void", "Only Managers can void a sale")
            return
        sale_id = self._selected_id()
        if not sale_id:
            self.app._flash_status("Select a sale to void")
            return
        sale, _ = ops.get_sale(sale_id)
        if not sale:
            return
        if sale["voided"]:
            messagebox.showerror("Void", "That sale is already voided")
            return
        if not messagebox.askyesno(
                "Void Sale",
                f"Void sale #{sale_id} for {fmt_money(sale['total'])}? "
                "Items will be returned to stock."):
            return
        ok, msg = ops.void_sale(sale_id)
        messagebox.showinfo("Void", msg)
        self._refresh()


# --------------------------------------------------------------------------
# PRODUCTS VIEW
# --------------------------------------------------------------------------
class ProductsView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=10, pady=10, ipady=8)

        fields = ["name", "category", "code", "price", "cost"]
        self.vars = {f: tk.StringVar() for f in fields}
        for i, f in enumerate(fields):
            label = "Product Code" if f == "code" else f.capitalize()
            tk.Label(form, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10)).grid(row=0, column=i * 2, padx=(10, 4))
            RoundedEntry(form, textvariable=self.vars[f], bg=PANEL2, fg=TEXT,
                         font=("Segoe UI", 11), width_chars=12).grid(
                row=1, column=i * 2, padx=10, pady=4
            )

        tk.Label(form, text="Stock", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).grid(row=0, column=10, padx=4)
        self.vars["stock"] = tk.StringVar(value="0")
        RoundedEntry(form, textvariable=self.vars["stock"], bg=PANEL2, fg=TEXT,
                     font=("Segoe UI", 11), width_chars=5).grid(
            row=1, column=10, padx=10
        )

        acc = tk.Frame(form, bg=PANEL)
        acc.grid(row=1, column=12, rowspan=2, padx=10)
        AccentButton(acc, text="Add Product", command=self._add).pack(pady=2)
        AccentButton(acc, text="Save Changes", command=self._edit,
                     bg=PANEL2).pack(pady=2)
        AccentButton(acc, text="Restock", command=self._restock,
                     bg=PANEL2).pack(pady=2)
        AccentButton(acc, text="Delete", command=self._delete,
                     bg=DANGER).pack(pady=2)
        self._editing_id = None

        # list
        cols = ("id", "name", "category", "code", "price", "cost", "stock")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c, w in [("id", 50), ("name", 200), ("category", 100),
                     ("code", 90), ("price", 110), ("cost", 110), ("stock", 70)]:
            self.tree.heading(c, text="Product Code" if c == "code" else c.upper())
            self.tree.column(c, width=w, anchor="center")
        self.tree.column("name", anchor="w")
        style = ttk.Style()
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                        relief="flat", font=("Segoe UI", 10, "bold"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.tag_configure("low", foreground=WARN)
        self.tree.tag_configure("out", foreground=DANGER)
        self.tree.tag_configure("empty", foreground=MUTED)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._refresh()

    def _parse_int(self, s, what):
        s = s.strip().replace(",", "").replace("KSh", "").replace(" ", "")
        try:
            return int(float(s))
        except ValueError:
            raise ValueError(f"{what} must be a number")

    def _add(self):
        try:
            ok, msg = ops.add_product(
                self.vars["name"].get(),
                self.vars["category"].get(),
                self.vars["code"].get(),
                self._parse_int(self.vars["price"].get(), "Price"),
                self._parse_int(self.vars["cost"].get(), "Cost"),
                int(self.vars["stock"].get() or 0),
            )
        except ValueError as e:
            messagebox.showerror("Product", str(e))
            return
        messagebox.showinfo("Product", msg)
        self._clear_form()
        self._refresh()

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            pid = int(sel[0])
        except ValueError:
            return
        p = ops.get_product(pid)
        if not p:
            return
        self._editing_id = pid
        self.vars["name"].set(p["name"])
        self.vars["category"].set(p["category"])
        self.vars["code"].set(p["code"])
        self.vars["price"].set(str(p["price"]))
        self.vars["cost"].set(str(p["cost_price"]))
        self.vars["stock"].set(str(p["stock_qty"]))

    def _edit(self):
        if not self._editing_id:
            messagebox.showerror("Product", "Select a product to edit")
            return
        try:
            ok, msg = ops.update_product(
                self._editing_id,
                self.vars["name"].get(),
                self.vars["category"].get(),
                self.vars["code"].get(),
                self._parse_int(self.vars["price"].get(), "Price"),
                self._parse_int(self.vars["cost"].get(), "Cost"),
            )
        except ValueError as e:
            messagebox.showerror("Product", str(e))
            return
        messagebox.showinfo("Product", msg)
        self._clear_form()
        self._refresh()

    def _restock(self):
        if not self._editing_id:
            messagebox.showerror("Product", "Select a product to restock")
            return
        p = ops.get_product(self._editing_id)
        amt = simpledialog.askinteger(
            "Restock",
            f"Adjust stock for {p['name']}.\n"
            f"Current stock: {p['stock_qty']}\n"
            "Enter a positive number to add, negative to remove:",
            parent=self, minvalue=-99999, maxvalue=99999,
        )
        if amt is None:
            return
        ok, msg = ops.restock(self._editing_id, amt)
        messagebox.showinfo("Restock", msg)
        self._clear_form()
        self._refresh()

    def _delete(self):
        if not self._editing_id:
            messagebox.showerror("Product", "Select a product to delete")
            return
        p = ops.get_product(self._editing_id)
        if not messagebox.askyesno(
                "Delete Product",
                f"Delete {p['name']} and its sales history? This cannot be undone."):
            return
        ok, msg = ops.delete_product(self._editing_id)
        messagebox.showinfo("Delete", msg)
        self._clear_form()
        self._refresh()

    def _clear_form(self):
        self._editing_id = None
        for v in self.vars.values():
            v.set("")
        self.tree.selection_remove(self.tree.selection())

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = ops.list_products()
        if not rows:
            _empty_row(self.tree, "No products yet — add your first product")
            return
        for p in rows:
            tag = ""
            if p["stock_qty"] <= 0:
                tag = "out"
            elif p["stock_qty"] <= 5:
                tag = "low"
            self.tree.insert("", "end", values=(
                p["id"], p["name"], p["category"], p["code"],
                fmt_money(p["price"]), fmt_money(p["cost_price"]), p["stock_qty"],
            ), tags=(tag,))


# --------------------------------------------------------------------------
# REPORTS VIEW
# --------------------------------------------------------------------------
class ReportsView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.chart = None

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(toolbar, text="Days:", bg=BG, fg=MUTED,
                 font=("Segoe UI", 11)).pack(side="left")
        self.days = tk.StringVar(value="30")
        cb = ttk.Combobox(toolbar, textvariable=self.days, state="readonly",
                          values=["7", "14", "30", "90"], width=5)
        cb.pack(side="left", padx=6)
        AccentButton(toolbar, text="Refresh", command=self._refresh).pack(side="left")
        AccentButton(toolbar, text="By Staff", command=self._staff_report).pack(
            side="left", padx=4)
        AccentButton(toolbar, text="End of Day", command=self._end_of_day).pack(
            side="left", padx=4)
        for text, cmd in [
            ("Export CSV", self._export_csv),
            ("Export PDF", self._export_pdf),
        ]:
            AccentButton(toolbar, text=text, command=cmd).pack(side="right", padx=4)

        self.overview = tk.Frame(self, bg=BG)
        self.overview.pack(fill="x", padx=10)
        self._build_overview()

        chart_area = tk.Frame(self, bg=BG)
        chart_area.pack(fill="both", expand=True, padx=10, pady=4)
        self.chart_frame = tk.Frame(chart_area, bg=BG)
        self.chart_frame.pack(side="left", fill="both", expand=True)

        side = tk.Frame(chart_area, bg=PANEL, width=260)
        side.pack(side="right", fill="y", padx=(8, 0))
        self.side = side
        self._build_side()

        self._refresh()

    def _build_overview(self):
        for c in self.overview.winfo_children():
            c.destroy()
        prof = ops.profit_overall()
        cards = [
            ("Revenue", fmt_money(prof['revenue']), ACCENT),
            ("Profit", fmt_money(prof['profit']), SUCCESS),
            ("Margin", f"{prof['margin']:.1f}%", WARN),
        ]
        for i, (label, val, color) in enumerate(cards):
            card = tk.Frame(self.overview, bg=PANEL, width=200, height=70)
            card.pack(side="left", padx=6, fill="both", expand=True, pady=4)
            card.pack_propagate(False)
            tk.Label(card, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10)).pack(pady=(8, 0))
            tk.Label(card, text=val, bg=PANEL, fg=color,
                     font=("Segoe UI", 16, "bold")).pack()

    def _build_side(self):
        for c in self.side.winfo_children():
            c.destroy()
        tk.Label(self.side, text="Top Sellers", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.side_tree = ttk.Treeview(
            self.side, columns=("units",), show="headings", height=12,
            style="Side.Treeview",
        )
        self.side_tree.heading("units", text="Units")
        self.side_tree.column("units", width=60, anchor="center")
        st = ttk.Style()
        st.configure("Side.Treeview", background=PANEL, fieldbackground=PANEL,
                     foreground=TEXT, rowheight=24)
        st.configure("Side.Treeview.Heading", background=PANEL2, foreground=TEXT)
        self.side_tree.column("#0", width=180, anchor="w")
        self.side_tree.pack(fill="both", expand=True, padx=8, pady=4)

        tk.Label(self.side, text="By Category", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.cat_labels = []
        cat_frame = tk.Frame(self.side, bg=PANEL)
        cat_frame.pack(fill="x", padx=12, pady=4)
        self.cat_frame = cat_frame

    def _refresh(self):
        try:
            days = int(self.days.get())
        except ValueError:
            days = 30
        self._render_pie(chart_days=30)
        self._render_bars(days)
        self._fill_side()
        self._build_overview()

    def _render_bars(self, days):
        try:
            import matplotlib
            matplotlib.use("TkAgg", force=True)
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            return self._draw_ascii_bars(days)
        for c in self.chart_frame.winfo_children():
            c.destroy()
        data = ops.revenue_by_range(days)
        x = [r["day"][5:] for r in data]
        y = [r["revenue"] for r in data]
        fig = Figure(figsize=(6, 3.4), dpi=90, facecolor="#0f172a")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#0f172a")
        ax.bar(x, y, color="#38bdf8" if len(x) < 35 else "none",
               edgecolor="#38bdf8", linewidth=0.6)
        if len(x) >= 35:
            ax.plot(x, y, color="#38bdf8")
        ax.set_title("Daily Revenue", color="#e2e8f0")
        ax.tick_params(colors="#94a3b8")
        ax.grid(color="#334155", alpha=0.4)
        ax.set_ylabel(CURRENCY_SYMBOL, color="#94a3b8")
        if len(x) > 12:
            ax.set_xticks(range(0, len(x), max(1, len(x) // 12)))
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_ascii_bars(self, days):
        # Fallback when matplotlib missing.
        for c in self.chart_frame.winfo_children():
            c.destroy()
        data = ops.revenue_by_range(days)
        box = tk.Text(self.chart_frame, bg=PANEL, fg=TEXT, relief="flat",
                      font=("Consolas", 10))
        box.pack(fill="both", expand=True)
        box.insert("1.0", "  Daily Revenue\n")
        if not data:
            box.insert("end", "  No sales yet.\n")
            return
        mx = max(r["revenue"] for r in data) or 1
        for r in data:
            bar = "█" * int(30 * r["revenue"] / mx)
            box.insert("end", f"  {r['day'][5:]} {bar} {fmt_money(r['revenue'])}\n")
        box.configure(state="disabled")

    def _render_pie(self, chart_days=30):
        # Category share pie in the side panel.
        try:
            import matplotlib
            matplotlib.use("TkAgg", force=True)
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            return
        cats = ops.sales_by_category()
        if not cats:
            return
        fig = Figure(figsize=(3.2, 2.2), dpi=90, facecolor=PANEL)
        ax = fig.add_subplot(111)
        ax.pie([c["revenue"] for c in cats], labels=[c["category"] for c in cats],
               autopct="%1.0f%%", textprops={"color": "white", "size": 8},
               colors=["#38bdf8", "#2563eb", "#22c55e", "#f59e0b", "#ef4444",
                       "#a855f7"])
        fig.tight_layout(pad=0)
        canvas = FigureCanvasTkAgg(fig, master=self.cat_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def _fill_side(self):
        self.side_tree.delete(*self.side_tree.get_children())
        for p in ops.top_products(10):
            self.side_tree.insert("", "end", text=p["name"], values=(p["units"],))

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        from export import export_csv
        export_csv(Path(path).name,
                   ["Day", "Revenue"],
                   [[r["day"], f"{r['revenue']:.2f}"] for r in ops.revenue_by_range(30)])
        self.app._flash_status(f"CSV saved: {path}")

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            from export import export_pdf
            prof = ops.profit_overall()
            sections = [
                ("Profit Overview", [
                    ("Revenue", fmt_money(prof['revenue'])),
                    ("Cost", fmt_money(prof['cost'])),
                    ("Profit", fmt_money(prof['profit'])),
                    ("Margin", f"{prof['margin']:.1f}%"),
                ]),
                ("Top Products", [
                    (p["name"], str(p["units"]), fmt_money(p['revenue']))
                    for p in ops.top_products(10)
                ]),
            ]
            export_pdf("Store Sales Report", sections)
            self.app._flash_status("PDF saved to exports/report.pdf")
        except Exception as e:
            messagebox.showerror("PDF", f"Could not build PDF: {e}")

    def _report_dialog(self, title, headers, rows):
        """Show a simple modal table with a Save CSV button."""
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        cols = tuple(str(h) for h in headers)
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for h in cols:
            tree.heading(h, text=h.title() if h != "id" else "ID")
            tree.column(h, anchor="center", width=110)
        tree.column("day" if "day" in cols else "cashier", width=140)
        for row in rows:
            tree.insert("", "end", values=tuple(row))
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def save_csv():
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            from export import export_csv
            export_csv(Path(path).name, list(headers), [list(r) for r in rows])
            self.app._flash_status(f"Saved: {Path(path).name}")

        btns = tk.Frame(win, bg=BG)
        btns.pack(pady=(0, 12))
        AccentButton(btns, text="Save CSV", command=save_csv).pack(
            side="left", padx=6)
        AccentButton(btns, text="Close", command=win.destroy, bg=PANEL2).pack(
            side="left", padx=6)

    def _staff_report(self):
        rows = ops.sales_by_cashier()
        if not rows:
            messagebox.showinfo("By Staff", "No sales recorded yet.")
            return
        data = [(r["cashier"], r["transactions"], r["units"],
                 fmt_money(r["revenue"])) for r in rows]
        self._report_dialog(
            "Sales by Staff",
            ["Cashier", "Sales", "Units", "Revenue"],
            data,
        )

    def _end_of_day(self):
        day = simpledialog.askstring(
            "End of Day",
            "Enter date as YYYY-MM-DD (leave blank for today):",
            parent=self,
        )
        if day is None:
            return
        day = day.strip() if day else None
        rep = ops.end_of_day_report(day)
        label = day or "Today"
        methods = rep["methods"]
        rows = []
        for m in ("cash", "card", "mobile"):
            r = methods.get(m)
            if r:
                rows.append((m.title(), r["txns"], fmt_money(r["val"])))
        rows.append(("Total", "-", fmt_money(rep["grand"])))
        rows.append(("Units sold", "-", str(rep["units"])))
        rows.append(("Voided sales", str(rep["voids"]), fmt_money(rep["void_value"])))
        self._report_dialog(f"End of Day - {label}",
                            ["Method", "Count", "Total"],
                            rows)


# --------------------------------------------------------------------------
# EMPLOYEES VIEW
# --------------------------------------------------------------------------
class EmployeesView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(top, text="Staff", bg=BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        if not app.is_manager:
            tk.Label(top, text="Only managers can add or edit staff.",
                     bg=BG, fg=WARN, font=("Segoe UI", 10)).pack(side="left", padx=16)

        # Columns
        cols = ("id", "name", "role", "pin", "actions")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c, w, txt in [("id", 40, "ID"), ("name", 200, "Name"),
                          ("role", 110, "Role"), ("pin", 90, "PIN"),
                          ("actions", 240, "")]:
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="w")
        self.tree.column("id", anchor="center")
        self.tree.column("pin", anchor="center")

        style = ttk.Style()
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=32, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                        relief="flat", font=("Segoe UI", 10, "bold"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.tag_configure("empty", foreground=MUTED)

        self._btn_frame = tk.Frame(self, bg=BG)
        self._btn_frame.pack(fill="x", padx=10, pady=6)
        self._selected_id = None
        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = ops.list_employees()
        if not rows:
            _empty_row(self.tree, "No staff yet — add your first cashier")
            self._build_actions()
            return
        for e in rows:
            self.tree.insert("", "end", iid=str(e["id"]), values=(
                e["id"], e["name"], e["role"], "••••", ""
            ))
        self._build_actions()

    def _build_actions(self):
        for c in self._btn_frame.winfo_children():
            c.destroy()

        if not self.app.is_manager:
            tk.Label(self._btn_frame, text="Viewing only.",
                     bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(side="left")
            return

        # Add-employee form
        tk.Label(self._btn_frame, text="Add staff:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 11)).pack(side="left")
        self._name_var = tk.StringVar()
        RoundedEntry(self._btn_frame, textvariable=self._name_var, bg=PANEL,
                     fg=TEXT, font=("Segoe UI", 11), width_chars=10).pack(
            side="left", padx=4)

        self._role_var = tk.StringVar(value="Employee")
        role = ttk.Combobox(self._btn_frame, textvariable=self._role_var,
                            values=["Manager", "Employee"], state="readonly",
                            width=8)
        role.pack(side="left", padx=4)

        self._pin_var = tk.StringVar()
        RoundedEntry(self._btn_frame, textvariable=self._pin_var, bg=PANEL,
                     fg=TEXT, font=("Segoe UI", 11), width_chars=6,
                     show="*").pack(side="left", padx=4)

        AccentButton(self._btn_frame, text="Add",
                     command=self._add_employee).pack(side="left", padx=4)

        # Actions on selection
        tk.Label(self._btn_frame, text="|  Selected:", bg=BG, fg=MUTED,
                 font=("Segoe UI", 11)).pack(side="left", padx=(16, 4))
        AccentButton(self._btn_frame, text="Set Manager",
                     command=lambda: self._set_role("Manager")).pack(
            side="left", padx=3)
        AccentButton(self._btn_frame, text="Set Employee",
                     command=lambda: self._set_role("Employee")).pack(
            side="left", padx=3)
        AccentButton(self._btn_frame, text="Reset PIN",
                     command=self._reset_pin).pack(side="left", padx=3)
        AccentButton(self._btn_frame, text="Delete", bg=DANGER,
                     command=self._delete).pack(side="left", padx=3)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _):
        sel = self.tree.selection()
        try:
            self._selected_id = int(sel[0]) if sel else None
        except ValueError:
            self._selected_id = None

    def _add_employee(self):
        name = self._name_var.get().strip()
        role = self._role_var.get()
        pin = self._pin_var.get().strip()
        if not name or not pin:
            messagebox.showerror("Add staff", "Name and PIN are required.")
            return
        if ops.employee_with_pin_exists(pin):
            messagebox.showerror("Add staff", "That PIN is already in use.")
            return
        ok, msg = ops.add_employee(name, role, pin)
        messagebox.showinfo("Add staff", msg)
        self._name_var.set("")
        self._pin_var.set("")
        self._refresh()

    def _set_role(self, role):
        if self._selected_id is None:
            self.app._flash_status("Select an employee first")
            return
        if self._selected_id == self.app.cashier_id:
            messagebox.showerror("Role", "You cannot change your own role.")
            return
        ok, msg = ops.update_employee_role(self._selected_id, role)
        messagebox.showinfo("Role", msg)
        self._refresh()

    def _reset_pin(self):
        if self._selected_id is None:
            self.app._flash_status("Select an employee first")
            return
        import tkinter.simpledialog as sd
        new_pin = sd.askstring(
            "Reset PIN", "New PIN:", show="*", parent=self)
        if new_pin is None:
            return
        ok, msg = ops.reset_employee_pin(self._selected_id, new_pin.strip())
        messagebox.showinfo("Reset PIN", msg)
        self._refresh()

    def _delete(self):
        if self._selected_id is None:
            self.app._flash_status("Select an employee first")
            return
        if self._selected_id == self.app.cashier_id:
            messagebox.showerror("Delete", "You cannot delete your own account.")
            return
        if not messagebox.askyesno(
                "Delete", "Delete this employee? This cannot be undone."):
            return
        ok, msg = ops.delete_employee(self._selected_id)
        messagebox.showinfo("Delete", msg)
        self._refresh()


def _set_window_icon(root):
    """Best-effort window/taskbar icon (never crashes if the file is absent)."""
    try:
        if ICON_PATH.exists():
            root.iconbitmap(str(ICON_PATH))
    except Exception:
        pass


def run_gui():
    init_db()
    conn = ops.get_conn()
    count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    conn.close()
    if count == 0:
        ops.add_employee("Manager", "Manager", "1234")

    root = tk.Tk()
    root.title("ElectronStore POS - Login")
    root.geometry("420x260")
    root.resizable(False, False)
    root.report_callback_exception = LoginWindow._error_hook
    _set_window_icon(root)

    LoginWindow(root)
    root.mainloop()


class LoginWindow(tk.Frame):
    def __init__(self, root):
        super().__init__(root, bg=BG)
        self.root = root
        self.pack(fill="both", expand=True)

        tk.Label(self, text="ElectronStore", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 24, "bold")).pack(pady=(30, 4))
        tk.Label(self, text="Enter your PIN to continue", bg=BG, fg=MUTED,
                 font=("Segoe UI", 12)).pack(pady=(0, 16))

        self.pin = tk.StringVar()
        entry = RoundedEntry(self, textvariable=self.pin, show="*",
                             bg=PANEL, fg=TEXT, justify="center",
                             font=("Segoe UI", 18), width_chars=10)
        entry.pack(pady=6)
        entry.entry.bind("<Return>", lambda _: self.try_login())
        entry.entry.focus_set()

        AccentButton(self, text="Login", command=self.try_login,
                     bg=SUCCESS).pack(pady=12)

        self.status = tk.Label(self, text="", bg=BG, fg=DANGER,
                               font=("Segoe UI", 10))
        self.status.pack()

    @staticmethod
    def _error_hook(exc, val, tb):
        import traceback

        from logutil import get_logger
        get_logger().error(
            "Unhandled exception", exc_info=(exc, val, tb))

        messagebox.showerror("ElectronStore", "Unexpected error:\n" + "".join(
            traceback.format_exception(exc, val, tb)))
        root = tk._default_root
        if root:
            root.destroy()

    def try_login(self):
        emp = ops.auth_employee(self.pin.get())
        if not emp:
            self.status.configure(text="Invalid PIN")
            self.pin.set("")
            return
        self.destroy()
        self.root.configure(bg=BG)
        self.root.title("ElectronStore POS")
        self.root.geometry("1100x700")
        self.root.resizable(True, True)
        Toplevel(self.root, emp["id"], emp["name"], emp["role"]).pack(
            fill="both", expand=True
        )


if __name__ == "__main__":
    run_gui()
