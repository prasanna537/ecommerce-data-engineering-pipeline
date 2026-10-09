import pytest

from src.transform import clean_and_validate
from tests.conftest import make_raw


def reasons_for(**overrides):
    _, rejected = clean_and_validate(make_raw(overrides))
    return rejected["rejection_reasons"].tolist()


@pytest.mark.parametrize("field", ["order_id", "order_date", "customer_id", "product_id",
                                   "product_name", "category", "quantity", "unit_price", "order_status"])
def test_missing_required_value_rejected(field):
    assert reasons_for(**{field: ""}) == [f"missing_{field}"]


def test_whitespace_only_counts_as_missing():
    assert reasons_for(customer_id="   ") == ["missing_customer_id"]


@pytest.mark.parametrize("qty", ["0", "-1", "abc", "2.5", "nan", "inf"])
def test_invalid_quantity_rejected(qty):
    assert reasons_for(quantity=qty) == ["invalid_quantity"]


@pytest.mark.parametrize("price", ["0", "-5", "free", "nan", "inf"])
def test_invalid_price_rejected(price):
    assert reasons_for(unit_price=price) == ["invalid_unit_price"]


def test_invalid_date_and_status_rejected():
    assert reasons_for(order_date="2025-13-45") == ["invalid_order_date"]
    assert reasons_for(order_status="Shipped") == ["invalid_order_status"]


def test_multiple_reasons_are_all_reported():
    assert reasons_for(quantity="0", unit_price="-1") == ["invalid_quantity;invalid_unit_price"]


def test_valid_row_passes_and_is_normalised():
    clean, rejected = clean_and_validate(make_raw({"order_id": " ord-9 ", "order_status": "completed"}))
    assert rejected.empty
    assert clean.loc[0, "order_id"] == "ORD-9"
    assert clean.loc[0, "order_status"] == "Completed"


def test_rejected_has_source_row_and_original_values():
    raw = make_raw({"order_id": "A"}, {"order_id": "B", "quantity": "-3"})
    _, rejected = clean_and_validate(raw)
    assert rejected.loc[0, "source_row"] == 3  # header is line 1, so 2nd data row = line 3
    assert rejected.loc[0, "quantity"] == "-3"


def test_generated_data_split(raw_orders):
    clean, rejected = clean_and_validate(raw_orders)
    assert len(clean) + len(rejected) == len(raw_orders)
    assert len(clean) >= 500
    assert (clean["quantity"] > 0).all() and (clean["unit_price"] > 0).all()
    assert clean["order_id"].is_unique
    assert (rejected["rejection_reasons"] != "").all()
