"""
tests/test_database.py
-----------------------
Unit tests for the Database class in database.py.

These tests use unittest.mock to fake the pymysql connection, so they run
WITHOUT needing a live MySQL server — good for CI pipelines and for
demonstrating automated testing on your resume.

Run with:
    pytest -v
"""

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Database  # noqa: E402


@pytest.fixture
def mock_conn():
    """Patches pymysql.connect so Database() never touches a real server."""
    with patch("database.pymysql.connect") as mock_connect:
        conn = MagicMock()
        conn.open = True
        mock_connect.return_value = conn
        yield conn


@pytest.fixture
def db(mock_conn):
    return Database()


# ============================================================
# add_product validation
# ============================================================
class TestAddProductValidation:
    def test_negative_price_raises_value_error(self, db):
        with pytest.raises(ValueError, match="cannot be negative"):
            db.add_product("Test Item", "Category", price=-10, stock_qty=5,
                            reorder_level=5, supplier_id=None)

    def test_negative_stock_raises_value_error(self, db):
        with pytest.raises(ValueError, match="cannot be negative"):
            db.add_product("Test Item", "Category", price=10, stock_qty=-1,
                            reorder_level=5, supplier_id=None)

    def test_valid_product_inserts_and_commits(self, db, mock_conn):
        cursor = mock_conn.cursor.return_value
        cursor.lastrowid = 42

        new_id = db.add_product("Notebook", "Stationery", price=60, stock_qty=100,
                                 reorder_level=20, supplier_id=1)

        assert new_id == 42
        cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ============================================================
# record_sale — the core transaction-safety logic
# ============================================================
class TestRecordSale:
    def test_insufficient_stock_raises_and_rolls_back(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {"price": 100.0, "stock_qty": 2}

        with pytest.raises(ValueError, match="Insufficient stock"):
            db.record_sale(product_id=1, quantity_sold=5)

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_product_not_found_raises_and_rolls_back(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Product not found"):
            db.record_sale(product_id=999, quantity_sold=1)

        mock_conn.rollback.assert_called_once()

    def test_successful_sale_commits_and_returns_total(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {"price": 90.0, "stock_qty": 60}

        result = db.record_sale(product_id=5, quantity_sold=3)

        assert result["total_amount"] == 270.0
        assert result["sale_price"] == 90.0
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
        # both the INSERT into sales and the UPDATE on products should run
        assert cursor.execute.call_count >= 3  # SELECT ... FOR UPDATE, INSERT, UPDATE

    def test_sale_starts_a_transaction(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {"price": 50.0, "stock_qty": 10}

        db.record_sale(product_id=2, quantity_sold=1)

        mock_conn.begin.assert_called_once()


# ============================================================
# update_product — partial-update behaviour
# ============================================================
class TestUpdateProduct:
    def test_no_fields_does_nothing(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor

        db.update_product(product_id=1)

        cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()

    def test_unknown_fields_are_ignored(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor

        db.update_product(product_id=1, not_a_real_column="hacked")

        cursor.execute.assert_not_called()

    def test_valid_field_updates_and_commits(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor

        db.update_product(product_id=1, price=99.99)

        cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ============================================================
# get_products — query building for filters
# ============================================================
class TestGetProducts:
    def test_low_stock_filter_adds_where_clause(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        db.get_products(low_stock_only=True)

        executed_query = cursor.execute.call_args[0][0]
        assert "stock_qty <= p.reorder_level" in executed_query

    def test_category_filter_adds_param(self, db, mock_conn):
        cursor = MagicMock()
        mock_conn.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        db.get_products(category="Electronics")

        args, kwargs = cursor.execute.call_args
        query, params = args[0], args[1]
        assert "p.category = %s" in query
        assert "Electronics" in params
