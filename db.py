import sqlite3
from contextlib import contextmanager

from paths import DB_PATH
from security import hash_pin, is_hashed

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    code TEXT UNIQUE,
    price INTEGER NOT NULL,
    cost_price INTEGER NOT NULL,
    stock_qty INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    pin TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    cashier_id INTEGER,
    total INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    tendered INTEGER,
    change INTEGER,
    voided INTEGER NOT NULL DEFAULT 0,
    void_reason TEXT,
    FOREIGN KEY (cashier_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    discount INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (sale_id) REFERENCES sales(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    """A committed connection; rolls back on error and always closes.

    Layers the repeated open/close/commit dance that every operations
    helper used to do by hand, so callers can just do:

        with connection() as conn:
            conn.execute(...)
    """
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _column_types(conn, table):
    return {
        r[1]: r[2]
        for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _migrate(conn):
    """Upgrade older databases to the current schema."""
    pcols = _column_types(conn, "products")
    if "sku" in pcols and "code" not in pcols:
        conn.execute("ALTER TABLE products RENAME COLUMN sku TO code")

    scols = _column_types(conn, "sales")
    # Add void columns to existing sales tables (idempotent)
    if "voided" not in scols:
        conn.execute(
            "ALTER TABLE sales ADD COLUMN voided INTEGER NOT NULL DEFAULT 0"
        )
    if "void_reason" not in scols:
        conn.execute("ALTER TABLE sales ADD COLUMN void_reason TEXT")
    if "tendered" not in scols:
        conn.execute("ALTER TABLE sales ADD COLUMN tendered INTEGER")
    if "change" not in scols:
        conn.execute("ALTER TABLE sales ADD COLUMN change INTEGER")

    def money_to_int(table, col):
        if table in ("products",) and col in pcols:
            ctype = pcols[col]
            if ctype.upper() not in ("INTEGER", "INT"):
                conn.execute(
                    f"UPDATE {table} SET {col} = CAST(ROUND({col}) AS INTEGER)"
                )
        elif table in ("sales",):
            cols = _column_types(conn, "sales")
            if col in cols and cols[col].upper() not in ("INTEGER", "INT"):
                conn.execute(
                    f"UPDATE {table} SET {col} = CAST(ROUND({col}) AS INTEGER)"
                )
        elif table in ("sale_items",):
            cols = _column_types(conn, "sale_items")
            if col in cols and cols[col].upper() not in ("INTEGER", "INT"):
                conn.execute(
                    f"UPDATE {table} SET {col} = CAST(ROUND({col}) AS INTEGER)"
                )

    # Convert money columns to integers where they are still REAL
    for t, c in [("products", "price"), ("products", "cost_price"),
                 ("sales", "total"), ("sales", "tendered"), ("sales", "change"),
                 ("sale_items", "unit_price"), ("sale_items", "discount")]:
        money_to_int(t, c)

    # Hash any plaintext PINs left by older databases.
    for r in conn.execute("SELECT id, pin FROM employees").fetchall():
        if not is_hashed(r["pin"]):
            conn.execute(
                "UPDATE employees SET pin=? WHERE id=?",
                (hash_pin(r["pin"]), r["id"]),
            )


def init_db():
    from paths import ensure_dirs
    ensure_dirs()
    conn = get_conn()
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    conn.close()
