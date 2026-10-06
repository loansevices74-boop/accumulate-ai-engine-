import streamlit as st
import pandas as pd
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. MULTI-SPORT API SERVICE & FULL CATALOG
# ==========================================
class MultiSportsAPIService:
    def __init__(self, odds_api_key: str, football_data_api_key: str, balldontlie_api_key: str, allsports_api_key: str):
        self.odds_api_key = odds_api_key
        self.football_data_api_key = football_data_api_key
        self.balldontlie_api_key = balldontlie_api_key
        self.allsports_api_key = allsports_api_key

        self.odds_base_url = "https://api.the-odds-api.com/v4/sports"
        self.football_data_base_url = "https://api.football-data.org/v4/competitions"
        self.balldontlie_base_url = "https://api.balldontlie.io/v1/games"
        self.allsports_football_base_url = "https://v1.football.api-sports.io/fixtures"
        self.allsports_basketball_base_url = "https://v1.basketball.api-sports.io/games"

    def get_odds_api_data(self, sport_key: str, regions: str = "eu,us", markets: str = "h2h,totals") -> List[Dict[str, Any]]:
        if not self.odds_api_key:
            return []
        url = f"{self.odds_base_url}/{sport_key}/odds/?apiKey={self.odds_api_key}&regions={regions}&markets={markets}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    def get_allsports_data(self, sport: str, league_id: str) -> List[Dict[str, Any]]:
        if not self.allsports_api_key:
            return []
        base_url = self.allsports_football_base_url if sport == "Football" else self.allsports_basketball_base_url
        headers = {"x-apisports-key": self.allsports_api_key}
        current_year = datetime.now().year
        try:
            response = requests.get(f"{base_url}?league={league_id}&season={current_year}", headers=headers, timeout=10)
            if response.status_code == 200:
                raw_data = response.json().get("response", [])
                valid_statuses = ["NS", "TBD", "1H", "2H", "HT", "3Q", "4Q"]
                return [self._adapt_allsports_to_odds_format(match, sport) for match in raw_data if match.get("status", {}).get("short") in valid_statuses]
        except Exception:
            pass
        return []

    def _adapt_allsports_to_odds_format(self, match: Dict[str, Any], sport: str) -> Dict[str, Any]:
        home_team = match.get("teams", {}).get("home", {}).get("name", "Home")
        away_team = match.get("teams", {}).get("away", {}).get("name", "Away")
        commence_time = match.get("date", "").replace(" ", "T") + "Z"
        
        bookmakers = []
        for bm in match.get("bookmakers", []):
            bm_name = bm.get("name", "Unknown").lower().replace(" ", "_")
            markets = []
            for bet in bm.get("bets", []):
                bet_name = bet.get("name", "").lower()
                values = bet.get("values", [])
                
                if "winner" in bet_name or "match winner" in bet_name:
                    outcomes = []
                    for v in values:
                        val_name = v.get("value", "").lower()
                        price = float(v.get("odd", 0)) if v.get("odd") not in [None, ""] else 0.0
                        if price <= 1.0: continue
                        
                        if "home" in val_name:
                            outcomes.append({"name": home_team, "price": price})
                        elif "away" in val_name:
                            outcomes.append({"name": away_team, "price": price})
                        elif "draw" in val_name:
                            outcomes.append({"name": "Draw", "price": price})
                    
                    if outcomes:
                        markets.append({"key": "h2h", "outcomes": outcomes})
                        
                elif "goals" in bet_name or "over/under" in bet_name or "totals" in bet_name:
                    outcomes = []
                    point = None
                    for v in values:
                        val_name = v.get("value", "").lower()
                        price = float(v.get("odd", 0)) if v.get("odd") not in [None, ""] else 0.0
                        if price <= 1.0: continue
                        
                        if "over" in val_name:
                            outcomes.append({"name": "Over", "price": price})
                            nums = re.findall(r"\d+\.?\d*", val_name)
                            if nums: point = float(nums[0])
                        elif "under" in val_name:
                            outcomes.append({"name": "Under", "price": price})
                    
                    if outcomes and point:
                        markets.append({"key": "totals", "point": point, "outcomes": outcomes})
                        
            if markets:
                bookmakers.append({"key": bm_name, "title": bm.get("name"), "markets": markets})
                
        return {
            "home_team": home_team,
            "away_team": away_team,
            "commence_time": commence_time,
            "bookmakers": bookmakers
        }

    @staticmethod
    def get_global_league_catalog() -> Dict[str, List[Dict[str, str]]]:
        return {
            "Football": [
                {"key": "soccer_uefa_champs_league", "title": "UEFA Champions League", "category": "UEFA", "region": "Europe", "allsports_id": "2"},
                {"key": "soccer_uefa_europa_league", "title": "UEFA Europa League", "category": "UEFA", "region": "Europe", "allsports_id": "3"},
                {"key": "soccer_epl", "title": "English Premier League", "category": "Domestic", "region": "England", "allsports_id": "39"},
                {"key": "soccer_spain_la_liga", "title": "Spanish La Liga", "category": "Domestic", "region": "Spain", "allsports_id": "140"},
                {"key": "soccer_italy_serie_a", "title": "Italian Serie A", "category": "Domestic", "region": "Italy", "allsports_id": "135"},
                {"key": "soccer_germany_bundesliga", "title": "German Bundesliga", "category": "Domestic", "region": "Germany", "allsports_id": "78"},
                {"key": "soccer_france_ligue_one", "title": "French Ligue 1", "category": "Domestic", "region": "France", "allsports_id": "61"},
                {"key": "soccer_netherlands_eredivisie", "title": "Dutch Eredivisie", "category": "Domestic", "region": "Netherlands", "allsports_id": "88"},
                {"key": "soccer_portugal_primeira_liga", "title": "Portuguese Primeira Liga", "category": "Domestic", "region": "Portugal", "allsports_id": "94"},
                {"key": "soccer_usa_mls", "title": "Major League Soccer (MLS)", "category": "Domestic", "region": "USA/Canada", "allsports_id": "253"},
                {"key": "soccer_brazil_campeonato", "title": "Brazilian Serie A", "category": "Domestic", "region": "Brazil", "allsports_id": "71"},
                {"key": "soccer_argentina_primera_division", "title": "Argentine Primera Division", "category": "Domestic", "region": "Argentina", "allsports_id": "128"},
                {"key": "soccer_mexico_ligamx", "title": "Mexican Liga MX", "category": "Domestic", "region": "Mexico", "allsports_id": "262"},
            ],
            "Basketball": [
                {"key": "basketball_nba", "title": "NBA", "category": "Domestic", "region": "USA", "allsports_id": "12"},
                {"key": "basketball_wnba", "title": "WNBA", "category": "Domestic", "region": "USA", "allsports_id": "16"},
                {"key": "basketball_euroleague", "title": "EuroLeague Basketball", "category": "UEFA", "region": "Europe", "allsports_id": "120"},
                {"key": "basketball_spain_acb", "title": "Liga ACB", "category": "Domestic", "region": "Spain", "allsports_id": "118"},
            ]
        }

