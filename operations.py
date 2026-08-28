import sqlite3

from db import connection, get_conn
from security import hash_pin, verify_pin


def add_product(name, category, code, price, cost_price, stock_qty):
    try:
        with connection() as conn:
            conn.execute(
                "INSERT INTO products (name, category, code, price, cost_price, stock_qty) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, category, code, price, cost_price, stock_qty),
            )
        return True, "Product added"
    except sqlite3.IntegrityError:
        return False, "Product code already exists"


def list_products(search=None):
    with connection() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR code LIKE ? OR category LIKE ? "
                "ORDER BY name",
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    return rows


def get_product(product_id):
    with connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)).fetchone()


def update_stock(product_id, delta):
    with connection() as conn:
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty + ? WHERE id=?",
            (delta, product_id),
        )


def low_stock(threshold=5):
    with connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE stock_qty <= ? ORDER BY stock_qty",
            (threshold,),
        ).fetchall()


def update_product(product_id, name, category, code, price, cost_price):
    """Edit a product's details. Returns (ok, message)."""
    try:
        with connection() as conn:
            conn.execute(
                "UPDATE products SET name=?, category=?, code=?, price=?, cost_price=? "
                "WHERE id=?",
                (name, category, code, price, cost_price, product_id),
            )
        return True, "Product updated"
    except sqlite3.IntegrityError:
        return False, "Product code already exists"


def restock(product_id, add_qty):
    """Increase (or decrease, with negative delta) the stock of a product."""
    with connection() as conn:
        row = conn.execute(
            "SELECT stock_qty FROM products WHERE id=?", (product_id,)).fetchone()
        if not row:
            return False, "Product not found"
        new_stock = row["stock_qty"] + add_qty
        if new_stock < 0:
            return False, "Stock cannot go below zero"
        conn.execute(
            "UPDATE products SET stock_qty=? WHERE id=?",
            (new_stock, product_id),
        )
    return True, f"Stock is now {new_stock}"


def delete_product(product_id):
    """Remove a product and its line-item history. Returns (ok, message)."""
    try:
        with connection() as conn:
            conn.execute("DELETE FROM sale_items WHERE product_id=?", (product_id,))
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        return True, "Product deleted"
    except Exception:
        return False, "Could not delete product"


def create_sale(cashier_id, payment_method, items, tendered=0):
    """items = list of (product_id, quantity, discount)

    All money values are integer shillings. tendered (cash) is used to
    compute change owed. Returns (True, sale_id) on success.
    """
    try:
        with connection() as conn:
            total = 0
            line_items = []
            if payment_method not in ("cash", "card", "mobile"):
                raise ValueError(
                    f"Unknown payment method: {payment_method}")
            for product_id, qty, line_discount in items:
                prod = conn.execute(
                    "SELECT * FROM products WHERE id=?", (product_id,)
                ).fetchone()
                if not prod:
                    raise ValueError(f"Product {product_id} not found")
                if prod["stock_qty"] < qty:
                    raise ValueError(f"Insufficient stock for {prod['name']}")
                line_total = (prod["price"] - line_discount) * qty
                total += line_total
                line_items.append((prod, qty, line_discount, line_total))

            change = 0
            if payment_method == "cash":
                if tendered < total:
                    raise ValueError("Amount tendered is less than the total")
                change = tendered - total

            cur = conn.execute(
                "INSERT INTO sales (cashier_id, total, payment_method, tendered, change) "
                "VALUES (?, ?, ?, ?, ?)",
                (cashier_id, total, payment_method, tendered, change),
            )
            sale_id = cur.lastrowid

            for prod, qty, line_discount, line_total in line_items:
                conn.execute(
                    "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (sale_id, prod["id"], qty, prod["price"], line_discount),
                )
                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty - ? WHERE id=?",
                    (qty, prod["id"]),
                )
        return True, sale_id
    except ValueError as e:
        return False, str(e)


