# Steam Indie Market Dashboard

**Dashboard Link:** https://steamdashboard-imt561.streamlit.app/
**GitHub Repository:** https://github.com/jenna-klein/Steam_Dashboard

---

## Overview

This interactive dashboard provides indie game developers with data-driven insights to inform strategic business decisions about Steam game launches. The dashboard analyzes 65,455 games released on Steam between 2021 and 2025, focusing specifically on trends relevant to independent game development teams.

---

## Stakeholders

**Primary Stakeholder: Indie Game Development Teams**

Our stakeholders are small independent game development teams (typically 5-20 people) preparing to launch games on the Steam platform. These teams operate with constrained budgets and resources, making every product decision critical to their survival and growth. Unlike AAA studios, indie developers cannot afford expensive market research, prolonged development cycles, or failed launches.

**Stakeholder Needs:**

Indie development teams require data-driven insights to make strategic decisions about:
- Genre selection based on market saturation and growth trajectories
- Competitive pricing strategies that balance revenue with user acquisition
- Optimal release timing to maximize visibility and user engagement
- Feature prioritization based on correlation with player recommendations

---

## Dataset

**Steam Games Dataset 2021-2025**

The dataset contains comprehensive metadata for 65,455 games released on Steam between 2021 and 2025, collected using Steam's official API.

**Dataset includes:**
- Game identifiers (unique app IDs and names)
- Temporal data (release year and date)
- Classification (semicolon-separated genre and category tags)
- Pricing (current price in USD)
- Engagement metrics (user recommendation counts)
- Publishing data (developer and publisher information)

**Source:** [Kaggle - Steam Games Dataset 2021-2025](https://www.kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k)

**Key Transformation:** Games were classified as "indie" if the string "Indie" appeared within their semicolon-separated genres field, enabling comparative analysis between indie and non-indie titles.

---

## Context and Purpose

The dashboard addresses four critical strategic questions that indie developers must answer before launching a game on Steam:

1. **Market Saturation:** How has the indie game market evolved from 2021 to 2025? Is the market growing or becoming oversaturated?

2. **Genre Opportunities:** Which genres are growing fastest and which show the highest engagement rates? Where are the best opportunities for indie developers?

3. **Pricing Strategy:** What is the relationship between price and player recommendations? What price range optimizes both revenue potential and user engagement?

4. **Release Timing:** When is the optimal time to release a game to maximize visibility while avoiding high-competition periods?

The dashboard provides interactive visualizations and key performance indicators (KPIs) that allow stakeholders to explore these questions dynamically, filtering by year, genre, and price range to gain insights specific to their planned game concept.

---

## Dashboard Features

### Key Performance Indicators (KPIs)
- **Indie Market Share (%)**: Shows the proportion of indie games in the Steam marketplace
- **Fastest Growing Genre**: Identifies the genre with the highest growth rate with visual indicator
- **Median Indie Price**: Provides pricing benchmark for indie games

### Interactive Filters
- **Select Year**: Filter data by specific years (2021-2025) or view all years
- **Select Genre**: Filter by specific game genres or view all genres
- **Price Range**: Adjust price range using slider control

### Visualizations
1. **Monthly Release Counts by Year**: Bar chart showing release volume trends over time
2. **Top 10 Most Common Genres**: Bar chart displaying genre popularity by game count
3. **Indie Market Share Over Time**: Line chart tracking indie market proportion from 2021-2025
4. **Game Price vs Popularity**: Scatter plot with log scale showing the relationship between price and recommendations, differentiated by indie/non-indie status

---

## Key Insights

Based on our analysis of 65,455 Steam games from 2021-2025:

- **Market Share Stability**: Indie games maintain approximately 70% market share, indicating a healthy and consistent presence in the Steam marketplace
- **Market Growth**: Game releases increased 140% from 2021 to 2025, showing substantial market expansion
- **Pricing Patterns**: Median indie game price is $3.99, with most indie games priced under $10
- **Genre Trends**: Utilities shows the fastest growth at 333.3%, though genre popularity varies significantly
- **Weak Price Correlation**: Limited correlation between price and recommendations, suggesting quality and marketing matter more than pricing alone

---

## Team

**Project Team Members:**
- Jenna Klein
- Shelly Zhao
- Srijami Das

**Course:** IMT 561 - Data Visualization: Design & Development
**Institution:** University of Washington Ischool
**Quarter:** Winter 2026

---

## Acknowledgments

- Dataset provided by [Kaggle contributor](https://www.kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k)
