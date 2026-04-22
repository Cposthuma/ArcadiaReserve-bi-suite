import streamlit as st

# Set page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="CardMarket BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar branding
with st.sidebar:
    st.title("📊 CardMarket BI")
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Dashboard for tracking CardMarket sales and performance.")

# Home page content
st.title("🏠 Welcome to CardMarket BI Dashboard")

st.markdown("""
### Getting Started
Use the sidebar navigation to explore different sections:

- **📊 Orders Overview** - View all your orders and track cumulative revenue
- **📈 Analytics** - Deep dive into your sales data (coming soon)
- **⚙️ Settings** - Configure dashboard preferences (coming soon)

---

### Quick Stats
Navigate to the Orders Overview page to see your complete sales dashboard!
""")