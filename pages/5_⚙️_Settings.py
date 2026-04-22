import streamlit as st

from data_loader import get_data_diagnostics, refresh_data, render_data_reload_button

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
render_data_reload_button(key="reload_settings")

st.title("⚙️ Settings")

if st.button("Cache legen en herladen", use_container_width=True):
    refresh_data()
    st.success("Cache geleegd.")

st.subheader("Data diagnostics")
d = get_data_diagnostics()

st.code(
    f"DATA_DIR env: {d['data_dir_env']}\n"
    f"Resolved dir: {d['data_dir']}\n"
    f"Exists: {d['exists']}"
)

if d["files"]:
    st.write("Gevonden bestanden:")
    st.code("\n".join(d["files"]))
else:
    st.info("Geen data-bestanden gevonden.")
