"""Deeper forensic-style fundamental checks, run only on stocks the daily
scan has already flagged for a significant move (see main.py) -- these
pull extra data (info snapshot, 5-year price history) per stock, so
running them against the whole watchlist every morning wouldn't be worth
the extra network calls.

Each function below implements one prompt from a "forensic equity
analyst" checklist (CFO-vs-PAT lives in fundamental.py as Prompt 1; this
module covers Prompts 2, 4, 6, 7 and 9). Three prompts in the checklist
-- customer/segment concentration (3), promoter pledging & related-party
transactions (5), and management credibility from earnings-call
transcripts (8) -- need data no free market-data API exposes, so they are
returned as explicit "requires manual review" notes rather than guessed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.statement_utils import common_years, find_row, year_label


# ---------------------------------------------------------------------------
# Prompt 2: Working Capital Trap
# ---------------------------------------------------------------------------

@dataclass
class WorkingCapitalVerdict:
    label: str = "Unknown"
    reasons: list[str] = field(default_factory=list)


def working_capital_audit(balance: pd.DataFrame, income: pd.DataFrame) -> WorkingCapitalVerdict:
    v = WorkingCapitalVerdict()
    receivables = find_row(balance, ["receivables", "accounts receivable"])
    inventory = find_row(balance, ["inventory"])
    payables = find_row(balance, ["accounts payable", "payables"])
    revenue = find_row(income, ["total revenue", "operating revenue"])
    cogs = find_row(income, ["cost of revenue", "cost of goods sold", "reconciled cost of revenue"])

    if revenue is None:
        v.reasons.append("Revenue data unavailable from the free data source")
        return v

    years = sorted(revenue.dropna().index, reverse=True)[:5]
    debtor_days: dict = {}
    inventory_days: dict = {}
    creditor_days: dict = {}

    for y in years:
        rev = revenue.get(y)
        if rev is None or pd.isna(rev) or rev == 0:
            continue
        if receivables is not None and y in receivables.index and not pd.isna(receivables[y]):
            debtor_days[y] = float(receivables[y]) / float(rev) * 365
        cogs_y = cogs.get(y) if cogs is not None else None
        if cogs_y is not None and not pd.isna(cogs_y) and cogs_y != 0:
            if inventory is not None and y in inventory.index and not pd.isna(inventory[y]):
                inventory_days[y] = float(inventory[y]) / abs(float(cogs_y)) * 365
            if payables is not None and y in payables.index and not pd.isna(payables[y]):
                creditor_days[y] = float(payables[y]) / abs(float(cogs_y)) * 365

    if not debtor_days and not inventory_days and not creditor_days:
        v.reasons.append("Receivables / inventory / payables data unavailable from the free data source")
        return v

    def _trend(d: dict, name: str) -> str | None:
        ys = sorted(d.keys(), reverse=True)
        if len(ys) < 2:
            return None
        latest, oldest = d[ys[0]], d[ys[-1]]
        direction = "up" if latest > oldest else "down"
        return f"{name} trend: {direction} from {oldest:.0f} to {latest:.0f} days ({year_label(ys[-1])} -> {year_label(ys[0])})"

    for d, name in ((debtor_days, "Debtor days"), (inventory_days, "Inventory days"), (creditor_days, "Creditor days")):
        note = _trend(d, name)
        if note:
            v.reasons.append(note)

    common = sorted(set(debtor_days) & set(inventory_days) & set(creditor_days), reverse=True)
    if len(common) >= 2:
        ccc = {y: debtor_days[y] + inventory_days[y] - creditor_days[y] for y in common}
        latest, oldest = ccc[common[0]], ccc[common[-1]]
        if latest > oldest * 1.1:
            v.label = "Deteriorating"
            v.reasons.append(
                f"Cash conversion cycle worsened from {oldest:.0f} to {latest:.0f} days -- "
                "the business is slowly consuming more cash to run"
            )
        elif latest < oldest * 0.9:
            v.label = "Improving"
            v.reasons.append(f"Cash conversion cycle improved from {oldest:.0f} to {latest:.0f} days -- getting more efficient")
        else:
            v.label = "Stable"
            v.reasons.append(f"Cash conversion cycle roughly stable ({oldest:.0f} -> {latest:.0f} days)")
    else:
        v.label = "Partial data"
    return v


# ---------------------------------------------------------------------------
# Prompt 4: Moat Strength Test (gross margin + ROCE trend; no peer/competitor data)
# ---------------------------------------------------------------------------

@dataclass
class MoatVerdict:
    label: str = "Unknown"
    reasons: list[str] = field(default_factory=list)
    note: str = (
        "Peer-relative ROCE and a count of direct competitors need an industry peer set "
        "beyond free financial-statement data -- not scored here."
    )


def roce_series(income: pd.DataFrame, balance: pd.DataFrame) -> dict:
    """Year -> ROCE% (EBIT / (total assets - current liabilities)).

    Shared by moat_strength_test() and multibagger_criteria_check() -- callers
    that need both can compute this once and pass it to each via the `roce`
    parameter instead of triggering the computation twice.
    """
    ebit = find_row(income, ["ebit", "operating income"])
    total_assets = find_row(balance, ["total assets"])
    current_liab = find_row(balance, ["current liabilities", "total current liabilities"])
    if ebit is None or total_assets is None or current_liab is None:
        return {}
    years = common_years(ebit, total_assets, current_liab, limit=5)
    out = {}
    for y in years:
        capital_employed = float(total_assets[y]) - float(current_liab[y])
        if capital_employed:
            out[y] = float(ebit[y]) / capital_employed * 100
    return out


def moat_strength_test(income: pd.DataFrame, balance: pd.DataFrame, roce: dict | None = None) -> MoatVerdict:
    v = MoatVerdict()

    revenue = find_row(income, ["total revenue", "operating revenue"])
    gross_profit = find_row(income, ["gross profit"])
    if revenue is not None and gross_profit is not None:
        years = sorted(set(revenue.dropna().index) & set(gross_profit.dropna().index), reverse=True)[:5]
        margins = {y: float(gross_profit[y]) / float(revenue[y]) * 100 for y in years if revenue[y]}
        if len(margins) >= 2:
            ys = sorted(margins.keys(), reverse=True)
            latest, oldest = margins[ys[0]], margins[ys[-1]]
            direction = "expanded" if latest > oldest else "compressed" if latest < oldest else "held steady"
            v.reasons.append(f"Gross margin {direction}, {oldest:.1f}% -> {latest:.1f}% over the period reviewed")

            if len(margins) >= 3:
                worst_year = min(margins, key=margins.get)
                worst_margin = margins[worst_year]
                if worst_margin >= min(oldest, latest) - 2:
                    v.reasons.append("Margins stayed resilient across the whole period reviewed, without a sharp dip in any year")
                else:
                    v.reasons.append(
                        f"Margins dipped noticeably in {year_label(worst_year)} (to {worst_margin:.1f}%) "
                        f"before {'recovering' if latest > worst_margin else 'staying pressured'}"
                    )

    roce = roce if roce is not None else roce_series(income, balance)
    if len(roce) >= 2:
        ys = sorted(roce.keys(), reverse=True)
        latest, oldest = roce[ys[0]], roce[ys[-1]]
        v.reasons.append(f"ROCE {'improved' if latest > oldest else 'declined'}, {oldest:.1f}% -> {latest:.1f}%")
        if latest >= 15 and latest >= oldest:
            v.label = "Signals of a durable moat"
        elif latest < 10:
            v.label = "Weak/no moat signal"
        else:
            v.label = "Moderate"

    if not v.reasons:
        v.label = "Unknown"
        v.reasons.append("Gross margin / ROCE inputs unavailable from the free data source")
    return v


# ---------------------------------------------------------------------------
# Prompt 6: Capital Allocation Audit (dividends, buybacks, capex; no deal-level data)
# ---------------------------------------------------------------------------

@dataclass
class CapitalAllocationVerdict:
    label: str = "Unknown"
    reasons: list[str] = field(default_factory=list)
    note: str = (
        "Whether specific acquisitions created or destroyed value, and any loans to promoter "
        "entities, need deal-level and related-party disclosures not in free financial-statement "
        "data -- check the annual report's related-party note directly."
    )


def capital_allocation_audit(cashflow: pd.DataFrame) -> CapitalAllocationVerdict:
    v = CapitalAllocationVerdict()
    dividends = find_row(cashflow, ["cash dividends paid", "dividends paid", "common stock dividend paid"])
    buybacks = find_row(cashflow, ["repurchase of capital stock", "common stock repurchased", "repurchase of stock"])
    capex = find_row(cashflow, ["capital expenditure"])
    cfo = find_row(cashflow, ["cash flow from operating", "operating cash flow", "total cash from operating"])

    if capex is None or cfo is None:
        v.reasons.append("Cash flow statement data unavailable from the free data source")
        return v

    years = common_years(capex, cfo, limit=5)
    if not years:
        v.reasons.append("Not enough overlapping capex / operating cash flow history")
        return v

    total_capex = sum(abs(float(capex[y])) for y in years)
    total_cfo = sum(float(cfo[y]) for y in years)

    if total_cfo > 0:
        ratio = total_capex / total_cfo
        v.reasons.append(f"Capex absorbed {ratio * 100:.0f}% of operating cash flow over the last {len(years)} years")
        if ratio <= 0.6:
            v.label = "Shareholder-friendly / disciplined"
        elif ratio > 1.0:
            v.label = "Aggressive reinvestment (or cash-strained)"
        else:
            v.label = "Moderate"
    else:
        v.reasons.append("Cumulative operating cash flow over the period was negative or zero")

    if dividends is not None:
        paid_years = [y for y in years if y in dividends.index and not pd.isna(dividends[y]) and dividends[y] != 0]
        v.reasons.append(f"Paid dividends in {len(paid_years)} of the last {len(years)} years")
    if buybacks is not None:
        bb_years = [y for y in years if y in buybacks.index and not pd.isna(buybacks[y]) and buybacks[y] != 0]
        if bb_years:
            v.reasons.append(f"Executed buybacks in {len(bb_years)} of the last {len(years)} years")

    return v


# ---------------------------------------------------------------------------
# Prompt 7: Valuation Reality Check
# ---------------------------------------------------------------------------

@dataclass
class ValuationVerdict:
    label: str = "Unknown"
    reasons: list[str] = field(default_factory=list)
    historical_pe_low: float | None = None
    historical_pe_high: float | None = None
    current_eps: float | None = None


def valuation_reality_check(
    income: pd.DataFrame,
    cashflow: pd.DataFrame,
    info: dict,
    price_history_5y: pd.DataFrame | None,
) -> ValuationVerdict:
    v = ValuationVerdict()

    net_income = find_row(income, ["net income", "net income common stockholders"])
    shares = info.get("sharesOutstanding")
    trailing_pe = info.get("trailingPE")

    if net_income is not None and shares:
        latest_years = sorted(net_income.dropna().index, reverse=True)[:1]
        if latest_years:
            eps = float(net_income[latest_years[0]]) / shares
            if eps > 0:
                v.current_eps = eps

        if price_history_5y is not None and not price_history_5y.empty:
            # yfinance's price history index is tz-aware (exchange timezone) while
            # its financial-statement period columns are tz-naive -- comparing them
            # directly raises TypeError, so normalize to tz-naive before the lookup.
            if price_history_5y.index.tz is not None:
                price_history_5y = price_history_5y.tz_localize(None)

            years = sorted(net_income.dropna().index, reverse=True)[:5]
            historical_pe = {}
            for y in years:
                eps_y = float(net_income[y]) / shares
                if eps_y <= 0:
                    continue
                idx = price_history_5y.index[price_history_5y.index <= y]
                if len(idx) == 0:
                    continue
                price_then = float(price_history_5y.loc[idx[-1], "Close"])
                historical_pe[y] = price_then / eps_y

            if len(historical_pe) >= 2:
                pe_values = sorted(historical_pe.values())
                median_pe = pe_values[len(pe_values) // 2]
                v.historical_pe_low = pe_values[0]
                v.historical_pe_high = pe_values[-1]
                v.reasons.append(
                    f"Current P/E vs its own {len(historical_pe)}-year median: "
                    f"{trailing_pe:.1f} vs {median_pe:.1f}" if trailing_pe else f"Own {len(historical_pe)}-year median P/E: {median_pe:.1f}"
                )
                if trailing_pe:
                    if trailing_pe > median_pe * 1.2:
                        v.label = "Expensive vs its own history"
                    elif trailing_pe < median_pe * 0.8:
                        v.label = "Cheap vs its own history"
                    else:
                        v.label = "Near fair value vs its own history"

    ev = info.get("enterpriseValue")
    ebitda = info.get("ebitda")
    if ev and ebitda:
        v.reasons.append(f"EV/EBITDA (current): {ev / ebitda:.1f}x -- a 5-year median needs paid historical fundamentals data")

    cfo = find_row(cashflow, ["cash flow from operating", "operating cash flow", "total cash from operating"])
    capex = find_row(cashflow, ["capital expenditure"])
    market_cap = info.get("marketCap")
    if cfo is not None and capex is not None and market_cap:
        years = common_years(cfo, capex, limit=1)
        if years:
            fcf = float(cfo[years[0]]) - abs(float(capex[years[0]]))
            if fcf > 0:
                v.reasons.append(f"P/FCF (latest year): {market_cap / fcf:.1f}x -- {'free cash flow covers the market price reasonably' if market_cap / fcf < 30 else 'market price is pricing in a lot of future growth relative to current FCF'}")
            else:
                v.reasons.append("Free cash flow was negative in the latest year -- market price isn't backed by current FCF")

    if not v.reasons:
        v.reasons.append("Insufficient data (net income, shares outstanding, or price history) for a valuation check")
    return v


# ---------------------------------------------------------------------------
# Prompt 9: Multibagger Criteria Check (3 of 5 criteria are computable)
# ---------------------------------------------------------------------------

@dataclass
class MultibaggerVerdict:
    score: float = 0.0
    max_scored: float = 0.0
    reasons: list[str] = field(default_factory=list)


def multibagger_criteria_check(income: pd.DataFrame, balance: pd.DataFrame, info: dict, roce: dict | None = None) -> MultibaggerVerdict:
    v = MultibaggerVerdict()

    roce = roce if roce is not None else roce_series(income, balance)
    if len(roce) >= 2:
        ys = sorted(roce.keys(), reverse=True)
        latest, oldest = roce[ys[0]], roce[ys[-1]]
        v.max_scored += 1
        if latest >= 15 and latest >= oldest:
            v.score += 1
            v.reasons.append(f"[Scored] ROCE {latest:.1f}%, improving from {oldest:.1f}% -- meets the >15%-and-improving bar")
        elif latest >= 15:
            v.score += 0.5
            v.reasons.append(f"[Scored, half credit] ROCE {latest:.1f}% clears 15% but hasn't improved from {oldest:.1f}%")
        else:
            v.reasons.append(f"[Scored] ROCE {latest:.1f}% is below the 15% multibagger bar")
    else:
        v.reasons.append("ROCE trend: insufficient data to score")

    held_insiders = info.get("heldPercentInsiders")
    if held_insiders is not None:
        pct = held_insiders * 100
        v.max_scored += 1
        if pct > 50:
            v.score += 1
            v.reasons.append(
                f"[Scored] Insider/promoter holding ~{pct:.0f}% (>50%) per Yahoo data -- "
                "note: pledging levels aren't available from this source, check separately"
            )
        else:
            v.reasons.append(f"[Scored] Insider/promoter holding ~{pct:.0f}% is below the 50% bar")
    else:
        v.reasons.append("Promoter/insider holding %: unavailable from the free data source")

    analyst_count = info.get("numberOfAnalystOpinions")
    if analyst_count is not None:
        v.max_scored += 1
        if analyst_count < 5:
            v.score += 1
            v.reasons.append(f"[Scored] Only {analyst_count} analyst(s) covering -- still under-the-radar")
        else:
            v.reasons.append(f"[Scored] {analyst_count} analysts already covering -- not under-the-radar")
    else:
        v.reasons.append("Analyst coverage count unavailable from the free data source")

    v.reasons.append("[Not scored] Expanding total addressable market -- needs qualitative industry research")
    v.reasons.append("[Not scored] Profits reinvested into core vs. unrelated ventures -- see the Capital Allocation Audit")
    return v


# ---------------------------------------------------------------------------
# Prompts 3, 5, 8: not computable from free market-data APIs
# ---------------------------------------------------------------------------

@dataclass
class ManualReviewNote:
    topic: str
    reason: str


REVENUE_CONCENTRATION_NOTE = ManualReviewNote(
    "Revenue Concentration Risk",
    "Top-customer and segment revenue % isn't exposed by free market-data APIs -- "
    "check the annual report's segment/customer concentration notes directly.",
)
PROMOTER_QUALITY_NOTE = ManualReviewNote(
    "Promoter Quality Scan",
    "Promoter pledging %, related-party transaction detail, and SEBI/regulatory actions aren't "
    "available from free market-data APIs -- check the BSE/NSE shareholding pattern filings and "
    "the annual report's related-party note directly.",
)
MANAGEMENT_CREDIBILITY_NOTE = ManualReviewNote(
    "Management Credibility Score",
    "Scoring this needs the actual text of the last 4 earnings-call transcripts, which free "
    "market-data APIs don't provide -- read them on the company's IR page, screener.in, or "
    "Trendlyne directly.",
)
