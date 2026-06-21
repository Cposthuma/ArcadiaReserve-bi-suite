"""Clean sold articles page focused on cards, sets, and rarity."""
import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_articles_data, render_data_reload_button

st.set_page_config(page_title="Sold Articles", page_icon="cards", layout="wide")
render_data_reload_button(key="reload_sold_articles")

ACCENT = "#7a5cff"
ACCENT_DARK = "#392878"
MUTED = "#6f6987"
GRID = "#ded9f5"


def money(value: float) -> str:
    return f"€{value:,.2f}"


def style_page() -> None:
    st.markdown(
        f"""
        <style>
          .block-container {{ padding-top: 1.4rem; }}
          .metric-card {{
            border: 1px solid {GRID};
            border-radius: 8px;
            padding: 15px 17px;
            background: #fbfaff;
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


style_page()
df = load_articles_data()

required = {"price", "name", "set_name", "rarity"}
if df is None or df.empty or not required.issubset(df.columns):
    st.error("Geen bruikbare artikeldata gevonden. Zet je Cardmarket Sold Articles CSV's in data/articles.")
    if df is not None and not df.empty:
        st.caption(f"Ontbrekende kolommen: {', '.join(sorted(required - set(df.columns)))}")
    st.stop()

df = df.copy()
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df = df.dropna(subset=["price"]).copy()

st.title("Sold Articles")
st.caption("Welke kaarten en sets leveren de meeste omzet op? Filter op TCG voor Pokemon of One Piece.")

if "tcg" in df.columns:
    values = sorted(v for v in df["tcg"].dropna().astype(str).unique() if v and v != "Unknown")
    if "Unknown" in set(df["tcg"].dropna().astype(str)):
        values.append("Unknown")
    selected_tcg = st.selectbox("TCG", ["Alle TCGs"] + values, key="sold_articles_tcg_filter")
    if selected_tcg != "Alle TCGs":
        df = df[df["tcg"] == selected_tcg].copy()

if df.empty:
    st.warning("Geen artikeldata voor deze TCG-selectie.")
    st.stop()

top_card = df.sort_values("price", ascending=False).iloc[0]
median_price = df["price"].median()
unique_sets = df["set_name"].nunique()

c1, c2, c3, c4 = st.columns(4)
metric_card(c1, "Singles verkocht", f"{len(df):,}", "Uit Sold Articles")
metric_card(c2, "Kaartomzet", money(df["price"].sum()), f"Mediaan {money(median_price)}")
metric_card(c3, "Unieke sets", f"{unique_sets:,}", "Sets met verkoop")
metric_card(c4, "Hoogste kaart", money(top_card["price"]), str(top_card["name"])[:42])

st.divider()

if "tcg" in df.columns:
    tcg_stats = (
        df.groupby("tcg", as_index=False)
        .agg(singles=("price", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
        .sort_values("revenue", ascending=False)
    )
    st.subheader("TCG verdeling")
    st.dataframe(
        tcg_stats.rename(columns={"tcg": "TCG", "singles": "Singles", "revenue": "Omzet", "avg_price": "Gem. prijs"}).style.format(
            {"Omzet": "\u20ac{:.2f}", "Gem. prijs": "\u20ac{:.2f}"}
        ),
        width="stretch",
        hide_index=True,
    )

set_stats = (
    df.groupby("set_name", as_index=False)
    .agg(cards=("price", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
    .sort_values("revenue", ascending=False)
    .head(15)
)
rarity_stats = (
    df.groupby("rarity", as_index=False)
    .agg(cards=("price", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
    .sort_values("revenue", ascending=False)
)

left, right = st.columns([3, 2])

with left:
    fig = px.bar(
        set_stats,
        x="revenue",
        y="set_name",
        orientation="h",
        color="revenue",
        color_continuous_scale=[[0, "#ded9f5"], [1, ACCENT]],
        text="revenue",
        labels={"set_name": "", "revenue": "Omzet"},
    )
    fig.update_traces(texttemplate="€%{text:,.0f}", hovertemplate="%{y}<br>Omzet: €%{x:,.2f}<extra></extra>")
    fig.update_layout(
        title="Top sets op omzet",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(tickprefix="€", gridcolor=GRID),
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")

with right:
    fig = px.bar(
        rarity_stats,
        x="revenue",
        y="rarity",
        orientation="h",
        color="avg_price",
        color_continuous_scale=[[0, "#ded9f5"], [1, ACCENT]],
        labels={"rarity": "", "revenue": "Omzet", "avg_price": "Gem. prijs"},
    )
    fig.update_layout(
        title="Rarity mix",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(tickprefix="€", gridcolor=GRID),
        yaxis=dict(autorange="reversed"),
        coloraxis_colorbar=dict(title="Gem. €"),
    )
    st.plotly_chart(fig, width="stretch")

st.subheader("Top verkochte kaarten")
card_stats = (
    df.groupby(["name", "set_name"], as_index=False)
    .agg(aantal=("price", "count"), omzet=("price", "sum"), gem_prijs=("price", "mean"))
    .sort_values("omzet", ascending=False)
    .head(25)
)
st.dataframe(
    card_stats.rename(columns={"name": "Kaart", "set_name": "Set", "aantal": "Aantal", "omzet": "Omzet", "gem_prijs": "Gem. prijs"}).style.format(
        {"Omzet": "€{:.2f}", "Gem. prijs": "€{:.2f}"}
    ),
    width="stretch",
    height=420,
)

with st.expander("Ruwe artikeldata"):
    st.dataframe(df, width="stretch")


