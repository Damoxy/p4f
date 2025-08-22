import streamlit as st
import requests
import pandas as pd
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
st.title("P4Fun FPL League Standings")

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
            team_name = manager.get('entry_name', 'Unknown Team')

            # Unique identifier = team + manager
            identifier = f"{team_name} ({manager_name})"

            history = fetch_player_history(manager_id)

            if history:
                for week in history.get('current', []):
                    gw = week.get('event')
                    points = week.get('points', 0)
                    month = gw_to_month.get(gw, "Unknown")

                    # --- Monthly scores ---
                    monthly_scores.setdefault(month, {})
                    monthly_scores[month][identifier] = monthly_scores[month].get(identifier, 0) + points

                    # --- Weekly scores ---
                    weekly_scores.setdefault(gw, {})
                    weekly_scores[gw][identifier] = points

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
        monthly_df = pd.DataFrame(
            {month: pd.Series(scores) for month, scores in monthly_scores.items()}
        ).fillna(0)

        st.subheader("Monthly Winners")
        for month in monthly_df.columns:
            top_scorer = monthly_df[month].idxmax()
            top_points = monthly_df[month].max()
            st.write(f"**{month}:** {top_scorer} ({top_points} points)")

        # -----------------------------
        # Monthly + Total Table
        # -----------------------------
        st.subheader("Monthly Points Table with Totals")

        # Add a "Total Points" column
        monthly_df["Total Points"] = monthly_df.sum(axis=1)

        # Sort entire table by Total Points (descending)
        sorted_monthly_df = monthly_df.sort_values("Total Points", ascending=False)

        st.dataframe(sorted_monthly_df)
