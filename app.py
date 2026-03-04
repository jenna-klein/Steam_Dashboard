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

st.write("Looking for CSV at:", DATA_PATH)
st.write("File exists:", os.path.exists(DATA_PATH))


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
        .apply(lambda lst: [g.strip() for g in lst if g.strip()]))

    # PRICE CLEANING
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    # INDIE FLAG
    df["is_indie"] = df["genres"].apply(lambda g: "Indie" in g)

    # RECOMMENDATION RATE
    if "positive_ratings" in df.columns and "negative_ratings" in df.columns:
        df["total_reviews"] = df["positive_ratings"] + df["negative_ratings"]
        df["recommendation_rate"] = (
            df["positive_ratings"] / df["total_reviews"].replace(0, np.nan)
        )
    else:
        df["recommendation_rate"] = np.nan

    return df

df = load_and_clean_data(DATA_PATH)

# FILTERING FUNCTION
def apply_filters(df, selected_year, selected_genre, price_range):
    filtered = df.copy()

    if selected_year != "ALL":
        filtered = filtered[filtered["release_year"] == selected_year]

    if selected_genre != "ALL":
        filtered= [filtered["genres"].apply(lambda g: selected_genre in g)]

    filtered = filtered[
        filtered["price"].between(price_range[0], price_range[1])]

    return filtered


# SIDEBAR FILTERS
st.sidebar.header("Filters")

# Year dropdown
year_options = ["ALL"] + sorted(df["release_year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", year_options)

# Genre dropdown
genre_options = ["ALL"] + sorted({g for sublist in df["genres"] for g in sublist})
selected_genre = st.sidebar.selectbox("Select Genre", genre_options)

# Price slider
min_price, max_price = float(df["price"].min()), float(df["price"].max())
selected_price = st.sidebar.slider(
    "Price Range", min_price, max_price, (min_price, max_price))

# Apply filters
filtered_df = apply_filters(df, selected_year, selected_genre, selected_price)


# KPI FUNCTIONS
def compute_indie_market_share(df):
    total = len(df)
    indie = df["is_indie"].sum()
    return (indie / total * 100) if total > 0 else 0


def compute_median_indie_price(df):
    indie_prices = df[df["is_indie"] == True]["price"]
    return indie_prices.median() if len(indie_prices) > 0 else 0


def compute_fastest_growing_genre(df):
    if df["release_year"].nunique() < 2:
        return None, None

    latest_year = df["release_year"].max()
    prev_year = latest_year - 1

    exploded = df.explode("genres")

    current = exploded[exploded["release_year"] == latest_year]["genres"].value_counts()
    previous = exploded[exploded["release_year"] == prev_year]["genres"].value_counts()

    growth_df = pd.DataFrame({
        "current": current,
        "previous": previous
    }).fillna(0)

    growth_df["growth"] = (
        (growth_df["current"] - growth_df["previous"]) /
        growth_df["previous"].replace(0, np.nan)
    )

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
    genre, growth = compute_fastest_growing_genre(df)
    if genre:
        st.metric("Fastest Growing Genre", genre, f"{growth:.1%}")
    else:
        st.metric("Fastest Growing Genre", "N/A")

with kpi3:
    median_price = compute_median_indie_price(filtered_df)
    st.metric("Median Indie Price", f"${median_price:.2f}")

st.markdown("---")


# VISUALIZATION 1 -- Releases by Month
st.subheader("Releases by Month")

df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

df_grouped = (
    df
    .groupby(pd.Grouper(key='release_date', freq='M'))
    .size()
    .reset_index(name='count')
)

df_grouped['year'] = df_grouped['release_date'].dt.year

fig = px.bar(
    df_grouped,
    x='release_date',
    y='count',
    color='year',
    title='Monthly Release Counts by Year'
)

fig.update_xaxes(
    dtick="M12",
    tickformat="%Y"
)

st.plotly_chart(fig, use_container_width=True)


# VISUALIZATION 2 -- Top Genres
st.subheader("Top 10 Genres Overall")

# Explode genres
genre_exploded = df.explode("genres")

# Count genres
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
    text="count"
)

fig_genres.update_layout(xaxis_title="Genre", yaxis_title="Number of Games")
fig_genres.update_traces(textposition="outside")

st.plotly_chart(fig_genres, use_container_width=True)


# VISUALIZATION 3 -- Indie Market Share Over Time
st.subheader("Indie Market Share Over Time")

yearly = df.groupby("release_year")["is_indie"].mean().reset_index()
yearly["is_indie"] *= 100

fig1 = px.line(
    yearly,
    x="release_year",
    y="is_indie",
    title="Indie Market Share (%) by Year"
)

fig1.update_xaxes(
    type="category",   # clean categorical years
    tickangle=0
)

st.plotly_chart(fig1, use_container_width=True)


# VISUALIZATION 4 -- Price vs Recommendation Rate
st.subheader("Price vs Recommendation Rate")

games_with_recs = filtered_df[filtered_df["recommendations"] > 0]

sample_size = min(5000, len(games_with_recs))
sample = games_with_recs.sample(sample_size) if sample_size > 0 else games_with_recs

if len(sample) == 0:
    st.warning("No games with recommendations available for the selected filters.")
else:
    fig_price_rec = px.scatter(
        sample,
        x="price",
        y="recommendations",
        color="is_indie",
        opacity=0.5,
        title="Game Price vs Popularity (Recommendations, Log Scale)",
        labels={
            "price": "Price ($)",
            "recommendations": "Recommendations (log scale)",
            "is_indie": "Indie Game"
        },
        color_discrete_map={
            True: "#1f77b4",   # Indie = blue
            False: "#b0b0b0"   # Non‑indie = gray
        }
    )

    fig_price_rec.update_yaxes(type="log")

    fig_price_rec.update_layout(
        xaxis_title="Price ($)",
        yaxis_title="Recommendations (log scale)",
        legend_title="Is Indie:",
        height=600
    )

    st.plotly_chart(fig_price_rec, use_container_width=True)


st.markdown("---")
st.caption("Built for the Indie Game Development Team — Steam Data 2021–2026")