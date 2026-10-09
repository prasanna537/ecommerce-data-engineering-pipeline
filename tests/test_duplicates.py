from src.transform import clean_and_validate
from tests.conftest import make_raw


def test_duplicate_order_id_rejected_first_kept():
    raw = make_raw({"order_id": "X", "quantity": "1"}, {"order_id": "X", "quantity": "5"})
    clean, rejected = clean_and_validate(raw)
    assert clean["quantity"].tolist() == [1]
    assert rejected["rejection_reasons"].tolist() == ["duplicate_order_id"]


def test_duplicates_are_case_and_whitespace_insensitive():
    clean, rejected = clean_and_validate(make_raw({"order_id": "x1"}, {"order_id": " X1 "}))
    assert len(clean) == 1 and len(rejected) == 1


def test_invalid_first_row_does_not_block_valid_duplicate():
    raw = make_raw({"order_id": "X", "quantity": "0"}, {"order_id": "X"})
    clean, rejected = clean_and_validate(raw)
    assert len(clean) == 1
    assert rejected["rejection_reasons"].tolist() == ["invalid_quantity"]


def test_all_generated_duplicates_are_caught(raw_orders):
    _, rejected = clean_and_validate(raw_orders)
    assert rejected["rejection_reasons"].eq("duplicate_order_id").sum() == 15
