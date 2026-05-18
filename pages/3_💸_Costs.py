"""
Costs Dashboard - Monthly Expenses Analysis
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_expenses_data

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Costs", page_icon="💸", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #faf7f5;
    color: #3b2323;
  }

  /* Main app background */
  .stApp {
    background-color: #faf7f5;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #f4ece8;
    border-right: 1px solid #ead9d2;
  }

  /* Metric cards */
  .metric-card {
    background: linear-gradient(145deg, #fff8f6, #f8ece8);
    border: 1px solid #ead9d2;
    border-radius: 18px;
    padding: 22px 24px;
    text-align: center;
    box-shadow: 0 4px 18px rgba(120, 60, 60, 0.06);
    transition: all 0.2s ease;
  }

  .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(120, 60, 60, 0.10);
  }

  .metric-card .label {
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #a06b6b;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .metric-card .value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.1rem;
    color: #7d2e2e;
    line-height: 1;
  }

  .metric-card .sub {
    font-size: 0.82rem;
    color: #8b6f6f;
    margin-top: 6px;
  }

  /* Section headers */
  .section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: #8f2d2d;
    margin: 10px 0 18px 0;
    border-left: 4px solid #c97c7c;
    padding-left: 14px;
    line-height: 1;
  }

  /* Login form */
  .login-wrapper {
    max-width: 380px;
    margin: 80px auto 0 auto;
    background: #fff8f6;
    border: 1px solid #ead9d2;
    border-radius: 20px;
    padding: 40px 36px;
    text-align: center;
    box-shadow: 0 10px 35px rgba(120, 60, 60, 0.08);
  }

  .login-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #7d2e2e;
    margin-bottom: 6px;
  }

  .login-sub {
    font-size: 0.9rem;
    color: #8f7a7a;
    margin-bottom: 28px;
  }

  /* Buttons */
  .stButton > button {
    background: #a94444;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    font-weight: 500;
  }

  .stButton > button:hover {
    background: #922f2f;
    color: white;
  }

  /* Multiselects + inputs */
  div[data-baseweb="select"] > div {
    background-color: #fff8f6;
    border-color: #e2cfc7;
  }

  /* Divider */
  hr {
    border-color: #ead9d2 !important;
  }

  /* Hide default streamlit top padding */
  .block-container {
    padding-top: 1.4rem !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Login gate ────────────────────────────────────────────────────────────────
CORRECT_PASSWORD = "test"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="login-wrapper">
          <div class="login-title">🔐 Costs</div>
          <div class="login-sub">This page is restricted. Enter the password to continue.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                                placeholder="Enter password…")
            submitted = st.form_submit_button("Unlock", use_container_width=True)
            if submitted:
                if pwd == CORRECT_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_expenses_data()

if df is None or df.empty:
    st.error("Could not load expenses data.")
    st.stop()

# ── Prep ──────────────────────────────────────────────────────────────────────
df['Order_Date'] = pd.to_datetime(df['Order_Date'], dayfirst=True)
df['Month']      = df['Order_Date'].dt.to_period('M').dt.to_timestamp()
df['MonthLabel'] = df['Order_Date'].dt.strftime('%b %Y')

CATEGORY_COLORS = {
    'Inventory':       '#7b5ea7',
    'Storage':         '#4e9af1',
    'Shipping':        '#f07d3a',
    'Postage':         '#4ecdc4',
    'Trustee Service': '#f7c59f',
    'Draft':           '#e05c6c',
}
COUNTRY_COLORS = {
    'Netherlands': '#f77f00',
    'France':      '#4361ee',
    'Germany':     '#e63946',
}

all_cats      = sorted(df['Cost_Category'].unique())
all_countries = sorted(df['Store_Country'].unique())

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    # ── Cost Category filter with Select All ──
    cat_all = st.checkbox("All Categories", value=True, key="cat_all")
    if cat_all:
        selected_cats = all_cats
        st.multiselect(
            "Cost Category",
            options=all_cats,
            default=all_cats,
            disabled=True,
            key="cat_multi",
        )
    else:
        selected_cats = st.multiselect(
            "Cost Category",
            options=all_cats,
            default=all_cats,
            key="cat_multi",
        )

    st.markdown("---")

    # ── Country filter with Select All ──
    country_all = st.checkbox("All Countries", value=True, key="country_all")
    if country_all:
        selected_countries = all_countries
        st.multiselect(
            "Country",
            options=all_countries,
            default=all_countries,
            disabled=True,
            key="country_multi",
        )
    else:
        selected_countries = st.multiselect(
            "Country",
            options=all_countries,
            default=all_countries,
            key="country_multi",
        )

    st.markdown("---")
    if st.button("🔒 Lock page", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

dff = df[
    df['Cost_Category'].isin(selected_cats) &
    df['Store_Country'].isin(selected_countries)
]

# ── Page title ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style='
        font-family:DM Serif Display,serif;
        color:#5e1f1f;
        margin-bottom:4px;
        font-size:3rem;
        letter-spacing:-0.02em;
    '>
    💸 Cost Overview
    </h1>

    <p style='
        color:#9a7b7b;
        font-size:0.95rem;
        margin-top:0;
        margin-bottom:0;
    '>
    Monthly purchasing expenses across all suppliers
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
total_spend   = dff['Item_Price'].sum()
avg_order     = dff['Item_Price'].mean()
num_orders    = len(dff)
biggest_cat   = dff.groupby('Cost_Category')['Item_Price'].sum().idxmax() if not dff.empty else "—"
biggest_spend = dff.groupby('Cost_Category')['Item_Price'].sum().max() if not dff.empty else 0

k1, k2, k3, k4 = st.columns(4)
for col, label, val, sub in [
    (k1, "Total Spend",    f"€{total_spend:,.2f}",   f"{num_orders} transactions"),
    (k2, "Avg per Order",  f"€{avg_order:,.2f}",     "across all categories"),
    (k3, "Top Category",   biggest_cat,               f"€{biggest_spend:,.2f} total"),
    (k4, "Active Months",  str(dff['Month'].nunique()), "in date range"),
]:
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value">{val}</div>
      <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Monthly spend line + Category donut ────────────────────────────────
st.markdown('<div class="section-header">Spenditure Over Time</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])
with col_left:
    monthly = (
        dff.groupby(['Month', 'Cost_Category'])['Item_Price']
        .sum()
        .reset_index()
    )
    fig_bar = px.bar(
        monthly,
        x='Month', y='Item_Price',
        color='Cost_Category',
        color_discrete_map=CATEGORY_COLORS,
        labels={'Item_Price': 'Spend (€)', 'Month': ''},
        barmode='stack',
        title='Monthly Spend by Category',
    )
    fig_bar.update_layout(
        paper_bgcolor='#fffaf8',
        plot_bgcolor='#fffaf8',
        title=dict(
            text='Monthly Spend by Category',
            font=dict(family='DM Serif Display', size=16, color='#7d2e2e'),
            x=0.5,
            xanchor='center',
        ),
        legend_title_text='',
        legend=dict(orientation='h', y=-0.2, font=dict(color='#6f4a4a')),
        margin=dict(l=0, r=0, t=50, b=0),
        hovermode='x unified',
        yaxis=dict(tickprefix='€'),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    cat_totals = dff.groupby('Cost_Category')['Item_Price'].sum().reset_index()
    fig_donut = px.pie(
        cat_totals,
        names='Cost_Category', values='Item_Price',
        hole=0.55,
        color='Cost_Category',
        color_discrete_map=CATEGORY_COLORS,
        template='plotly_dark',
    )
    fig_donut.update_traces(
        textposition='none',
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>',
    )
    fig_donut.update_layout(
        paper_bgcolor='#fffaf8',
        font_color='#5b3a3a',
        title=dict(
            text='Spend by Category',
            font=dict(family='DM Serif Display', size=16, color='#7d2e2e'),
            x=0.5,
            xanchor='center',
        ),
        showlegend=True,
        legend=dict(orientation='v', x=1.05, y=0.5, xanchor='left', yanchor='middle', font=dict(color='#6f4a4a')),
        margin=dict(l=20, r=120, t=50, b=20),
        annotations=[dict(
            text=f"€{total_spend:,.0f}",
            font=dict(family='DM Serif Display', size=18, color='#7d2e2e'),
            showarrow=False,
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)
# ── Row 2: Country grouped bar + Heatmap ─────────────────────────────────────
st.markdown('<div class="section-header">Country Breakdown</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([2, 3])

with col_a:
    country_cat = (
        dff.groupby(['Store_Country', 'Cost_Category'])['Item_Price']
        .sum()
        .reset_index()
    )
    fig_bar = px.bar(
        country_cat,
        x='Store_Country', y='Item_Price',
        color='Cost_Category',
        color_discrete_map=CATEGORY_COLORS,
        barmode='stack',
        labels={'Item_Price': 'Spend (€)', 'Store_Country': ''},
        template='plotly_dark',
    )
    fig_bar.update_layout(
        paper_bgcolor='#fffaf8',
        plot_bgcolor='#fffaf8',
        legend_title_text='',
        legend=dict(orientation='h', y=-0.25, font_size=11),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    pivot = (
        dff.groupby(['MonthLabel', 'Cost_Category'])['Item_Price']
        .sum()
        .unstack(fill_value=0)
    )
    # Keep month order
    month_order = (
        dff[['Month', 'MonthLabel']]
        .drop_duplicates()
        .sort_values('Month')['MonthLabel']
        .tolist()
    )
    pivot = pivot.reindex([m for m in month_order if m in pivot.index])

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, '#fff5f2'],
            [0.2, '#f7d9d4'],
            [0.4, '#eeb8b0'],
            [0.6, '#dd8f86'],
            [0.8, '#c76565'],
            [1.0, '#9f3d3d']
        ],
        hovertemplate='%{y} · %{x}<br>€%{z:,.2f}<extra></extra>',
        colorbar=dict(
        tickfont=dict(color='#7b5b5b'),
        title='€'
        ),
    ))
    fig_heat.update_layout(
        paper_bgcolor='#fffaf8',
        plot_bgcolor='#fffaf8',
        xaxis=dict(tickfont=dict(color='#7d2e2e'), side='bottom'),
        yaxis=dict(tickfont=dict(color='#8a6a6a')),
        margin=dict(l=0, r=0, t=10, b=0),
        font_color='#5b3a3a',
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Row 3: Transaction table ──────────────────────────────────────────────────
with st.expander("📋 Raw Transactions", expanded=False):
    display_cols = ['Order_Date', 'Store_Name', 'Store_Country', 'Cost_Category', 'Item_Price', 'Description']
    st.dataframe(
        dff[display_cols]
        .sort_values('Order_Date', ascending=False)
        .reset_index(drop=True)
        .style.format({'Item_Price': '€{:.2f}'})
        .background_gradient(subset=['Item_Price'], cmap='Reds'),
        use_container_width=True,
        height=350,
    )

