import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import load_articles_data, render_data_reload_button

# Set page configuration
st.set_page_config(
    page_title="Sold Articles Overview",
    layout="wide"
)
render_data_reload_button(key="reload_sold_articles")

st.title("🎴 Sold Articles Overview")

# Load local data
df = load_articles_data()

if df is None:
    st.error("Could not load articles data. Controleer of de CSV lokaal in de data map staat.")
    st.stop()

# Display the dataframe
st.dataframe(df, use_container_width=True)

# Display variety of stats about the sold articles
st.markdown("### Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    total_articles_sold = len(df)
    st.metric("Total Articles Sold", total_articles_sold)

with col2:
    total_revenue = df['card_prices'].sum()
    st.metric("Total Revenue", f"€{total_revenue:.2f}")

with col3:
    unique_sets = df['set_names'].nunique()
    st.metric("Unique Sets", unique_sets)

# Display the number of cards sold per card_rarity
st.markdown("---")
st.markdown("### Articles Sold by Rarity")

rarity_order = ['Common', 'Uncommon', 'Rare', 'Mythic', 'Land', 'Unknown']
rarity_counts = (
    df['card_rarities']
    .value_counts()
    .reindex(rarity_order)
    .dropna()
    .reset_index()
)
rarity_counts.columns = ['Rarity', 'Count']

fig_rarity = px.bar(
    rarity_counts,
    x='Rarity', y='Count',
    category_orders={'Rarity': rarity_order},
)
st.plotly_chart(fig_rarity, use_container_width=True)

# ===============================
# 🌳 Cards Sold by Set (Count)
# ===============================
st.markdown("---")
st.title("🌳 Cards Sold by Set")

treemap_count = df.groupby('set_names').size().reset_index(name='count')

fig1 = go.Figure(go.Treemap(
    labels=treemap_count['set_names'],
    parents=[''] * len(treemap_count),
    values=treemap_count['count'],
    marker=dict(
        colors=treemap_count['count'],
        colorscale='Viridis_r',
        showscale=True,
        colorbar=dict(
            title='Cards Sold',
            thickness=15,       # 👈 same thickness for both
            len=0.95,           # 👈 same length for both
        )
    ),
    textposition="middle center",
    textfont=dict(size=14),
    hovertemplate='<b>%{label}</b><br>Cards Sold: %{value}<extra></extra>',
))

fig1.update_layout(
    title='Cards Sold per Set',
    margin=dict(t=50, l=0, r=0, b=0),  # 👈 remove all padding
)

st.plotly_chart(fig1, use_container_width=True)


# =====================================
# 🌳 Total Value of Cards Sold per Set
# =====================================

treemap_value = (
    df.groupby('set_names')['card_prices']
      .sum()
      .reset_index(name='total_value')
)

fig2 = go.Figure(go.Treemap(
    labels=treemap_value['set_names'],
    parents=[''] * len(treemap_value),
    values=treemap_value['total_value'],
    marker=dict(
        colors=treemap_value['total_value'],
        colorscale='Viridis_r',
        showscale=True,
        colorbar=dict(
            title='Total Value (EUR)',
            thickness=15,       # 👈 same thickness for both
            len=0.95,           # 👈 same length for both
        )
    ),
    textposition="middle center",
    textfont=dict(size=14),
    hovertemplate='<b>%{label}</b><br>Total Value: €%{value:,.2f}<extra></extra>',
))

fig2.update_layout(
    title='Total Value of Cards Sold per Set',
    margin=dict(t=50, l=0, r=0, b=0),  # 👈 remove all padding
)

st.plotly_chart(fig2, use_container_width=True)
