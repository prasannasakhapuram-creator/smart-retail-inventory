"""
report_generator.py
--------------------
Generates a polished, multi-sheet Excel report from the MySQL data:
  1. Sales Summary sheet (with a bar chart of top products)
  2. Category Revenue sheet (with a pie/bar chart)
  3. Sales Trend sheet (with a line chart)
  4. Inventory sheet (with conditional formatting for low stock)

Uses pandas for aggregation and openpyxl for formatting + charts.
"""

import os
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

from database import Database

HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
THIN_BORDER = Border(*(Side(style="thin", color="B7B7B7"),) * 4)


def style_header_row(ws, row_num, num_cols):
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER


def autofit_columns(ws, df, start_col=1):
    for i, col in enumerate(df.columns, start=start_col):
        max_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 4
        ws.column_dimensions[get_column_letter(i)].width = min(max_len, 40)


def write_df(ws, df, start_row=1, start_col=1, title=None):
    r = start_row
    if title:
        ws.cell(row=r, column=start_col, value=title).font = TITLE_FONT
        r += 2
    header_row = r
    for j, col_name in enumerate(df.columns, start=start_col):
        ws.cell(row=header_row, column=j, value=col_name)
    style_header_row(ws, header_row, len(df.columns))
    for i, row in enumerate(df.itertuples(index=False), start=header_row + 1):
        for j, val in enumerate(row, start=start_col):
            cell = ws.cell(row=i, column=j, value=val)
            cell.border = THIN_BORDER
    return header_row, header_row + len(df)  # (header_row, last_data_row)


