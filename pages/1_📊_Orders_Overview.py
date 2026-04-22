"""
Orders Overview Dashboard — Teal / light-blue theme
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_articles_data, load_orders_data, render_data_reload_button

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Orders Overview", page_icon="📊", layout="wide")
render_data_reload_button(key="reload_orders_overview")

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = '#f0f8f8'   # very light teal-white — blends with white Streamlit bg
SURFACE   = '#dff0f0'   # card surface: soft teal wash
BORDER    = '#a8d4d4'   # card border: muted teal
ACCENT    = '#1a9090'   # primary teal
ACCENT2   = '#0d5c6e'   # deep teal for headings / values
MUTED     = '#5c8a8a'   # muted teal for subtitles & labels
GRID      = '#cce4e4'   # light grid lines
TEXT      = '#0d2e2e'   # very dark teal for body text
POS       = '#1aab8a'   # positive delta — green-teal
NEG       = '#d45c5c'   # negative delta — warm red

# Gradient scale for single-metric charts: pale teal → strong teal
TEAL_GRAD = [[0, '#9fd8d8'], [1.0, ACCENT]]

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {BG};
    color: {TEXT};
  }}

  .metric-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    height: 100%;
  }}
  .metric-card .label {{
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: 6px;
  }}
  .metric-card .value {{
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: {ACCENT2};
    line-height: 1.1;
  }}
  .metric-card .sub {{
    font-size: 0.78rem;
    color: {MUTED};
    margin-top: 4px;
  }}
  .metric-card .delta-pos {{
    font-size: 0.8rem;
    color: {POS};
    margin-top: 4px;
  }}
  .metric-card .delta-neg {{
    font-size: 0.8rem;
    color: {NEG};
    margin-top: 4px;
  }}

  .section-header {{
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: {ACCENT2};
    margin: 8px 0 16px 0;
    border-left: 3px solid {ACCENT};
    padding-left: 12px;
  }}

  .store-link {{
    display: inline-block;
    background: {SURFACE};
    border: 1px solid {ACCENT};
    border-radius: 8px;
    padding: 6px 16px;
    color: {ACCENT2} !important;
    font-size: 0.85rem;
    text-decoration: none;
    margin-bottom: 16px;
  }}

  .block-container {{ padding-top: 1.5rem !important; }}
  hr {{ border-color: {BORDER} !important; opacity: 1; }}
</style>
""", unsafe_allow_html=True)

# ── Shared Plotly base — light teal background, no margin (set per chart) ────
PLOTLY_BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font_color=TEXT,
)
M = dict(l=0, r=0, t=10, b=0)

# ── Load data ─────────────────────────────────────────────────────────────────
df          = load_orders_data()
articles_df = load_articles_data()

if df is None or df.empty:
    st.error("Could not load orders data.")
    st.stop()

if articles_df is None or articles_df.empty:
    st.error("Could not load articles data.")
    st.stop()

# ── Prep ──────────────────────────────────────────────────────────────────────
df['Date of Purchase'] = pd.to_datetime(df['Date of Purchase'])
df['Month']            = df['Date of Purchase'].dt.to_period('M').dt.to_timestamp()
df['MonthLabel']       = df['Date of Purchase'].dt.strftime('%b %Y')
df['Cumulative Net']   = df['Net Value'].cumsum()

monthly = (
    df.groupby('Month')
    .agg(Orders=('Net Value', 'count'), Net_Revenue=('Net Value', 'sum'))
    .reset_index()
)
monthly['MonthLabel'] = monthly['Month'].dt.strftime('%b %Y')

if len(monthly) >= 2:
    last_rev  = monthly.iloc[-1]['Net_Revenue']
    prev_rev  = monthly.iloc[-2]['Net_Revenue']
    rev_delta = last_rev - prev_rev
    rev_pct   = (rev_delta / prev_rev * 100) if prev_rev else 0
else:
    rev_delta = rev_pct = 0

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='font-family:DM Serif Display,serif; color:{ACCENT2}; margin-bottom:4px;'>📊 Orders Overview</h1>"
    f"<p style='color:{MUTED}; font-size:0.9rem; margin-top:0;'>Sales performance across all shipped orders &amp; articles</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<a class='store-link' href='https://www.cardmarket.com/en/Magic/Users/ExCardin' target='_blank'>"
    "🔗 Visit ExCardin's Cardmarket Store</a>",
    unsafe_allow_html=True,
)
st.divider()

