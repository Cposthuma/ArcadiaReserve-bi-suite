import os

import streamlit as st
from data_loader import refresh_data

st.set_page_config(
    page_title="Settings",
    layout="wide"
)

st.title("⚙️ Settings")

st.markdown("### Data Management")

source = os.getenv("DATA_SOURCE", "local")
source_label = "Local files" if source.lower() != "s3" else "AWS S3"

st.write(
    f"Current data source: **{source_label}**. "
    "Data is cached for 1 hour to improve performance."
)

if st.button("🔄 Refresh Data"):
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
**Data Source:** {source_label}  
**Update Frequency:** Manual (monthly)  
**Privacy:** Sensitive data (usernames, order IDs) removed before display
"""
)
