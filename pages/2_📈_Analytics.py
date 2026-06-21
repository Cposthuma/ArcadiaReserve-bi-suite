"""Clean analytics page with TCG-scoped sales patterns."""
import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_articles_data, load_orders_data, render_data_reload_button

st.set_page_config(page_title="Analytics", page_icon="chart", layout="wide")
render_data_reload_button(key="reload_analytics")

ACCENT = "#5a8c1a"
ACCENT_DARK = "#2d4a0c"
MUTED = "#6b7c45"
GRID = "#d4ddb8"
PALETTE = ["#5a8c1a", "#4f9fd4", "#e07840", "#9b6cc4", "#d44f7c", "#3aab98"]
EURO = "€"


def money(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{EURO}{value:,.2f}"


def style_page() -> None:
    st.markdown(
        f"""
        <style>
          .block-container {{ padding-top: 1.4rem; }}
          .metric-card {{
            border: 1px solid {GRID};
            border-radius: 8px;
            padding: 15px 17px;
            background: #fbfcf7;
          }}
          .metric-card .label {{ color: {MUTED}; font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }}
          .metric-card .value {{ color: {ACCENT_DARK}; font-size: 1.55rem; font-weight: 650; margin-top: 4px; }}
          .metric-card .sub {{ color: {MUTED}; font-size: .82rem; margin-top: 2px; }}
          h1, h2, h3 {{ color: {ACCENT_DARK}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(
        f"""
        <div class="metric-card">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tcg_options(articles: pd.DataFrame) -> list[str]:
    if "tcg" not in articles.columns:
        return ["Alle TCGs"]
    values = sorted(v for v in articles["tcg"].dropna().astype(str).unique() if v and v != "Unknown")
    if "Unknown" in set(articles["tcg"].dropna().astype(str)):
        values.append("Unknown")
    return ["Alle TCGs"] + values


def filter_articles_by_tcg(articles: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    selected = st.selectbox("TCG", tcg_options(articles), key="analytics_tcg_filter")
    if selected == "Alle TCGs" or "tcg" not in articles.columns:
        return articles.copy(), selected
    return articles[articles["tcg"] == selected].copy(), selected


def build_sales_facts(articles: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    sales = articles.copy()
    sales["price"] = pd.to_numeric(sales["price"], errors="coerce")
    sales = sales.dropna(subset=["price"]).copy()

    if "sold_date" in sales.columns:
        sales["date"] = pd.to_datetime(sales["sold_date"], errors="coerce")
    else:
        sales["date"] = pd.NaT

    order_cols = [c for c in ["order_id", "country", "date", "order_total"] if c in orders.columns]
    if "order_id" in sales.columns and "order_id" in order_cols:
        order_dim = orders[order_cols].copy()
        order_dim["order_id"] = order_dim["order_id"].astype(str)
        order_dim = order_dim.drop_duplicates(subset=["order_id"])
        sales["order_id"] = sales["order_id"].astype(str)
        sales = sales.merge(order_dim, on="order_id", how="left", suffixes=("", "_order"))
        if "date_order" in sales.columns:
            sales["date"] = sales["date"].combine_first(pd.to_datetime(sales["date_order"], errors="coerce"))
            sales = sales.drop(columns=["date_order"])
    if "country" not in sales.columns:
        sales["country"] = "Unknown"
    sales["country"] = sales["country"].fillna("Unknown").astype(str)
    sales = sales.dropna(subset=["date"]).copy()
    sales["weekday"] = sales["date"].dt.day_name()
    sales["month"] = sales["date"].dt.to_period("M").dt.to_timestamp()
    return sales


style_page()
orders = load_orders_data()
articles = load_articles_data()

if orders is None or orders.empty:
    st.error("Geen orderdata gevonden.")
    st.stop()
if articles is None or articles.empty:
    st.error("Geen artikeldata gevonden.")
    st.stop()

st.title("Analytics")
st.caption("Alle grafieken gebruiken artikelregels als bron, zodat een TCG-filter geen omzet uit andere TCG's meeneemt.")

orders = orders.copy()
articles = articles.copy()
filtered_articles, selected_tcg = filter_articles_by_tcg(articles)
sales = build_sales_facts(filtered_articles, orders)

if sales.empty:
    st.warning("Geen verkoopdata voor deze TCG-selectie.")
    st.stop()

order_revenue = (
    sales.groupby("order_id", as_index=False)
    .agg(card_revenue=("price", "sum"), cards=("price", "count"))
    .query("order_id != ''")
)

top_country = sales["country"].value_counts().idxmax()
median_order = order_revenue["card_revenue"].median() if not order_revenue.empty else pd.NA
low_value_share = (order_revenue["card_revenue"].lt(5).mean() * 100) if not order_revenue.empty else 0
best_weekday = sales["weekday"].value_counts().idxmax()

c1, c2, c3, c4 = st.columns(4)
metric_card(c1, "Top land", str(top_country), f"{sales['country'].value_counts().max()} singles")
metric_card(c2, "Median TCG-order", money(median_order), "Kaartomzet binnen selectie")
metric_card(c3, f"TCG-orders < {EURO}5", f"{low_value_share:.1f}%" if not order_revenue.empty else "-", "Op kaartomzet selectie")
metric_card(c4, "Beste weekday", best_weekday, "Meeste verkochte singles")

if selected_tcg != "Alle TCGs":
    st.caption(f"Actieve scope: {selected_tcg}. Order-gerelateerde grafieken tellen alleen artikelomzet van deze TCG; orderdata wordt alleen gebruikt voor land/datum-koppeling.")

st.divider()

if "tcg" in articles.columns and selected_tcg == "Alle TCGs":
    tcg_summary = (
        articles.assign(price=pd.to_numeric(articles["price"], errors="coerce"))
        .dropna(subset=["price"])
        .groupby("tcg", as_index=False)
        .agg(singles=("price", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
        .sort_values("revenue", ascending=False)
    )
    st.subheader("TCG overzicht")
    st.dataframe(
        tcg_summary.rename(columns={"tcg": "TCG", "singles": "Singles", "revenue": "Omzet", "avg_price": "Gem. prijs"}).style.format(
            {"Omzet": f"{EURO}{{:.2f}}", "Gem. prijs": f"{EURO}{{:.2f}}"}
        ),
        width="stretch",
        hide_index=True,
    )

country = (
    sales.groupby("country", as_index=False)
    .agg(singles=("price", "count"), orders=("order_id", "nunique"), revenue=("price", "sum"), avg_card=("price", "mean"))
    .sort_values("revenue", ascending=False)
    .head(10)
)

left, right = st.columns([3, 2])
with left:
    fig = px.bar(
        country,
        x="revenue",
        y="country",
        orientation="h",
        color="revenue",
        color_continuous_scale=[[0, "#c8dca0"], [1, ACCENT]],
        text="revenue",
        labels={"country": "", "revenue": "Omzet"},
    )
    fig.update_traces(texttemplate=f"{EURO}%{{text:,.0f}}", hovertemplate=f"%{{y}}<br>Omzet: {EURO}%{{x:,.2f}}<extra></extra>")
    fig.update_layout(
        title="Top landen op TCG-kaartomzet",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(tickprefix=EURO, gridcolor=GRID),
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")

with right:
    st.dataframe(
        country.rename(columns={"country": "Land", "singles": "Singles", "orders": "Orders", "revenue": "Omzet", "avg_card": "Gem. kaart"}).style.format(
            {"Omzet": f"{EURO}{{:.2f}}", "Gem. kaart": f"{EURO}{{:.2f}}"}
        ),
        width="stretch",
        height=420,
        hide_index=True,
    )

bins = [0, 1, 2, 5, 10, 20, 50, 100, 200, float("inf")]
labels = [f"<{EURO}1", f"{EURO}1-2", f"{EURO}2-5", f"{EURO}5-10", f"{EURO}10-20", f"{EURO}20-50", f"{EURO}50-100", f"{EURO}100-200", f"{EURO}200+"]
order_revenue["value_bucket"] = pd.cut(order_revenue["card_revenue"], bins=bins, labels=labels, include_lowest=True)
buckets = order_revenue["value_bucket"].value_counts().reindex(labels).fillna(0).reset_index()
buckets.columns = ["Bucket", "Orders"]

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekdays = sales["weekday"].value_counts().reindex(weekday_order).fillna(0).reset_index()
weekdays.columns = ["Weekday", "Singles"]

left, right = st.columns(2)
with left:
    fig = px.bar(buckets, x="Bucket", y="Orders", color="Orders", color_continuous_scale=[[0, "#c8dca0"], [1, ACCENT]])
    fig.update_layout(
        title="TCG-orders per waardebucket",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        yaxis=dict(gridcolor=GRID),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")

with right:
    fig = px.bar(weekdays, x="Weekday", y="Singles", color="Singles", color_continuous_scale=[[0, "#c8dca0"], [1, ACCENT]])
    fig.update_layout(
        title="Singles per weekdag",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(tickangle=-25),
        yaxis=dict(gridcolor=GRID),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")

monthly = (
    sales.groupby("month", as_index=False)
    .agg(singles=("price", "count"), revenue=("price", "sum"), orders=("order_id", "nunique"))
    .sort_values("month")
)
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

fig = px.bar(
    monthly,
    x="month_label",
    y="revenue",
    color="singles",
    color_continuous_scale=[[0, "#c8dca0"], [1, ACCENT]],
    labels={"month_label": "", "revenue": "Omzet", "singles": "Singles"},
)
fig.update_layout(
    title="TCG-kaartomzet per maand",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=0, r=0, t=45, b=0),
    yaxis=dict(tickprefix=EURO, gridcolor=GRID),
    coloraxis_colorbar=dict(title="Singles"),
)
st.plotly_chart(fig, width="stretch")

set_group = ["tcg", "set_name"] if "tcg" in sales.columns else ["set_name"]
set_stats = (
    sales.groupby(set_group, as_index=False)
    .agg(cards=("price", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
    .sort_values("revenue", ascending=False)
    .head(15)
)

st.subheader("Top sets")
fig = px.bar(
    set_stats,
    x="revenue",
    y="set_name",
    orientation="h",
    color="tcg" if "tcg" in set_stats.columns and selected_tcg == "Alle TCGs" else "avg_price",
    color_continuous_scale=[[0, "#c8dca0"], [1, ACCENT]],
    color_discrete_sequence=PALETTE,
    hover_data={"cards": True, "avg_price": ":.2f"},
    labels={"set_name": "", "revenue": "Omzet", "avg_price": "Gem. prijs", "tcg": "TCG"},
)
fig.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(tickprefix=EURO, gridcolor=GRID),
    yaxis=dict(autorange="reversed"),
    coloraxis_colorbar=dict(title=f"Gem. {EURO}"),
)
st.plotly_chart(fig, width="stretch")

card_group = ["tcg", "name", "set_name"] if "tcg" in sales.columns else ["name", "set_name"]
card_stats = (
    sales.groupby(card_group, as_index=False)
    .agg(aantal=("price", "count"), omzet=("price", "sum"), gem_prijs=("price", "mean"))
    .sort_values("omzet", ascending=False)
    .head(25)
)
columns = {"tcg": "TCG", "name": "Kaart", "set_name": "Set", "aantal": "Aantal", "omzet": "Omzet", "gem_prijs": "Gem. prijs"}
st.subheader("Top kaarten")
st.dataframe(
    card_stats.rename(columns=columns).style.format({"Omzet": f"{EURO}{{:.2f}}", "Gem. prijs": f"{EURO}{{:.2f}}"}),
    width="stretch",
    height=420,
    hide_index=True,
)

with st.expander("Controle: ruwe analytics scope"):
    display_cols = [c for c in ["date", "order_id", "tcg", "country", "name", "set_name", "price"] if c in sales.columns]
    st.dataframe(sales[display_cols].sort_values("date", ascending=False), width="stretch")
