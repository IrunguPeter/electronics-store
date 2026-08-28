import os
import sqlite3
import tempfile

import pytest

import db
import operations as ops
from security import is_hashed, verify_pin


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    yield db_path


def seed_product(price=1000, cost=600, stock=10):
    ok, _ = ops.add_product("Widget", "Gadgets", "W-1", price, cost, stock)
    assert ok
    return ops.list_products(search="W-1")[0]


def seed_cashier():
    ok, _ = ops.add_employee("Alice", "Employee", "4321")
    assert ok
    return ops.auth_employee("4321")


def test_money_is_integer_in_schema(fresh_db):
    cols = {r[1]: r[2] for r in db.get_conn().execute(
        "PRAGMA table_info(products)").fetchall()}
    assert cols["price"].upper() == "INTEGER"
    assert cols["cost_price"].upper() == "INTEGER"


def test_sale_records_integer_total_and_change(fresh_db):
    p = seed_product(price=2000, stock=5)
    emp = seed_cashier()
    ok, sale_id = ops.create_sale(emp["id"], "cash", [(p["id"], 2, 100)],
                                  tendered=5000)
    assert ok
    sale, items = ops.get_sale(sale_id)
    assert sale["total"] == (2000 - 100) * 2  # 3800
    assert sale["change"] == 5000 - 3800       # 1200
    assert sale["payment_method"] == "cash"
    assert isinstance(sale["total"], int)
    assert items[0]["unit_price"] == 2000


def test_sale_deducts_stock(fresh_db):
    p = seed_product(stock=10)
    emp = seed_cashier()
    ops.create_sale(emp["id"], "card", [(p["id"], 3, 0)])
    refreshed = ops.get_product(p["id"])
    assert refreshed["stock_qty"] == 7


def test_cash_tendered_insufficient(fresh_db):
    p = seed_product(price=1000, stock=2)
    emp = seed_cashier()
    ok, msg = ops.create_sale(emp["id"], "cash", [(p["id"], 1, 0)],
                              tendered=500)
    assert not ok
    assert "less than" in msg.lower()


def test_void_sale_restocks_and_marks_voided(fresh_db):
    p = seed_product(stock=10)
    emp = seed_cashier()
    ok, sale_id = ops.create_sale(emp["id"], "card", [(p["id"], 4, 0)])
    assert ok
    assert ops.get_product(p["id"])["stock_qty"] == 6
    ok, msg = ops.void_sale(sale_id, "wrong item")
    assert ok
    assert ops.get_product(p["id"])["stock_qty"] == 10
    sale, _ = ops.get_sale(sale_id)
    assert sale["voided"] == 1


def test_double_void_rejected(fresh_db):
    p = seed_product()
    emp = seed_cashier()
    _, sale_id = ops.create_sale(emp["id"], "card", [(p["id"], 1, 0)])
    ops.void_sale(sale_id)
    ok, msg = ops.void_sale(sale_id)
    assert not ok
    assert "already" in msg.lower()


def test_employee_guards_keep_last_manager(fresh_db):
    ok, _ = ops.add_employee("Boss", "Manager", "1111")
    assert ok
    boss = ops.auth_employee("1111")
    ok, _ = ops.update_employee_role(boss["id"], "Employee")
    assert not ok
    ok, _ = ops.delete_employee(boss["id"])
    assert not ok


def test_duplicate_pin_rejected(fresh_db):
    ops.add_employee("A", "Employee", "9999")
    ok, msg = ops.add_employee("B", "Employee", "9999")
    assert not ok
    assert "PIN" in msg


def _prod(price=1000, cost=600, stock=10, code="T1"):
    ok, _ = ops.add_product("Widget", "Gadgets", code, price, cost, stock)
    assert ok
    return ops.list_products(search=code)[0]


def _emp(pin, name="Alice"):
    ops.add_employee(name, "Employee", pin)
    return ops.auth_employee(pin)


def test_update_product(fresh_db):
    p = _prod(code="U1")
    ok, msg = ops.update_product(p["id"], "NewName", "Tech", "U2", 1500, 900)
    assert ok
    q = ops.get_product(p["id"])
    assert q["name"] == "NewName" and q["price"] == 1500 and q["code"] == "U2"


def test_restock(fresh_db):
    p = _prod(stock=10, code="R1")
    ok, _ = ops.restock(p["id"], 5)
    assert ops.get_product(p["id"])["stock_qty"] == 15
    ok, _ = ops.restock(p["id"], -100)
    assert not ok


def test_payment_method_validated(fresh_db):
    p = _prod(code="V1")
    emp = _emp("7777")
    ok, msg = ops.create_sale(emp["id"], "bitcoin", [(p["id"], 1, 0)])
    assert not ok
    assert "payment" in msg.lower()


def test_sales_by_cashier_and_end_of_day(fresh_db):
    p = _prod(price=2000, cost=1200, stock=50, code="S1")
    a = _emp("1111", "Alice")
    ops.create_sale(a["id"], "cash", [(p["id"], 2, 0)], tendered=5000)
    ops.create_sale(a["id"], "card", [(p["id"], 1, 0)])
    b = _emp("2222", "Bob")
    ops.create_sale(b["id"], "mobile", [(p["id"], 1, 0)])
    # void Bob's so it drops out
    bob_sale = [s for s in ops.recent_sales() if s["cashier"] == "Bob"][0]
    ops.void_sale(bob_sale["id"])

    staff = {r["cashier"]: r for r in ops.sales_by_cashier()}
    assert staff["Alice"]["transactions"] == 2
    assert staff["Alice"]["revenue"] == 6000
    assert staff["Alice"]["units"] == 3

    eod = ops.end_of_day_report()
    assert eod["grand"] == 6000
    assert eod["units"] == 3
    assert eod["methods"]["cash"]["val"] == 4000
    assert eod["methods"]["card"]["val"] == 2000
    assert "mobile" not in eod["methods"]
    assert eod["voids"] == 1 and eod["void_value"] == 2000


def test_pin_stored_hashed_not_plaintext(fresh_db):
    ops.add_employee("Hank", "Employee", "5555")
    rows = db.get_conn().execute("SELECT pin FROM employees").fetchall()
    stored = rows[0]["pin"]
    assert stored != "5555"
    assert is_hashed(stored)
    assert verify_pin("5555", stored)
    assert not verify_pin("0000", stored)


def test_legacy_plaintext_pin_migrated_to_hash(fresh_db):
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO employees (name, role, pin) VALUES (?, ?, ?)",
        ("Legacy", "Employee", "1234"),
    )
    conn.commit()
    conn.close()
    assert ops.auth_employee("1234") is not None  # works pre-migration too
    db.init_db()  # re-runs _migrate -> hashes plaintext pins
    [row] = db.get_conn().execute("SELECT pin FROM employees").fetchall()
    assert is_hashed(row["pin"])
    assert row["pin"] != "1234"
    assert ops.auth_employee("1234") is not None
