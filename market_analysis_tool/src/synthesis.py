"""Prompt 10: Master Synthesis.

Rolls up the technical read, the CFO-vs-PAT earnings-quality audit, and
the deep-dive checks (working capital, moat, capital allocation,
valuation, multibagger criteria) into: top bullish reasons, top red
flags, a rough fair-value range, and the single most important question
to ask management next -- and explicitly lists what could NOT be
assessed from free data, per the original prompt's own instruction to
"state every assumption, flag where you are uncertain."
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.deep_analysis import (
    MANAGEMENT_CREDIBILITY_NOTE,
    PROMOTER_QUALITY_NOTE,
    REVENUE_CONCENTRATION_NOTE,
    CapitalAllocationVerdict,
    MoatVerdict,
    MultibaggerVerdict,
    ValuationVerdict,
    WorkingCapitalVerdict,
)
from src.fundamental import FundamentalVerdict
from src.technical import TechnicalVerdict


@dataclass
class SynthesisVerdict:
    bull_points: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    fair_value_range: str | None = None
    key_question: str = ""
    uncertain_notes: list[str] = field(default_factory=list)


_BULLISH_LABELS = {
    "Bullish",
    "Healthy",
    "Improving",
    "Signals of a durable moat",
    "Shareholder-friendly / disciplined",
    "Cheap vs its own history",
}
_BEARISH_LABELS = {
    "Bearish",
    "Caution",
    "Deteriorating",
    "Weak/no moat signal",
    "Aggressive reinvestment (or cash-strained)",
    "Expensive vs its own history",
}


def synthesize(
    tech: TechnicalVerdict,
    cfo_pat: FundamentalVerdict,
    working_capital: WorkingCapitalVerdict,
    moat: MoatVerdict,
    capital_allocation: CapitalAllocationVerdict,
    valuation: ValuationVerdict,
    multibagger: MultibaggerVerdict,
) -> SynthesisVerdict:
    s = SynthesisVerdict()

    bull_candidates: list[str] = []
    red_candidates: list[str] = []

    if tech.label == "Bullish":
        bull_candidates.append(f"Technicals are bullish (score {tech.score}): {tech.reasons[0] if tech.reasons else 'multiple signals aligned'}")
    elif tech.label == "Bearish":
        red_candidates.append(f"Technicals are bearish (score {tech.score}): {tech.reasons[0] if tech.reasons else 'multiple signals aligned'}")

    if cfo_pat.label == "Healthy":
        bull_candidates.append(f"Earnings quality: {cfo_pat.cfo_vs_pat_note}")
    elif cfo_pat.label == "Caution":
        red_candidates.append(f"Earnings quality: {cfo_pat.cfo_vs_pat_note}")

    if working_capital.label == "Improving":
        bull_candidates.append(f"Working capital: {working_capital.reasons[-1] if working_capital.reasons else 'cash conversion cycle improving'}")
    elif working_capital.label == "Deteriorating":
        red_candidates.append(f"Working capital: {working_capital.reasons[-1] if working_capital.reasons else 'cash conversion cycle deteriorating'}")

    # moat.label is decided by the ROCE check, which is always the last reason
    # appended in moat_strength_test (after the margin lines) -- use reasons[-1],
    # not reasons[0], so the displayed explanation actually matches the verdict
    # instead of surfacing an unrelated (and possibly contradictory) margin note.
    if moat.label == "Signals of a durable moat":
        bull_candidates.append(f"Moat: {moat.reasons[-1] if moat.reasons else 'margin/ROCE trend supportive'}")
    elif moat.label == "Weak/no moat signal":
        red_candidates.append(f"Moat: {moat.reasons[-1] if moat.reasons else 'margin/ROCE trend weak'}")

    if capital_allocation.label == "Shareholder-friendly / disciplined":
        bull_candidates.append(f"Capital allocation: {capital_allocation.reasons[0] if capital_allocation.reasons else 'disciplined capex vs. cash flow'}")
    elif capital_allocation.label == "Aggressive reinvestment (or cash-strained)":
        red_candidates.append(f"Capital allocation: {capital_allocation.reasons[0] if capital_allocation.reasons else 'capex is outrunning operating cash flow'}")

    if valuation.label == "Cheap vs its own history":
        bull_candidates.append(f"Valuation: {valuation.reasons[0] if valuation.reasons else 'trading below its own historical P/E range'}")
    elif valuation.label == "Expensive vs its own history":
        red_candidates.append(f"Valuation: {valuation.reasons[0] if valuation.reasons else 'trading above its own historical P/E range'}")

    if multibagger.max_scored > 0 and multibagger.score / multibagger.max_scored >= 0.75:
        bull_candidates.append(f"Multibagger screen: scored {multibagger.score:.1f}/{multibagger.max_scored:.0f} on the computable criteria")
    elif multibagger.max_scored > 0 and multibagger.score / multibagger.max_scored <= 0.25:
        red_candidates.append(f"Multibagger screen: only {multibagger.score:.1f}/{multibagger.max_scored:.0f} on the computable criteria")

    s.bull_points = bull_candidates[:3] or ["No strong bullish signal surfaced from the checks that could be run on free data."]
    s.red_flags = red_candidates[:3] or ["No strong red flag surfaced from the checks that could be run on free data."]

    if valuation.current_eps and valuation.historical_pe_low and valuation.historical_pe_high:
        low = valuation.current_eps * valuation.historical_pe_low
        high = valuation.current_eps * valuation.historical_pe_high
        s.fair_value_range = (
            f"{min(low, high):,.0f} - {max(low, high):,.0f} "
            f"(latest EPS x its own historical P/E range -- a rough anchor, not a DCF)"
        )
    else:
        s.fair_value_range = "Not enough data to build a range (needs net income, shares outstanding and 5y price history)"

    if red_candidates:
        s.key_question = f"Ask management directly about this: {red_candidates[0]}"
    else:
        s.key_question = "No major red flag surfaced from computable checks -- ask management what could break the current trend (margins, demand, or competition) over the next 2-3 quarters."

    s.uncertain_notes = [
        f"{n.topic}: {n.reason}" for n in (REVENUE_CONCENTRATION_NOTE, PROMOTER_QUALITY_NOTE, MANAGEMENT_CREDIBILITY_NOTE)
    ]
    s.uncertain_notes.append(moat.note)
    s.uncertain_notes.append(capital_allocation.note)
    return s
