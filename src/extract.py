"""Extract step: read the raw CSV with every value kept as text."""
import pandas as pd

from .config import RAW_COLUMNS


def extract_orders(path) -> pd.DataFrame:
    """Read raw orders. Blank cells stay as '' so validation sees them as missing."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    missing_cols = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Raw file is missing columns: {missing_cols}")
    return df[RAW_COLUMNS]
