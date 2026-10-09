import pandas as pd
import pytest

from src.config import RAW_COLUMNS, Paths
from src.generate_data import generate_orders


@pytest.fixture
def raw_orders():
    return generate_orders()


@pytest.fixture
def tmp_paths(tmp_path):
    """Isolated project root so tests never touch the real data/ folder."""
    return Paths(root=tmp_path)


def make_raw(*rows):
    """Build a raw (all-string) frame from dicts; unspecified fields use valid defaults."""
    base = {
        "order_id": "ORD-1", "order_date": "2025-03-01", "customer_id": "C1",
        "product_id": "P1", "product_name": "Thing", "category": "Books",
        "quantity": "2", "unit_price": "10.50", "order_status": "Completed",
    }
    return pd.DataFrame([{**base, **r} for r in rows], columns=RAW_COLUMNS)
