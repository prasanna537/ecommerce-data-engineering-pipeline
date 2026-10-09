-- Star schema for the e-commerce analytics database.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key   TEXT PRIMARY KEY,          -- YYYY-MM-DD
    year       INTEGER NOT NULL,
    quarter    INTEGER NOT NULL,
    month      INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    year_month TEXT NOT NULL              -- YYYY-MM
);

-- One row per order (each source record holds a single product line).
-- order_id as PRIMARY KEY is what makes reloading idempotent.
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id     TEXT PRIMARY KEY,
    order_date   TEXT NOT NULL REFERENCES dim_date (date_key),
    customer_id  TEXT NOT NULL REFERENCES dim_customer (customer_id),
    product_id   TEXT NOT NULL REFERENCES dim_product (product_id),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    unit_price   REAL NOT NULL CHECK (unit_price > 0),
    revenue      REAL NOT NULL,           -- quantity * unit_price
    order_status TEXT NOT NULL CHECK (order_status IN ('Completed', 'Cancelled', 'Returned', 'Pending'))
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_fact_orders_product ON fact_orders (product_id);
