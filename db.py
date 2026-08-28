import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "store.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    code TEXT UNIQUE,
    price REAL NOT NULL,
    cost_price REAL NOT NULL,
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
    total REAL NOT NULL,
    payment_method TEXT NOT NULL,
    FOREIGN KEY (cashier_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (sale_id) REFERENCES sales(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn):
    """Rename legacy 'sku' column to 'code' if it still exists."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()]
    if "sku" in cols and "code" not in cols:
        conn.execute("ALTER TABLE products RENAME COLUMN sku TO code")


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    conn.close()
