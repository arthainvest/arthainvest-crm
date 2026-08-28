"""Render the daily market + stock analysis report."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from src.signals import Verdict


def render_markdown(run_date: date, market_snapshot: dict, verdicts: list[Verdict]) -> str:
    lines = [f"# Morning Market Brief - {run_date.isoformat()}", ""]

    lines.append("## Market conditions")
    for name, snap in market_snapshot.items():
        if snap is None:
            lines.append(f"- **{name}**: data unavailable")
            continue
        arrow = "up" if snap["change_pct"] >= 0 else "down"
        lines.append(f"- **{name}**: {snap['last']:,.2f} ({arrow} {snap['change_pct']:+.2f}%)")
    lines.append("")

    alerts = [v for v in verdicts if v.alert]
    lines.append(f"## Flagged for a significant move today ({len(alerts)})")
    if not alerts:
        lines.append("No stock in the watchlist crossed the alert thresholds today.")
    for v in sorted(alerts, key=lambda x: abs(x.technical.score), reverse=True):
        lines.append(_render_stock(v))
    lines.append("")

    others = [v for v in verdicts if not v.alert]
    if others:
        lines.append(f"## Rest of the watchlist ({len(others)}) - no significant move flagged")
        for v in others:
            price = f"{v.technical.last_price:,.2f}" if v.technical.last_price is not None else "n/a"
            chg = f"{v.technical.change_pct_1d:+.2f}%" if v.technical.change_pct_1d is not None else "n/a"
            lines.append(f"- **{v.symbol}** ({v.market}) - {price} ({chg}) - {v.call}")
    lines.append("")
    lines.append("---")
    lines.append(
        "_Not investment advice, and not from a SEBI-registered research analyst. Signals are "
        "rule-based, run on free/delayed data, and should be verified independently before acting._"
    )
    return "\n".join(lines)


def _render_stock(v: Verdict) -> str:
    price = f"{v.technical.last_price:,.2f}" if v.technical.last_price is not None else "n/a"
    chg = f"{v.technical.change_pct_1d:+.2f}%" if v.technical.change_pct_1d is not None else "n/a"
    out = [
        f"### {v.symbol} ({v.market}) - {price} ({chg})",
        f"**Call:** {v.call}",
        f"**Technical ({v.technical.label}, score {v.technical.score}):**",
    ]
    out += [f"- {r}" for r in v.technical.reasons] or ["- No specific technical trigger"]
    out.append(f"**Fundamentals ({v.fundamental.label}):** {v.fundamental.cfo_vs_pat_note}")
    out += [f"- {r}" for r in v.fundamental.reasons]
    out.append("")
    return "\n".join(out)


def save_report(content: str, run_date: date, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{run_date.isoformat()}.md"
    path.write_text(content, encoding="utf-8")
    return path
