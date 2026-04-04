"""
Analytics Dashboard – Enhanced
Light mode, organic green-yellow accent
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_orders_data, load_articles_data

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

# ── Palette — light mode ──────────────────────────────────────────────────────
BG      = '#f4f7ee'   # warm off-white with a green tint
SURFACE = '#e8eed8'   # slightly deeper card surface
BORDER  = '#c8d4a8'   # soft sage border
ACCENT  = '#5a8c1a'   # strong olive-green for accents
ACCENT2 = '#2d4a0c'   # dark forest green for headings/values
MUTED   = '#6b7c45'   # muted sage for subtitles
GRID    = '#d4ddb8'   # light grid lines
TEXT    = '#1e2a10'   # very dark green for readable body text

# Gradient scale (dark → accent) for single-metric charts
GRAD = [[0, '#b8cc80'], [1.0, ACCENT]]

# Full distinguishable palette for multi-series charts
COUNTRY_PALETTE = [
    '#4f9fd4',   # steel blue
    '#e07840',   # warm orange
    '#9b6cc4',   # soft purple
    '#d44f7c',   # rose
    '#3aab98',   # teal
    '#c49820',   # gold
    '#5a8c1a',   # olive green
    '#d06060',   # coral
]

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

  .section-header {{
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: {ACCENT2};
    margin: 8px 0 16px 0;
    border-left: 3px solid {ACCENT};
    padding-left: 12px;
  }}

  .block-container {{ padding-top: 1.5rem !important; }}
  hr {{ border-color: {BORDER} !important; opacity: 1; }}
</style>
""", unsafe_allow_html=True)

# ── Plotly base — light mode, margin excluded to avoid keyword conflicts ──────
PLOTLY_BASE = dict(
    paper_bgcolor=SURFACE,  # '#e8eed8' — slightly darker than page BG
    plot_bgcolor=SURFACE,
    font_color=TEXT,        # '#1e2a10' — always dark, always legible
)
M = dict(l=0, r=0, t=10, b=0)

# ── Load data ─────────────────────────────────────────────────────────────────
orders_df   = load_orders_data()
articles_df = load_articles_data()

if orders_df is None or articles_df is None:
    st.error("Could not load data. Please check your S3 bucket configuration.")
    st.stop()

# ── Prep ──────────────────────────────────────────────────────────────────────
orders_df['Date of Purchase'] = pd.to_datetime(orders_df['Date of Purchase'])
orders_df['Month']            = orders_df['Date of Purchase'].dt.to_period('M').dt.to_timestamp()
orders_df['MonthLabel']       = orders_df['Date of Purchase'].dt.strftime('%b %Y')
orders_df['WeekDay']          = orders_df['Date of Purchase'].dt.day_name()
orders_df['MonthNum']         = orders_df['Date of Purchase'].dt.month
orders_df['MonthName']        = orders_df['Date of Purchase'].dt.strftime('%b')

top_countries = orders_df['Country'].value_counts().head(6).index.tolist()

monthly_country = (
    orders_df.groupby(['Month', 'Country'])
    .agg(Orders=('Net Value', 'count'), Revenue=('Net Value', 'sum'))
    .reset_index()
)
monthly_country['Revenue'] = monthly_country['Revenue'].round(2)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='font-family:DM Serif Display,serif; color:{ACCENT2}; margin-bottom:4px;'>📈 Analytics</h1>"
    f"<p style='color:{MUTED}; font-size:0.9rem; margin-top:0;'>Deep-dive into geography, timing, buyer behaviour &amp; article trends</p>",
    unsafe_allow_html=True,
)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# Section 1 — Geography
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🌍 Geography</div>', unsafe_allow_html=True)

country_orders_ser = orders_df['Country'].value_counts()
country_rev        = orders_df.groupby('Country')['Net Value'].sum().round(2)
top4               = country_orders_ser.head(4)