# ── KPI Row 1 — Orders ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Orders</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

commission_pct = (df['Commission'].sum() / df['Total Value'].sum() * 100) if df['Total Value'].sum() else 0
avg_order_val  = df['Net Value'].mean()
best_month_row = monthly.loc[monthly['Net_Revenue'].idxmax()]

delta_html = (
    f"<div class='delta-pos'>▲ €{rev_delta:,.2f} ({rev_pct:.1f}%) vs prev month</div>"
    if rev_delta >= 0 else
    f"<div class='delta-neg'>▼ €{abs(rev_delta):,.2f} ({abs(rev_pct):.1f}%) vs prev month</div>"
)

for col, label, val, sub in [
    (k1, "Total Orders",     f"{len(df):,}",                        f"{monthly['Orders'].mean():.1f} avg / month"),
    (k2, "Gross Revenue",    f"€{df['Total Value'].sum():,.2f}",    "incl. shipping"),
    (k3, "Total Commission", f"€{df['Commission'].sum():,.2f}",     f"{commission_pct:.1f}% of gross"),
    (k4, "Net Revenue",      f"€{df['Net Value'].sum():,.2f}",      f"avg €{avg_order_val:.2f} / order"),
    (k5, "Best Month",       best_month_row['MonthLabel'],          f"€{best_month_row['Net_Revenue']:,.2f} net"),
]:
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value">{val}</div>
      <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Row 2 — Articles ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">Singles Sold</div>', unsafe_allow_html=True)

a1, a2, a3, a4 = st.columns(4)

median_price = articles_df['card_prices'].median()
top_card     = articles_df.loc[articles_df['card_prices'].idxmax()] if not articles_df.empty else None

for col, label, val, sub in [
    (a1, "Singles Sold",     f"{len(articles_df):,}",                       "individual cards"),
    (a2, "Articles Revenue", f"€{articles_df['card_prices'].sum():,.2f}",   "total card value"),
    (a3, "Avg Card Price",   f"€{articles_df['card_prices'].mean():,.2f}",  f"median €{median_price:.2f}"),
    (a4, "Highest Sale",
         f"€{top_card['card_prices']:.2f}" if top_card is not None else "—",
         top_card['name'] if top_card is not None and 'name' in top_card else ""),
]:
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value">{val}</div>
      <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue Over Time ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Revenue Over Time</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])

with col_left:
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=df['Date of Purchase'],
        y=df['Cumulative Net'],
        mode='lines',
        fill='tozeroy',
        line=dict(color=ACCENT, width=2),
        fillcolor='rgba(26,144,144,0.12)',
        hovertemplate='%{x|%d %b %Y}<br>€%{y:,.2f}<extra>Cumulative Net</extra>',
    ))
    fig_cum.update_layout(
        **PLOTLY_BASE,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRID, tickprefix='€', tickformat=',.2f'),
        hovermode='x unified',
        margin=M,
    )
    st.plotly_chart(fig_cum, use_container_width=True)

with col_right:
    fig_mbar = px.bar(
        monthly,
        x='MonthLabel', y='Net_Revenue',
        labels={'MonthLabel': '', 'Net_Revenue': 'Net Revenue (€)'},
        color='Net_Revenue',
        color_continuous_scale=TEAL_GRAD,
    )
    fig_mbar.update_traces(hovertemplate='<b>%{x}</b><br>€%{y:,.2f}<extra></extra>')
    fig_mbar.update_layout(
        **PLOTLY_BASE,
        coloraxis_showscale=False,
        xaxis=dict(tickangle=-45),
        yaxis=dict(tickprefix='€', tickformat=',.2f', gridcolor=GRID),
        margin=M,
    )
    st.plotly_chart(fig_mbar, use_container_width=True)

