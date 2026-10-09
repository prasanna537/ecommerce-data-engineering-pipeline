"""Run the SQL analytics queries stored in sql/*.sql."""
import sqlite3

import pandas as pd

from .config import Paths

# Table name -> SQL file (without extension)
TABLE_QUERIES = {
    "monthly_revenue": "monthly_revenue",
    "category_revenue": "category_revenue",
    "top_selling_products": "top_selling_products",
}
SCALAR_QUERIES = ["total_revenue", "total_completed_orders", "average_order_value"]


def run_query(conn: sqlite3.Connection, name: str, paths: Paths = Paths()) -> pd.DataFrame:
    sql = (paths.sql_dir / f"{name}.sql").read_text(encoding="utf-8")
    return pd.read_sql_query(sql, conn)


def kpi_summary(conn: sqlite3.Connection, paths: Paths = Paths()) -> pd.DataFrame:
    """One-row table with the headline KPIs."""
    values = {name: run_query(conn, name, paths).iloc[0, 0] for name in SCALAR_QUERIES}
    return pd.DataFrame([values])


def analytics_tables(conn: sqlite3.Connection, paths: Paths = Paths()) -> dict[str, pd.DataFrame]:
    tables = {t: run_query(conn, q, paths) for t, q in TABLE_QUERIES.items()}
    tables["kpi_summary"] = kpi_summary(conn, paths)
    return tables