def get_sale(sale_id):
    """Return a sale row with its line items."""
    with connection() as conn:
        sale = conn.execute(
            "SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if sale:
            items = conn.execute(
                """
                SELECT si.*, p.name
                FROM sale_items si JOIN products p ON p.id = si.product_id
                WHERE si.sale_id=? ORDER BY si.id
                """,
                (sale_id,),
            ).fetchall()
        else:
            items = []
    return sale, items


def void_sale(sale_id, reason=""):
    """Reverse a sale: restock items, mark it voided. Guards against double-void."""
    try:
        with connection() as conn:
            sale = conn.execute(
                "SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
            if not sale:
                return False, "Sale not found"
            if sale["voided"]:
                return False, "Sale already voided"
            items = conn.execute(
                "SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)).fetchall()
            for it in items:
                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty + ? WHERE id=?",
                    (it["quantity"], it["product_id"]),
                )
            conn.execute(
                "UPDATE sales SET voided=1, void_reason=? WHERE id=?",
                (reason, sale_id),
            )
        return True, "Sale voided and restocked"
    except Exception:
        return False, "Could not void sale"


def add_employee(name, role, pin):
    if employee_with_pin_exists(pin):
        return False, "Invalid or duplicate PIN"
    try:
        with connection() as conn:
            conn.execute(
                "INSERT INTO employees (name, role, pin) VALUES (?, ?, ?)",
                (name, role, hash_pin(pin)),
            )
        return True, "Employee added"
    except sqlite3.IntegrityError:
        return False, "Invalid or duplicate PIN"


def list_employees():
    with connection() as conn:
        return conn.execute(
            "SELECT * FROM employees ORDER BY role DESC, name").fetchall()


def auth_employee(pin):
    with connection() as conn:
        for row in conn.execute(
                "SELECT * FROM employees ORDER BY id").fetchall():
            if verify_pin(pin, row["pin"]):
                return row
    return None


def manager_count():
    with connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM employees WHERE role='Manager'").fetchone()[0]


def employee_with_pin_exists(pin, exclude_id=None):
    with connection() as conn:
        for row in conn.execute(
                "SELECT id, pin FROM employees").fetchall():
            if exclude_id is not None and row["id"] == exclude_id:
                continue
            if verify_pin(pin, row["pin"]):
                return True
    return False


def update_employee_role(employee_id, role):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
        if not row:
            return False, "Employee not found"
        # Prevent removing the last manager.
        if row["role"] == "Manager" and role != "Manager":
            n = conn.execute(
                "SELECT COUNT(*) FROM employees WHERE role='Manager'"
            ).fetchone()[0]
            if n <= 1:
                return False, "Cannot demote the last manager"
        conn.execute("UPDATE employees SET role=? WHERE id=?", (role, employee_id))
    return True, "Role updated"


def reset_employee_pin(employee_id, new_pin):
    if employee_with_pin_exists(new_pin, exclude_id=employee_id):
        return False, "That PIN is already in use"
    with connection() as conn:
        conn.execute(
            "UPDATE employees SET pin=? WHERE id=?",
            (hash_pin(new_pin), employee_id),
        )
    return True, "PIN updated"


def delete_employee(employee_id):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
        if not row:
            return False, "Employee not found"
        if row["role"] == "Manager":
            n = conn.execute(
                "SELECT COUNT(*) FROM employees WHERE role='Manager'"
            ).fetchone()[0]
            if n <= 1:
                return False, "Cannot delete the last manager"
        conn.execute("DELETE FROM employees WHERE id=?", (employee_id,))
    return True, "Employee deleted"


def sales_report():
    with connection() as conn:
        return conn.execute(
            """
            SELECT date(datetime) as day, count(*) as num_sales, sum(total) as revenue
            FROM sales WHERE voided=0 GROUP BY day ORDER BY day DESC LIMIT 14
            """
        ).fetchall()


def recent_sales(limit=20):
    """Most recent sales (non-voided), for review/voiding."""
    with connection() as conn:
        return conn.execute(
            """
            SELECT s.id, s.datetime, s.total, s.payment_method, s.tendered, s.change,
                   s.cashier_id, e.name as cashier, s.voided, s.void_reason
            FROM sales s LEFT JOIN employees e ON e.id = s.cashier_id
            ORDER BY s.id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


def top_products(limit=5):
    with connection() as conn:
        return conn.execute(
            """
            SELECT p.name, sum(si.quantity) as units, sum(si.quantity * si.unit_price) as revenue
            FROM sale_items si
            JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.voided=0
            GROUP BY p.id ORDER BY units DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


def revenue_by_range(days=30):
    """Daily revenue for the last N days (including empty days)."""
    with connection() as conn:
        return conn.execute(
            """
            SELECT date(datetime) as day,
                   COALESCE(sum(total), 0) as revenue,
                   count(*) as num_sales
            FROM sales
            WHERE voided=0 AND date(datetime) >= date('now', ?)
            GROUP BY day ORDER BY day ASC
            """,
            (f"-{days} days",),
        ).fetchall()


def sales_by_category():
    """Units and revenue grouped by product category."""
    with connection() as conn:
        return conn.execute(
            """
            SELECT p.category, sum(si.quantity) as units,
                   sum(si.quantity * si.unit_price) as revenue
            FROM sale_items si JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.voided=0
            GROUP BY p.category ORDER BY revenue DESC
            """
        ).fetchall()


def profit_by_product(limit=10):
    """Gross profit and margin per product (all time)."""
    with connection() as conn:
        return conn.execute(
            """
            SELECT p.name, p.category,
                   sum(si.quantity * (si.unit_price - si.discount)) as revenue,
                   sum(si.quantity * p.cost_price) as cost,
                   sum(si.quantity * (si.unit_price - si.discount - p.cost_price)) as profit
            FROM sale_items si JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.voided=0
            GROUP BY p.id ORDER BY profit DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


def profit_overall():
    """Overall revenue vs cost vs profit."""
    with connection() as conn:
        row = conn.execute(
            """
            SELECT sum(si.quantity * (si.unit_price - si.discount)) as revenue,
                   sum(si.quantity * p.cost_price) as cost
            FROM sale_items si JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.voided=0
            """
        ).fetchone()
    if not row or not row["revenue"]:
        return {"revenue": 0.0, "cost": 0.0, "profit": 0.0, "margin": 0.0}
    revenue = row["revenue"] or 0.0
    cost = row["cost"] or 0.0
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue else 0.0
    return {"revenue": revenue, "cost": cost, "profit": profit, "margin": margin}


def sales_by_cashier():
    """Per-staff sales (non-voided): transactions, revenue, items sold."""
    with connection() as conn:
        return conn.execute(
            """
            SELECT COALESCE(e.name, 'Deleted user') as cashier,
                   COUNT(s.id) as transactions,
                   COALESCE(SUM(s.total), 0) as revenue,
                   COALESCE(SUM(si.quantity), 0) as units
            FROM sales s
            LEFT JOIN employees e ON e.id = s.cashier_id
            LEFT JOIN sale_items si ON si.sale_id = s.id
            WHERE s.voided=0
            GROUP BY s.cashier_id
            ORDER BY revenue DESC
            """
        ).fetchall()


def end_of_day_report(day=None):
    """Monthly-end/single-day summary. day = 'YYYY-MM-DD' or None for today.

    Returns units sold, cash/card/mobile totals, voided count and value.
    """
    with connection() as conn:
        if day:
            clause, params = "date(datetime)=?", (day,)
        else:
            clause, params = "date(datetime)=date('now','localtime')", ()
        totals = conn.execute(
            f"""
            SELECT payment_method, COUNT(*) as txns, COALESCE(SUM(total),0) as val
            FROM sales
            WHERE voided=0 AND {clause}
            GROUP BY payment_method
            """,
            params,
        ).fetchall()
        voids = conn.execute(
            f"""
            SELECT COUNT(*) as count, COALESCE(SUM(total),0) as value
            FROM sales
            WHERE voided=1 AND {clause}
            """,
            params,
        ).fetchone()
        units = conn.execute(
            f"""
            SELECT COALESCE(SUM(si.quantity),0)
            FROM sale_items si JOIN sales s ON s.id = si.sale_id
            WHERE s.voided=0 AND {clause}
            """,
            params,
        ).fetchone()[0]
    summary = {
        "units": units,
        "methods": {r["payment_method"]: r for r in totals},
        "voids": voids["count"] if voids else 0,
        "void_value": voids["value"] if voids else 0,
    }
    summary["grand"] = sum(r["val"] for r in totals)
    return summary