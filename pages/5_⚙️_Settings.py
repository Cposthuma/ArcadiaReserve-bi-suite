import streamlit as st
from data_loader import get_data_diagnostics, refresh_data, render_data_reload_button

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


diagnostics = get_data_diagnostics()

st.markdown("### Local Data Diagnostics")
st.code(
    f"DATA_DIR env: {diagnostics['data_dir_env']}\n"
    f"Resolved data dir: {diagnostics['data_dir']}\n"
    f"Data dir exists: {diagnostics['data_dir_exists']}\n"
    f"Orders dir: {diagnostics['orders_dir']}\n"
    f"Articles dir: {diagnostics['articles_dir']}\n"
    f"Expenses dir: {diagnostics['expenses_dir']}"
)

if diagnostics["files"]:
    st.write("Detected local files:")
    st.code("\n".join(diagnostics["files"]))
else:
    st.warning("No local data files gevonden in de data folder.")


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
