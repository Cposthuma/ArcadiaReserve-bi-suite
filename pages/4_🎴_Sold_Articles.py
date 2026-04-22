import plotly.express as px
import streamlit as st

from data_loader import load_articles_data, render_data_reload_button

st.set_page_config(page_title="Sold Articles", page_icon="🎴", layout="wide")
render_data_reload_button(key="reload_articles")

st.title("🎴 Sold Articles")

df = load_articles_data()
if df.empty:
    st.warning("Geen bruikbare sold articles data gevonden.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Verkochte kaarten", f"{len(df):,}")
k2.metric("Totale omzet", f"€{df['price'].sum():,.2f}")
k3.metric("Gemiddelde prijs", f"€{df['price'].mean():,.2f}")

set_perf = df.groupby("set_name", as_index=False).agg(cards=("name", "count"), revenue=("price", "sum")).sort_values("revenue", ascending=False)

left, right = st.columns(2)
with left:
    st.plotly_chart(px.treemap(set_perf, path=["set_name"], values="revenue", title="Omzet per set"), use_container_width=True)
with right:
    rarity = df.groupby("rarity", as_index=False).agg(cards=("name", "count"))
    st.plotly_chart(px.bar(rarity, x="rarity", y="cards", title="Aantal per rarity"), use_container_width=True)

st.subheader("Ruwe data")
st.dataframe(df, use_container_width=True)