# ==========================================
# 2. PROBABILITY FILTER
# ==========================================
class ProbabilityFilter:
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
st.set_page_config(page_title="Global Multi-Sport 20-Leg Accumulator Machine", layout="wide", page_icon="")

# Title
st.title("⚡ Global Multi-Sport 20-Leg Accumulator Machine (>70% Probability)")
st.caption("Builds daily & weekly slips using all 4 API keys. (ODDS_API_KEY = FOOTBALL_DATA_API_KEY = BALLDONTLIE_API_KEY = ALLSPORTS_API_KEY = )")

# Sidebar
st.sidebar.header("⚙️ Configuration")
odds_api_key = st.sidebar.text_input("The Odds API Key", type="password", value=st.secrets.get("ODDS_API_KEY", ""))
football_data_api_key = st.sidebar.text_input("Football-Data.org API Key", type="password", value=st.secrets.get("FOOTBALL_DATA_API_KEY", ""))
balldontlie_api_key = st.sidebar.text_input("BallDontLie API Key", type="password", value=st.secrets.get("BALLDONTLIE_API_KEY", ""))
allsports_api_key = st.sidebar.text_input("AllSports (API-Sports) Key", type="password", value=st.secrets.get("ALLSPORTS_API_KEY", ""))

# API Status
st.sidebar.markdown("### 🔑 API Status")
if odds_api_key:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.error("❌ Missing")
st.sidebar.text("The Odds API (Primary)")

if football_data_api_key:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.warning("⚠️ Missing (Optional)")
st.sidebar.text("Football-Data.org")

if balldontlie_api_key:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.warning("⚠️ Missing (Optional)")
st.sidebar.text("BallDontLie")

if allsports_api_key:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.warning("️ Missing (Optional)")
st.sidebar.text("AllSports / API-Sports (Fallback)")

selected_sport = st.sidebar.radio("Select Sport View", ["Football", "Basketball"])
min_confidence = st.sidebar.slider("Minimum Confidence (%)", 50, 95, 70)

catalog = MultiSportsAPIService.get_global_league_catalog()
entries = catalog[selected_sport]

selected_leagues = st.sidebar.multiselect(
    "Leagues to scan",
    [e["title"] for e in entries],
    default=[e["title"] for e in entries[:3]]
)

def fetch_selected_leagues():
    api = MultiSportsAPIService(
        odds_api_key=odds_api_key,
        football_data_api_key=football_data_api_key,
        balldontlie_api_key=balldontlie_api_key,
        allsports_api_key=allsports_api_key
    )
    results = []
    bar = st.progress(0.0)
    
    for i, title in enumerate(selected_leagues):
        entry = next((e for e in entries if e["title"] == title), None)
        if not entry: continue
        
        fixtures = []
        if entry.get("key"):
            fixtures = api.get_odds_api_data(entry["key"])
            
        if not fixtures and entry.get("allsports_id"):
            fixtures = api.get_allsports_data(selected_sport, entry["allsports_id"])
            
        results.append({"sport": selected_sport, "league": title, "fixtures": fixtures})
        bar.progress((i + 1) / len(selected_leagues))
    bar.empty()
    return results

def build_slip(slip_type: str, hours: float):
    if not odds_api_key and not allsports_api_key:
        st.info("👉 Add at least `ODDS_API_KEY` or `ALLSPORTS_API_KEY` in Streamlit Secrets to load real fixtures with odds.")
        return
    if not selected_leagues:
        st.warning("Select at least one league in the sidebar.")
        return
    with st.spinner("Scanning real fixtures across multiple APIs (Win & Totals markets)..."):
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

# Tabs
tabs = st.tabs(["Daily Accumulator (48h)", "Weekly Accumulator (7 Days)"])

with tabs[0]:
    st.header("Daily Slip — Real Fixtures Kicking Off Within 48 Hours")
    if st.button("Build Today's Slip from Live Fixtures", type="primary"):
        build_slip("Daily", 48)

with tabs[1]:
    st.header("Weekly Slip — Real Fixtures Kicking Off Within 7 Days")
    if st.button("Build Weekly Slip from Live Fixtures", type="primary"):
        build_slip("Weekly", 168)