"""
Data loader for CardMarket Dashboard.
Supports loading from local files (default) or public S3 URLs.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Data source configuration
# ----------------------------------------------------------------------------
# DATA_SOURCE options:
# - local (default): read files from DATA_DIR
# - s3           : read files from public S3 URLs
DATA_SOURCE = os.getenv("DATA_SOURCE", "local").strip().lower()
DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()

# S3 Configuration - Public bucket (no credentials required)
BUCKET_NAME = "mtg-streamlit-dashboard-s3-bucket"
PUBLIC_BASE_URL = f"https://{BUCKET_NAME}.s3.eu-central-1.amazonaws.com"

# Local file paths
LOCAL_ORDERS_CSV = DATA_DIR / "cardmarket_orders_data.csv"
LOCAL_ARTICLES_CSV = DATA_DIR / "cardmarket_articles_sold.csv"
LOCAL_EXPENSES_ODS = DATA_DIR / "Expenses.ods"

# S3 file URLs
ORDERS_CSV_URL = f"{PUBLIC_BASE_URL}/public/exports/cardmarket_orders_data.csv"
ARTICLES_CSV_URL = f"{PUBLIC_BASE_URL}/public/exports/cardmarket_articles_sold.csv"
EXPENSES_ODS_URL = f"{PUBLIC_BASE_URL}/raw/monthly_expenses/Expenses.ods"


def _clean_numeric(series: pd.Series) -> pd.Series:
    """
    Robustly convert a column to float.
    Handles: currency symbols (€), European decimals (1.234,56),
    regular decimals (1234.56), and already-numeric columns.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    return (
        series
        .astype(str)
        .str.replace(r"[€$£\s]", "", regex=True)
        .str.replace(r"\.(?=\d{3})", "", regex=True)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def _load_csv(local_path: Path, s3_url: str) -> pd.DataFrame:
    if DATA_SOURCE == "local":
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        return pd.read_csv(local_path)
    if DATA_SOURCE == "s3":
        return pd.read_csv(s3_url)
    raise ValueError("DATA_SOURCE must be 'local' or 's3'.")


def _load_ods(local_path: Path, s3_url: str) -> pd.DataFrame:
    if DATA_SOURCE == "local":
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        return pd.read_excel(local_path, engine="odf")
    if DATA_SOURCE == "s3":
        return pd.read_excel(s3_url, engine="odf")
    raise ValueError("DATA_SOURCE must be 'local' or 's3'.")


@st.cache_data(ttl=3600)
def load_orders_data():
    """Load orders data."""
    try:
        df = _load_csv(LOCAL_ORDERS_CSV, ORDERS_CSV_URL)

        df["Date of Purchase"] = pd.to_datetime(df["Date of Purchase"])

        for col in ["Merchandise Value", "Shipment Costs", "Total Value", "Commission"]:
            if col in df.columns:
                df[col] = _clean_numeric(df[col])

        df["Net Value"] = df["Total Value"] - df["Commission"]
        df = df.sort_values("Date of Purchase").reset_index(drop=True)
        return df

    except Exception as e:
        st.error(f"Error loading orders data: {str(e)}")
        st.error(f"DATA_SOURCE={DATA_SOURCE}")
        st.error(f"Local path: {LOCAL_ORDERS_CSV}")
        st.error(f"S3 URL: {ORDERS_CSV_URL}")
        return None


@st.cache_data(ttl=3600)
def load_articles_data():
    """Load sold articles data."""
    try:
        df = _load_csv(LOCAL_ARTICLES_CSV, ARTICLES_CSV_URL)

        if "card_prices" in df.columns:
            df["card_prices"] = _clean_numeric(df["card_prices"])

        return df

    except Exception as e:
        st.error(f"Error loading articles data: {str(e)}")
        st.error(f"DATA_SOURCE={DATA_SOURCE}")
        st.error(f"Local path: {LOCAL_ARTICLES_CSV}")
        st.error(f"S3 URL: {ARTICLES_CSV_URL}")
        return None


@st.cache_data(ttl=3600)
def load_expenses_data():
    """Load monthly expenses data (ODS format)."""
    try:
        df = _load_ods(LOCAL_EXPENSES_ODS, EXPENSES_ODS_URL)

        df["Order_Date"] = pd.to_datetime(df["Order_Date"], dayfirst=True)

        if "Item_Price" in df.columns:
            df["Item_Price"] = _clean_numeric(df["Item_Price"])

        df = df.sort_values("Order_Date").reset_index(drop=True)
        return df

    except Exception as e:
        st.error(f"Error loading expenses data: {str(e)}")
        st.error(f"DATA_SOURCE={DATA_SOURCE}")
        st.error(f"Local path: {LOCAL_EXPENSES_ODS}")
        st.error(f"S3 URL: {EXPENSES_ODS_URL}")
        return None


def refresh_data():
    """Clear cache to force data refresh."""
    st.cache_data.clear()
    st.success("Data cache cleared! Reload the page to fetch fresh data.")
