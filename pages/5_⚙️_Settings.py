import streamlit as st

from data_loader import DATA_DIR, DATA_SOURCE, refresh_data

st.set_page_config(
    page_title="Settings",
    layout="wide",
)

st.title("⚙️ Settings")

st.markdown("### Data Management")

if DATA_SOURCE == "local":
    st.write(f"The dashboard is reading local files from: `{DATA_DIR}`")
else:
    st.write("The dashboard is reading data from the public AWS S3 bucket.")

st.write("Data is cached for 1 hour to improve performance.")

if st.button("🔄 Refresh Data"):
    refresh_data()

st.markdown("---")

st.markdown("### Planned Settings")
st.markdown(
    """
- Currency preferences
- Date format
- Export options
- Display preferences
- Notification settings
"""
)

st.markdown("---")

st.markdown("### About This Dashboard")
st.info(
    f"""
**Data Source Mode:** `{DATA_SOURCE}`  
**Local Data Directory:** `{DATA_DIR}`  
**Update Frequency:** Manual (monthly)  
**Privacy:** Sensitive data (usernames, order IDs) removed before display
"""
)
