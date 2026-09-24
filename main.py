"""
main.py
-------
CLI entry point for the Smart Retail Inventory & Sales Analytics System.
Run this after setting up the database (see README.md).
"""

from database import Database
from report_generator import generate_report
from datetime import datetime


def print_menu():
    print("\n" + "=" * 55)
    print(" SMART RETAIL INVENTORY & SALES ANALYTICS SYSTEM")
    print("=" * 55)
    print("1.  Add Product")
    print("2.  View All Products")
    print("3.  Update Product")
    print("4.  Delete Product")
    print("5.  Search Products")
    print("6.  Record a Sale")
    print("7.  View Sales History")
    print("8.  View Low Stock Alerts")
    print("9.  Add Supplier")
    print("10. View Suppliers")
    print("11. Generate Excel Report")
    print("0.  Exit")
    print("=" * 55)


def add_product(db):
    try:
        name = input("Product name: ").strip()
        category = input("Category: ").strip()
        price = float(input("Price: "))
        stock_qty = int(input("Initial stock quantity: "))
        reorder_level = int(input("Reorder level (default 10): ") or 10)

        suppliers = db.get_suppliers()
        if suppliers:
            print("\nAvailable suppliers:")
            for s in suppliers:
                print(f"  {s['supplier_id']}: {s['name']}")
            supplier_id = input("Supplier ID (leave blank for none): ").strip()
            supplier_id = int(supplier_id) if supplier_id else None
        else:
            supplier_id = None

        pid = db.add_product(name, category, price, stock_qty, reorder_level, supplier_id)
        print(f"✅ Product added with ID {pid}")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def view_products(db):
    products = db.get_products()
    if not products:
        print("No products found.")
        return
    print(f"\n{'ID':<4}{'Name':<22}{'Category':<15}{'Price':<10}{'Stock':<8}{'Reorder':<9}{'Supplier':<20}")
    print("-" * 90)
    for p in products:
        flag = " ⚠" if p["stock_qty"] <= p["reorder_level"] else ""
        print(f"{p['product_id']:<4}{p['name']:<22}{p['category']:<15}"
              f"{p['price']:<10}{p['stock_qty']:<8}{p['reorder_level']:<9}"
              f"{(p['supplier_name'] or '-'): <20}{flag}")


def update_product(db):
    try:
        pid = int(input("Product ID to update: "))
        print("Leave blank to keep current value.")
        fields = {}
        name = input("New name: ").strip()
        if name:
            fields["name"] = name
        category = input("New category: ").strip()
        if category:
            fields["category"] = category
        price = input("New price: ").strip()
        if price:
            fields["price"] = float(price)
        stock = input("New stock quantity: ").strip()
        if stock:
            fields["stock_qty"] = int(stock)
        db.update_product(pid, **fields)
        print("✅ Product updated.")
    except Exception as e:
        print(f"❌ Error: {e}")


def delete_product(db):
    try:
        pid = int(input("Product ID to delete: "))
        confirm = input(f"Confirm delete product {pid}? (y/n): ").lower()
        if confirm == "y":
            db.delete_product(pid)
            print("✅ Product deleted.")
    except Exception as e:
        print(f"❌ Error: {e}")


def search_products(db):
    keyword = input("Search keyword: ").strip()
    results = db.search_products(keyword)
    if not results:
        print("No matches found.")
        return
    for p in results:
        print(f"  [{p['product_id']}] {p['name']} ({p['category']}) - "
              f"₹{p['price']} - Stock: {p['stock_qty']}")


def record_sale(db):
    try:
        pid = int(input("Product ID: "))
        qty = int(input("Quantity sold: "))
        result = db.record_sale(pid, qty)
        print(f"✅ Sale recorded. Total: ₹{result['total_amount']:.2f}")
    except Exception as e:
        print(f"❌ Sale failed: {e}")


def view_sales(db):
    sales = db.get_sales()
    if not sales:
        print("No sales recorded yet.")
        return
    print(f"\n{'ID':<5}{'Product':<22}{'Qty':<6}{'Total':<12}{'Date':<20}")
    print("-" * 70)
    for s in sales:
        print(f"{s['sale_id']:<5}{s['product_name']:<22}{s['quantity_sold']:<6}"
              f"₹{s['total_amount']:<10}{str(s['sale_date']):<20}")


def view_low_stock(db):
    items = db.low_stock_products()
    if not items:
        print("✅ All products are sufficiently stocked.")
        return
    print("\n⚠ LOW STOCK ALERTS:")
    for p in items:
        print(f"  {p['name']} — Stock: {p['stock_qty']} (Reorder level: {p['reorder_level']})")


def add_supplier(db):
    name = input("Supplier name: ").strip()
    contact = input("Contact number: ").strip()
    email = input("Email: ").strip()
    sid = db.add_supplier(name, contact, email)
    print(f"✅ Supplier added with ID {sid}")


def view_suppliers(db):
    suppliers = db.get_suppliers()
    for s in suppliers:
        print(f"  [{s['supplier_id']}] {s['name']} — {s['contact_number']} — {s['email']}")


def main():
    try:
        db = Database()
    except Exception:
        print("Could not start: check your db_config.py and MySQL server.")
        return

    actions = {
        "1": lambda: add_product(db),
        "2": lambda: view_products(db),
        "3": lambda: update_product(db),
        "4": lambda: delete_product(db),
        "5": lambda: search_products(db),
        "6": lambda: record_sale(db),
        "7": lambda: view_sales(db),
        "8": lambda: view_low_stock(db),
        "9": lambda: add_supplier(db),
        "10": lambda: view_suppliers(db),
        "11": lambda: generate_report(
            f"exports/sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
    }

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye! 👋")
            db.close()
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
