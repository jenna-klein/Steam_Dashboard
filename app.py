import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import re

# PAGE CONFIG
st.set_page_config(
    page_title="Steam Indie Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded")

# PATH HANDLING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "steam_clean_finished.csv")

# LOAD + CLEAN DATA
@st.cache_data
def load_and_clean_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # DATE PROCESSING
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year
    df["release_month"] = df["release_date"].dt.month
    df["release_quarter"] = df["release_date"].dt.quarter

    # GENRE PROCESSING
    df["genres"] = (
        df["genres"]
        .fillna("")
        .apply(lambda x: re.split(r"[;,/|]+", x))
        .apply(lambda lst: [g.strip() for g in lst if g.strip()])
    )

    # Remove non-genre labels
    NON_GENRES = {
        "Utilities", "Early Access", "Free to Play", "Software", "Animation & Modeling",
        "Audio Production", "Video Production", "Design & Illustration", "Education",
        "Web Publishing", "Photo Editing", "Accounting", "Game Development", "Software Training"
    }

    df["genres"] = df["genres"].apply(
        lambda lst: [g for g in lst if g not in NON_GENRES]
    )

    # PRICE CLEANING
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    # INDIE FLAG
    df["is_indie"] = df["genres"].apply(lambda g: "Indie" in g)

    # RECOMMENDATION RATE
    df["recommendations"] = pd.to_numeric(df["recommendations"], errors="coerce").fillna(0)

    # RECOMMENDATION RATE - if not already in CSV
    if "recommendation_rate" not in df.columns:
        df["recommendation_rate"] = np.nan

    return df


df = load_and_clean_data(DATA_PATH)

# FILTERING FUNCTION
def apply_filters(df, selected_year, selected_genre, price_range):
    filtered = df.copy()

    # Cap prices before filtering
    filtered["price"] = filtered["price"].clip(upper=100)

    if selected_year != "ALL":
        filtered = filtered[filtered["release_year"] == selected_year]

    if selected_genre != "ALL":
        filtered = filtered[filtered["genres"].apply(lambda g: selected_genre in g)]

    filtered = filtered[
        filtered["price"].between(price_range[0], price_range[1])]

    return filtered


# SIDEBAR FILTERS
st.sidebar.header("Filters")

