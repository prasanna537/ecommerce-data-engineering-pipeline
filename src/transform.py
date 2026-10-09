"""Clean, validate and transform raw orders. Pure pandas, no file I/O."""
import numpy as np
import pandas as pd

from .config import DATE_FORMAT, REQUIRED_COLUMNS, VALID_STATUSES


def _normalise(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    for col in ("order_id", "customer_id", "product_id"):
        df[col] = df[col].str.upper()
    df["order_status"] = df["order_status"].str.title()
    return df


def find_rejection_reasons(df: pd.DataFrame) -> pd.Series:
    """Return a ';'-joined reason string per row ('' means the row is valid)."""
    reasons = pd.DataFrame(index=df.index)

    for col in REQUIRED_COLUMNS:
        reasons[f"missing_{col}"] = df[col] == ""

    dates = pd.to_datetime(df["order_date"], format=DATE_FORMAT, errors="coerce")
    reasons["invalid_order_date"] = (df["order_date"] != "") & dates.isna()

    qty = pd.to_numeric(df["quantity"], errors="coerce")
    qty_ok = np.isfinite(qty) & (qty > 0) & (qty == np.floor(qty))
    reasons["invalid_quantity"] = (df["quantity"] != "") & ~qty_ok

    price = pd.to_numeric(df["unit_price"], errors="coerce")
    price_ok = np.isfinite(price) & (price > 0)
    reasons["invalid_unit_price"] = (df["unit_price"] != "") & ~price_ok

    reasons["invalid_order_status"] = (
        (df["order_status"] != "") & ~df["order_status"].isin(VALID_STATUSES)
    )

    # Duplicates: among otherwise-valid rows, keep the first occurrence of each order_id.
    valid_so_far = ~reasons.any(axis=1)
    reasons["duplicate_order_id"] = valid_so_far & df["order_id"].where(valid_so_far).duplicated()

    return reasons.apply(lambda r: ";".join(r.index[r.to_numpy()]), axis=1)


def clean_and_validate(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split raw orders into (clean, rejected).

    `rejected` holds the original raw values plus `source_row` (line number in the
    CSV file, header = line 1) and `rejection_reasons`.
    """
    norm = _normalise(raw)
    reasons = find_rejection_reasons(norm)
    bad = reasons != ""

    rejected = raw.loc[bad].copy()
    rejected.insert(0, "source_row", rejected.index + 2)
    rejected["rejection_reasons"] = reasons[bad]

    clean = norm.loc[~bad].copy()
    clean["order_date"] = pd.to_datetime(clean["order_date"], format=DATE_FORMAT).dt.strftime(DATE_FORMAT)
    clean["quantity"] = clean["quantity"].astype(float).astype(int)
    clean["unit_price"] = clean["unit_price"].astype(float).round(2)
    clean["revenue"] = (clean["quantity"] * clean["unit_price"]).round(2)
    return clean.reset_index(drop=True), rejected.reset_index(drop=True)
