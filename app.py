import streamlit as st
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta, date

# ==========================================
# 1. MULTI-API SERVICES
# ==========================================
class OddsAPIService:
    """Primary source for betting odds (Required for Accumulator)."""
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

class FootballDataService:
    """Deep football fixtures and stats from football-data.org"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"X-Auth-Token": self.api_key}

    def get_upcoming_matches(self, competition_code: str, days: int = 7) -> List[Dict[str, Any]]:
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=days)).isoformat()
        url = f"{self.base_url}/competitions/{competition_code}/matches?dateFrom={today}&dateTo={future}&status=SCHEDULED"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("matches", [])
        except Exception:
            pass
        return []

class BalldontlieService:
    """Deep basketball fixtures and stats from balldontlie.io"""
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://www.balldontlie.io/api/v1"
        self.headers = {"Authorization": self.api_key} if self.api_key else {}

    def get_upcoming_games(self, days: int = 7) -> List[Dict[str, Any]]:
        # Balldontlie requires specific dates. We'll fetch today and the next few days.
        all_games = []
        for i in range(days):
            target_date = (date.today() + timedelta(days=i)).isoformat()
            url = f"{self.base_url}/games?dates[]={target_date}&per_page=100"
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    # Filter for future games
                    for game in data:
                        if game["status"] == "Scheduled":
                            all_games.append(game)
            except Exception:
                pass
        return all_games

# ==========================================
# 2. PROBABILITY FILTER (Win + Over/Under)
# ==========================================
class ProbabilityFilter:
    MIN_CONFIDENCE = 70.0

    @staticmethod
    def implied_prob(odds: float) -> float:
        return 1.0 / odds if odds and odds > 1.0 else 0.0

    @classmethod
    def extract_best_selection(cls, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        best_overall = None
        best_conf = 0

        for bm in match.get("bookmakers", []):
            for market in bm.get("markets", []):
                m_key = market.get("key")
                outcomes = market.get("outcomes", [])

                if m_key == "h2h" and len(outcomes) >= 2:
                    probs = [{"name": o["name"], "odds": o["price"], "raw": cls.implied_prob(o["price"])} for o in outcomes]
                    total = sum(p["raw"] for p in probs)
                    if total > 0:
                        for p in probs: p["conf"] = (p["raw"] / total) * 100.0
                        best = max(probs, key=lambda p: p["conf"])
                        if best["conf"] > best_conf:
                            best_conf = best["conf"]
                            best_overall = {"selection": f"{best['name']} Win", "odds": best["odds"], "confidence": round(best["conf"], 1)}

                elif m_key == "totals" and len(outcomes) == 2:
                    point = market.get("point")
                    if not point: continue
                    over_outcome = next((o for o in outcomes if o["name"] == "Over"), None)
                    under_outcome = next((o for o in outcomes if o["name"] == "Under"), None)
                    
                    if over_outcome and under_outcome:
                        p_over = cls.implied_prob(over_outcome["price"])
                        p_under = cls.implied_prob(under_outcome["price"])
                        total = p_over + p_under
                        if total > 0:
                            conf_over = (p_over / total) * 100.0
                            conf_under = (p_under / total) * 100.0
                            if conf_over > best_conf:
                                best_conf = conf_over
                                best_overall = {"selection": f"Over {point}", "odds": over_outcome["price"], "confidence": round(conf_over, 1)}
                            if conf_under > best_conf:
                                best_conf = conf_under
                                best_overall = {"selection": f"Under {point}", "odds": under_outcome["price"], "confidence": round(conf_under, 1)}
        return best_overall

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
                "Leg": i, "Slip": slip_type, "Sport": r["Sport"], "League": r["League"],
                "Match": r["Match"], "Selection": r["Selection"], "Odds": round(r["Odds"], 2),
                "Confidence": r["Confidence"], "Kickoff (UTC)": r["Kickoff"],
            })

        df = pd.DataFrame(rows)
        combined_odds = 1.0
        for r in ranked: combined_odds *= r["Odds"]
        df.attrs["combined_odds"] = round(combined_odds, 2)
        df.attrs["avg_confidence"] = round(sum(r["_conf"] for r in ranked) / max(len(ranked), 1), 1)
        return df

# ==========================================
# 4. STREAMLIT APP UI
# ==========================================
st.set_page_config(page_title="Global Multi-Sport Accumulator & Data Hub", layout="wide", page_icon="⚽")

st.title("⚡ Global Multi-Sport Data Hub & Accumulator Machine")
st.caption("Powered by The Odds API, Football-Data.org, and Balldontlie.io")

st.sidebar.header("🔑 API Credentials")
odds_api_key = st.sidebar.text_input("The Odds API Key", type="password", value=st.secrets.get("ODDS_API_KEY", ""))
football_api_key = st.sidebar.text_input("Football-Data.org Key", type="password", value=st.secrets.get("FOOTBALL_DATA_API_KEY", ""))
basketball_api_key = st.sidebar.text_input("Balldontlie.io Key (Optional)", type="password", value=st.secrets.get("BALLDONTLIE_API_KEY", ""))

st.sidebar.header("⚙️ Accumulator Settings")
min_confidence = st.sidebar.slider("Min Confidence (%)", 50, 95, 70)

# League Catalog for Odds API
ODDS_CATALOG = {
    "Football": [
        {"key": "soccer_epl", "title": "English Premier League"},
        {"key": "soccer_spain_la_liga", "title": "Spanish La Liga"},
        {"key": "soccer_italy_serie_a", "title": "Italian Serie A"},
        {"key": "soccer_germany_bundesliga", "title": "German Bundesliga"},
        {"key": "soccer_france_ligue_one", "title": "French Ligue 1"},
        {"key": "soccer_uefa_champs_league", "title": "UEFA Champions League"},
    ],
    "Basketball": [
        {"key": "basketball_nba", "title": "NBA"},
        {"key": "basketball_euroleague", "title": "EuroLeague"},
        {"key": "basketball_spain_acb", "title": "Liga ACB"},
    ]
}

# Football-Data.org Competition Codes
FOOTBALL_COMPETITIONS = {
    "English Premier League": "PL", "Spanish La Liga": "PD", "Italian Serie A": "SA",
    "German Bundesliga": "BL1", "French Ligue 1": "FL1", "UEFA Champions League": "CL"
}

tabs = st.tabs([
    "📅 Accumulator Builder (Odds API)", 
    "⚽ Football Fixtures (Football-Data.org)", 
    "🏀 Basketball Fixtures (Balldontlie)"
])

# --- TAB 0: ACCUMULATOR BUILDER ---
with tabs[0]:
    st.header("Build 20-Leg Accumulator (Requires Odds API)")
    selected_sport = st.radio("Sport", ["Football", "Basketball"], horizontal=True)
    selected_leagues = st.multiselect("Select Leagues to Scan", [e["title"] for e in ODDS_CATALOG[selected_sport]], default=[ODDS_CATALOG[selected_sport][0]["title"]])
    
    if st.button("Build Accumulator Slip", type="primary"):
        if not odds_api_key:
            st.error("Please add your ODDS_API_KEY in the sidebar.")
        elif not selected_leagues:
            st.warning("Select at least one league.")
        else:
            with st.spinner("Scanning live odds markets..."):
                api = OddsAPIService(odds_api_key)
                data = []
                for title in selected_leagues:
                    key = next(e["key"] for e in ODDS_CATALOG[selected_sport] if e["title"] == title)
                    fixtures = api.get_fixtures_and_odds(key)
                    data.append({"sport": selected_sport, "league": title, "fixtures": fixtures})
                
                df = AccumulatorBuilder.build_live_accumulator(data, slip_type="Multi-Sport", min_confidence=min_confidence, hours_window=168.0)
                
                if df.empty:
                    st.warning("No fixtures met the confidence threshold. Try lowering the slider or adding more leagues.")
                else:
                    st.success(f"✅ Built {len(df)}-leg accumulator from real odds!")
                    st.dataframe(df, use_container_width=True)
                    c1, c2 = st.columns(2)
                    c1.metric("Avg Confidence", f"{df.attrs['avg_confidence']}%")
                    c2.metric("Combined Odds", f"{df.attrs['combined_odds']}x")

# --- TAB 1: FOOTBALL FIXTURES ---
with tabs[1]:
    st.header("⚽ Deep Football Fixtures & Stats")
    if not football_api_key:
        st.info("Enter your Football-Data.org API key in the sidebar to view detailed fixtures.")
    else:
        fb_service = FootballDataService(football_api_key)
        comp_choice = st.selectbox("Select Competition", list(FOOTBALL_COMPETITIONS.keys()))
        comp_code = FOOTBALL_COMPETITIONS[comp_choice]
        
        if st.button("Load Football Fixtures"):
            with st.spinner("Fetching from football-data.org..."):
                matches = fb_service.get_upcoming_matches(comp_code, days=7)
            
            if not matches:
                st.warning("No upcoming matches found for this competition in the next 7 days.")
            else:
                st.success(f"Found {len(matches)} upcoming matches")
                rows = []
                for m in matches:
                    rows.append({
                        "Date": m["utcDate"][:10],
                        "Time": m["utcDate"][11:16] + " UTC",
                        "Home": m["homeTeam"]["name"],
                        "Away": m["awayTeam"]["name"],
                        "Venue": m["venue"],
                        "Matchday": m["matchday"]
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

# --- TAB 2: BASKETBALL FIXTURES ---
with tabs[2]:
    st.header("🏀 Deep Basketball Fixtures (NBA / NCAA)")
    if st.button("Load Basketball Fixtures"):
        with st.spinner("Fetching from balldontlie.io..."):
            bb_service = BalldontlieService(basketball_api_key)
            games = bb_service.get_upcoming_games(days=7)
        
        if not games:
            st.warning("No upcoming games found in the next 7 days.")
        else:
            st.success(f"Found {len(games)} upcoming games")
            rows = []
            for g in games:
                rows.append({
                    "Date": g["date"][:10],
                    "Time": g["time"],
                    "Home Team": g["home_team"]["full_name"],
                    "Away Team": g["visitor_team"]["full_name"],
                    "League": "NBA" if g["season"] >= 2000 else "NCAA", # Simplified
                    "Status": g["status"]
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)