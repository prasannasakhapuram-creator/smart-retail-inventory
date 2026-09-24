"""
database.py
-----------
Handles all MySQL interactions: connection, CRUD operations,
transactional sale recording, and analytics queries.
"""

import pymysql
import pymysql.cursors
from pymysql import MySQLError
from datetime import datetime
from db_config import DB_CONFIG


class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                autocommit=False,
                cursorclass=pymysql.cursors.Cursor
            )
            print("✅ Connected to MySQL database.")
        except MySQLError as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def close(self):
        if self.conn and self.conn.open:
            self.conn.close()

    def _dict_cursor(self):
        return self.conn.cursor(pymysql.cursors.DictCursor)

    # ------------------------------------------------------------
    # SUPPLIER OPERATIONS
    # ------------------------------------------------------------
    def add_supplier(self, name, contact, email):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (name, contact_number, email) VALUES (%s, %s, %s)",
            (name, contact, email)
        )
        self.conn.commit()
        cur.close()
        return cur.lastrowid

    def get_suppliers(self):
        cur = self._dict_cursor()
        cur.execute("SELECT * FROM suppliers")
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------
    # PRODUCT OPERATIONS (CRUD)
    # ------------------------------------------------------------
    def add_product(self, name, category, price, stock_qty, reorder_level, supplier_id):
        if price < 0 or stock_qty < 0:
            raise ValueError("Price and stock quantity cannot be negative.")
        cur = self.conn.cursor()
        try:
            cur.execute(
                """INSERT INTO products (name, category, price, stock_qty, reorder_level, supplier_id)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (name, category, price, stock_qty, reorder_level, supplier_id)
            )
            self.conn.commit()
            return cur.lastrowid
        except MySQLError as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def update_product(self, product_id, **fields):
        if not fields:
            return
        allowed = {"name", "category", "price", "stock_qty", "reorder_level", "supplier_id"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [product_id]
        cur = self.conn.cursor()
        try:
            cur.execute(f"UPDATE products SET {set_clause} WHERE product_id = %s", values)
            self.conn.commit()
        except MySQLError as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def delete_product(self, product_id):
        cur = self.conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            self.conn.commit()
        except MySQLError as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def get_products(self, category=None, low_stock_only=False):
        cur = self._dict_cursor()
        query = """
            SELECT p.*, s.name AS supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        """
        conditions, params = [], []
        if category:
            conditions.append("p.category = %s")
            params.append(category)
        if low_stock_only:
            conditions.append("p.stock_qty <= p.reorder_level")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def search_products(self, keyword):
        cur = self._dict_cursor()
        cur.execute(
            "SELECT * FROM products WHERE name LIKE %s OR category LIKE %s",
            (f"%{keyword}%", f"%{keyword}%")
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------
    # SALES OPERATIONS (with transaction safety)
    # ------------------------------------------------------------
    def record_sale(self, product_id, quantity_sold):
        """
        Records a sale AND decrements stock atomically.
        If either step fails, the whole transaction rolls back.
        """
        cur = self._dict_cursor()
        try:
            self.conn.begin()

            cur.execute("SELECT price, stock_qty FROM products WHERE product_id = %s FOR UPDATE", (product_id,))
            product = cur.fetchone()
            if not product:
                raise ValueError("Product not found.")
            if product["stock_qty"] < quantity_sold:
                raise ValueError(
                    f"Insufficient stock. Available: {product['stock_qty']}, Requested: {quantity_sold}"
                )

            sale_price = product["price"]
            total_amount = float(sale_price) * quantity_sold

            cur.execute(
                """INSERT INTO sales (product_id, quantity_sold, sale_price, total_amount, sale_date)
                   VALUES (%s, %s, %s, %s, %s)""",
                (product_id, quantity_sold, sale_price, total_amount, datetime.now())
            )
            cur.execute(
                "UPDATE products SET stock_qty = stock_qty - %s WHERE product_id = %s",
                (quantity_sold, product_id)
            )

            self.conn.commit()
            return {"total_amount": total_amount, "sale_price": float(sale_price)}
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def get_sales(self, start_date=None, end_date=None):
        cur = self._dict_cursor()
        query = """
            SELECT sa.sale_id, p.name AS product_name, p.category,
                   sa.quantity_sold, sa.sale_price, sa.total_amount, sa.sale_date
            FROM sales sa
            JOIN products p ON sa.product_id = p.product_id
        """
        params = []
        if start_date and end_date:
            query += " WHERE sa.sale_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        query += " ORDER BY sa.sale_date DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------
    # ANALYTICS QUERIES (used by report_generator.py)
    # ------------------------------------------------------------
    def sales_by_category(self):
        cur = self._dict_cursor()
        cur.execute("""
            SELECT p.category, SUM(sa.total_amount) AS revenue, SUM(sa.quantity_sold) AS units_sold
            FROM sales sa JOIN products p ON sa.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return rows

    def top_selling_products(self, limit=5):
        cur = self._dict_cursor()
        cur.execute("""
            SELECT p.name, SUM(sa.quantity_sold) AS units_sold, SUM(sa.total_amount) AS revenue
            FROM sales sa JOIN products p ON sa.product_id = p.product_id
            GROUP BY p.name
            ORDER BY units_sold DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        return rows

    def daily_sales_trend(self, days=30):
        cur = self._dict_cursor()
        cur.execute("""
            SELECT DATE(sale_date) AS sale_day, SUM(total_amount) AS revenue
            FROM sales
            WHERE sale_date >= NOW() - INTERVAL %s DAY
            GROUP BY DATE(sale_date)
            ORDER BY sale_day
        """, (days,))
        rows = cur.fetchall()
        cur.close()
        return rows

    def low_stock_products(self):
        return self.get_products(low_stock_only=True)
