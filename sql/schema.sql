-- ============================================================
-- Smart Retail Inventory & Sales Analytics System
-- Database Schema
-- ============================================================

DROP DATABASE IF EXISTS retail_inventory;
CREATE DATABASE retail_inventory;
USE retail_inventory;

-- ------------------------------------------------------------
-- Table: suppliers
-- ------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id     INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    contact_number  VARCHAR(20),
    email           VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: products
-- ------------------------------------------------------------
CREATE TABLE products (
    product_id      INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(50)  NOT NULL,
    price           DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock_qty       INT NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    reorder_level   INT NOT NULL DEFAULT 10,
    supplier_id     INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        ON DELETE SET NULL,
    UNIQUE KEY unique_product_name (name)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: sales
-- ------------------------------------------------------------
CREATE TABLE sales (
    sale_id         INT AUTO_INCREMENT PRIMARY KEY,
    product_id      INT NOT NULL,
    quantity_sold   INT NOT NULL CHECK (quantity_sold > 0),
    sale_price      DECIMAL(10,2) NOT NULL,
    total_amount    DECIMAL(10,2) NOT NULL,
    sale_date       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Indexes for faster reporting queries
-- ------------------------------------------------------------
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_products_category ON products(category);

-- ------------------------------------------------------------
-- Sample seed data
-- ------------------------------------------------------------
INSERT INTO suppliers (name, contact_number, email) VALUES
('Global Traders Pvt Ltd', '9876543210', 'contact@globaltraders.com'),
('Sunrise Distributors', '9123456780', 'info@sunrisedist.com'),
('Metro Wholesale', '9988776655', 'sales@metrowholesale.com');

INSERT INTO products (name, category, price, stock_qty, reorder_level, supplier_id) VALUES
('Basmati Rice 5kg', 'Grocery', 450.00, 40, 10, 1),
('Sunflower Oil 1L', 'Grocery', 150.00, 8, 15, 1),
('Notebook A4 200pg', 'Stationery', 60.00, 100, 20, 2),
('Ball Pen Pack (10)', 'Stationery', 45.00, 5, 10, 2),
('LED Bulb 9W', 'Electronics', 90.00, 60, 15, 3),
('Extension Board', 'Electronics', 350.00, 12, 5, 3),
('Toothpaste 150g', 'Personal Care', 55.00, 7, 20, 1),
('Shampoo 340ml', 'Personal Care', 210.00, 25, 10, 2);

INSERT INTO sales (product_id, quantity_sold, sale_price, total_amount, sale_date) VALUES
(1, 2, 450.00, 900.00, NOW() - INTERVAL 5 DAY),
(3, 10, 60.00, 600.00, NOW() - INTERVAL 4 DAY),
(5, 5, 90.00, 450.00, NOW() - INTERVAL 4 DAY),
(2, 3, 150.00, 450.00, NOW() - INTERVAL 3 DAY),
(6, 1, 350.00, 350.00, NOW() - INTERVAL 3 DAY),
(4, 6, 45.00, 270.00, NOW() - INTERVAL 2 DAY),
(8, 4, 210.00, 840.00, NOW() - INTERVAL 2 DAY),
(7, 5, 55.00, 275.00, NOW() - INTERVAL 1 DAY),
(1, 1, 450.00, 450.00, NOW()),
(5, 8, 90.00, 720.00, NOW());
INSERT INTO products (name, category, price, stock_qty, reorder_level, supplier_id) VALUES
('Whole Wheat Atta 5kg', 'Grocery', 280.00, 35, 10, 1),
('Turmeric Powder 200g', 'Grocery', 65.00, 50, 15, 1),
('Green Tea Bags (25pk)', 'Grocery', 120.00, 30, 10, 2),
('Gel Pen Set (5)', 'Stationery', 85.00, 60, 15, 2),
('A5 Sketchbook', 'Stationery', 110.00, 40, 10, 2),
('Geometry Box', 'Stationery', 75.00, 25, 8, 2),
('USB-C Cable 1m', 'Electronics', 199.00, 45, 12, 3),
('Wireless Mouse', 'Electronics', 450.00, 20, 5, 3),
('Power Bank 10000mAh', 'Electronics', 999.00, 15, 5, 3),
('Face Wash 100ml', 'Personal Care', 145.00, 30, 10, 1),
('Hand Sanitizer 200ml', 'Personal Care', 90.00, 6, 15, 2),
('Body Lotion 200ml', 'Personal Care', 175.00, 22, 8, 1);

