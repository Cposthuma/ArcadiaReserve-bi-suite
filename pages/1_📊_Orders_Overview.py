"""Clean order overview focused on values that exist in Cardmarket exports."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_articles_data, load_orders_data, render_data_reload_button

st.set_page_config(page_title="Orders Overview", page_icon="EUR", layout="wide")
render_data_reload_button(key="reload_orders_overview")

ACCENT = "#1a9090"
ACCENT_DARK = "#0d5c6e"
MUTED = "#5c7373"
GRID = "#d7e8e8"
WARNING = "#f0a64f"
DANGER = "#d95f6a"
BLUE = "#6aaed6"


def money(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"€{value:,.2f}"


def available_sum(df: pd.DataFrame, column: str) -> float | None:
    if column not in df or df[column].dropna().empty:
        return None
    return float(df[column].sum(skipna=True))


def tcg_options(df: pd.DataFrame) -> list[str]:
    if df is None or df.empty or "tcg" not in df.columns:
        return ["Alle TCGs"]
    values = sorted(v for v in df["tcg"].dropna().astype(str).unique() if v and v != "Unknown")
    if "Unknown" in set(df["tcg"].dropna().astype(str)):
        values.append("Unknown")
    return ["Alle TCGs"] + values


def style_page() -> None:
    st.markdown(
        f"""
        <style>
          .block-container {{ padding-top: 1.4rem; }}
          .metric-card {{
            border: 1px solid {GRID};
            border-radius: 8px;
            padding: 16px 18px;
            background: #f8fbfb;
          }}
          .metric-card .label {{ color: {MUTED}; font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }}
          .metric-card .value {{ color: {ACCENT_DARK}; font-size: 1.65rem; font-weight: 650; margin-top: 4px; }}
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


style_page()
orders = load_orders_data()
articles = load_articles_data()

if orders is None or orders.empty:
    st.error("Geen orderdata gevonden. Zet je Cardmarket Sold Shipments CSV's in data/orders.")
    st.stop()

orders = orders.copy()
articles = articles.copy() if articles is not None and not articles.empty else pd.DataFrame()
if not articles.empty and "tcg" in articles.columns:
    selected_tcg = st.selectbox("TCG", tcg_options(articles), key="orders_tcg_filter")
    if selected_tcg != "Alle TCGs":
        articles = articles[articles["tcg"] == selected_tcg].copy()
        if "order_id" in articles.columns and "order_id" in orders.columns:
            order_ids = set(articles["order_id"].dropna().astype(str))
            orders = orders[orders["order_id"].astype(str).isin(order_ids)].copy()
else:
    selected_tcg = "Alle TCGs"
orders["date"] = pd.to_datetime(orders["date"])
orders["month"] = orders["date"].dt.to_period("M").dt.to_timestamp()
orders["card_value"] = pd.to_numeric(orders["gross_value"], errors="coerce")
orders["shipping"] = pd.to_numeric(orders["shipping_cost"], errors="coerce") if "shipping_cost" in orders else pd.NA
orders["fees"] = pd.to_numeric(orders["commission"], errors="coerce") if "commission" in orders else pd.NA
orders["order_total_export"] = pd.to_numeric(orders["order_total"], errors="coerce") if "order_total" in orders else pd.NA
orders["value_after_fees"] = orders["card_value"] - orders["fees"] if orders["fees"].notna().any() else pd.NA

total_orders = len(orders)
article_revenue = available_sum(articles, "price") if not articles.empty else None
card_revenue = article_revenue if selected_tcg != "Alle TCGs" and article_revenue is not None else available_sum(orders, "card_value")
shipping_revenue = available_sum(orders, "shipping")
fees = available_sum(orders, "fees")
order_total = available_sum(orders, "order_total_export")
value_after_fees = available_sum(orders, "value_after_fees")
article_count = len(articles) if articles is not None and not articles.empty else None

st.title("Orders Overview")
st.caption("Alleen waarden uit de lokale Cardmarket exports. Geen demo- of placeholderdata.")

if not articles.empty and "tcg" in articles.columns:
    tcg_summary = (
        articles.groupby("tcg", as_index=False)
        .agg(singles=("price", "count"), card_revenue=("price", "sum"), orders=("order_id", "nunique"))
        .sort_values("card_revenue", ascending=False)
    )
    st.subheader("Sales per TCG")
    st.dataframe(
        tcg_summary.rename(columns={"tcg": "TCG", "singles": "Singles", "card_revenue": "Kaartomzet", "orders": "Orders"}).style.format(
            {"Kaartomzet": "\u20ac{:.2f}"}
        ),
        width="stretch",
        hide_index=True,
    )

k1, k2, k3, k4, k5 = st.columns(5)
metric_card(k1, "Orders", f"{total_orders:,}", f"{orders['date'].min():%d %b} - {orders['date'].max():%d %b %Y}")
metric_card(k2, "Order total", money(order_total), "Total Value uit export")
metric_card(k3, "Kaartwaarde", money(card_revenue), f"{article_count:,} singles" if article_count is not None else "")
metric_card(k4, "Shipping charged", money(shipping_revenue), "Shipment Costs uit export")
metric_card(k5, "Cardmarket fees", money(fees), "Commission uit export")

if value_after_fees is not None:
    st.caption(f"Kaartwaarde na Cardmarket fees: {money(value_after_fees)}. Dit is berekend uit aanwezige exportkolommen")
