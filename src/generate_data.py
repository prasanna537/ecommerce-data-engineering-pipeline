"""Generate synthetic e-commerce orders, including deliberate data defects."""
import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .config import RAW_COLUMNS, Paths

PRODUCTS = [
    ("P001", "Wireless Mouse", "Electronics", 19.99),
    ("P002", "Bluetooth Headphones", "Electronics", 59.50),
    ("P003", "USB-C Charger", "Electronics", 24.99),
    ("P004", "Smart Watch", "Electronics", 129.00),
    ("P005", "Running Shoes", "Fashion", 79.90),
    ("P006", "Denim Jacket", "Fashion", 64.00),
    ("P007", "Cotton T-Shirt", "Fashion", 14.50),
    ("P008", "Leather Wallet", "Fashion", 34.00),
    ("P009", "Coffee Maker", "Home & Kitchen", 49.99),
    ("P010", "Non-stick Pan", "Home & Kitchen", 29.90),
    ("P011", "Blender", "Home & Kitchen", 39.00),
    ("P012", "Desk Lamp", "Home & Kitchen", 21.75),
    ("P013", "Yoga Mat", "Sports", 25.00),
    ("P014", "Dumbbell Set", "Sports", 89.00),
    ("P015", "Water Bottle", "Sports", 12.99),
    ("P016", "Camping Tent", "Sports", 149.00),
    ("P017", "Bestselling Novel", "Books", 11.99),
    ("P018", "Cookbook", "Books", 22.50),
    ("P019", "Python Handbook", "Books", 39.99),
    ("P020", "Storybook for Kids", "Books", 9.99),
]
STATUSES = ["Completed", "Cancelled", "Returned", "Pending"]
STATUS_WEIGHTS = [75, 10, 5, 10]


def generate_orders(
    n_orders: int = 550,
    seed: int = 42,
    n_duplicates: int = 15,
    n_missing: int = 12,
    n_bad_quantity: int = 10,
    n_bad_price: int = 10,
) -> pd.DataFrame:
    """Return a raw orders table (all values are strings, like a CSV read).

    `n_orders` base orders get unique IDs. Defects are injected into distinct
    rows, then `n_duplicates` exact copies of untouched rows are appended, so
    the output has `n_orders + n_duplicates` rows.
    """
    n_defective = n_missing + n_bad_quantity + n_bad_price
    if n_orders < n_defective + n_duplicates:
        raise ValueError("n_orders is too small for the requested defects")

    rng = random.Random(seed)
    start = date(2025, 1, 1)
    rows = []
    for i in range(1, n_orders + 1):
        pid, name, category, price = rng.choice(PRODUCTS)
        order_date = start + timedelta(days=rng.randint(0, 364))
        rows.append({
            "order_id": f"ORD-{i:05d}",
            "order_date": order_date.isoformat(),
            "customer_id": f"C{rng.randint(1, 150):04d}",
            "product_id": pid,
            "product_name": name,
            "category": category,
            "quantity": str(rng.randint(1, 5)),
            "unit_price": f"{price:.2f}",
            "order_status": rng.choices(STATUSES, STATUS_WEIGHTS)[0],
        })

    indices = rng.sample(range(n_orders), n_defective)
    missing_idx = indices[:n_missing]
    qty_idx = indices[n_missing:n_missing + n_bad_quantity]
    price_idx = indices[n_missing + n_bad_quantity:]

    blankable = ["customer_id", "product_id", "order_date", "product_name", "category"]
    for k, i in enumerate(missing_idx):
        rows[i][blankable[k % len(blankable)]] = ""
    for k, i in enumerate(qty_idx):
        rows[i]["quantity"] = ["0", "-3", "abc", "2.5"][k % 4]
    for k, i in enumerate(price_idx):
        rows[i]["unit_price"] = ["0", "-9.99", "free"][k % 3]

    touched = set(indices)
    untouched = [i for i in range(n_orders) if i not in touched]
    for i in rng.sample(untouched, n_duplicates):
        rows.append(dict(rows[i]))

    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def write_raw(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic raw orders CSV")
    parser.add_argument("--orders", type=int, default=550)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    paths = Paths()
    df = generate_orders(n_orders=args.orders, seed=args.seed)
    write_raw(df, paths.raw_csv)
    print(f"Wrote {len(df)} raw rows to {paths.raw_csv.relative_to(paths.root)}")


if __name__ == "__main__":
    main()
