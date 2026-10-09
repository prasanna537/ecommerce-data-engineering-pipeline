"""ETL entry point: extract -> clean/validate -> load -> analytics -> export.

Run with:  python -m src.etl
"""
import json
import logging
from collections import Counter

from .config import Paths
from .export import export_all
from .extract import extract_orders
from .generate_data import generate_orders, write_raw
from .load import connect, count_rows, init_schema, load_clean_orders
from .transform import clean_and_validate

log = logging.getLogger("etl")


def run_etl(paths: Paths = Paths(), generate_if_missing: bool = True) -> dict:
    """Run the full pipeline and return a summary dict (also saved as JSON)."""
    if not paths.raw_csv.exists():
        if not generate_if_missing:
            raise FileNotFoundError(f"Raw file not found: {paths.raw_csv}")
        log.info("No raw file found; generating synthetic data")
        write_raw(generate_orders(), paths.raw_csv)

    raw = extract_orders(paths.raw_csv)
    clean, rejected = clean_and_validate(raw)

    paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(paths.clean_csv, index=False, encoding="utf-8")
    rejected.to_csv(paths.rejected_csv, index=False, encoding="utf-8")

    conn = connect(paths.db_path)
    try:
        init_schema(conn, paths)
        load_clean_orders(conn, clean)
        exported = export_all(conn, paths)
        db_orders = count_rows(conn, "fact_orders")
    finally:
        conn.close()

    reason_counts = Counter(r for rs in rejected["rejection_reasons"] for r in rs.split(";"))
    summary = {
        "raw_rows": len(raw),
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "rejection_reason_counts": dict(sorted(reason_counts.items())),
        "orders_in_database": db_orders,
        "exported_files": exported,
    }
    paths.summary_json.parent.mkdir(parents=True, exist_ok=True)
    paths.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("ETL finished: %s", summary)
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_etl()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
