import streamlit as st

st.set_page_config(page_title="ArcadiaReserve BI Suite", page_icon="📊", layout="wide")

with st.sidebar:
    st.title("ArcadiaReserve BI")
    st.caption("Herbouwde dashboard-suite")

st.title("📊 ArcadiaReserve BI Suite")
st.markdown(
    """
Welkom in de nieuwe versie van het dashboard.

Gebruik de navigatie links om naar:
- **Orders Overview** voor omzet en orders
- **Analytics** voor trends en uitsplitsingen
- **Costs** voor expense-inzicht
- **Sold Articles** voor kaartverkoop
- **Settings** voor datadiagnostics
"""
)

st.info("Plaats je exports in `data/orders`, `data/articles` en `data/expenses`.")
