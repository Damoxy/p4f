import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# League ID
LEAGUE_ID = 610588
FPL_LEAGUE_URL = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"


# Function to fetch league standings
def fetch_league_standings():
    response = requests.get(FPL_LEAGUE_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch league data. Please try again later.")
        return None


# Function to fetch player history
def fetch_player_history(manager_id):
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Function to fetch gameweek dates
def fetch_gameweek_dates():
    response = requests.get(FPL_FIXTURES_URL)
    if response.status_code == 200:
        fixtures = response.json()
        gw_to_month = {}
        for fixture in fixtures:
            gw = fixture["event"]
            date_str = fixture["kickoff_time"]
            if date_str:
                month = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%B")
                gw_to_month[gw] = month
        return gw_to_month
    return {}


# Fetch actual gameweek-to-month mapping
gw_to_month = fetch_gameweek_dates()

# Streamlit UI
st.title("FPL Monthly League Standings")
st.write("Fetching data for League ID:", LEAGUE_ID)

data = fetch_league_standings()
if data:
    managers = data['standings']['results']
    monthly_scores = {}

    for manager in managers:
        manager_id = manager['entry']
        manager_name = manager['player_name']
        history = fetch_player_history(manager_id)

        if history:
            for week in history['current']:
                gw = week['event']
                points = week['points']
                month = gw_to_month.get(gw, "Unknown")

                if month not in monthly_scores:
                    monthly_scores[month] = {}

                if manager_name not in monthly_scores[month]:
                    monthly_scores[month][manager_name] = 0

                monthly_scores[month][manager_name] += points

    # Convert to DataFrame
    monthly_df = {month: pd.Series(scores) for month, scores in monthly_scores.items()}
    monthly_df = pd.DataFrame(monthly_df).fillna(0)
    st.dataframe(monthly_df)

    # Plot
    st.subheader("Top Scorers by Month")
    for month in monthly_df.columns:
        top_scorer = monthly_df[month].idxmax()
        top_points = monthly_df[month].max()
        st.write(f"**{month}:** {top_scorer} ({top_points} points)")

    st.subheader("Monthly Points Trend")
    monthly_df.T.plot(kind='bar', figsize=(12, 6))
    st.pyplot(plt)
