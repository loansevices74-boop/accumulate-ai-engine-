import streamlit as st
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import concurrent.futures
import re

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================

ST_PAGE_TITLE = "⚡ Real-Odds Accumulator Generator"
DEFAULT_SPORTS = [
    ("soccer_epl", "Football - EPL"),
    ("soccer_la_liga", "Football - La Liga"),
    ("soccer_bundesliga_germany", "Football - Bundesliga"),
    ("basketball_nba", "Basketball - NBA"),
    ("tennis_atp_us_open", "Tennis - ATP US Open") # Example, adjust keys as per your plan
]

# ==========================================
# 1. SERVICE CLASSES (REAL DATA ONLY)
# ==========================================

class OddsAPIService:
    """Handles fetching and processing REAL betting odds from The Odds API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    def fetch_sports_odds(self, sport_key: str, regions: str = "eu,us", markets: str = "h2h,totals") -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/{sport_key}/odds/"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 429:
                st.warning(f"Rate limit hit for {sport_key}. Please wait or upgrade plan.")
                return []
            else:
                st.error(f"API Error ({res.status_code}) for {sport_key}: {res.text[:100]}")
                return []
        except Exception as e:
            st.error(f"Connection failed for {sport_key}: {str(e)}")
            return []

class FixtureDiscoveryService:
    """
    Placeholder for other APIs (Football-Data.org, etc.).
    NOTE: These do NOT provide betting odds. 
    They are only useful if you have a separate statistical model to predict odds.
    For this app, we rely primarily on The Odds API for actual money-line data.
    """
    pass 

# ==========================================
# 2. ACCUMULATION ENGINE (MATH & LOGIC)
# ==========================================

class AccumulatorEngine:

    @staticmethod
    def normalize_team_name(name: str) -> str:
        """Removes common suffixes/prefixes to help with deduplication."""
        name = name.lower().strip()
        # Remove common words like FC, CF, SC, Club, Team
        name = re.sub(r'\b(fc|cf|sc|club|team)\b', '', name)
        # Remove extra spaces
        name = ' '.join(name.split())
        return name

    @staticmethod
    def calc_vig_removed_prob(outcomes: List[Dict]) -> List[Dict]:
        """
        Calculates the 'Fair Probability' by removing the bookmaker's margin (vig).
        Formula: P_fair(i) = (1/Odds_i) / Sum(1/Odds_j for all j)
        """
        if not outcomes:
            return []
        
        raw_probs = []
        total_raw = 0.0
        
        for o in outcomes:
            price = float(o.get('price', 0))
            if price <= 1.0: continue
            
            inv_price = 1.0 / price
            raw_probs.append({'name': o['name'], 'odds': price, 'inv': inv_price})
            total_raw += inv_price
        
        if total_raw == 0:
            return []

        normalized = []
        for rp in raw_probs:
            fair_prob = (rp['inv'] / total_raw) * 100.0
            normalized.append({
                'name': rp['name'],
                'odds': round(rp['odds'], 2),
                'fair_prob': round(fair_prob, 1)
            })
            
        return normalized

    @classmethod
    def process_match_data(cls, raw_matches: List[Dict], sport_name: str, hours_window: float) -> List[Dict]:
        parsed_candidates = []
        now = datetime.now(timezone.utc)
        cutoff_time = now + timedelta(hours=hours_window)

        for m in raw_matches:
            commence_str = m.get("commence_time", "")
            try:
                # Parse ISO date string safely
                dt = datetime.fromisoformat(commence_str.replace("Z", "+00:00"))
                
                # Filter by time window
                if dt < now or dt > cutoff_time:
                    continue
                    
                kickoff_display = dt.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                continue

            home_raw = m.get("home_team", "Unknown Home")
            away_raw = m.get("away_team", "Unknown Away")
            
            # Normalize for display and matching
            home_norm = cls.normalize_team_name(home_raw)
            away_norm = cls.normalize_team_name(away_raw)
            match_id = f"{home_norm} vs {away_norm}"
            
            league_title = m.get("sport_title", sport_name)

            # Process Bookmakers to find best prices and aggregate stats
            # We want the BEST price available across all bookies for each outcome
            aggregated_outcomes = {} # Key: Outcome Name, Value: Best Price

            for bm in m.get("bookmakers", []):
                for market in bm.get("markets", []):
                    m_key = market.get("key")
                    
                    # Focus on H2H (Winner) and Totals (Over/Under)
                    if m_key not in ["h2h", "totals"]:
                        continue
                        
                    point = market.get("point") # For totals
                    outcomes = market.get("outcomes", [])
                    
                    for o in outcomes:
                        o_name = o["name"]
                        o_price = float(o["price"])
                        
                        # Create a unique key for aggregation
                        # For Totals, include the line (e.g., "Over 2.5")
                        agg_key = f"{o_name}_{point}" if point else o_name
                        
                        if agg_key not in aggregated_outcomes or o_price > aggregated_outcomes[agg_key]["price"]:
                            aggregated_outcomes[agg_key] = {
                                "name": o_name,
                                "price": o_price,
                                "type": m_key,
                                "point": point
                            }

            # Now convert aggregated best prices into candidates
            # Group by Market Type to calculate Vig properly? 
            # Actually, standard practice is to take the single best leg from the whole match.
            # Let's evaluate each distinct outcome independently first.
            
            final_candidates_for_match = []
            
            for agg_key, data in aggregated_outcomes.items():
                # To get Fair Prob, we need ALL outcomes for that specific market instance.
                # Since we aggregated across bookies, we lost the context of "which outcomes belong together".
                # STRATEGY CHANGE: Instead of aggregating across ALL bookies immediately,
                # let's pick the SINGLE BEST BOOKMAKER for this match to ensure consistent vig calculation,
                # OR iterate through each bookmaker's market individually.
                
                # Better Approach for Accuracy: Iterate through original raw matches again per bookmaker?
                # No, too slow. Let's stick to the previous logic but refine it.
                # We will calculate confidence based on the specific market structure found in the FIRST valid bookmaker entry
                # to keep the "Vig Removal" mathematically sound within one set of odds.
                pass 
            
            # RE-EVALUATION FOR SIMPLICITY AND CORRECTNESS:
            # It is hard to remove vig correctly when mixing odds from different books because lines differ.
            # Solution: Pick the top 3 most popular bookmakers (highest trust) and average their H2H odds, 
            # then remove vig from that average. Or simpler: Just use the Highest Available Odds for the Favorite.
            
            # Let's simplify: Find the favorite (lowest odds) in H2H and Over/Under in Totals.
            
            h2h_best = None
            totals_best = None
            
            for bm in m.get("bookmakers", []):
                for market in bm.get("markets", []):
                    if market.get("key") == "h2h":
                        outcomes = market.get("outcomes", [])
                        probs = cls.calc_vig_removed_prob(outcomes)
                        if probs:
                            # Get highest probability selection
                            fav = max(probs, key=lambda x: x['fair_prob'])
                            # Keep track of the absolute best odds/prob combo seen so far for this match
                            if h2h_best is None or fav['fair_prob'] > h2h_best['fair_prob']:
                                h2h_best = {
                                    "selection": fav['name'],
                                    "odds": fav['odds'],
                                    "confidence": fav['fair_prob'],
                                    "market": "H2H"
                                }
                                
                    elif market.get("key") == "totals":
                        outcomes = market.get("outcomes", [])
                        point = market.get("point")
                        if len(outcomes) == 2 and point:
                            # Calculate prob for Over specifically as it's usually the bet people look for
                            over_o = next((o for o in outcomes if o["name"] == "Over"), None)
                            under_o = next((o for o in outcomes if o["name"] == "Under"), None)
                            
                            if over_o and under_o:
                                # Simple binary normalization for totals
                                p_over = 1.0 / float(over_o["price"])
                                p_under = 1.0 / float(under_o["price"])
                                tot_p = p_over + p_under
                                fair_over = (p_over / tot_p) * 100.0
                                
                                candidate = {
                                    "selection": f"Over {point}",
                                    "odds": round(float(over_o["price"]), 2),
                                    "confidence": round(fair_over, 1),
                                    "market": "Totals"
                                }
                                
                                if totals_best is None or candidate['confidence'] > totals_best['confidence']:
                                    totals_best = candidate

            # Add best options to global list
            if h2h_best:
                parsed_candidates.append({
                    "Sport": sport_name,
                    "League": league_title,
                    "Match": f"{home_raw} vs {away_raw}",
                    "Selection": h2h_best['selection'],
                    "Odds": h2h_best['odds'],
                    "Confidence": h2h_best['confidence'],
                    "Kickoff": kickoff_display,
                    "Type": "Winner"
                })
                
            if totals_best:
                parsed_candidates.append({
                    "Sport": sport_name,
                    "League": league_title,
                    "Match": f"{home_raw} vs {away_raw}",
                    "Selection": totals_best['selection'],
                    "Odds": totals_best['odds'],
                    "Confidence": totals_best['confidence'],
                    "Kickoff": kickoff_display,
                    "Type": "Goals/Points"
                })

        return parsed_candidates

# ==========================================
# 3. STREAMLIT APP UI
# ==========================================

st.set_page_config(page_title=ST_PAGE_TITLE, layout="wide", page_icon="🎲")

st.title(ST_PAGE_TITLE)
st.caption("Generates high-value accumulators using real-time market data from The Odds API.")

# --- Sidebar Configuration ---
st.sidebar.header("🔑 API Configuration")

# Try loading from secrets first, fallback to manual input
default_odds_key = st.secrets.get("ODDS_API_KEY", "")

odds_api_key = st.sidebar.text_input(
    "The Odds API Key", 
    value=default_odds_key, 
    type="password",
    help="Get a free key at the-odds-api.com"
)

if not odds_api_key:
    st.sidebar.warning("⚠️ Enter an API Key to enable data fetching.")

# Filters
col_filt1, col_filt2 = st.sidebar.columns([1, 1])
with col_filt1:
    min_conf = st.number_input("Min Fair Prob (%)", min_value=50, max_value=95, value=70, step=1)
with col_filt2:
    min_odds = st.number_input("Min Decimal Odds", min_value=1.01, max_value=5.0, value=1.20, step=0.05)

time_window_hours = st.sidebar.selectbox(
    "Time Window",
    options=[{"label": "Next 24 Hours", "val": 24}, {"label": "Next 48 Hours", "val": 48}, {"label": "Next 7 Days", "val": 168}],
    index=1,
    format_func=lambda x: x["label"]
)["val"]

# Select Sports dynamically based on what user wants (simplified here to main ones)
selected_sports_keys = st.sidebar.multiselect(
    "Select Leagues/Sports",
    options=[k for k, v in DEFAULT_SPORTS],
    default=["soccer_epl", "basketball_nba"],
    format_func=lambda x: dict(DEFAULT_SPORTS)[x]
)

# --- Main Logic ---

def run_generation():
    if not odds_api_key:
        st.error("Please enter your The Odds API Key in the sidebar.")
        return
    
    if not selected_sports_keys:
        st.error("Please select at least one sport/league.")
        return

    all_candidates = []
    
    # Spinner for parallel execution
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Define tasks for ThreadPool
    def fetch_task(sport_key, sport_name):
        service = OddsAPIService(odds_api_key)
        raw_data = service.fetch_sports_odds(sport_key)
        processed = AccumulatorEngine.process_match_data(raw_data, sport_name, time_window_hours)
        return processed

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected_sports_keys)) as executor:
        # Submit all tasks
        for s_key in selected_sports_keys:
            s_name = dict(DEFAULT_SPORTS)[s_key]
            future = executor.submit(fetch_task, s_key, s_name)
            futures.append(future)
            
        # Collect results as they complete
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                all_candidates.extend(result)
                completed_count += 1
                progress_bar.progress(completed_count / len(futures))
            except Exception as exc:
                st.error(f"A task generated an exception: {exc}")

    status_text.empty()
    progress_bar.empty()

    if not all_candidates:
        st.info("No fixtures found matching criteria in the selected timeframe.")
        return

    # --- Post-Processing: Filter, Dedupe, Rank ---
    
    df_all = pd.DataFrame(all_candidates)
    
    # 1. Filter by Confidence and Odds
    df_filtered = df_all[
        (df_all['Confidence'] >= min_conf) & 
        (df_all['Odds'] >= min_odds)
    ].copy()
    
    if df_filtered.empty:
        st.warning(f"No selections met the criteria (Min Conf: {min_conf}%, Min Odds: {min_odds}). Try lowering thresholds.")
        return

    # 2. Deduplicate Matches
    # Strategy: If two picks come from the same match, keep the one with higher Confidence.
    # Sort by Confidence descending, then drop duplicates keeping first occurrence of Match
    df_sorted = df_filtered.sort_values(by='Confidence', ascending=False)
    df_deduped = df_sorted.drop_duplicates(subset=['Match'], keep='first')
    
    # 3. Limit to Top 20 Legs
    top_20 = df_deduped.head(20)
    
    if top_20.empty:
        st.warning("Could not form a 20-leg accumulator with current filters.")
        return

    # --- Display Results ---
    
    st.success(f"✅ Generated Optimal {len(top_20)}-Leg Accumulator")
    
    # Calculate Metrics
    combined_odds = top_20['Odds'].prod()
    avg_confidence = top_20['Confidence'].mean()
    # Theoretical payout for $1 stake
    potential_return = combined_odds 
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Legs", len(top_20))
    c2.metric("Combined Odds", f"{combined_odds:.2f}x")
    c3.metric("Avg Fair Prob", f"{avg_confidence:.1f}%")
    c4.metric("$1 Stake Return", f"${potential_return:.2f}")

    # Format DataFrame for display
    display_df = top_20[['Sport', 'League', 'Match', 'Selection', 'Odds', 'Confidence', 'Kickoff']].copy()
    display_df['Confidence'] = display_df['Confidence'].apply(lambda x: f"{x:.1f}%")
    display_df['Odds'] = display_df['Odds'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download Button
    csv = top_20.to_csv(index=False)
    st.download_button(
        label="Download Slip (CSV)",
        data=csv,
        file_name=f"accumulator_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

    # Disclaimer
    st.markdown("""
    ---
    ⚠️ **Disclaimer**: 
    1. **Fair Probability ≠ Win Probability**: Calculated by removing bookmaker margins (vig). It represents market consensus, not guaranteed outcomes.
    2. **Gambling Risk**: Accumulators have low strike rates due to multiplication of risk. Never bet more than you can afford to lose.
    3. **Data Latency**: Odds change rapidly. Verify with your bookmaker before placing bets.
    """)

# Run App
if st.button("🚀 Generate Accumulator", type="primary"):
    run_generation()
else:
    st.info("Configure settings in the sidebar and click 'Generate Accumulator'.")