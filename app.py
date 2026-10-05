import streamlit as st
import pandas as pd
from engine.odds_api import OddsAPIService
from engine.accumulator import AccumulatorBuilder

st.set_page_config(page_title="Global Multi-Sport 20-Leg Accumulator Machine", layout="wide", page_icon="⚽")

st.title("⚡ Global Multi-Sport 20-Leg Accumulator Machine (>70% Probability)")
st.caption("Builds daily & weekly slips using ONLY real live fixtures from The Odds API.")

st.sidebar.header("⚙️ Configuration")
odds_api_key = st.sidebar.text_input("The Odds API Key", type="password", value=st.secrets.get("ODDS_API_KEY", ""))
selected_sport = st.sidebar.radio("Select Sport View", ["Football", "Basketball"])
min_confidence = st.sidebar.slider("Minimum Confidence (%)", 50, 95, 70)

catalog = OddsAPIService.get_global_league_catalog()
# Extend basketball coverage with USA leagues (real fixtures available in October)
catalog["Basketball"] = [
    {"key": "basketball_nba", "title": "NBA", "category": "Domestic", "region": "USA"},
    {"key": "basketball_wnba", "title": "WNBA", "category": "Domestic", "region": "USA"},
    {"key": "basketball_ncaab", "title": "NCAA Basketball", "category": "Domestic", "region": "USA"},
] + catalog["Basketball"]

entries = catalog[selected_sport]
default_titles = [e["title"] for e in entries[:6]]
selected_leagues = st.sidebar.multiselect(
    "Leagues to scan",
    [e["title"] for e in entries],
    default=default_titles
)
st.sidebar.caption("⚠️ Each league scanned consumes Odds API credits.")

def fetch_selected_leagues():
    api = OddsAPIService(odds_api_key)
    results = []
    bar = st.progress(0.0)
    for i, title in enumerate(selected_leagues):
        key = [e for e in entries if e["title"] == title][0]["key"]
        fixtures = api.get_fixtures_and_odds(key)
        results.append({"sport": selected_sport, "league": title, "fixtures": fixtures})
        bar.progress((i + 1) / len(selected_leagues))
    bar.empty()
    return results

def build_slip(slip_type: str, hours: float):
    if not odds_api_key:
        st.info(" Add your ODDS_API_KEY in Streamlit Secrets to load real fixtures.")
        return
    if not selected_leagues:
        st.warning("Select at least one league in the sidebar.")
        return
    with st.spinner("Scanning real fixtures..."):
        data = fetch_selected_leagues()
    df = AccumulatorBuilder.build_live_accumulator(
        data, slip_type=slip_type, min_confidence=min_confidence, hours_window=hours
    )
    if df.empty:
        st.warning("No real fixtures meet the confidence threshold in this window. Lower the confidence slider or add more leagues.")
    else:
        st.success(f"✅ {len(df)} real legs built from live fixtures")
        st.dataframe(df, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.metric("Avg Confidence", f"{df.attrs['avg_confidence']}%")
        c2.metric("Combined Odds", f"{df.attrs['combined_odds']}x")

tabs = st.tabs(["📅 Daily Accumulator (48h)", "📆 Weekly Accumulator (7 Days)", "🌍 Global League Directory"])

with tabs[0]:
    st.header("Daily Slip — Real Fixtures Kicking Off Within 48 Hours")
    if st.button("Build Today's Slip from Live Fixtures", type="primary"):
        build_slip("Daily", 48)

with tabs[1]:
    st.header("Weekly Slip — Real Fixtures Kicking Off Within 7 Days")
    if st.button("Build Weekly Slip from Live Fixtures", type="primary"):
        build_slip("Weekly", 168)

with tabs[2]:
    st.header("Global League Coverage Directory")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚽ Football Leagues (Europe, Americas, Asia, Oceania)")
        df_fb = pd.DataFrame(catalog["Football"])
        st.dataframe(df_fb[["title", "category", "region"]], use_container_width=True)
    with col2:
        st.subheader("🏀 Basketball Leagues (USA, Europe, Asia, Americas, Oceania)")
        df_bk = pd.DataFrame(catalog["Basketball"])
        st.dataframe(df_bk[["title", "category", "region"]], use_container_width=True)