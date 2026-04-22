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

# Local paths
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


def _validate_local_file(path: Path, label: str) -> bool:
    if path.exists():
        return True
    st.error(f"Missing local {label} file: {path}")
    st.info("Add your exports to the data/ folder or switch DATA_SOURCE=s3.")
    return False


@st.cache_data(ttl=3600)
def load_orders_data():
    """Load orders data from configured source."""
    source = _resolve_source(ORDERS_LOCAL_PATH, ORDERS_S3_URL)

    if DATA_SOURCE != "s3" and not _validate_local_file(ORDERS_LOCAL_PATH, "orders"):
        return None

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
    source = _resolve_source(ARTICLES_LOCAL_PATH, ARTICLES_S3_URL)

    if DATA_SOURCE != "s3" and not _validate_local_file(ARTICLES_LOCAL_PATH, "articles"):
        return None

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
    source = _resolve_source(EXPENSES_LOCAL_PATH, EXPENSES_S3_URL)

    if DATA_SOURCE != "s3" and not _validate_local_file(EXPENSES_LOCAL_PATH, "expenses"):
        return None

    try:
        df = pd.read_excel(source, engine="odf")
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