if selected_tcg != "Alle TCGs":
    st.caption("Bij een TCG-filter komt kaartwaarde uit artikelregels; shipping en fees blijven orderwaarden voor orders met die TCG.")

st.divider()

monthly = (
    orders.groupby("month", as_index=False)
    .agg(
        orders=("order_id", "count"),
        order_total=("order_total_export", "sum"),
        cards=("card_value", "sum"),
        shipping=("shipping", "sum"),
        fees=("fees", "sum"),
        value_after_fees=("value_after_fees", "sum"),
    )
)
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

left, right = st.columns([3, 2])

with left:
    monthly_parts = monthly.melt(
        id_vars=["month_label"],
        value_vars=["cards", "shipping"],
        var_name="Component",
        value_name="Value",
    ).dropna(subset=["Value"])
    monthly_parts["Component"] = monthly_parts["Component"].map({"cards": "Kaartwaarde", "shipping": "Shipping charged"})
    fig = px.bar(
        monthly_parts,
        x="month_label",
        y="Value",
        color="Component",
        color_discrete_map={"Kaartwaarde": ACCENT, "Shipping charged": BLUE},
        labels={"month_label": "", "Value": "Waarde"},
    )
    fig.add_scatter(
        x=monthly["month_label"],
        y=monthly["fees"],
        name="Cardmarket fees",
        mode="lines+markers",
        line=dict(color=DANGER, width=2),
        hovertemplate="%{x}<br>Fees: €%{y:,.2f}<extra></extra>",
    )
    fig.update_layout(
        title="Maandelijkse exportwaarden",
        barmode="stack",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        yaxis=dict(tickprefix="€", gridcolor=GRID),
        legend=dict(orientation="h", y=-0.18),
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")

with right:
    components = []
    if card_revenue is not None:
        components.append({"Component": "Kaartwaarde", "Value": card_revenue})
    if shipping_revenue is not None:
        components.append({"Component": "Shipping charged", "Value": shipping_revenue})
    if fees is not None:
        components.append({"Component": "Cardmarket fees", "Value": fees})

    fig = px.bar(
        pd.DataFrame(components),
        x="Component",
        y="Value",
        color="Component",
        text="Value",
        color_discrete_map={"Kaartwaarde": ACCENT, "Shipping charged": BLUE, "Cardmarket fees": DANGER},
    )
    fig.update_traces(texttemplate="€%{text:,.0f}", hovertemplate="%{x}: €%{y:,.2f}<extra></extra>")
    fig.update_layout(
        title="Beschikbare totalen",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        yaxis=dict(tickprefix="€", gridcolor=GRID),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

st.subheader("Orderregels")

recent = orders.sort_values("date", ascending=False).head(20).copy()
recent["order_label"] = recent["order_id"].astype(str).where(
    recent["order_id"].astype(str).str.len() > 0,
    recent["date"].dt.strftime("%d %b"),
)
parts = recent.sort_values("date").melt(
    id_vars=["order_label"],
    value_vars=["card_value", "shipping", "fees"],
    var_name="Component",
    value_name="Value",
).dropna(subset=["Value"])
parts["Component"] = parts["Component"].map({"card_value": "Kaartwaarde", "shipping": "Shipping charged", "fees": "Cardmarket fees"})

chart_col, table_col = st.columns([3, 2])

with chart_col:
    fig = px.bar(
        parts,
        x="order_label",
        y="Value",
        color="Component",
        color_discrete_map={"Kaartwaarde": ACCENT, "Shipping charged": BLUE, "Cardmarket fees": DANGER},
    )
    fig.update_layout(
        title="Laatste 20 orders met beschikbare exportwaarden",
        barmode="stack",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(tickangle=-35),
        yaxis=dict(tickprefix="€", gridcolor=GRID),
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")

with table_col:
    table = recent[
        ["date", "order_id", "country", "card_value", "shipping", "fees", "order_total_export", "value_after_fees"]
    ].rename(
        columns={
            "date": "Datum",
            "order_id": "Order",
            "country": "Land",
            "card_value": "Kaartwaarde",
            "shipping": "Shipping",
            "fees": "Fees",
            "order_total_export": "Order total",
            "value_after_fees": "Kaartwaarde na fees",
        }
    )
    st.dataframe(
        table.style.format(
            {
                "Datum": "{:%d-%m-%Y}",
                "Kaartwaarde": "€{:.2f}",
                "Shipping": "€{:.2f}",
                "Fees": "€{:.2f}",
                "Order total": "€{:.2f}",
                "Kaartwaarde na fees": "€{:.2f}",
            },
            na_rep="-",
        ),
        width="stretch",
        height=420,
    )

if not articles.empty and "tcg" in articles.columns:
    with st.expander("Ruwe artikeldata voor TCG-overzicht"):
        display_cols = [c for c in ["sold_date", "order_id", "tcg", "name", "set_name", "category", "price"] if c in articles.columns]
        st.dataframe(articles[display_cols].sort_values(display_cols[0], ascending=False), width="stretch")

with st.expander("Ruwe orderdata"):
    display_cols = [
        c
        for c in ["date", "order_id", "country", "article_count", "gross_value", "shipping_cost", "order_total", "commission", "net_value"]
        if c in orders.columns
    ]
    st.dataframe(orders[display_cols].sort_values("date", ascending=False), width="stretch")
