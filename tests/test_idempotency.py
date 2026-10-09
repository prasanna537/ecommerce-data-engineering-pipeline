import pandas as pd

from src.config import Paths
from src.etl import run_etl
from src.extract import extract_orders
from src.generate_data import generate_orders, write_raw
from src.load import connect, count_rows, init_schema, load_clean_orders
from src.transform import clean_and_validate


def snapshot(paths):
    conn = connect(paths.db_path)
    try:
        return {t: pd.read_sql_query(f"SELECT * FROM {t} ORDER BY 1", conn)
                for t in ("fact_orders", "dim_customer", "dim_product", "dim_date")}
    finally:
        conn.close()


def test_rerunning_etl_does_not_duplicate_or_change_data(tmp_paths):
    first = run_etl(tmp_paths)
    before = snapshot(tmp_paths)
    second = run_etl(tmp_paths)
    after = snapshot(tmp_paths)

    assert first["orders_in_database"] == second["orders_in_database"] == first["clean_rows"]
    for table in before:
        pd.testing.assert_frame_equal(before[table], after[table])


def test_loading_same_data_twice_keeps_row_count(tmp_paths):
    write_raw(generate_orders(), tmp_paths.raw_csv)
    clean, _ = clean_and_validate(extract_orders(tmp_paths.raw_csv))
    conn = connect(tmp_paths.db_path)
    init_schema(conn, tmp_paths)
    load_clean_orders(conn, clean)
    n = count_rows(conn, "fact_orders")
    load_clean_orders(conn, clean)
    assert count_rows(conn, "fact_orders") == n == len(clean)
    conn.close()


def test_changed_order_is_updated_not_duplicated(tmp_paths):
    write_raw(generate_orders(), tmp_paths.raw_csv)
    run_etl(tmp_paths)

    raw = extract_orders(tmp_paths.raw_csv)
    target = raw.loc[raw["order_id"] == "ORD-00001"].index[0]
    raw.loc[target, ["quantity", "unit_price", "order_status"]] = ["4", "10.00", "Cancelled"]
    write_raw(raw, tmp_paths.raw_csv)
    run_etl(tmp_paths)

    fact = snapshot(tmp_paths)["fact_orders"]
    row = fact[fact["order_id"] == "ORD-00001"]
    assert len(row) == 1
    assert row.iloc[0]["revenue"] == 40.0 and row.iloc[0]["order_status"] == "Cancelled"


def test_etl_writes_outputs_and_rejections(tmp_paths):
    summary = run_etl(tmp_paths)
    assert summary["raw_rows"] == summary["clean_rows"] + summary["rejected_rows"]
    rejected = pd.read_csv(tmp_paths.rejected_csv)
    assert len(rejected) == summary["rejected_rows"] > 0
    assert "rejection_reasons" in rejected.columns
    assert (tmp_paths.export_dir / "fact_orders.csv").exists()
    assert (tmp_paths.export_dir / "kpi_summary.csv").exists()
