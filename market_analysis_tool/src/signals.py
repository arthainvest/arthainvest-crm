"""Combine technical + fundamental verdicts into a single daily call per instrument."""
from __future__ import annotations

from dataclasses import dataclass

from config import THRESHOLDS
from src.fundamental import FundamentalVerdict
from src.technical import TechnicalVerdict


@dataclass
class Verdict:
    symbol: str
    market: str
    technical: TechnicalVerdict
    fundamental: FundamentalVerdict
    call: str
    alert: bool


def combine(symbol: str, market: str, tech: TechnicalVerdict, fund: FundamentalVerdict) -> Verdict:
    alert = abs(tech.score) >= THRESHOLDS.min_technical_score_alert

    if tech.label == "Bullish" and fund.label == "Healthy":
        call = "Likely up-move, and fundamentals support it"
    elif tech.label == "Bullish" and fund.label == "Caution":
        call = "Likely up-move short-term, but earnings quality is questionable - treat with caution"
    elif tech.label == "Bearish" and fund.label == "Caution":
        call = "Likely down-move, and weak fundamentals reinforce the risk"
    elif tech.label == "Bearish" and fund.label == "Healthy":
        call = "Likely down-move despite decent fundamentals - may be sentiment/technical-driven"
    elif tech.label == "Bullish":
        call = "Likely up-move (fundamentals inconclusive)"
    elif tech.label == "Bearish":
        call = "Likely down-move (fundamentals inconclusive)"
    else:
        call = "No significant move expected"

    return Verdict(symbol=symbol, market=market, technical=tech, fundamental=fund, call=call, alert=alert)