g1, g2, g3, g4 = st.columns(4)
for col, country in zip([g1, g2, g3, g4], top4.index):
    pct = top4[country] / len(orders_df) * 100
    rev = country_rev.get(country, 0)
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">#{list(top4.index).index(country)+1} — {country}</div>
      <div class="value">{top4[country]:,}</div>
      <div class="sub">{pct:.1f}% of orders · €{rev:,.2f} net</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Map left, donut right
col_map, col_donut = st.columns([3, 2])

with col_map:
    country_data = (
        orders_df.groupby('Country')
        .agg(order_count=('Net Value', 'count'), net_revenue=('Net Value', 'sum'))
        .reset_index()
    )
    country_data['net_revenue'] = country_data['net_revenue'].round(2)

    fig_map = px.choropleth(
        country_data,
        locations='Country',
        locationmode='country names',
        color='order_count',
        hover_name='Country',
        hover_data={'net_revenue': ':,.2f', 'order_count': True},
        color_continuous_scale=[[0, '#c8dca0'], [0.35, '#7aac30'], [1.0, ACCENT]],
    )
    fig_map.update_geos(
        scope='europe',
        projection_scale=1.3,
        showland=True,
        landcolor='#dde8c0',
        showcountries=True,
        countrycolor=BORDER,
        countrywidth=0.8,
        bgcolor=BG,
    )
    fig_map.update_layout(
        **PLOTLY_BASE,
        geo_bgcolor=BG,
        coloraxis_colorbar=dict(tickfont=dict(color=MUTED), title='Orders'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_donut:
    # Revenue per country as a donut
    rev_donut = (
        orders_df.groupby('Country')['Net Value']
        .sum().round(2).reset_index()
        .sort_values('Net Value', ascending=False)
    )
    fig_donut = px.pie(
        rev_donut,
        names='Country',
        values='Net Value',
        hole=0.52,
        color_discrete_sequence=COUNTRY_PALETTE,
    )
    fig_donut.update_traces(
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>',
    )
    fig_donut.update_layout(
        paper_bgcolor=SURFACE,
        font_color=TEXT,
        showlegend=False,
        annotations=[dict(
            text='Revenue',
            font=dict(family='DM Serif Display', size=14, color=TEXT),
            showarrow=False,
        )],
        margin=dict(l=80, r=80, t=60, b=80),
        height=420,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 2 — Cumulative Orders by Country
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Cumulative Orders by Country</div>', unsafe_allow_html=True)

df_sorted = orders_df.sort_values('Date of Purchase').copy()
cumulative_data = []
for country in top_countries:
    country_series = df_sorted[df_sorted['Country'] == country]['Date of Purchase']
    all_dates      = sorted(df_sorted['Date of Purchase'].unique())
    cumulative_count = 0
    for date in all_dates:
        cumulative_count += (country_series == date).sum()
        cumulative_data.append({
            'Date of Purchase': date,
            'Country': country,
            'Cumulative Orders': cumulative_count,
        })

cumulative_df = pd.DataFrame(cumulative_data)

fig_cumulative = px.area(
    cumulative_df,
    x='Date of Purchase', y='Cumulative Orders',
    color='Country',
    color_discrete_sequence=COUNTRY_PALETTE,
)
fig_cumulative.update_traces(hovertemplate='<b>%{fullData.name}</b><br>%{y}<extra></extra>')
fig_cumulative.update_layout(
    **PLOTLY_BASE,
    xaxis_title='',
    yaxis_title='Total Orders',
    hovermode='x unified',
    legend_title_text='',
    legend=dict(orientation='h', y=-0.15),
    yaxis=dict(gridcolor=GRID),
    xaxis=dict(showgrid=False),
    height=380,
    margin=M,
)
st.plotly_chart(fig_cumulative, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 3 — Monthly Revenue by Top Countries — STACKED BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">💶 Monthly Revenue by Top Countries</div>', unsafe_allow_html=True)

monthly_top = (
    monthly_country[monthly_country['Country'].isin(top_countries)]
    .copy()
)
monthly_top['MonthLabel'] = monthly_top['Month'].dt.strftime('%b %Y')

fig_stacked = px.bar(
    monthly_top,
    x='MonthLabel', y='Revenue',
    color='Country',
    color_discrete_sequence=COUNTRY_PALETTE,
    labels={'Revenue': 'Net Revenue (€)', 'MonthLabel': ''},
    barmode='stack',
)
fig_stacked.update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>€%{y:,.2f}<extra></extra>',
)
fig_stacked.update_layout(
    **PLOTLY_BASE,
    hovermode='x unified',
    legend_title_text='',
    legend=dict(orientation='h', y=-0.15),
    yaxis=dict(tickprefix='€', gridcolor=GRID, tickformat=',.2f'),
    xaxis=dict(showgrid=False, tickangle=-30),
    height=420,
    margin=M,
)
st.plotly_chart(fig_stacked, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 4 — Orders by Day of Week
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🕐 Orders by Day of Week</div>', unsafe_allow_html=True)

day_order  = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_counts = (
    orders_df['WeekDay'].value_counts()
    .reindex(day_order).reset_index()
)
dow_counts.columns = ['Day', 'Orders']

fig_dow = px.bar(
    dow_counts,
    x='Day', y='Orders',
    labels={'Day': '', 'Orders': 'Orders'},
    color='Orders',
    color_continuous_scale=GRAD,
)
fig_dow.update_traces(hovertemplate='<b>%{x}</b><br>%{y} orders<extra></extra>')
fig_dow.update_layout(
    **PLOTLY_BASE,
    coloraxis_showscale=False,
    yaxis=dict(gridcolor=GRID),
    xaxis=dict(tickangle=-20),
    height=340,
    margin=M,
)
st.plotly_chart(fig_dow, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 5 — Orders by Value Bracket
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">💰 Orders by Value Bracket</div>', unsafe_allow_html=True)

bins   = [0, 5, 10, 20, 50, 100, 200, float('inf')]
labels = ['<€5', '€5–10', '€10–20', '€20–50', '€50–100', '€100–200', '€200+']
orders_df['Value Bucket'] = pd.cut(orders_df['Net Value'], bins=bins, labels=labels)
bucket_data = orders_df['Value Bucket'].value_counts().reindex(labels).reset_index()
bucket_data.columns = ['Bucket', 'Count']

fig_bucket = px.bar(
    bucket_data,
    x='Bucket', y='Count',
    labels={'Bucket': 'Order Value', 'Count': 'Orders'},
    color='Count',
    color_continuous_scale=GRAD,
)
fig_bucket.update_traces(hovertemplate='<b>%{x}</b><br>%{y} orders<extra></extra>')
fig_bucket.update_layout(
    **PLOTLY_BASE,
    coloraxis_showscale=False,
    xaxis=dict(tickangle=-20),
    yaxis=dict(gridcolor=GRID),
    height=340,
    margin=M,
)
st.plotly_chart(fig_bucket, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 7 — Rarity Breakdown
# ══════════════════════════════════════════════════════════════════════════════
if 'card_rarities' in articles_df.columns:
    st.markdown('<div class="section-header">✨ Rarity Breakdown</div>', unsafe_allow_html=True)

    rarity_stats = (
        articles_df.groupby('card_rarities')
        .agg(Count=('card_prices', 'count'), Total=('card_prices', 'sum'), Avg=('card_prices', 'mean'))
        .round(2)
        .sort_values('Total', ascending=False).reset_index()
    )

    col_rar1, col_rar2, col_rar3 = st.columns(3)

    with col_rar1:
        fig_rar_count = px.pie(
            rarity_stats,
            names='card_rarities', values='Count',
            hole=0.5,
            color_discrete_sequence=COUNTRY_PALETTE,
        )
        fig_rar_count.update_traces(
            textposition='none',
            textinfo='none',
            hovertemplate='<b>%{label}</b><br>%{value} cards<br>%{percent}<extra></extra>',
        )
        fig_rar_count.update_layout(
            paper_bgcolor=SURFACE,
            font_color=TEXT,
            title=dict(text='Cards Sold by Rarity', font=dict(color=TEXT, size=12), x=0.5, xanchor='center'),
            showlegend=True,
            legend=dict(orientation='v', x=1.05, y=0.5, xanchor='left', yanchor='middle', font=dict(color=TEXT)),
            margin=dict(l=20, r=120, t=50, b=20),
            height=400,
        )
        st.plotly_chart(fig_rar_count, use_container_width=True)

    with col_rar2:
        fig_rar_rev = px.pie(
            rarity_stats,
            names='card_rarities', values='Total',
            hole=0.5,
            color_discrete_sequence=COUNTRY_PALETTE,
        )
        fig_rar_rev.update_traces(
            textposition='none',
            textinfo='none',
            hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>',
        )
        fig_rar_rev.update_layout(
            paper_bgcolor=SURFACE,
            font_color=TEXT,
            title=dict(text='Revenue Share by Rarity', font=dict(color=TEXT, size=12), x=0.5, xanchor='center'),
            showlegend=True,
            legend=dict(orientation='v', x=1.05, y=0.5, xanchor='left', yanchor='middle', font=dict(color=TEXT)),
            margin=dict(l=20, r=120, t=50, b=20),
            height=400,
        )
        st.plotly_chart(fig_rar_rev, use_container_width=True)

    with col_rar3:
        # Fix: sort ascending so bars grow left-to-right, give generous left margin
        # so long rarity names aren't cut off, and use automargin on xaxis
        rarity_sorted = rarity_stats.sort_values('Avg')
        fig_rar_avg = px.bar(
            rarity_sorted,
            x='card_rarities', y='Avg',
            labels={'card_rarities': 'Rarity', 'Avg': 'Avg Price (€)'},
            color='Avg',
            color_continuous_scale=GRAD,
        )
        fig_rar_avg.update_traces(
            hovertemplate='<b>%{x}</b><br>€%{y:.2f}<extra></extra>',
        )
        fig_rar_avg.update_layout(
            **PLOTLY_BASE,
            title=dict(text='Avg Price per Rarity', font=dict(color=TEXT, size=12), x=0),
            coloraxis_showscale=False,
            xaxis=dict(tickangle=-30, automargin=True),
            yaxis=dict(tickprefix='€', tickformat=',.2f', gridcolor=GRID),
            margin=dict(l=0, r=0, t=30, b=60),
            height=400,
        )
        st.plotly_chart(fig_rar_avg, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 8 — Set Performance
# ══════════════════════════════════════════════════════════════════════════════
if 'set_names' in articles_df.columns:
    st.markdown('<div class="section-header">📦 Set Performance — Volume vs Revenue</div>', unsafe_allow_html=True)

    set_stats = (
        articles_df.groupby('set_names')
        .agg(Cards_Sold=('card_prices', 'count'),
             Total_Revenue=('card_prices', 'sum'),
             Avg_Price=('card_prices', 'mean'))
        .round(2)
        .reset_index()
    )

    fig_scatter = px.scatter(
        set_stats,
        x='Cards_Sold', y='Total_Revenue',
        size='Avg_Price',
        color='Avg_Price',
        hover_name='set_names',
        color_continuous_scale=GRAD,
        labels={
            'Cards_Sold':    'Cards Sold',
            'Total_Revenue': 'Total Revenue (€)',
            'Avg_Price':     'Avg Card Price (€)',
        },
        size_max=40,
    )
    fig_scatter.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>Cards Sold: %{x}<br>Revenue: €%{y:,.2f}<extra></extra>',
    )
    fig_scatter.update_layout(
        **PLOTLY_BASE,
        coloraxis_colorbar=dict(
            title='Avg €',
            tickfont=dict(color=MUTED),
            tickformat=',.2f',
        ),
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(tickprefix='€', tickformat=',.2f', gridcolor=GRID),
        height=480,
        margin=M,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)