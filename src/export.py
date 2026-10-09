"""Export model tables and analytics tables as Power BI-friendly CSV files."""
import sqlite3

import pandas as pd

from .analytics import analytics_tables
from .config import Paths

MODEL_TABLES = ["fact_orders", "dim_customer", "dim_product", "dim_date"]


def export_all(conn: sqlite3.Connection, paths: Paths = Paths()) -> list[str]:
    """Write every table to data/exports as UTF-8 CSV; returns the file names."""
    paths.export_dir.mkdir(parents=True, exist_ok=True)
    tables = {t: pd.read_sql_query(f"SELECT * FROM {t} ORDER BY 1", conn) for t in MODEL_TABLES}
    tables.update(analytics_tables(conn, paths))
    for name, df in tables.items():
        df.to_csv(paths.export_dir / f"{name}.csv", index=False, encoding="utf-8")
    return sorted(f"{n}.csv" for n in tables)
