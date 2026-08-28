import sqlite3

from db import get_conn


def add_product(name, category, code, price, cost_price, stock_qty):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO products (name, category, code, price, cost_price, stock_qty) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, category, code, price, cost_price, stock_qty),
        )
        conn.commit()
        return True, "Product added"
    except sqlite3.IntegrityError:
        return False, "Product code already exists"
    finally:
        conn.close()


def list_products(search=None):
    conn = get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR code LIKE ? OR category LIKE ? "
            "ORDER BY name",
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return row


def update_stock(product_id, delta):
    conn = get_conn()
    conn.execute(
        "UPDATE products SET stock_qty = stock_qty + ? WHERE id=?",
        (delta, product_id),
    )
    conn.commit()
    conn.close()


def low_stock(threshold=5):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE stock_qty <= ? ORDER BY stock_qty", (threshold,)
    ).fetchall()
    conn.close()
    return rows


def create_sale(cashier_id, payment_method, items):
    """items = list of (product_id, quantity, discount)"""
    conn = get_conn()
    try:
        total = 0.0
        for product_id, qty, discount in items:
            prod = conn.execute(
                "SELECT * FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if not prod:
                raise ValueError(f"Product {product_id} not found")
            if prod["stock_qty"] < qty:
                raise ValueError(f"Insufficient stock for {prod['name']}")
            total += (prod["price"] - discount) * qty

        cur = conn.execute(
            "INSERT INTO sales (cashier_id, total, payment_method) VALUES (?, ?, ?)",
            (cashier_id, total, payment_method),
        )
        sale_id = cur.lastrowid

        for product_id, qty, discount in items:
            prod = conn.execute(
                "SELECT * FROM products WHERE id=?", (product_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount) "
                "VALUES (?, ?, ?, ?, ?)",
                (sale_id, product_id, qty, prod["price"], discount),
            )
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty - ? WHERE id=?",
                (qty, product_id),
            )

        conn.commit()
        return True, sale_id
    except ValueError as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_employee(name, role, pin):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO employees (name, role, pin) VALUES (?, ?, ?)",
            (name, role, pin),
        )
        conn.commit()
        return True, "Employee added"
    except sqlite3.IntegrityError:
        return False, "Invalid or duplicate PIN"
    finally:
        conn.close()


def list_employees():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM employees ORDER BY role DESC, name").fetchall()
    conn.close()
    return rows


def auth_employee(pin):
    conn = get_conn()
    row = conn.execute("SELECT * FROM employees WHERE pin=?", (pin,)).fetchone()
    conn.close()
    return row


def manager_count():
    conn = get_conn()
    n = conn.execute(
        "SELECT COUNT(*) FROM employees WHERE role='Manager'").fetchone()[0]
    conn.close()
    return n


def employee_with_pin_exists(pin, exclude_id=None):
    conn = get_conn()
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM employees WHERE pin=? AND id<>?",
            (pin, exclude_id)).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM employees WHERE pin=?", (pin,)).fetchone()
    conn.close()
    return row is not None


def update_employee_role(employee_id, role):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
    if not row:
        conn.close()
        return False, "Employee not found"
    # Prevent removing the last manager
    if row["role"] == "Manager" and role != "Manager" and manager_count() <= 1:
        conn.close()
        return False, "Cannot demote the last manager"
    conn.execute("UPDATE employees SET role=? WHERE id=?", (role, employee_id))
    conn.commit()
    conn.close()
    return True, "Role updated"


def reset_employee_pin(employee_id, new_pin):
    conn = get_conn()
    if employee_with_pin_exists(new_pin, exclude_id=employee_id):
        conn.close()
        return False, "That PIN is already in use"
    conn.execute(
        "UPDATE employees SET pin=? WHERE id=?", (new_pin, employee_id))
    conn.commit()
    conn.close()
    return True, "PIN updated"


def delete_employee(employee_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
    if not row:
        conn.close()
        return False, "Employee not found"
    if row["role"] == "Manager" and manager_count() <= 1:
        conn.close()
        return False, "Cannot delete the last manager"
    conn.execute("DELETE FROM employees WHERE id=?", (employee_id,))
    conn.commit()
    conn.close()
    return True, "Employee deleted"


def sales_report():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT date(datetime) as day, count(*) as num_sales, sum(total) as revenue
        FROM sales GROUP BY day ORDER BY day DESC LIMIT 14
        """
    ).fetchall()
    conn.close()
    return rows


def top_products(limit=5):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.name, sum(si.quantity) as units, sum(si.quantity * si.unit_price) as revenue
        FROM sale_items si JOIN products p ON p.id = si.product_id
        GROUP BY p.id ORDER BY units DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def revenue_by_range(days=30):
    """Daily revenue for the last N days (including empty days)."""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT date(datetime) as day,
               COALESCE(sum(total), 0) as revenue,
               count(*) as num_sales
        FROM sales
        WHERE date(datetime) >= date('now', ?)
        GROUP BY day ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return rows


def sales_by_category():
    """Units and revenue grouped by product category."""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.category, sum(si.quantity) as units,
               sum(si.quantity * si.unit_price) as revenue
        FROM sale_items si JOIN products p ON p.id = si.product_id
        GROUP BY p.category ORDER BY revenue DESC
        """
    ).fetchall()
    conn.close()
    return rows


def profit_by_product(limit=10):
    """Gross profit and margin per product (all time)."""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.name, p.category,
               sum(si.quantity * (si.unit_price - si.discount)) as revenue,
               sum(si.quantity * p.cost_price) as cost,
               sum(si.quantity * (si.unit_price - si.discount - p.cost_price)) as profit
        FROM sale_items si JOIN products p ON p.id = si.product_id
        GROUP BY p.id ORDER BY profit DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def profit_overall():
    """Overall revenue vs cost vs profit."""
    conn = get_conn()
    row = conn.execute(
        """
        SELECT sum(si.quantity * (si.unit_price - si.discount)) as revenue,
               sum(si.quantity * p.cost_price) as cost
        FROM sale_items si JOIN products p ON p.id = si.product_id
        """
    ).fetchone()
    conn.close()
    if not row or not row["revenue"]:
        return {"revenue": 0.0, "cost": 0.0, "profit": 0.0, "margin": 0.0}
    revenue = row["revenue"] or 0.0
    cost = row["cost"] or 0.0
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue else 0.0
    return {"revenue": revenue, "cost": cost, "profit": profit, "margin": margin}
