"""
Data loader for CardMarket Dashboard
Reads CSV files from public S3 bucket
"""
import pandas as pd
import streamlit as st

# S3 Configuration - Public bucket, geen credentials nodig!
BUCKET_NAME = "mtg-streamlit-dashboard-s3-bucket"
PUBLIC_BASE_URL = f"https://{BUCKET_NAME}.s3.eu-central-1.amazonaws.com"

# File paths
ORDERS_CSV_URL   = f"{PUBLIC_BASE_URL}/public/exports/cardmarket_orders_data.csv"
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
        .str.replace(r'[€$£\s]', '', regex=True)   # strip currency symbols
        .str.replace(r'\.(?=\d{3})', '', regex=True) # remove thousands separator dots (1.234 → 1234)
        .str.replace(',', '.', regex=False)           # European decimal comma → dot
        .pipe(pd.to_numeric, errors='coerce')         # cast; unparseable values → NaN
    )


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_orders_data():
    """
    Load orders data from S3
    Returns: pandas DataFrame
    """
    try:
        df = pd.read_csv(ORDERS_CSV_URL)

        # Convert Date of Purchase to datetime
        df['Date of Purchase'] = pd.to_datetime(df['Date of Purchase'])

        # Robustly convert all monetary columns
        for col in ['Merchandise Value', 'Shipment Costs', 'Total Value', 'Commission']:
            if col in df.columns:
                df[col] = _clean_numeric(df[col])

        # Calculate net value (now guaranteed to be float - float)
        df['Net Value'] = df['Total Value'] - df['Commission']

        # Sort by date
        df = df.sort_values('Date of Purchase').reset_index(drop=True)

        return df

    except Exception as e:
        st.error(f"Error loading orders data: {str(e)}")
        st.error(f"Tried to load from: {ORDERS_CSV_URL}")
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_articles_data():
    """
    Load articles data from S3
    Returns: pandas DataFrame
    """
    try:
        df = pd.read_csv(ARTICLES_CSV_URL)

        # Robustly convert card prices
        if 'card_prices' in df.columns:
            df['card_prices'] = _clean_numeric(df['card_prices'])

        return df

    except Exception as e:
        st.error(f"Error loading articles data: {str(e)}")
        st.error(f"Tried to load from: {ARTICLES_CSV_URL}")
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_expenses_data():
    """
    Load monthly expenses data from S3 (ODS format)
    Returns: pandas DataFrame
    """
    try:
        df = pd.read_excel(EXPENSES_ODS_URL, engine='odf')

        # Convert Order_Date to datetime
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], dayfirst=True)

        # Robustly convert item prices if needed
        if 'Item_Price' in df.columns:
            df['Item_Price'] = _clean_numeric(df['Item_Price'])

        # Sort by date
        df = df.sort_values('Order_Date').reset_index(drop=True)

        return df

    except Exception as e:
        st.error(f"Error loading expenses data: {str(e)}")
        st.error(f"Tried to load from: {EXPENSES_ODS_URL}")
        return None


def refresh_data():
    """
    Clear cache to force data refresh
    """
    st.cache_data.clear()
    st.success("Data cache cleared! Reload the page to fetch fresh data.")