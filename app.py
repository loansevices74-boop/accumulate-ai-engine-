import streamlit as st
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. ODDS API SERVICE
# ==========================================
class OddsAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    def get_fixtures_and_odds(self, sport_key: str, regions: str = "eu,us", markets: str = "h2h,totals") -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{sport_key}/odds/?apiKey={self.api_key}&regions={regions}&markets={markets}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    @staticmethod
    def get_global_league_catalog() -> Dict[str, List[Dict[str, str]]]:
        return {
            "Football": [
                {"key": "soccer_epl", "title": "English Premier League", "category": "Domestic", "region": "England"},
                {"key": "soccer_spain_la_liga", "title": "Spanish La Liga", "category": "Domestic", "region": "Spain"},
                {"key": "soccer_italy_serie_a", "title": "Italian Serie A", "category": "Domestic", "region": "Italy"},
                {"key": "soccer_germany_bundesliga", "title": "German Bundesliga", "category": "Domestic", "region": "Germany"},
                {"key": "soccer_france_ligue_one", "title": "French Ligue 1", "category": "Domestic", "region": "France"},
                {"key": "soccer_uefa_champs_league", "title": "UEFA Champions League", "category": "UEFA", "region": "Europe"},
            ],
            "Basketball": [
                {"key": "basketball_nba", "title": "NBA", "category": "Domestic", "region": "USA"},
                {"key": "basketball_euroleague", "title": "EuroLeague", "category": "UEFA", "region": "Europe"},
                {"key": "basketball_spain_acb", "title": "Liga ACB", "category": "Domestic", "region": "Spain"},
                {"key": "basketball_australia_nbl", "title": "Australian NBL", "category": "Domestic", "region": "Australia"},
            ]
        }

# ==========================================
# 2. PROBABILITY FILTER
# ==========================================
class ProbabilityFilter:
    MIN_CONFIDENCE = 70.0

    @staticmethod
    def implied_prob(odds: float) -> float:
        return 1.0 / odds if odds and odds > 1.0 else 0.0

    @classmethod
    def extract_best_selection(cls, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for bm in match.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                outcomes = market.get("outcomes", [])
                if len(outcomes) < 2:
                    continue
                probs = []
                for o in outcomes:
                    price = o.get("price", 0)
                    probs.append({"name": o.get("name", ""), "odds": price, "raw": cls.implied_prob(price)})
                total = sum(p["raw"] for p in probs)
                if total <= 0:
                    continue
                for p in probs:
                    p["conf"] = (p["raw"] / total) * 100.0
                best = max(probs, key=lambda p: p["conf"])
                return {
                    "selection": f"{best['name']} Win",
                    "odds": best["odds"],
                    "confidence": round(best["conf"], 1)
                }
        return None

    @staticmethod
    def within_window(commence_time: str, hours: float) -> bool:
        try:
            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            return dt <= datetime.now(timezone.utc) + timedelta(hours=hours)
        except Exception:
            return True

# ==========================================
# 3. ACCUMULATOR BUILDER
# ==========================================
class AccumulatorBuilder:
    TARGET_LEGS = 20

    @classmethod
    def build_live_accumulator(cls, league_fixtures: List[Dict[str, Any]], slip_type: str = "Daily",
                               min_confidence: float = 70.0, hours_window: float = 48.0) -> pd.DataFrame:
        candidates = []
        for item in league_fixtures:
            for match in item.get("fixtures", []):
                if not ProbabilityFilter.within_window(match.get("commence_time", ""), hours_window):
                    continue
                best = ProbabilityFilter.extract_best_selection(match)
                if not best or best["confidence"] < min_confidence:
                    continue
                candidates.append({
                    "Sport": item.get("sport", ""),
                    "League": item.get("league", ""),
                    "Match": f"{match.get('away_team', '')} @ {match.get('home_team', '')}",
                    "Selection": best["selection"],
                    "Odds": best["odds"],
                    "Confidence": f"{best['confidence']}%",
                    "_conf": best["confidence"],
                    "Kickoff": (match.get("commence_time") or "")[:16].replace("T", " "),
                })

        ranked = sorted(candidates, key=lambda c: c["_conf"], reverse=True)[:cls.TARGET_LEGS]

        rows = []
        for i, r in enumerate(ranked, 1):
            rows.append({
                "Leg": i,
                "Slip": slip_type,
                "Sport": r["Sport"],
                "League": r["League"],
                "Match": r["Match"],
                "Selection": r["Selection"],
                "Odds": round(r["Odds"], 2),
                "Confidence": r["Confidence"],
                "Kickoff (UTC)": r["Kickoff"],
            })

        df = pd.DataFrame(rows)
        combined_odds = 1.0
        for r in ranked:
            combined_odds *= r["Odds"]
        df.attrs["combined_odds"] = round(combined_odds, 2)
        df.attrs["avg_confidence"] = round(sum(r["_conf"] for r in ranked) / max(len(ranked), 1), 1)
        return df

# ==========================================
# 4. STREAMLIT APP UI
# ==========================================
st.set_page_config(page_title="Global Multi-Sport 20-Leg Accumulator Machine", layout="wide", page_icon="⚽")

st.title("⚡ Global Multi-Sport 20-Leg Accumulator Machine (>70% Probability)")
st.caption("Builds daily & weekly slips using ONLY real live fixtures from The Odds API.")

st.sidebar.header("⚙️ Configuration")
odds_api_key = st.sidebar.text_input("The Odds API Key", type="password", value=st.secrets.get("ODDS_API_KEY", ""))
selected_sport = st.sidebar.radio("Select Sport View", ["Football", "Basketball"])
min_confidence = st.sidebar.slider("Minimum Confidence (%)", 50, 95, 70)

catalog = OddsAPIService.get_global_league_catalog()
entries = catalog[selected_sport]

selected_leagues = st.sidebar.multiselect(
    "Leagues to scan",
    [e["title"] for e in entries],
    default=[e["title"] for e in entries[:3]]
)

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
        st.info("👉 Add your ODDS_API_KEY in Streamlit Secrets to load real fixtures.")
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

tabs = st.tabs(["📅 Daily Accumulator (48h)", "📆 Weekly Accumulator (7 Days)", " Global League Directory"])

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
        st.subheader("⚽ Football Leagues")
        df_fb = pd.DataFrame(catalog["Football"])
        st.dataframe(df_fb[["title", "category", "region"]], use_container_width=True)
    with col2:
        st.subheader("🏀 Basketball Leagues")
        df_bk = pd.DataFrame(catalog["Basketball"])
        st.dataframe(df_bk[["title", "category", "region"]], use_container_width=True)