import pandas as pd
from typing import List, Dict, Any
from engine.predictor import ProbabilityFilter

class AccumulatorBuilder:
    """Daily & Weekly 20-Leg Slip Generator — built ONLY from real live fixtures."""

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