# ── Order Volume & Cost Breakdown ─────────────────────────────────────────────
st.markdown('<div class="section-header">Order Volume &amp; Cost Breakdown</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    fig_orders = px.bar(
        monthly,
        x='MonthLabel', y='Orders',
        labels={'MonthLabel': '', 'Orders': 'Orders'},
        color='Orders',
        color_continuous_scale=TEAL_GRAD,
    )
    fig_orders.update_traces(hovertemplate='<b>%{x}</b><br>%{y} orders<extra></extra>')
    fig_orders.update_layout(
        **PLOTLY_BASE,
        coloraxis_showscale=False,
        xaxis=dict(tickangle=-45),
        yaxis=dict(gridcolor=GRID),
        margin=M,
    )
    st.plotly_chart(fig_orders, use_container_width=True)

with col_b:
    total_gross = df['Total Value'].sum()
    total_net   = df['Net Value'].sum()
    total_comm  = df['Commission'].sum()

    breakdown = pd.DataFrame({
        'Component': ['Net Revenue (Merchandise + Shipping)', 'Commission'],
        'Value':     [round(total_net, 2), round(total_comm, 2)],
    })
    fig_donut = px.pie(
        breakdown,
        names='Component', values='Value',
        hole=0.55,
        color='Component',
        color_discrete_map={
            'Net Revenue': '#7b5ea7',
            'Commission':  '#e05c6c',
        },
        template='plotly_dark',
        title='Revenue vs Commission Breakdown',
    )
    fig_donut.update_traces(textposition='outside', textinfo='label+percent')
    fig_donut.update_layout(
        paper_bgcolor=BG,
        showlegend=False,
        margin=dict(l=80, r=80, t=60, b=80),
        title=dict(
            text='Revenue vs Commission Breakdown',
            font=dict(family='DM Serif Display', size=16, color=ACCENT2),
            x=0.5,
            xanchor='center',
        ),
        annotations=[dict(
            text=f"€{total_gross:,.0f}",
            font=dict(family='DM Serif Display', size=18, color=ACCENT2),
            showarrow=False,
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Card Price Distribution ───────────────────────────────────────────────────
st.markdown('<div class="section-header">Card Price Distribution</div>', unsafe_allow_html=True)

col_x, col_y = st.columns([2, 3])

with col_x:
    fig_hist = px.histogram(
        articles_df,
        x='card_prices',
        nbins=30,
        labels={'card_prices': 'Card Price (€)', 'count': 'Count'},
        color_discrete_sequence=[ACCENT],
    )
    fig_hist.update_traces(hovertemplate='€%{x:.2f}<br>%{y} cards<extra></extra>')
    fig_hist.update_layout(
        **PLOTLY_BASE,
        bargap=0.05,
        xaxis=dict(tickprefix='€', tickformat=',.2f', gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
        margin=M,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_y:
    bins   = [0, 0.5, 1, 2, 5, 10, 25, 50, float('inf')]
    labels = ['<€0.50', '€0.50–1', '€1–2', '€2–5', '€5–10', '€10–25', '€25–50', '€50+']
    articles_df['Price Bucket'] = pd.cut(articles_df['card_prices'], bins=bins, labels=labels)
    bucket_counts = articles_df['Price Bucket'].value_counts().reindex(labels).reset_index()
    bucket_counts.columns = ['Bucket', 'Count']

    fig_buck = px.bar(
        bucket_counts,
        x='Bucket', y='Count',
        labels={'Bucket': 'Price Range', 'Count': 'Cards Sold'},
        color='Count',
        color_continuous_scale=TEAL_GRAD,
    )
    fig_buck.update_traces(hovertemplate='<b>%{x}</b><br>%{y} cards<extra></extra>')
    fig_buck.update_layout(
        **PLOTLY_BASE,
        coloraxis_showscale=False,
        xaxis=dict(tickangle=-20),
        yaxis=dict(gridcolor=GRID),
        margin=M,
    )
    st.plotly_chart(fig_buck, use_container_width=True)

# ── Raw orders table ──────────────────────────────────────────────────────────
with st.expander("📋 Raw Orders", expanded=False):
    display_cols = [c for c in ['Date of Purchase', 'Total Value', 'Commission', 'Net Value'] if c in df.columns]
    st.dataframe(
        df[display_cols]
        .sort_values('Date of Purchase', ascending=False)
        .reset_index(drop=True)
        .style
        .format({c: '€{:.2f}' for c in ['Total Value', 'Commission', 'Net Value'] if c in display_cols})
        .background_gradient(subset=['Net Value'], cmap='Blues'),
        use_container_width=True,
        height=350,
    )
