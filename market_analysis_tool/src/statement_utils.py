"""Shared helpers for reading yfinance's financial-statement DataFrames.

yfinance's cashflow / financials / balance_sheet DataFrames index line
items by (loosely standardized, version-dependent) label strings and
column by period-end Timestamps, most recent first. These helpers make
that lookup tolerant of label drift across yfinance versions.
"""
from __future__ import annotations

import pandas as pd


def find_row(df: pd.DataFrame | None, candidates: list[str]) -> pd.Series | None:
    """Returns the first row whose (lowercased) label contains any candidate substring."""
    if df is None or df.empty:
        return None
    for idx in df.index:
        low = str(idx).lower()
        if any(c in low for c in candidates):
            return df.loc[idx]
    return None


def year_label(period) -> str:
    return str(period.year) if hasattr(period, "year") else str(period)


def common_years(*rows: pd.Series | None, limit: int = 5) -> list:
    """Years present (non-NaN) across all given rows, most recent first."""
    valid = [r.dropna().index for r in rows if r is not None]
    if not valid:
        return []
    years = set(valid[0])
    for idx in valid[1:]:
        years &= set(idx)
    return sorted(years, reverse=True)[:limit]
