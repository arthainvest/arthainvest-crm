#!/usr/bin/env python3
"""Daily Indian + global market & stock analysis tool.

Run every morning before market open:
    python3 main.py run

Combines technical signals (moving averages, RSI, MACD, volume, breakouts)
with fundamental earnings-quality checks -- including a CFO-vs-PAT audit
that flags whether reported profits are backed by real cash -- to surface
stocks likely to move, and prints/saves a daily brief.

For any stock flagged that way, a deeper forensic-analyst-style dive runs
on top (working capital trends, moat strength, capital allocation,
valuation vs. own history, and a multibagger-criteria score), synthesised
into a bull case / red flags / fair-value range / key question for
management -- see src/deep_analysis.py and src/synthesis.py. This deeper
layer only runs on flagged stocks, not the whole watchlist, to keep
runtime and API calls reasonable.

See README.md for setup, scheduling and data-source notes.
"""
from __future__ import annotations

import argparse
import logging
from datetime import date

from config import MARKET_INDEXES, REPORTS_DIR
from src.data_fetch import get_financials, get_info, get_market_index_snapshot, get_price_history
from src.deep_analysis import (
    capital_allocation_audit,
    moat_strength_test,
    multibagger_criteria_check,
    valuation_reality_check,
    working_capital_audit,
)
from src.fundamental import FundamentalVerdict, analyse as analyse_fundamental
from src.report import render_markdown, save_report
from src.signals import DeepDiveResult, combine
from src.synthesis import synthesize
from src.technical import analyse as analyse_technical
from src.watchlist import load_universe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("market_analysis")


def _run_deep_dive(symbol: str, fin: dict, tech, fund) -> DeepDiveResult:
    log.info("Deep dive on %s (flagged for a significant move)...", symbol)
    info = get_info(symbol)
    price_5y = get_price_history(symbol, period="5y")

    working_capital = working_capital_audit(fin["balance"], fin["income"])
    moat = moat_strength_test(fin["income"], fin["balance"])
    capital_allocation = capital_allocation_audit(fin["cashflow"])
    valuation = valuation_reality_check(fin["income"], fin["cashflow"], info, price_5y)
    multibagger = multibagger_criteria_check(fin["income"], fin["balance"], info)

    synthesis = synthesize(tech, fund, working_capital, moat, capital_allocation, valuation, multibagger)

    return DeepDiveResult(
        working_capital=working_capital,
        moat=moat,
        capital_allocation=capital_allocation,
        valuation=valuation,
        multibagger=multibagger,
        synthesis=synthesis,
    )


def run(skip_fundamentals: bool = False) -> None:
    universe = load_universe()
    log.info("Watchlist: %d instruments", len(universe))

    log.info("Fetching market index snapshot...")
    market_snapshot = {name: get_market_index_snapshot(sym) for name, sym in MARKET_INDEXES.items()}

    verdicts = []
    financials_by_symbol: dict[str, dict] = {}
    for inst in universe:
        log.info("Analysing %s (%s)...", inst.symbol, inst.market)
        price_hist = get_price_history(inst.symbol)
        tech = analyse_technical(price_hist)

        if skip_fundamentals:
            fund = FundamentalVerdict()
        else:
            fin = get_financials(inst.symbol)
            financials_by_symbol[inst.symbol] = fin
            fund = analyse_fundamental(fin["cashflow"], fin["income"], fin["balance"])

        verdicts.append(combine(inst.symbol, inst.market, tech, fund))

    if not skip_fundamentals:
        for v in verdicts:
            if v.alert:
                fin = financials_by_symbol.get(v.symbol)
                if fin is not None:
                    v.deep_dive = _run_deep_dive(v.symbol, fin, v.technical, v.fundamental)

    report = render_markdown(date.today(), market_snapshot, verdicts)
    path = save_report(report, date.today(), REPORTS_DIR)
    log.info("Report saved to %s", path)

    alerts = [v for v in verdicts if v.alert]
    print("\n" + "=" * 60)
    print(f"MORNING MARKET BRIEF - {date.today().isoformat()}")
    print("=" * 60)
    if alerts:
        print(f"{len(alerts)} stock(s) flagged for a significant move:")
        for v in sorted(alerts, key=lambda x: abs(x.technical.score), reverse=True):
            print(f"  - {v.symbol} ({v.market}): {v.call}")
    else:
        print("No significant moves flagged today.")
    print(f"\nFull report: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Indian + global market & stock analysis tool")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run today's analysis and save the report")
    run_p.add_argument(
        "--skip-fundamentals",
        action="store_true",
        help="Technical-only run (faster; also skips the deep-dive checks, which need fundamentals)",
    )
    args = parser.parse_args()

    if args.command == "run":
        run(skip_fundamentals=args.skip_fundamentals)


if __name__ == "__main__":
    main()
