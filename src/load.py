"""Load step: idempotent upserts of clean data into SQLite."""
import sqlite3

import pandas as pd

from .config import Paths


def connect(db_path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection, paths: Paths = Paths()) -> None:
    conn.executescript((paths.sql_dir / "schema.sql").read_text(encoding="utf-8"))


def _build_dim_date(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(pd.Series(sorted(set(dates))))
    return pd.DataFrame({
        "date_key": d.dt.strftime("%Y-%m-%d"),
        "year": d.dt.year,
        "quarter": d.dt.quarter,
        "month": d.dt.month,
        "month_name": d.dt.strftime("%B"),
        "year_month": d.dt.strftime("%Y-%m"),
    })


def load_clean_orders(conn: sqlite3.Connection, clean: pd.DataFrame) -> None:
    """Upsert dimensions and facts. Re-running with the same data changes nothing;
    re-running with changed values for an existing order_id updates that order."""
    dates = list(_build_dim_date(clean["order_date"]).astype(object).itertuples(index=False, name=None))
    customers = [(c,) for c in clean["customer_id"].unique()]
    products = clean.drop_duplicates("product_id", keep="last")[["product_id", "product_name", "category"]]
    facts = clean[[
        "order_id", "order_date", "customer_id", "product_id",
        "quantity", "unit_price", "revenue", "order_status",
    ]]
    # Python ints/floats rather than numpy types, which sqlite3 cannot bind.
    fact_rows = [tuple(r) for r in facts.astype(object).itertuples(index=False, name=None)]

    with conn:  # one transaction: all-or-nothing
        conn.executemany("INSERT OR IGNORE INTO dim_date VALUES (?,?,?,?,?,?)", dates)
        conn.executemany("INSERT OR IGNORE INTO dim_customer VALUES (?)", customers)
        conn.executemany(
            """INSERT INTO dim_product VALUES (?,?,?)
               ON CONFLICT(product_id) DO UPDATE SET
                 product_name = excluded.product_name, category = excluded.category""",
            list(products.itertuples(index=False, name=None)),
        )
        conn.executemany(
            """INSERT INTO fact_orders VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(order_id) DO UPDATE SET
                 order_date = excluded.order_date, customer_id = excluded.customer_id,
                 product_id = excluded.product_id, quantity = excluded.quantity,
                 unit_price = excluded.unit_price, revenue = excluded.revenue,
                 order_status = excluded.order_status""",
            fact_rows,
        )


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
