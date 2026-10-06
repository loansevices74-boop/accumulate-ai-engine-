import streamlit as st
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. ODDS API SERVICE & FULL CATALOG
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
                {"key": "soccer_uefa_champs_league", "title": "UEFA Champions League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_europa_league", "title": "UEFA Europa League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_europa_conference_league", "title": "UEFA Conference League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_nations_league", "title": "UEFA Nations League", "category": "International", "region": "Europe"},
                {"key": "soccer_epl", "title": "English Premier League", "category": "Domestic", "region": "England"},
                {"key": "soccer_efl_champ", "title": "EFL Championship", "category": "Domestic", "region": "England"},
                {"key": "soccer_spain_la_liga", "title": "Spanish La Liga", "category": "Domestic", "region": "Spain"},
                {"key": "soccer_spain_segunda_division", "title": "Spanish Segunda Division", "category": "Domestic", "region": "Spain"},
                {"key": "soccer_italy_serie_a", "title": "Italian Serie A", "category": "Domestic", "region": "Italy"},
                {"key": "soccer_italy_serie_b", "title": "Italian Serie B", "category": "Domestic", "region": "Italy"},
                {"key": "soccer_germany_bundesliga", "title": "German Bundesliga", "category": "Domestic", "region": "Germany"},
                {"key": "soccer_germany_bundesliga2", "title": "German 2. Bundesliga", "category": "Domestic", "region": "Germany"},
                {"key": "soccer_france_ligue_one", "title": "French Ligue 1", "category": "Domestic", "region": "France"},
                {"key": "soccer_france_ligue_two", "title": "French Ligue 2", "category": "Domestic", "region": "France"},
                {"key": "soccer_netherlands_eredivisie", "title": "Dutch Eredivisie", "category": "Domestic", "region": "Netherlands"},
                {"key": "soccer_portugal_primeira_liga", "title": "Portuguese Primeira Liga", "category": "Domestic", "region": "Portugal"},
                {"key": "soccer_turkey_super_league", "title": "Turkish Super Lig", "category": "Domestic", "region": "Turkiye"},
                {"key": "soccer_belgium_first_div", "title": "Belgian Pro League", "category": "Domestic", "region": "Belgium"},
                {"key": "soccer_scotland_premiership", "title": "Scottish Premiership", "category": "Domestic", "region": "Scotland"},
                {"key": "soccer_greece_super_league", "title": "Greek Super League", "category": "Domestic", "region": "Greece"},
                {"key": "soccer_switzerland_superleague", "title": "Swiss Super League", "category": "Domestic", "region": "Switzerland"},
                {"key": "soccer_austria_bundesliga", "title": "Austrian Bundesliga", "category": "Domestic", "region": "Austria"},
                {"key": "soccer_denmark_superliga", "title": "Danish Superliga", "category": "Domestic", "region": "Denmark"},
                {"key": "soccer_norway_eliteserien", "title": "Norwegian Eliteserien", "category": "Domestic", "region": "Norway"},
                {"key": "soccer_sweden_allsvenskan", "title": "Swedish Allsvenskan", "category": "Domestic", "region": "Sweden"},
                {"key": "soccer_poland_ekstraklasa", "title": "Polish Ekstraklasa", "category": "Domestic", "region": "Poland"},
                {"key": "soccer_usa_mls", "title": "Major League Soccer (MLS)", "category": "Domestic", "region": "USA/Canada"},
                {"key": "soccer_argentina_primera_division", "title": "Argentine Primera Division", "category": "Domestic", "region": "Argentina"},
                {"key": "soccer_brazil_campeonato", "title": "Brazilian Serie A", "category": "Domestic", "region": "Brazil"},
                {"key": "soccer_mexico_ligamx", "title": "Mexican Liga MX", "category": "Domestic", "region": "Mexico"},
                {"key": "soccer_conmebol_copa_libertadores", "title": "Copa Libertadores", "category": "Continental", "region": "South America"},
                {"key": "soccer_concacaf_champions_league", "title": "CONCACAF Champions Cup", "category": "Continental", "region": "North America"},
                {"key": "soccer_japan_j_league", "title": "Japanese J1 League", "category": "Domestic", "region": "Japan"},
                {"key": "soccer_korea_kleague1", "title": "K League 1", "category": "Domestic", "region": "South Korea"},
                {"key": "soccer_australia_aleague", "title": "Australian A-League", "category": "Domestic", "region": "Australia"},
                {"key": "soccer_saudi_pro_league", "title": "Saudi Pro League", "category": "Domestic", "region": "Saudi Arabia"},
                {"key": "soccer_fifa_world_cup", "title": "FIFA World Cup", "category": "International", "region": "Global"},
                {"key": "soccer_conmebol_copa_america", "title": "Copa America", "category": "International", "region": "Americas"}
            ],
            "Basketball": [
                {"key": "basketball_nba", "title": "NBA", "category": "Domestic", "region": "USA"},
                {"key": "basketball_wnba", "title": "WNBA", "category": "Domestic", "region": "USA"},
                {"key": "basketball_ncaab", "title": "NCAA Basketball", "category": "Domestic", "region": "USA"},
                {"key": "basketball_euroleague", "title": "EuroLeague Basketball", "category": "UEFA", "region": "Europe"},
                {"key": "basketball_eurocup", "title": "EuroCup", "category": "UEFA", "region": "Europe"},
                {"key": "basketball_spain_acb", "title": "Liga ACB", "category": "Domestic", "region": "Spain"},
                {"key": "basketball_germany_bbl", "title": "Basketball Bundesliga (BBL)", "category": "Domestic", "region": "Germany"},
                {"key": "basketball_italy_lega_a", "title": "Lega Basket Serie A", "category": "Domestic", "region": "Italy"},
                {"key": "basketball_turkey_bsl", "title": "Basketbol Super Ligi", "category": "Domestic", "region": "Turkiye"},
                {"key": "basketball_france_lnb", "title": "LNB Pro A", "category": "Domestic", "region": "France"},
                {"key": "basketball_greece_basket_league", "title": "Greek Basket League", "category": "Domestic", "region": "Greece"},
                {"key": "basketball_brazil_nbb", "title": "Novo Basquete Brasil (NBB)", "category": "Domestic", "region": "Brazil"},
                {"key": "basketball_argentina_liga_nacional", "title": "Liga Nacional de Basquet", "category": "Domestic", "region": "Argentina"},
                {"key": "basketball_australia_nbl", "title": "Australian NBL", "category": "Domestic", "region": "Australia"},
                {"key": "basketball_china_cba", "title": "Chinese Basketball Association (CBA)", "category": "Domestic", "region": "China"},
                {"key": "basketball_japan_bleague", "title": "Japanese B.League", "category": "Domestic", "region": "Japan"},
                {"key": "basketball_korea_kbl", "title": "Korean Basketball League (KBL)", "category": "Domestic", "region": "South Korea"},
                {"key": "basketball_fiba_world_cup", "title": "FIBA World Cup", "category": "International", "region": "Global"}
            ]
        }

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
        """Scans all markets (h2h and totals) to find the single highest-confidence pick."""
        best_overall = None
        best_conf = 0

        for bm in match.get("bookmakers", []):
            for market in bm.get("markets", []):
                m_key = market.get("key")
                outcomes = market.get("outcomes", [])

                # --- Logic for Win Markets (1X2) ---
                if m_key == "h2h" and len(outcomes) >= 2:
                    probs = [{"name": o["name"], "odds": o["price"], "raw": cls.implied_prob(o["price"])} for o in outcomes]
                    total = sum(p["raw"] for p in probs)
                    if total > 0:
                        for p in probs: p["conf"] = (p["raw"] / total) * 100.0
                        best = max(probs, key=lambda p: p["conf"])
                        if best["conf"] > best_conf:
                            best_conf = best["conf"]
                            best_overall = {"selection": f"{best['name']} Win", "odds": best["odds"], "confidence": round(best["conf"], 1)}

                # --- Logic for Totals Markets (Over/Under) ---
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
                            
                            # Check Over
                            if conf_over > best_conf:
                                best_conf = conf_over
                                best_overall = {"selection": f"Over {point}", "odds": over_outcome["price"], "confidence": round(conf_over, 1)}
                            # Check Under
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
st.set_page_config(page_title="Global Multi-Sport 20-Leg Accumulator Machine", layout="wide", page_icon="⚽")

st.title("⚡ Global Multi-Sport 20-Leg Accumulator Machine (>70% Probability)")
st.caption("Builds daily & weekly slips using ONLY real live fixtures. Scans Win (1X2) and Over/Under markets.")

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
    with st.spinner("Scanning real fixtures (Win & Totals markets)..."):
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
        st.subheader(" Football Leagues (38 Leagues)")
        df_fb = pd.DataFrame(catalog["Football"])
        st.dataframe(df_fb[["title", "category", "region"]], use_container_width=True)
    with col2:
        st.subheader("🏀 Basketball Leagues (18 Leagues)")
        df_bk = pd.DataFrame(catalog["Basketball"])
        st.dataframe(df_bk[["title", "category", "region"]], use_container_width=True)