import plotly.express as px
import streamlit as st

from data_loader import load_orders_data, render_data_reload_button

st.set_page_config(page_title="Orders Overview", page_icon="📊", layout="wide")
render_data_reload_button(key="reload_orders")

st.title("📊 Orders Overview")

df = load_orders_data()
if df.empty:
    st.warning("Geen bruikbare orders-data gevonden.")
    st.stop()

total_orders = len(df)
total_gross = df["gross_value"].sum()
total_net = df["net_value"].sum()
commission = df["commission"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Orders", f"{total_orders:,}")
k2.metric("Bruto omzet", f"€{total_gross:,.2f}")
k3.metric("Netto omzet", f"€{total_net:,.2f}")
k4.metric("Commissie", f"€{commission:,.2f}")

monthly = df.groupby("month", as_index=False).agg(net_value=("net_value", "sum"), orders=("date", "count"))

c1, c2 = st.columns([2, 1])
with c1:
    fig = px.line(monthly, x="month", y="net_value", markers=True, title="Netto omzet per maand")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig2 = px.bar(monthly, x="month", y="orders", title="Aantal orders per maand")
    st.plotly_chart(fig2, use_container_width=True)

country = df.groupby("country", as_index=False).agg(orders=("date", "count"), net_value=("net_value", "sum")).sort_values("net_value", ascending=False)
st.subheader("Landenoverzicht")
st.dataframe(country, use_container_width=True)