year_options = ["ALL"] + sorted(df["release_year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", year_options)

genre_options = ["ALL"] + sorted({g for sublist in df["genres"] for g in sublist})
selected_genre = st.sidebar.selectbox("Select Genre", genre_options)

# Cap price filter at $100 to match visualization
min_price = 0
max_price = 100

selected_price = st.sidebar.slider(
    "Price Range ($)",
    min_price,
    max_price,
    (min_price, max_price))

filtered_df = apply_filters(df, selected_year, selected_genre, selected_price)

# KPI FUNCTIONS
def compute_indie_market_share(data_df):
    total = len(filtered_df)
    indie = filtered_df["is_indie"].sum()
    return (indie / total * 100) if total > 0 else 0

def compute_median_indie_price(data_df):
    indie_prices = filtered_df[filtered_df["is_indie"] == True]["price"]
    return indie_prices.median() if len(indie_prices) > 0 else 0

def compute_fastest_growing_genre(data_df):
    if filtered_df["release_year"].nunique() < 2:
        return None, None

    latest_year = filtered_df["release_year"].max()
    prev_year = latest_year - 1

    exploded = filtered_df.explode("genres")

    current = exploded[exploded["release_year"] == latest_year]["genres"].value_counts()
    previous = exploded[exploded["release_year"] == prev_year]["genres"].value_counts()

    growth_df = pd.DataFrame({
        "current": current,
        "previous": previous
    }).fillna(0)

    growth_df["growth"] = (
        (growth_df["current"] - growth_df["previous"]) /
        growth_df["previous"].replace(0, np.nan))

    if growth_df["growth"].dropna().empty:
        return None, None

    fastest = growth_df["growth"].idxmax()
    fastest_growth = growth_df["growth"].max()

    return fastest, fastest_growth


# KPI SECTION
st.title("Steam Indie Market Dashboard")

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    share = compute_indie_market_share(filtered_df)
    st.metric("Indie Market Share (%)", f"{share:.1f}%")

with kpi2:
    genre, growth = compute_fastest_growing_genre(filtered_df)
    if genre:
        st.metric("Fastest Growing Genre", genre, f"{growth:.1%}")
    else:
        st.metric("Fastest Growing Genre", "N/A")

with kpi3:
    median_price = compute_median_indie_price(filtered_df)
    st.metric("Median Indie Price", f"${median_price:.2f}")

st.markdown("---")


# VISUALIZATION 1 — Monthly Releases (Filtered)
st.subheader("Releases by Month")

df_grouped = (
    filtered_df
    .groupby(pd.Grouper(key='release_date', freq='M'))
    .size()
    .reset_index(name='count'))

df_grouped['year'] = df_grouped['release_date'].dt.year

fig = px.bar(
    df_grouped,
    x='release_date',
    y='count',
    color='year',
    title='Monthly Release Counts by Year')

fig.update_traces(
    hovertemplate="%{x|%B %Y}<br>Releases: %{y}")

fig.update_xaxes(
    dtick="M12",
    tickformat="%Y")

st.plotly_chart(fig, use_container_width=True)


# VISUALIZATION 2 — Top Genres (Filtered)
st.subheader("Top 10 Genres Overall")

genre_exploded = filtered_df.explode("genres")

genre_counts = (
    genre_exploded["genres"]
    .value_counts()
    .head(10)
    .reset_index())

genre_counts.columns = ["genre", "count"]

fig_genres = px.bar(
    genre_counts,
    x="genre",
    y="count",
    title="Top 10 Most Common Genres",
    text="count")

fig_genres.update_layout(xaxis_title="Genre", yaxis_title="Number of Games")
fig_genres.update_traces(textposition="outside")

st.plotly_chart(fig_genres, use_container_width=True)


# VISUALIZATION 3 — Indie Market Share Over Time (Genre filter only)
st.subheader("Indie Market Share Over Time")

# Start with full dataset
genre_filtered_df = df.copy()

# Apply ONLY the genre filter
if selected_genre != "ALL":
    genre_filtered_df = genre_filtered_df[
        genre_filtered_df["genres"].apply(lambda g: selected_genre in g)]

# Compute indie share per year
yearly = (
    genre_filtered_df
    .groupby("release_year")["is_indie"]
    .mean()
    .reset_index())

yearly["is_indie"] *= 100  # convert to %

fig1 = px.line(
    yearly,
    x="release_year",
    y="is_indie",
    title=f"Indie Market Share (%) by Year — Genre: {selected_genre}")

fig1.update_xaxes(
    type="category",
    tickangle=0)

st.plotly_chart(fig1, use_container_width=True)


# VISUALIZATION 4 — Price vs Recommendation Count (log scale)
st.subheader("Price vs Recommendation Count")

# --- Clean and prepare data ---
scatter_df = filtered_df.copy()

# Ensure recommendations are numeric
scatter_df["recommendations"] = pd.to_numeric(
    scatter_df["recommendations"], errors="coerce"
).fillna(0)

# Remove games with 0 recommendations (log scale cannot show 0)
scatter_df = scatter_df[scatter_df["recommendations"] > 0]


# Cap price at $100
scatter_df["price"] = scatter_df["price"].clip(upper=100)

# --- Handle empty results ---
if scatter_df.empty:
    st.warning("No games available for the selected filters.")
else:
    fig_price_rec = px.scatter(
        scatter_df,
        x="price",
        y="recommendations",
        color="is_indie",
        color_discrete_map={
            True: "#1f77b4",  # indie
            False: "#b0b0b0"  # non‑indie
        },
        opacity=0.65,
        title="Price vs Recommendation Count",
        labels={
            "price": "Price ($, capped at 100)",
            "recommendations": "Recommendation Count (log scale)",
            "is_indie": "Indie Game"
        },
        hover_data={
            "name": True,
            "price": True,
            "recommendations": True,
            "genres": True,
            "is_indie": True
        }
    )

    # Log scale for recommendations
    fig_price_rec.update_yaxes(type="log")

    fig_price_rec.update_layout(
        xaxis_title="Price ($, capped at 100)",
        yaxis_title="Recommendation Count (log scale)",
        legend_title="Game Type:",
        height=750
    )

    fig_price_rec.for_each_trace(lambda t: t.update(
        name="Indie Games" if t.name == "True" else "Non-Indie Games"
    ))

    st.plotly_chart(fig_price_rec, use_container_width=True)


st.markdown("---")
st.caption("Built for the Indie Game Development Team — Steam Data 2021–2026")
