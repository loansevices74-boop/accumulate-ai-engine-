from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

class ProbabilityFilter:
    """>70% High-Probability Filter Engine (real odds based)."""

    MIN_CONFIDENCE = 70.0

    @staticmethod
    def parse_confidence(value: Any) -> float:
        if isinstance(value, str):
            return float(value.replace("%", "").strip())
        return float(value)

    @staticmethod
    def implied_prob(odds: float) -> float:
        return 1.0 / odds if odds and odds > 1.0 else 0.0

    @classmethod
    def extract_best_selection(cls, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extracts the bookmaker favorite from the h2h market with de-margined implied probability."""
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