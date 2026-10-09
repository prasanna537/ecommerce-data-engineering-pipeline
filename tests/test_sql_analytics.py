import pytest

from src.analytics import kpi_summary, run_query
from src.load import connect, init_schema, load_clean_orders
from src.transform import clean_and_validate
from tests.conftest import make_raw


@pytest.fixture
def conn(tmp_paths):
    """Small hand-made dataset with known answers.

    Completed: A (2 x 10 = 20, Jan, Books), B (1 x 50 = 50, Jan, Toys), C (3 x 10 = 30, Feb, Books)
    Not completed: D Cancelled 1000, E Pending 500.
    """
    raw = make_raw(
        {"order_id": "A", "order_date": "2025-01-10", "product_id": "P1", "product_name": "Novel", "category": "Books", "quantity": "2", "unit_price": "10"},
        {"order_id": "B", "order_date": "2025-01-20", "product_id": "P2", "product_name": "Robot", "category": "Toys", "quantity": "1", "unit_price": "50"},
        {"order_id": "C", "order_date": "2025-02-05", "product_id": "P1", "product_name": "Novel", "category": "Books", "quantity": "3", "unit_price": "10"},
        {"order_id": "D", "order_date": "2025-02-06", "product_id": "P2", "product_name": "Robot", "category": "Toys", "quantity": "1", "unit_price": "1000", "order_status": "Cancelled"},
        {"order_id": "E", "order_date": "2025-02-07", "product_id": "P2", "product_name": "Robot", "category": "Toys", "quantity": "1", "unit_price": "500", "order_status": "Pending"},
    )
    clean, rejected = clean_and_validate(raw)
    assert rejected.empty
    c = connect(tmp_paths.db_path)
    init_schema(c, tmp_paths)
    load_clean_orders(c, clean)
    yield c
    c.close()


def test_total_revenue_counts_only_completed(conn, tmp_paths):
    assert run_query(conn, "total_revenue", tmp_paths).iloc[0, 0] == 100.0


def test_total_completed_orders(conn, tmp_paths):
    assert run_query(conn, "total_completed_orders", tmp_paths).iloc[0, 0] == 3


def test_average_order_value(conn, tmp_paths):
    assert run_query(conn, "average_order_value", tmp_paths).iloc[0, 0] == pytest.approx(33.33)


def test_monthly_revenue(conn, tmp_paths):
    df = run_query(conn, "monthly_revenue", tmp_paths)
    assert df["year_month"].tolist() == ["2025-01", "2025-02"]
    assert df["monthly_revenue"].tolist() == [70.0, 30.0]
    assert df["completed_orders"].tolist() == [2, 1]


def test_category_revenue(conn, tmp_paths):
    df = run_query(conn, "category_revenue", tmp_paths)
    assert df["category"].tolist() == ["Books", "Toys"]  # tie on revenue -> alphabetical
    assert dict(zip(df["category"], df["category_revenue"])) == {"Books": 50.0, "Toys": 50.0}


def test_top_selling_products(conn, tmp_paths):
    df = run_query(conn, "top_selling_products", tmp_paths)
    assert df.iloc[0]["product_id"] == "P1" and df.iloc[0]["units_sold"] == 5
    assert df.iloc[1]["product_id"] == "P2" and df.iloc[1]["units_sold"] == 1


def test_kpi_summary_matches_individual_queries(conn, tmp_paths):
    kpi = kpi_summary(conn, tmp_paths).iloc[0]
    assert kpi["total_revenue"] == 100.0 and kpi["total_completed_orders"] == 3


def test_monthly_revenue_sums_to_total(conn, tmp_paths):
    monthly = run_query(conn, "monthly_revenue", tmp_paths)["monthly_revenue"].sum()
    assert monthly == pytest.approx(run_query(conn, "total_revenue", tmp_paths).iloc[0, 0])
