from src.config import RAW_COLUMNS, VALID_STATUSES
from src.generate_data import generate_orders


def test_at_least_500_records(raw_orders):
    assert len(raw_orders) >= 500


def test_expected_columns(raw_orders):
    assert list(raw_orders.columns) == RAW_COLUMNS


def test_generation_is_reproducible():
    assert generate_orders(seed=7).equals(generate_orders(seed=7))


def test_different_seed_gives_different_data():
    assert not generate_orders(seed=1).equals(generate_orders(seed=2))


def test_defects_are_injected(raw_orders):
    assert raw_orders["order_id"].duplicated().sum() == 15
    assert (raw_orders[RAW_COLUMNS] == "").any(axis=None)
    assert set(raw_orders["order_status"]) <= set(VALID_STATUSES)
