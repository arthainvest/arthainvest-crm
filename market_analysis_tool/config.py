"""Configuration and tunable thresholds for the market analysis tool."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WATCHLIST_DIR = ROOT / "watchlists"
REPORTS_DIR = ROOT / "reports"

# Index tickers used for the overall "market conditions" read (yfinance symbols).
MARKET_INDEXES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "India VIX": "^INDIAVIX",
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "CBOE VIX": "^VIX",
}


@dataclass
class Thresholds:
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_spike_ratio: float = 1.8       # today's volume vs 20-day average
    breakout_lookback_days: int = 60      # window for high/low breakout checks
    near_52w_pct: float = 2.0             # within X% of 52-week high/low
    momentum_alert_pct: float = 3.0       # single-session % move considered "significant"
    min_technical_score_alert: int = 2    # |technical score| >= this triggers an alert
    cfo_pat_gap_red_flag_years: int = 2   # years of CFO < PAT needed to flag earnings quality


THRESHOLDS = Thresholds()
