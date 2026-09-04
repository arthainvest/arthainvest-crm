# Market Analysis Tool

A standalone command-line tool that reads Indian + global market
conditions every morning, runs technical and fundamental analysis on a
watchlist of stocks, and flags the ones likely to make a significant move
that day.

It is intentionally **not** wired into the ArthaInvest CRM app -- it's a
separate script you run on your own machine or schedule via cron.

## What it checks

**Market conditions** (top of every report): Nifty 50, Sensex, India VIX,
S&P 500, Nasdaq, Dow Jones, CBOE VIX.

**Per stock, technical:**
- 50-day / 200-day moving average crossovers (golden/death cross)
- RSI (overbought/oversold)
- MACD crossovers
- Volume spikes vs. the 20-day average
- Breakouts above/below the recent 60-day range
- Proximity to the 52-week high/low
- Same-day % move

**Per stock, fundamental -- including a "CFO vs PAT audit":** compares
cash flow from operations against reported net profit (PAT) across the
last available years to flag whether earnings look cash-backed or
potentially manufactured -- the same style of earnings-quality check a
research analyst runs by hand (years where PAT grew but CFO fell, whether
the CFO-PAT gap is narrowing or widening, any year with negative CFO
despite a positive PAT) -- plus profit growth and debt-to-equity trend.

A stock is **flagged** when its technical score crosses the alert
threshold (`config.py` -> `min_technical_score_alert`); the fundamental
read is shown alongside it for context/conviction, not as a separate
trigger.

**Deep dive on flagged stocks only** -- once a stock is flagged, the tool
runs a second, deeper layer modeled on a "forensic equity analyst"
checklist (`src/deep_analysis.py`, synthesised in `src/synthesis.py`).
This only runs on flagged names, not the whole watchlist, since it needs
extra API calls per stock:
- **Working capital trend** -- debtor / inventory / creditor days and the
  cash conversion cycle over the last available years: is the business
  getting more efficient or slowly consuming more cash?
- **Moat strength** -- gross margin trend, whether margins held up through
  the 2022-23 inflation cycle, and ROCE trend. (Peer-relative ROCE and a
  competitor count need an industry peer set this tool doesn't have --
  flagged as not scored rather than guessed.)
- **Capital allocation** -- how much of operating cash flow went to capex
  vs. dividends/buybacks over the last available years. (Whether specific
  acquisitions created or destroyed value, and loans to promoter entities,
  need deal-level disclosures not in free statement data -- flagged as
  not scored.)
- **Valuation reality check** -- current P/E vs. its own historical P/E
  range (built from historical EPS and price on each fiscal year-end),
  current EV/EBITDA, and P/FCF for the latest year.
- **Multibagger criteria** -- scores the 3 of 5 classic criteria that are
  computable from free data (ROCE >15% and improving, promoter/insider
  holding >50%, low analyst coverage as a proxy for "under-the-radar");
  TAM expansion and core-vs-unrelated reinvestment are explicitly left
  unscored (qualitative / covered by the capital allocation section).
- **Master synthesis** -- rolls all of the above (plus the technical read
  and the CFO-vs-PAT audit) into top bullish points, top red flags, a
  rough fair-value range (latest EPS x its own historical P/E range -- a
  quick anchor, not a DCF), and the single most important question to
  put to management next.

Three checks from the original checklist genuinely can't be built from a
free market-data API and are reported as explicit "verify manually"
notes rather than fabricated: **customer/segment revenue concentration**,
**promoter pledging % and related-party transactions**, and **management
credibility scored from earnings-call transcripts**. All three need data
(company disclosures, transcript text) that yfinance doesn't expose.

## Setup

```bash
cd market_analysis_tool
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

## Run

```bash
python3 main.py run
```

This prints a summary of flagged stocks to the console and saves the full
report to `reports/YYYY-MM-DD.md`. Use `--skip-fundamentals` for a faster,
technical-only run.

## Running it every morning

Schedule it with cron before market open. Example: weekdays at 8:00 AM IST
(adjust the hour if your server runs in a different timezone):

```
0 8 * * 1-5  cd /path/to/market_analysis_tool && /path/to/.venv/bin/python3 main.py run >> cron.log 2>&1
```

## Notifications

Right now "being informed" means: a console summary plus a saved
Markdown report. No email/WhatsApp/Slack channel was hooked up in this
build. To add one:
- Easiest: pipe `main.py run`'s output through your own mail/WhatsApp CLI
  in the cron line above.
- Or wire it directly: add a `notify()` call in `main.py` after
  `save_report(...)`, called with the `alerts` list, and send through
  whatever channel you want (SMTP, a WhatsApp Business API, Slack
  webhook, etc.).

## Extending the watchlist

- `watchlists/nifty50.txt` and `watchlists/global_core.txt` are the
  bundled defaults (approximate as of this build -- index constituents
  change, so refresh periodically from NSE's published index CSV or your
  broker's index page).
- Add anything else to `watchlists/custom.txt`, one symbol per line, in
  yfinance format (`RELIANCE.NS`, `ZOMATO.NS`, `AAPL`, ...).
- "Track every listed stock" isn't practical against a free data source
  (thousands of tickers, rate limits, hours of runtime) -- this defaults
  to a broad-but-tractable universe (Nifty 50 + a global large-cap core)
  that you can widen as needed.

## Data source & limitations

Uses [yfinance](https://github.com/ranaroussi/yfinance) (free, unofficial
Yahoo Finance access):
- Prices are typically real-time/near-real-time for US tickers and
  15-20 minute delayed for NSE tickers.
- Fundamentals are annual and limited to roughly the last 4 years.
- No promoter shareholding/pledge data, no corporate-action or news feed.
- Yahoo occasionally rate-limits or changes its endpoints; if a run fails
  outright, check `pip install -U yfinance` first.

## Disclaimer

This is a personal research tool, not investment advice, and not output
from a SEBI-registered research analyst. Signals are rule-based on
free/delayed data and can be wrong -- verify independently before acting
on anything in the report.
