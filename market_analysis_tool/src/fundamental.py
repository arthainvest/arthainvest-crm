"""Fundamental analysis: earnings-quality checks, growth and leverage trends.

The core check here is the "CFO vs PAT audit": comparing cash flow from
operations (CFO) against reported net profit (PAT) year by year, to flag
whether a company's profits are backed by real cash or look manufactured.
This mirrors a standard sell-side/independent-research earnings-quality
screen: years where PAT grew but CFO fell, the size and direction of the
CFO-PAT gap over time, and any year where CFO was negative despite a
positive PAT.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from config import THRESHOLDS
from src.statement_utils import find_row, year_label


@dataclass
class FundamentalVerdict:
    label: str = "Unknown"
    reasons: list[str] = field(default_factory=list)
    cfo_vs_pat_note: str | None = None
    data_years: int = 0


def _cfo_pat_audit(cashflow: pd.DataFrame, income: pd.DataFrame) -> tuple[str, list[str]]:
    cfo_row = find_row(cashflow, ["cash flow from operating", "operating cash flow", "total cash from operating"])
    pat_row = find_row(income, ["net income", "net income common stockholders"])

    if cfo_row is None or pat_row is None:
        return "Not enough data", ["Cash flow / net income data unavailable from the free data source"]

    years = sorted(set(cfo_row.dropna().index) & set(pat_row.dropna().index), reverse=True)[:5]
    if len(years) < 2:
        return "Not enough data", ["Fewer than 2 years of financials available to compare CFO against PAT"]

    notes: list[str] = []
    weak_years = 0
    gaps: list[tuple[object, float, float, float]] = []

    for y in years:
        cfo, pat = float(cfo_row[y]), float(pat_row[y])
        gaps.append((y, cfo - pat, cfo, pat))
        if cfo < pat:
            weak_years += 1
        if cfo < 0 and pat > 0:
            notes.append(f"{year_label(y)}: cash flow from operations was negative despite a positive reported profit")

    for i in range(len(gaps) - 1):
        y_now, _gap_now, cfo_now, pat_now = gaps[i]
        _y_prev, _gap_prev, cfo_prev, pat_prev = gaps[i + 1]
        if pat_now > pat_prev and cfo_now < cfo_prev:
            notes.append(f"{year_label(y_now)}: reported profit grew year-on-year while operating cash flow fell")

    if len(gaps) >= 2:
        trend = "narrowing" if abs(gaps[0][1]) < abs(gaps[-1][1]) else "widening"
        notes.append(f"Gap between cash generated and reported profit is {trend} across the years reviewed")

    negative_cfo_years = sum(1 for _y, gap, cfo, pat in gaps if cfo < 0 and pat > 0)
    if negative_cfo_years > 0 or weak_years >= THRESHOLDS.cfo_pat_gap_red_flag_years:
        verdict = (
            "Profits may be partly manufactured - cash generation has lagged reported profit in "
            "multiple years; worth independent verification before relying on the reported numbers"
        )
    else:
        verdict = "Profits look cash-backed - operating cash flow has tracked reported profit reasonably well"

    return verdict, notes


def analyse(cashflow: pd.DataFrame, income: pd.DataFrame, balance: pd.DataFrame) -> FundamentalVerdict:
    v = FundamentalVerdict()

    cfo_verdict, cfo_notes = _cfo_pat_audit(cashflow, income)
    v.cfo_vs_pat_note = cfo_verdict
    v.reasons.extend(cfo_notes)

    pat_row = find_row(income, ["net income", "net income common stockholders"])
    if pat_row is not None and len(pat_row.dropna()) >= 2:
        years = sorted(pat_row.dropna().index, reverse=True)[:2]
        latest, prior = float(pat_row[years[0]]), float(pat_row[years[1]])
        if prior != 0:
            growth = (latest - prior) / abs(prior) * 100
            v.reasons.append(f"Net profit {'grew' if growth >= 0 else 'declined'} {growth:+.0f}% year-on-year")

    debt_row = find_row(balance, ["total debt", "long term debt"])
    equity_row = find_row(balance, ["total stockholder equity", "common stock equity", "stockholders equity"])
    if debt_row is not None and equity_row is not None:
        years = sorted(set(debt_row.dropna().index) & set(equity_row.dropna().index), reverse=True)[:2]
        if len(years) == 2 and equity_row[years[0]] and equity_row[years[1]]:
            de_latest = float(debt_row[years[0]]) / float(equity_row[years[0]])
            de_prior = float(debt_row[years[1]]) / float(equity_row[years[1]])
            if de_latest > de_prior * 1.15:
                v.reasons.append(f"Debt-to-equity rising ({de_prior:.2f} -> {de_latest:.2f})")
            elif de_latest < de_prior * 0.85:
                v.reasons.append(f"Debt-to-equity falling ({de_prior:.2f} -> {de_latest:.2f})")

    if cashflow is not None and income is not None and not cashflow.empty and not income.empty:
        v.data_years = len(set(cashflow.columns) & set(income.columns))

    if "manufactured" in cfo_verdict:
        v.label = "Caution"
    elif cfo_verdict == "Not enough data":
        v.label = "Unknown"
    else:
        v.label = "Healthy"
    return v
