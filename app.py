import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# -----------------------------
# Constants
# -----------------------------
LEAGUE_ID = 610588
FPL_LEAGUE_URL = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"

# -----------------------------
# Functions
# -----------------------------

@st.cache_data
def fetch_league_standings():
    """Fetch league standings from FPL API"""
    response = requests.get(FPL_LEAGUE_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch league data. Please try again later.")
        return None

@st.cache_data
def fetch_player_history(manager_id):
    """Fetch individual manager's history from FPL API"""
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data
def fetch_gameweek_dates():
    """Map gameweeks to month names"""
    response = requests.get(FPL_FIXTURES_URL)
    gw_to_month = {}
    if response.status_code == 200:
        fixtures = response.json()
        for fixture in fixtures:
            gw = fixture.get("event")
            date_str = fixture.get("kickoff_time")
            if gw and date_str:
                month = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%B")
                gw_to_month[gw] = month
    return gw_to_month

# -----------------------------
# Main Streamlit App
# -----------------------------
st.title("FPL League Standings")
#st.write(f"League ID: {LEAGUE_ID}")

# Fetch mapping of gameweeks to months
gw_to_month = fetch_gameweek_dates()

# Fetch league standings
data = fetch_league_standings()

if data:
    managers = data.get('standings', {}).get('results', [])
    if not managers:
        st.warning("No managers found in this league.")
    else:
        monthly_scores = {}
        weekly_scores = {}

        for manager in managers:
            manager_id = manager.get('entry')
            manager_name = manager.get('player_name', 'Unknown')
            history = fetch_player_history(manager_id)

            if history:
                for week in history.get('current', []):
                    gw = week.get('event')
                    points = week.get('points', 0)
                    month = gw_to_month.get(gw, "Unknown")

                    # --- Monthly scores ---
                    monthly_scores.setdefault(month, {})
                    monthly_scores[month][manager_name] = monthly_scores[month].get(manager_name, 0) + points

                    # --- Weekly scores ---
                    weekly_scores.setdefault(gw, {})
                    weekly_scores[gw][manager_name] = points

        # -----------------------------
        # Weekly winners
        # -----------------------------
        st.subheader("Weekly Winners")
        for gw in sorted(weekly_scores.keys()):
            week_data = weekly_scores[gw]
            top_scorer = max(week_data, key=week_data.get)
            top_points = week_data[top_scorer]
            st.write(f"**GW{gw}:** {top_scorer} ({top_points} points)")

        # -----------------------------
        # Monthly winners
        # -----------------------------
        monthly_df = pd.DataFrame({month: pd.Series(scores) for month, scores in monthly_scores.items()}).fillna(0)
        st.subheader("Monthly Winners")
        for month in monthly_df.columns:
            top_scorer = monthly_df[month].idxmax()
            top_points = monthly_df[month].max()
            st.write(f"**{month}:** {top_scorer} ({top_points} points)")

        # -----------------------------
        # Monthly table
        # -----------------------------
        st.subheader("Monthly Points Table")
        st.dataframe(monthly_df)

        # -----------------------------
        # Monthly trend plot
        # -----------------------------
        st.subheader("Monthly Points Trend")
        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_df.T.plot(kind='bar', ax=ax)
        ax.set_ylabel("Points")
        ax.set_xlabel("Month")
        ax.set_title("FPL Monthly Points by Manager")
        plt.xticks(rotation=45)
        st.pyplot(fig)

