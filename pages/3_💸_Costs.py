import plotly.express as px
import streamlit as st

from data_loader import load_expenses_data, render_data_reload_button

st.set_page_config(page_title="Costs", page_icon="💸", layout="wide")
render_data_reload_button(key="reload_costs")

st.title("💸 Costs")

df = load_expenses_data()
if df.empty:
    st.warning("Geen bruikbare expense-data gevonden.")
    st.stop()

total = df["item_price"].sum()
avg = df["item_price"].mean()
count = len(df)

k1, k2, k3 = st.columns(3)
k1.metric("Totale kosten", f"€{total:,.2f}")
k2.metric("Gemiddelde kosten", f"€{avg:,.2f}")
k3.metric("Transacties", f"{count:,}")

monthly = df.groupby("month", as_index=False).agg(spend=("item_price", "sum"))
by_cat = df.groupby("cost_category", as_index=False).agg(spend=("item_price", "sum")).sort_values("spend", ascending=False)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(px.line(monthly, x="month", y="spend", markers=True, title="Kosten per maand"), use_container_width=True)
with c2:
    st.plotly_chart(px.bar(by_cat, x="cost_category", y="spend", title="Kosten per categorie"), use_container_width=True)
