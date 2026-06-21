import streamlit as st

from data_loader import get_data_diagnostics, refresh_data, render_data_reload_button

st.set_page_config(page_title="Settings", page_icon="Settings", layout="wide")
render_data_reload_button(key="reload_settings")

st.title("Settings")

if st.button("Cache legen en herladen", width="stretch"):
    refresh_data()
    st.success("Cache geleegd.")

st.subheader("Data diagnostics")
d = get_data_diagnostics()

selected = d.get("selected_files", {})
rows = d.get("dataset_rows", {})

st.code(
    f"DATA_DIR env: {d['data_dir_env']}\n"
    f"Resolved dir: {d['data_dir']}\n"
    f"Exists: {d['exists']}\n"
    f"Selected order files: {', '.join(selected.get('orders', [])) or '-'}\n"
    f"Selected article files: {', '.join(selected.get('articles', [])) or '-'}\n"
    f"Selected expense files: {', '.join(selected.get('expenses', [])) or '-'}\n"
    f"Orders rows: {rows.get('orders')}\n"
    f"Article rows: {rows.get('articles')}\n"
    f"Expense rows: {rows.get('expenses')}"
)

if d["files"]:
    st.write("Gevonden bestanden:")
    st.code("\n".join(d["files"]))
else:
    st.info("Geen data-bestanden gevonden.")


