import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import re

# PAGE CONFIG
st.set_page_config(
    page_title="Steam Indie Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

    # Remove non-genre labels (case-insensitive)
    NON_GENRES = {
        "utilities", "early access", "free to play", "software",
        "animation & modeling", "audio production", "video production",
        "design & illustration", "education", "web publishing",
        "photo editing", "accounting", "game development", "software training"
    }

    df["genres"] = df["genres"].apply(
        lambda lst: [g for g in lst if g.lower() not in NON_GENRES]
    )

    # INDIE FLAG (before removing "Indie")
    df["is_indie"] = df["genres"].apply(
        lambda g: any(x.lower() == "indie" for x in g)
    )

    # Remove "Indie" from genres
    df["genres"] = df["genres"].apply(
        lambda lst: [g for g in lst if g.lower() != "indie"]
    )

    # PRICE CLEANING
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    # RECOMMENDATIONS
    df["recommendations"] = pd.to_numeric(df["recommendations"], errors="coerce").fillna(0)

    return df


df = load_and_clean_data(DATA_PATH)

# FILTERING FUNCTION
def apply_filters(df, selected_year, selected_genre, price_range):
    filtered = df.copy()

    filtered["price"] = filtered["price"].clip(upper=100)

    if selected_year != "ALL":
        filtered = filtered[filtered["release_year"] == selected_year]

    if selected_genre != "ALL":
        filtered = filtered[filtered["genres"].apply(lambda g: selected_genre in g)]

    filtered = filtered[
        filtered["price"].between(price_range[0], price_range[1])
    ]

    return filtered


# SIDEBAR FILTERS
st.sidebar.header("Filters")

year_options = ["ALL"] + sorted(df["release_year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", year_options)

genre_options = ["ALL"] + sorted({g for sub in df["genres"] for g in sub})
selected_genre = st.sidebar.selectbox("Select Genre", genre_options)

selected_price = st.sidebar.slider(
    "Price Range ($)",
    0, 100,
    (0, 100)
)

filtered_df = apply_filters(df, selected_year, selected_genre, selected_price)

# KPI FUNCTIONS
def compute_indie_market_share(data_df):
    total = len(data_df)
    indie = data_df["is_indie"].sum()
    return (indie / total * 100) if total > 0 else 0

def compute_average_indie_price(data_df):
    indie_prices = data_df[data_df["is_indie"] == True]["price"]
    return indie_prices.mean() if len(indie_prices) > 0 else 0

def compute_fastest_growing_genre(data_df):
    if data_df["release_year"].nunique() < 2:
        return None, None

    latest_year = data_df["release_year"].max()
    prev_year = latest_year - 1

    exploded = data_df.explode("genres")

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
    genre, growth = compute_fastest_growing_genre(filtered_df)
    if genre:
        st.metric("Fastest Growing Genre", genre, f"{growth:.1%}")
    else:
        st.metric("Fastest Growing Genre", "N/A")

with kpi3:
    avg_price = compute_average_indie_price(filtered_df)
    st.metric("Average Indie Price", f"${avg_price:.2f}")

st.markdown("---")


# VISUALIZATION 1 — Monthly Releases
st.subheader("Releases by Month")

df_grouped = (
    filtered_df
    .groupby(pd.Grouper(key='release_date', freq='M'))
    .size()
    .reset_index(name='count')
)

df_grouped['year'] = df_grouped['release_date'].dt.year

fig_releases = px.bar(
    df_grouped,
    x='release_date',
    y='count',
    color='year',
    title='Monthly Release Counts by Year'
)

fig_releases.update_xaxes(dtick="M12", tickformat="%Y")
fig_releases.update_layout(xaxis_title="Release Date", yaxis_title="Release Count")
fig_releases.update_traces(
    hovertemplate="%{x|%B %Y}<br>Releases: %{y}<extra></extra>"
)

st.plotly_chart(fig_releases, use_container_width=True)


# VISUALIZATION 2 — Most Common Genres (Default = All Games)
st.subheader("Most Common Genres")

# Compute genre stats
exploded = filtered_df.explode("genres")

genre_stats = (
    exploded.groupby("genres")
    .agg(
        total_games=("name", "count"),
        indie_games=("is_indie", "sum")
    )
)

# Compute non‑indie and percentages
genre_stats["non_indie_games"] = genre_stats["total_games"] - genre_stats["indie_games"]
genre_stats["indie_percentage"] = (
    genre_stats["indie_games"] / genre_stats["total_games"] * 100
)

# Sort by total games
genre_stats = genre_stats.sort_values("total_games", ascending=False)

show_indie_overlay = st.toggle("Show Indie Games Overlay")

fig = go.Figure()

if show_indie_overlay:
    # ORANGE FIRST — Indie Games (bottom of stack)
    fig.add_trace(go.Bar(
        x=genre_stats.index,
        y=genre_stats["indie_games"],
        name="Indie Games",
        marker_color="#f39c12",
        customdata=np.stack([
            genre_stats["total_games"],
            genre_stats["indie_games"],
            genre_stats["non_indie_games"],
            genre_stats["indie_percentage"]
        ], axis=-1),
        hovertemplate=(
            "<b>%{x}</b><br><br>"
            "Total Games: %{customdata[0]}<br>"
            "Indie Games: %{customdata[1]}<br>"
            "Non‑Indie Games: %{customdata[2]}<br>"
            "Indie %: %{customdata[3]:.1f}%<extra></extra>"
        )
    ))

    # BLUE SECOND — Non‑Indie Games (top of stack)
    fig.add_trace(go.Bar(
        x=genre_stats.index,
        y=genre_stats["non_indie_games"],
        name="Non‑Indie Games",
        marker_color="#1f77b4",
        customdata=np.stack([
            genre_stats["total_games"],
            genre_stats["indie_games"],
            genre_stats["non_indie_games"],
            genre_stats["indie_percentage"]
        ], axis=-1),
        hovertemplate=(
            "<b>%{x}</b><br><br>"
            "Total Games: %{customdata[0]}<br>"
            "Indie Games: %{customdata[1]}<br>"
            "Non‑Indie Games: %{customdata[2]}<br>"
            "Indie %: %{customdata[3]:.1f}%<extra></extra>"
        )
    ))

else:
    # DEFAULT VIEW — ALL GAMES (blue only)
    fig.add_trace(go.Bar(
        x=genre_stats.index,
        y=genre_stats["total_games"],
        name="All Games",
        marker_color="#1f77b4",
        customdata=np.stack([
            genre_stats["total_games"],
            genre_stats["indie_games"],
            genre_stats["non_indie_games"],
            genre_stats["indie_percentage"]
        ], axis=-1),
        hovertemplate=(
            "<b>%{x}</b><br><br>"
            "Total Games: %{customdata[0]}<br>"
            "Indie Games: %{customdata[1]}<br>"
            "Non‑Indie Games: %{customdata[2]}<br>"
            "Indie %: %{customdata[3]:.1f}%<extra></extra>"
        )
    ))

fig.update_layout(
    xaxis_title="Genre",
    yaxis_title="Number of Games",
    title="Most Common Genres",
    barmode="stack" if show_indie_overlay else "group",
    height=600
)

st.plotly_chart(fig, use_container_width=True)


# VISUALIZATION 3 — Indie Market Share Over Time
st.subheader("Indie Market Share Over Time")

genre_filtered_df = df.copy()

if selected_genre != "ALL":
    genre_filtered_df = genre_filtered_df[
        genre_filtered_df["genres"].apply(lambda g: selected_genre in g)
    ]

yearly = (
    genre_filtered_df
    .groupby("release_year")["is_indie"]
    .mean()
    .reset_index()
)

yearly["is_indie"] *= 100

fig_indieshare = px.line(
    yearly,
    x="release_year",
    y="is_indie",
    title=f"Indie Market Share (%) by Year — Genre: {selected_genre}"
)

fig_indieshare.update_layout(
    xaxis_title="Release Year",
    yaxis_title="Indie Market Share"
)

st.plotly_chart(fig_indieshare, use_container_width=True)


# VISUALIZATION 4 — Price vs Recommendation Count
st.subheader("Price vs Recommendation Count")

scatter_df = filtered_df.copy()

scatter_df["recommendations"] = pd.to_numeric(
    scatter_df["recommendations"], errors="coerce"
).fillna(0)

scatter_df = scatter_df[scatter_df["recommendations"] > 0]

scatter_df["price"] = scatter_df["price"].clip(upper=100)

if scatter_df.empty:
    st.warning("No games available for the selected filters.")
else:
    fig_price_rec = px.scatter(
        scatter_df,
        x="price",
        y="recommendations",
        color="is_indie",
        color_discrete_map={
            True: "#f39c12",  # Indie = orange
            False: "#1f77b4"  # Non‑indie = blue
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