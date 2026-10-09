"""Central configuration: paths, column names and business rules."""
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_COLUMNS = [
    "order_id", "order_date", "customer_id", "product_id",
    "product_name", "category", "quantity", "unit_price", "order_status",
]
REQUIRED_COLUMNS = RAW_COLUMNS  # every column is mandatory
VALID_STATUSES = ["Completed", "Cancelled", "Returned", "Pending"]
REVENUE_STATUS = "Completed"  # only completed orders count as revenue
DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class Paths:
    """All file locations, derived from one root so tests can use a temp dir."""
    root: Path = PROJECT_ROOT
    sql_dir: Path = PROJECT_ROOT / "sql"

    @property
    def raw_csv(self) -> Path:
        return self.root / "data" / "raw" / "orders_raw.csv"

    @property
    def clean_csv(self) -> Path:
        return self.root / "data" / "processed" / "clean_orders.csv"

    @property
    def rejected_csv(self) -> Path:
        return self.root / "data" / "processed" / "rejected_records.csv"

    @property
    def export_dir(self) -> Path:
        return self.root / "data" / "exports"

    @property
    def db_path(self) -> Path:
        return self.root / "data" / "ecommerce.db"

    @property
    def summary_json(self) -> Path:
        return self.root / "reports" / "etl_run_summary.json"
