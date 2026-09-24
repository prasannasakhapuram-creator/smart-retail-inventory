# Smart Retail Inventory & Sales Analytics System

A fresher-friendly but interview-worthy project combining **Python + MySQL + Excel automation**.

It simulates a small retail shop: manage products & suppliers, record sales with
transaction-safe stock deduction, and auto-generate a polished multi-sheet Excel
report (with charts and conditional formatting) straight from live MySQL data.

---

## 🧱 Tech Stack
- **Python 3.9+**
- **MySQL 8.0+**
- **openpyxl / pandas** for Excel report generation
- **PyMySQL** for DB connectivity

---

## 📁 Project Structure
```
smart-retail-inventory/
├── main.py                # CLI entry point (menu-driven app)
├── streamlit_app.py       # Web dashboard (same database.py backend)
├── database.py            # All DB logic: CRUD + transactions + analytics queries
├── report_generator.py    # Builds the multi-sheet Excel report with charts
├── db_config.py            # Your MySQL connection settings
├── requirements.txt
├── sql/
│   └── schema.sql         # Full schema + sample seed data
├── tests/
│   └── test_database.py   # pytest suite (mocked DB, no server needed)
├── exports/                # Generated Excel reports land here
└── README.md
```

---

## ⚙️ Setup

### 1. Create the database
```bash
mysql -u root -p < sql/schema.sql
```
This creates the `retail_inventory` database with 3 tables
(`suppliers`, `products`, `sales`), proper foreign keys, `CHECK` constraints,
and some sample data so you can demo immediately.

### 2. Configure your connection
Edit `db_config.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "retail_inventory"
}
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python main.py
```

You'll get a menu-driven CLI: add products, record sales, view low-stock alerts,
and generate the Excel report (option `11`) — it will drop a timestamped
`.xlsx` file into `exports/`.

---

## 🗄️ Database Design (why it's not just one flat table)

```
suppliers (1) ───< (many) products (1) ───< (many) sales
```

- **suppliers** → who you buy stock from
- **products** → what you sell, with `reorder_level` for low-stock logic
- **sales** → every transaction, linked back to the product

Constraints used: `FOREIGN KEY`, `UNIQUE`, `CHECK (price >= 0)`,
`CHECK (stock_qty >= 0)` — this is what separates a "9" project from a
beginner one; most freshers skip constraints entirely.

---

## 🔒 Transaction Safety (the part that impresses interviewers)

`record_sale()` in `database.py` wraps the **insert into `sales`** and the
**stock deduction in `products`** inside a single MySQL transaction:

- If stock is insufficient → the whole operation is rolled back, nothing is
  written.
- If any step fails (network blip, constraint violation) → automatic rollback,
  so your data never ends up half-updated.

This is a classic real-world requirement (you never want a "sale" to exist
without the stock actually being reduced, or vice versa).

---

## 📊 What the Excel Report Contains

Running option `11` (or `python report_generator.py` directly) generates a
workbook with **5 sheets**:

| Sheet | Contents |
|---|---|
| **Top Products** | Top 10 best-sellers + bar chart |
| **Category Revenue** | Revenue grouped by category + bar chart |
| **Sales Trend** | Last 30 days of revenue + line chart |
| **Inventory Status** | Full stock list, rows auto-highlighted red when `stock_qty <= reorder_level` |
| **Low Stock Alerts** | Quick-reference list of products needing reorder |

All aggregation is done with **pandas** (`GROUP BY`-style queries pulled from
MySQL), and the formatting/charts are built with **openpyxl** — headers are
styled, columns auto-fit, and charts are native Excel chart objects (not
images), so they're still editable if you open the file.

---

## 🖥️ Streamlit Dashboard (recommended for your resume/demo)

Instead of (or alongside) the CLI, you can run a full web dashboard on top
of the exact same `database.py` — no duplicated logic:

```bash
streamlit run streamlit_app.py
```

This opens a browser app with:
- **Dashboard** — live KPIs (total revenue, low-stock count) + bar/line charts
- **Products** — searchable table, add/update/delete forms
- **Record Sale** — dropdown + quantity, same transaction-safe `record_sale()`
- **Sales History** — table + CSV download
- **Low Stock Alerts**, **Suppliers**, and **Export Report** (downloads the
  same 5-sheet Excel report straight from the browser)

Deploy it for free on [Streamlit Community Cloud](https://streamlit.io/cloud)
(pair it with a free-tier MySQL host like Railway or Aiven) so you can put a
**live link** on your resume instead of just a repo link — this is the
single highest-impact upgrade for making the project stand out.

---

## 🧪 Automated Tests

`tests/test_database.py` uses `pytest` + `unittest.mock` to test the core
business logic — especially the transaction-safety of `record_sale()` —
**without needing a live MySQL server** (so it also works in CI pipelines).

```bash
pytest -v
```

Covers:
- Validation errors (negative price/stock) raise before hitting the DB
- `record_sale()` rolls back on insufficient stock or missing product
- `record_sale()` commits and returns the correct total on success
- `record_sale()` actually opens a transaction (`conn.begin()`)
- `update_product()` is a no-op when no fields are given, and ignores
  unknown/unsafe field names
- `get_products()` builds the correct `WHERE` clause for category and
  low-stock filters

This is worth mentioning explicitly in interviews — most fresher projects
have zero tests, so even a small, well-targeted suite around the riskiest
logic (money + stock changing together) stands out.

---

## 🚀 Ideas to Push This Further (optional stretch goals)
- Add `smtplib` to auto-email the generated report every night.
- Add a `schedule`-based daily report job (`pip install schedule`).
- Add user authentication (admin vs staff roles) for extra realism.

---

## 🗣️ How to explain this project in an interview (30-second pitch)
> "I built a retail inventory and sales system where MySQL stores normalized
> product, supplier, and sales data with proper constraints and foreign keys.
> The Python layer handles CRUD operations and uses database transactions so
> a sale and its stock deduction either both succeed or both roll back. I
> wrote pytest unit tests with mocking to verify that transaction logic
> without needing a live database — useful for CI. On top of that, I used
> pandas to aggregate sales data and openpyxl to auto-generate a multi-sheet
> Excel report with real chart objects and conditional formatting for
> low-stock alerts. I also built a Streamlit dashboard on top of the same
> backend so it's usable as a live web app, not just a terminal script,
> and deployed it at [link]."
