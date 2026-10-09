import pytest

from src.transform import clean_and_validate
from tests.conftest import make_raw


def test_revenue_is_quantity_times_price():
    clean, _ = clean_and_validate(make_raw(
        {"order_id": "A", "quantity": "3", "unit_price": "19.99"},
        {"order_id": "B", "quantity": "1", "unit_price": "100"},
    ))
    assert clean["revenue"].tolist() == [pytest.approx(59.97), pytest.approx(100.0)]


def test_revenue_rounded_to_cents():
    clean, _ = clean_and_validate(make_raw({"quantity": "3", "unit_price": "0.1"}))
    assert clean.loc[0, "revenue"] == 0.3


def test_revenue_for_all_generated_rows(raw_orders):
    clean, _ = clean_and_validate(raw_orders)
    assert (clean["revenue"] == (clean["quantity"] * clean["unit_price"]).round(2)).all()
