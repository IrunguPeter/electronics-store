import os
import sqlite3
import tempfile

import pytest

import db
import operations as ops


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
