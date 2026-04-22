import streamlit as st
from data_loader import refresh_data, render_data_reload_button

st.set_page_config(
    page_title="Settings",
    layout="wide"
)
render_data_reload_button(key="reload_settings_sidebar")

st.title("⚙️ Settings")

st.markdown("### Data Management")

st.write(
    "Current data source: **Local files**. "
    "Data is cached for 1 hour to improve performance."
)

if st.button("🔄 Refresh Data", key="refresh_data_settings_main"):
    refresh_data()

st.markdown("---")

st.markdown("### Planned Settings")
st.markdown("""
- Currency preferences
- Date format
- Export options
- Display preferences
- Notification settings
""")

st.markdown("---")

st.markdown("### About This Dashboard")
st.info(
    f"""
**Data Source:** Local files  
**Update Frequency:** Manual (monthly)  
**Privacy:** Sensitive data (usernames, order IDs) removed before display
"""
)
