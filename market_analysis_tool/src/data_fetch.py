"""Thin wrappers around yfinance for price history and financial statements.

All functions fail soft (return None / empty DataFrame + log a warning)
instead of raising, so one bad ticker never aborts the whole morning run.
"""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def get_price_history(symbol: str, period: str = "1y") -> pd.DataFrame | None:
    try:
        df = yf.Ticker(symbol).history(period=period, auto_adjust=False)
        if df is None or df.empty:
            log.warning("no price history returned for %s", symbol)
            return None
        return df
    except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a best-effort fetch
        log.warning("price history failed for %s: %s", symbol, exc)
        return None


def get_financials(symbol: str) -> dict[str, pd.DataFrame]:
    """Yearly cashflow, income statement and balance sheet.

    Yahoo's free endpoint typically exposes ~4 years of annual data.
    """
    t = yf.Ticker(symbol)
    out: dict[str, pd.DataFrame] = {}
    for name, attr in (("cashflow", "cashflow"), ("income", "financials"), ("balance", "balance_sheet")):
        try:
            df = getattr(t, attr)
            out[name] = df if df is not None else pd.DataFrame()
        except Exception as exc:  # noqa: BLE001
            log.warning("%s fetch failed for %s: %s", name, symbol, exc)
            out[name] = pd.DataFrame()
    return out


def get_info(symbol: str) -> dict:
    """Snapshot fields (P/E, market cap, insider holding %, analyst count, ...).

    Only fetched for stocks that already triggered an alert (see main.py) --
    this call is slower and less reliable than the statement fetches above.
    """
    try:
        return yf.Ticker(symbol).info or {}
    except Exception as exc:  # noqa: BLE001
        log.warning("info fetch failed for %s: %s", symbol, exc)
        return {}


def get_market_index_snapshot(symbol: str) -> dict | None:
    df = get_price_history(symbol, period="5d")
    if df is None or len(df) < 2:
        return None
    last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
    if prev == 0:
        return None
    return {
        "last": float(last),
        "change_pct": float((last - prev) / prev * 100),
    }
