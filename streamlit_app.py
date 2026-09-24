"""
streamlit_app.py
-----------------
Web dashboard for the Smart Retail Inventory & Sales Analytics System.
Run with:  streamlit run streamlit_app.py

Uses the SAME database.py as the CLI — no duplicated logic. This just
gives you a browser UI on top of the exact same MySQL backend.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from database import Database
from report_generator import generate_report

st.set_page_config(
    page_title="Smart Retail Inventory",
    page_icon="🛒",
    layout="wide"
)


@st.cache_resource
def get_db():
    return Database()


def refresh():
    st.cache_data.clear()
    st.rerun()


try:
    db = get_db()
except Exception as e:
    st.error(f"❌ Could not connect to MySQL. Check db_config.py and make sure your MySQL server is running.\n\n{e}")
    st.stop()

st.sidebar.title("🛒 Retail Inventory")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "📦 Products", "💰 Record Sale", "🧾 Sales History",
     "⚠️ Low Stock Alerts", "🏭 Suppliers", "📥 Export Report"]
)

# ============================================================
# DASHBOARD
# ============================================================
if page == "📊 Dashboard":
    st.title("📊 Sales & Inventory Dashboard")

    products = db.get_products()
    sales = db.get_sales()
    low_stock = db.low_stock_products()

    col1, col2, col3, col4 = st.columns(4)
    total_revenue = sum(s["total_amount"] for s in sales) if sales else 0
    col1.metric("Total Products", len(products))
    col2.metric("Total Sales Recorded", len(sales))
    col3.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    col4.metric("Low Stock Items", len(low_stock), delta=None,
                delta_color="inverse")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top Selling Products")
        top = db.top_selling_products(limit=10)
        if top:
            df_top = pd.DataFrame(top).rename(
                columns={"name": "Product", "units_sold": "Units Sold", "revenue": "Revenue"})
            st.bar_chart(df_top.set_index("Product")["Units Sold"])
        else:
            st.info("No sales data yet.")

    with c2:
        st.subheader("Revenue by Category")
        cat = db.sales_by_category()
        if cat:
            df_cat = pd.DataFrame(cat).rename(
                columns={"category": "Category", "revenue": "Revenue"})
            st.bar_chart(df_cat.set_index("Category")["Revenue"])
        else:
            st.info("No sales data yet.")

    st.subheader("Sales Trend (Last 30 Days)")
    trend = db.daily_sales_trend(days=30)
    if trend:
        df_trend = pd.DataFrame(trend).rename(
            columns={"sale_day": "Date", "revenue": "Revenue"})
        st.line_chart(df_trend.set_index("Date")["Revenue"])
    else:
        st.info("No sales data yet.")

# ============================================================
# PRODUCTS
# ============================================================
elif page == "📦 Products":
    st.title("📦 Product Management")

    tab1, tab2, tab3 = st.tabs(["View / Search", "➕ Add Product", "✏️ Update / Delete"])

    with tab1:
        keyword = st.text_input("Search by name or category")
        products = db.search_products(keyword) if keyword else db.get_products()
        if products:
            df = pd.DataFrame(products)
            df["low_stock"] = df["stock_qty"] <= df["reorder_level"]
            st.dataframe(
                df.style.apply(
                    lambda row: ["background-color:#ffcccc" if row.low_stock else "" for _ in row],
                    axis=1
                ),
                use_container_width=True
            )
        else:
            st.info("No products found.")

    with tab2:
        with st.form("add_product_form"):
            name = st.text_input("Product name")
            category = st.text_input("Category")
            price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
            stock_qty = st.number_input("Initial stock quantity", min_value=0, step=1)
            reorder_level = st.number_input("Reorder level", min_value=0, step=1, value=10)
            suppliers = db.get_suppliers()
            supplier_options = {s["name"]: s["supplier_id"] for s in suppliers}
            supplier_choice = st.selectbox("Supplier", ["-- None --"] + list(supplier_options.keys()))
            submitted = st.form_submit_button("Add Product")
            if submitted:
                try:
                    supplier_id = supplier_options.get(supplier_choice)
                    db.add_product(name, category, price, int(stock_qty), int(reorder_level), supplier_id)
                    st.success(f"✅ Added '{name}'")
                    refresh()
                except Exception as e:
                    st.error(f"❌ {e}")

    with tab3:
        products = db.get_products()
        if products:
            options = {f"[{p['product_id']}] {p['name']}": p["product_id"] for p in products}
            choice = st.selectbox("Select product", list(options.keys()))
            pid = options[choice]

            new_price = st.number_input("New price (0 = no change)", min_value=0.0, step=1.0)
            new_stock = st.number_input("New stock qty (-1 = no change)", min_value=-1, step=1, value=-1)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Update"):
                    fields = {}
                    if new_price > 0:
                        fields["price"] = new_price
                    if new_stock >= 0:
                        fields["stock_qty"] = int(new_stock)
                    db.update_product(pid, **fields)
                    st.success("✅ Updated")
                    refresh()
            with col_b:
                if st.button("🗑️ Delete Product", type="secondary"):
                    db.delete_product(pid)
                    st.success("✅ Deleted")
                    refresh()

# ============================================================
# RECORD SALE
# ============================================================
elif page == "💰 Record Sale":
    st.title("💰 Record a Sale")
    products = db.get_products()
    if not products:
        st.info("Add some products first.")
    else:
        options = {f"[{p['product_id']}] {p['name']} — Stock: {p['stock_qty']}": p for p in products}
        choice = st.selectbox("Select product", list(options.keys()))
        product = options[choice]
        st.write(f"Price: ₹{product['price']} | Available stock: {product['stock_qty']}")
        qty = st.number_input("Quantity sold", min_value=1, step=1)

        if st.button("Record Sale", type="primary"):
            try:
                result = db.record_sale(product["product_id"], int(qty))
                st.success(f"✅ Sale recorded! Total: ₹{result['total_amount']:.2f}")
                refresh()
            except Exception as e:
                st.error(f"❌ {e}")

# ============================================================
# SALES HISTORY
# ============================================================
elif page == "🧾 Sales History":
    st.title("🧾 Sales History")
    sales = db.get_sales()
    if sales:
        df = pd.DataFrame(sales)
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "Download as CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="sales_history.csv",
            mime="text/csv"
        )
    else:
        st.info("No sales recorded yet.")

# ============================================================
# LOW STOCK ALERTS
# ============================================================
elif page == "⚠️ Low Stock Alerts":
    st.title("⚠️ Low Stock Alerts")
    low_stock = db.low_stock_products()
    if low_stock:
        df = pd.DataFrame(low_stock)
        st.dataframe(df, use_container_width=True)
        st.warning(f"{len(low_stock)} product(s) need reordering.")
    else:
        st.success("✅ All products are sufficiently stocked.")

# ============================================================
# SUPPLIERS
# ============================================================
elif page == "🏭 Suppliers":
    st.title("🏭 Suppliers")
    suppliers = db.get_suppliers()
    if suppliers:
        st.dataframe(pd.DataFrame(suppliers), use_container_width=True)

    with st.expander("➕ Add Supplier"):
        with st.form("add_supplier_form"):
            name = st.text_input("Supplier name")
            contact = st.text_input("Contact number")
            email = st.text_input("Email")
            if st.form_submit_button("Add Supplier"):
                db.add_supplier(name, contact, email)
                st.success("✅ Supplier added")
                refresh()

# ============================================================
# EXPORT REPORT
# ============================================================
elif page == "📥 Export Report":
    st.title("📥 Export Excel Report")
    st.write("Generates the same 5-sheet report as the CLI (Top Products, "
             "Category Revenue, Sales Trend, Inventory Status, Low Stock Alerts).")
    if st.button("Generate Report", type="primary"):
        path = f"exports/sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        generate_report(path)
        with open(path, "rb") as f:
            st.download_button(
                "⬇️ Download Excel Report",
                f,
                file_name=path.split("/")[-1],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.success("✅ Report generated!")