def generate_report(output_path="exports/sales_report.xlsx"):
    db = Database()
    wb = Workbook()

    # ============================================================
    # SHEET 1: Top Selling Products (+ Bar Chart)
    # ============================================================
    ws1 = wb.active
    ws1.title = "Top Products"
    top_products = db.top_selling_products(limit=10)
    df_top = pd.DataFrame(top_products) if top_products else pd.DataFrame(
        columns=["name", "units_sold", "revenue"])
    df_top.rename(columns={"name": "Product", "units_sold": "Units Sold", "revenue": "Revenue (₹)"}, inplace=True)

    header_row, last_row = write_df(ws1, df_top, title="Top Selling Products",
                                     start_row=1)
    autofit_columns(ws1, df_top)

    if not df_top.empty:
        chart = BarChart()
        chart.title = "Top Selling Products (by Units Sold)"
        chart.y_axis.title = "Units Sold"
        chart.x_axis.title = "Product"
        data = Reference(ws1, min_col=2, min_row=header_row, max_row=last_row)
        cats = Reference(ws1, min_col=1, min_row=header_row + 1, max_row=last_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.width, chart.height = 22, 12
        ws1.add_chart(chart, f"E{header_row}")

    # ============================================================
    # SHEET 2: Revenue by Category (+ Bar Chart)
    # ============================================================
    ws2 = wb.create_sheet("Category Revenue")
    cat_data = db.sales_by_category()
    df_cat = pd.DataFrame(cat_data) if cat_data else pd.DataFrame(
        columns=["category", "revenue", "units_sold"])
    df_cat.rename(columns={"category": "Category", "revenue": "Revenue (₹)",
                            "units_sold": "Units Sold"}, inplace=True)

    header_row2, last_row2 = write_df(ws2, df_cat, title="Revenue by Category", start_row=1)
    autofit_columns(ws2, df_cat)

    if not df_cat.empty:
        chart2 = BarChart()
        chart2.type = "col"
        chart2.title = "Revenue by Category"
        chart2.y_axis.title = "Revenue (₹)"
        data2 = Reference(ws2, min_col=2, min_row=header_row2, max_row=last_row2)
        cats2 = Reference(ws2, min_col=1, min_row=header_row2 + 1, max_row=last_row2)
        chart2.add_data(data2, titles_from_data=True)
        chart2.set_categories(cats2)
        chart2.width, chart2.height = 20, 12
        ws2.add_chart(chart2, f"E{header_row2}")

    # ============================================================
    # SHEET 3: Daily Sales Trend (+ Line Chart)
    # ============================================================
    ws3 = wb.create_sheet("Sales Trend")
    trend_data = db.daily_sales_trend(days=30)
    df_trend = pd.DataFrame(trend_data) if trend_data else pd.DataFrame(
        columns=["sale_day", "revenue"])
    df_trend.rename(columns={"sale_day": "Date", "revenue": "Revenue (₹)"}, inplace=True)

    header_row3, last_row3 = write_df(ws3, df_trend, title="Daily Sales Trend (Last 30 Days)", start_row=1)
    autofit_columns(ws3, df_trend)

    if not df_trend.empty:
        chart3 = LineChart()
        chart3.title = "Sales Trend"
        chart3.y_axis.title = "Revenue (₹)"
        chart3.x_axis.title = "Date"
        data3 = Reference(ws3, min_col=2, min_row=header_row3, max_row=last_row3)
        cats3 = Reference(ws3, min_col=1, min_row=header_row3 + 1, max_row=last_row3)
        chart3.add_data(data3, titles_from_data=True)
        chart3.set_categories(cats3)
        chart3.width, chart3.height = 22, 12
        ws3.add_chart(chart3, f"E{header_row3}")

    # ============================================================
    # SHEET 4: Inventory Status (+ Conditional Formatting)
    # ============================================================
    ws4 = wb.create_sheet("Inventory Status")
    products = db.get_products()
    df_inv = pd.DataFrame(products) if products else pd.DataFrame(
        columns=["name", "category", "price", "stock_qty", "reorder_level", "supplier_name"])
    if not df_inv.empty:
        df_inv = df_inv[["name", "category", "price", "stock_qty", "reorder_level", "supplier_name"]]
    df_inv.rename(columns={
        "name": "Product", "category": "Category", "price": "Price (₹)",
        "stock_qty": "Stock Qty", "reorder_level": "Reorder Level",
        "supplier_name": "Supplier"
    }, inplace=True)

    header_row4, last_row4 = write_df(ws4, df_inv, title="Current Inventory Status", start_row=1)
    autofit_columns(ws4, df_inv)

    if not df_inv.empty:
        stock_col_letter = get_column_letter(4)  # "Stock Qty" is 4th column
        reorder_col_letter = get_column_letter(5)
        cell_range = f"{stock_col_letter}{header_row4 + 1}:{stock_col_letter}{last_row4}"

        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        # Highlight stock cells that are <= a fixed low-stock threshold visually via formula compare isn't
        # directly cross-column in openpyxl CellIsRule, so we do a manual pass instead:
        for row in range(header_row4 + 1, last_row4 + 1):
            stock_val = ws4.cell(row=row, column=4).value
            reorder_val = ws4.cell(row=row, column=5).value
            if stock_val is not None and reorder_val is not None and stock_val <= reorder_val:
                for col in range(1, len(df_inv.columns) + 1):
                    ws4.cell(row=row, column=col).fill = red_fill

    # ============================================================
    # SHEET 5: Low Stock Alerts (quick-reference list)
    # ============================================================
    ws5 = wb.create_sheet("Low Stock Alerts")
    low_stock = db.low_stock_products()
    df_low = pd.DataFrame(low_stock) if low_stock else pd.DataFrame(
        columns=["name", "category", "stock_qty", "reorder_level", "supplier_name"])
    if not df_low.empty:
        df_low = df_low[["name", "category", "stock_qty", "reorder_level", "supplier_name"]]
    df_low.rename(columns={
        "name": "Product", "category": "Category", "stock_qty": "Current Stock",
        "reorder_level": "Reorder Level", "supplier_name": "Supplier"
    }, inplace=True)
    write_df(ws5, df_low, title="⚠ Products Needing Reorder", start_row=1)
    autofit_columns(ws5, df_low)

    # ============================================================
    # Save
    # ============================================================
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wb.save(output_path)
    db.close()
    print(f"✅ Report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_report(f"exports/sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
