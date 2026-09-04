"""Build the universe of tickers to analyse each morning.

Default universe = bundled Nifty 50 (India) + a core set of large global
stocks, plus anything you add to watchlists/custom.txt. Scanning literally
every listed stock worldwide daily against a free data source isn't
practical (thousands of tickers, rate limits, hours of runtime) -- this
keeps the default broad but tractable, and lets you extend it freely.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from config import WATCHLIST_DIR


class Instrument(NamedTuple):
    symbol: str   # yfinance symbol, e.g. "RELIANCE.NS" or "AAPL"
    market: str   # "India" or "Global"


def _read_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def load_universe(include_custom: bool = True) -> list[Instrument]:
    instruments: list[Instrument] = []

    for sym in _read_list(WATCHLIST_DIR / "nifty50.txt"):
        instruments.append(Instrument(f"{sym}.NS", "India"))

    for sym in _read_list(WATCHLIST_DIR / "global_core.txt"):
        instruments.append(Instrument(sym, "Global"))

    if include_custom:
        for sym in _read_list(WATCHLIST_DIR / "custom.txt"):
            market = "India" if sym.upper().endswith((".NS", ".BO")) else "Global"
            instruments.append(Instrument(sym, market))

    seen: set[str] = set()
    unique: list[Instrument] = []
    for inst in instruments:
        if inst.symbol not in seen:
            seen.add(inst.symbol)
            unique.append(inst)
    return unique
