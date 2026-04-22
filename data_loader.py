"""
Data loader for CardMarket Dashboard.
Supports local files (default) and S3 URLs (optional via env vars).
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# Data source configuration
# - local (default): read from /app/data (Docker) or ./data (local)
# - s3: keep backward-compatible remote loading
DATA_SOURCE = os.getenv("DATA_SOURCE", "local").strip().lower()
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# Optional S3 configuration
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "mtg-streamlit-dashboard-s3-bucket")
S3_REGION = os.getenv("S3_REGION", "eu-central-1")
PUBLIC_BASE_URL = f"https://{BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com"

# Expected filenames
ORDERS_FILENAME = "cardmarket_orders_data.csv"
ARTICLES_FILENAME = "cardmarket_articles_sold.csv"
EXPENSES_FILENAME = "Expenses.ods"

# Local paths (support both root `data/` and placeholder subfolders)
ORDERS_DIR = DATA_DIR / "orders"
ARTICLES_DIR = DATA_DIR / "articles"
EXPENSES_DIR = DATA_DIR / "expenses"

ORDERS_LOCAL_PATH = DATA_DIR / ORDERS_FILENAME
ARTICLES_LOCAL_PATH = DATA_DIR / ARTICLES_FILENAME
EXPENSES_LOCAL_PATH = DATA_DIR / EXPENSES_FILENAME

# S3 paths
ORDERS_S3_URL = f"{PUBLIC_BASE_URL}/public/exports/{ORDERS_FILENAME}"
ARTICLES_S3_URL = f"{PUBLIC_BASE_URL}/public/exports/{ARTICLES_FILENAME}"
EXPENSES_S3_URL = f"{PUBLIC_BASE_URL}/raw/monthly_expenses/{EXPENSES_FILENAME}"


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Robustly convert a column to float."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    return (
        series.astype(str)
        .str.replace(r"[€$£\s]", "", regex=True)
        .str.replace(r"\.(?=\d{3})", "", regex=True)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def _resolve_source(local_path: Path, s3_url: str) -> str:
    if DATA_SOURCE == "s3":
        return s3_url
    return str(local_path)


def _find_local_file(
    label: str,
    preferred_path: Path,
    preferred_subdir: Path,
    known_filenames: list[str],
    keyword_patterns: list[str],
    allowed_extensions: tuple[str, ...] = (".csv",),
) -> Path | None:
    """Find a local file in common export locations and names."""
    candidates = [preferred_path, preferred_subdir / preferred_path.name]
    candidates.extend(DATA_DIR / name for name in known_filenames)
    candidates.extend(preferred_subdir / name for name in known_filenames)

    for candidate in candidates:
        if candidate.exists() and candidate.suffix.lower() in allowed_extensions:
            return candidate

    pattern_hits: list[Path] = []
    for keyword in keyword_patterns:
        pattern_hits.extend(DATA_DIR.glob(f"*{keyword}*"))
        pattern_hits.extend(preferred_subdir.glob(f"*{keyword}*"))

    filtered_hits = [
        p for p in pattern_hits if p.is_file() and p.suffix.lower() in allowed_extensions
    ]
    if filtered_hits:
        return max(filtered_hits, key=lambda p: p.stat().st_mtime)

    st.error(f"Missing local {label} file.")
    st.info(
        f"Place a matching file in `{DATA_DIR}` or `{preferred_subdir}` "
        f"(extensions: {', '.join(allowed_extensions)}), or switch DATA_SOURCE=s3."
    )
    return None


@st.cache_data(ttl=3600)
def load_orders_data():
    """Load orders data from configured source."""
    source = ORDERS_S3_URL
    local_path = ORDERS_LOCAL_PATH

    if DATA_SOURCE != "s3":
        resolved = _find_local_file(
            label="orders",
            preferred_path=ORDERS_LOCAL_PATH,
            preferred_subdir=ORDERS_DIR,
            known_filenames=[
                ORDERS_FILENAME,
                "PurchaseData.csv",
                "Orders.csv",
                "order_exports.csv",
            ],
            keyword_patterns=["purchase", "order", "orders", "buying"],
            allowed_extensions=(".csv",),
        )
        if resolved is None:
            return None
        local_path = resolved
        source = str(local_path)

    try:
        df = pd.read_csv(source)
        df["Date of Purchase"] = pd.to_datetime(df["Date of Purchase"])

        for col in ["Merchandise Value", "Shipment Costs", "Total Value", "Commission"]:
            if col in df.columns:
                df[col] = _clean_numeric(df[col])

        df["Net Value"] = df["Total Value"] - df["Commission"]
        df = df.sort_values("Date of Purchase").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error loading orders data: {e}")
        st.error(f"Tried to load from: {source}")
        return None


@st.cache_data(ttl=3600)
def load_articles_data():
    """Load sold articles data from configured source."""
    source = ARTICLES_S3_URL
    local_path = ARTICLES_LOCAL_PATH

    if DATA_SOURCE != "s3":
        resolved = _find_local_file(
            label="articles",
            preferred_path=ARTICLES_LOCAL_PATH,
            preferred_subdir=ARTICLES_DIR,
            known_filenames=[
                ARTICLES_FILENAME,
                "SalesData.csv",
                "SoldArticles.csv",
                "sold_articles.csv",
            ],
            keyword_patterns=["sold", "sales", "selling", "article"],
            allowed_extensions=(".csv",),
        )
        if resolved is None:
            return None
        local_path = resolved
        source = str(local_path)

    try:
        df = pd.read_csv(source)

        if "card_prices" in df.columns:
            df["card_prices"] = _clean_numeric(df["card_prices"])

        return df
    except Exception as e:
        st.error(f"Error loading articles data: {e}")
        st.error(f"Tried to load from: {source}")
        return None


@st.cache_data(ttl=3600)
def load_expenses_data():
    """Load monthly expenses data from configured source."""
    source = EXPENSES_S3_URL
    local_path = EXPENSES_LOCAL_PATH

    if DATA_SOURCE != "s3":
        resolved = _find_local_file(
            label="expenses",
            preferred_path=EXPENSES_LOCAL_PATH,
            preferred_subdir=EXPENSES_DIR,
            known_filenames=[
                "Expenses.ods",
                "Expenses.xlsx",
                "Expenses.xls",
                "Expenses.csv",
            ],
            keyword_patterns=["expense", "expenses", "cost"],
            allowed_extensions=(".ods", ".xlsx", ".xls", ".csv"),
        )
        if resolved is None:
            return None
        local_path = resolved
        source = str(local_path)

    try:
        suffix = local_path.suffix.lower() if DATA_SOURCE != "s3" else Path(source).suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(source)
        elif suffix == ".ods":
            df = pd.read_excel(source, engine="odf")
        else:
            df = pd.read_excel(source)
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], dayfirst=True)

        if "Item_Price" in df.columns:
            df["Item_Price"] = _clean_numeric(df["Item_Price"])

        df = df.sort_values("Order_Date").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error loading expenses data: {e}")
        st.error(f"Tried to load from: {source}")
        return None


def refresh_data():
    """Clear cache to force data refresh."""
    st.cache_data.clear()
    st.success("Data cache cleared! Reload the page to fetch fresh data.")
