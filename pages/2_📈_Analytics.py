import plotly.express as px
import streamlit as st

from data_loader import load_articles_data, load_orders_data, render_data_reload_button

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")
render_data_reload_button(key="reload_analytics")

st.title("📈 Analytics")

orders = load_orders_data()
articles = load_articles_data()

if orders.empty and articles.empty:
    st.warning("Geen data beschikbaar voor analytics.")
    st.stop()

if not orders.empty:
    st.subheader("Order trends")
    monthly_orders = orders.groupby("month", as_index=False).agg(
        net_value=("net_value", "sum"),
        gross_value=("gross_value", "sum"),
        order_count=("date", "count"),
    )
    fig_orders = px.area(monthly_orders, x="month", y="net_value", title="Netto omzettrend")
    st.plotly_chart(fig_orders, use_container_width=True)

if not articles.empty:
    st.subheader("Artikelanalyse")
    set_perf = articles.groupby("set_name", as_index=False).agg(
        sold=("name", "count"),
        revenue=("price", "sum"),
    ).sort_values("revenue", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.bar(set_perf.head(15), x="set_name", y="revenue", title="Top 15 sets op omzet"), use_container_width=True)
    with col2:
        rarity = articles.groupby("rarity", as_index=False).agg(sold=("name", "count"))
        st.plotly_chart(px.pie(rarity, names="rarity", values="sold", title="Rarity verdeling"), use_container_width=True)
