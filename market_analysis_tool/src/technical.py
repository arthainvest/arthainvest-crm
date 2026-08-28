"""Technical analysis: indicators + rule-based signals for a likely up/down move."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from config import THRESHOLDS


@dataclass
class TechnicalVerdict:
    score: int = 0                 # positive = bullish, negative = bearish
    label: str = "Neutral"
    reasons: list[str] = field(default_factory=list)
    last_price: float | None = None
    change_pct_1d: float | None = None


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line


def analyse(df: pd.DataFrame | None) -> TechnicalVerdict:
    v = TechnicalVerdict()
    if df is None or len(df) < 30:
        v.label = "Insufficient data"
        return v

    close = df["Close"]
    volume = df["Volume"]
    v.last_price = float(close.iloc[-1])
    v.change_pct_1d = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)

    if abs(v.change_pct_1d) >= THRESHOLDS.momentum_alert_pct:
        direction = "up" if v.change_pct_1d > 0 else "down"
        v.reasons.append(f"Moved {v.change_pct_1d:+.1f}% in the last session ({direction} sharply)")
        v.score += 1 if v.change_pct_1d > 0 else -1

    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean() if len(close) >= 200 else None
    if sma200 is not None and not sma50.isna().iloc[-1] and not sma200.isna().iloc[-1]:
        if sma50.iloc[-1] > sma200.iloc[-1] and sma50.iloc[-2] <= sma200.iloc[-2]:
            v.reasons.append("Golden cross: 50-day average just crossed above the 200-day average")
            v.score += 2
        elif sma50.iloc[-1] < sma200.iloc[-1] and sma50.iloc[-2] >= sma200.iloc[-2]:
            v.reasons.append("Death cross: 50-day average just crossed below the 200-day average")
            v.score -= 2
        elif sma50.iloc[-1] > sma200.iloc[-1]:
            v.reasons.append("Trading above both the 50- and 200-day averages (uptrend intact)")
            v.score += 1
        else:
            v.reasons.append("Trading below both the 50- and 200-day averages (downtrend intact)")
            v.score -= 1

    rsi = _rsi(close)
    if not rsi.isna().iloc[-1]:
        rsi_last = rsi.iloc[-1]
        if rsi_last >= THRESHOLDS.rsi_overbought:
            v.reasons.append(f"RSI at {rsi_last:.0f} - overbought, risk of a pullback")
            v.score -= 1
        elif rsi_last <= THRESHOLDS.rsi_oversold:
            v.reasons.append(f"RSI at {rsi_last:.0f} - oversold, risk of a bounce")
            v.score += 1

    macd_line, signal_line = _macd(close)
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        v.reasons.append("MACD bullish crossover")
        v.score += 1
    elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        v.reasons.append("MACD bearish crossover")
        v.score -= 1

    avg_vol20 = volume.rolling(20).mean()
    if not avg_vol20.isna().iloc[-1] and avg_vol20.iloc[-1] > 0:
        ratio = volume.iloc[-1] / avg_vol20.iloc[-1]
        if ratio >= THRESHOLDS.volume_spike_ratio:
            v.reasons.append(f"Volume {ratio:.1f}x the 20-day average - unusual interest")
            v.score += 1 if (v.change_pct_1d or 0) > 0 else -1

    lookback = min(THRESHOLDS.breakout_lookback_days, len(df) - 1)
    recent_high = close.iloc[-lookback - 1:-1].max()
    recent_low = close.iloc[-lookback - 1:-1].min()
    if v.last_price > recent_high:
        v.reasons.append(f"Broke above its {lookback}-day high")
        v.score += 2
    elif v.last_price < recent_low:
        v.reasons.append(f"Broke below its {lookback}-day low")
        v.score -= 2

    high52 = close.max()
    low52 = close.min()
    if high52 > 0 and (high52 - v.last_price) / high52 * 100 <= THRESHOLDS.near_52w_pct:
        v.reasons.append("Trading within striking distance of its 52-week high")
        v.score += 1
    if low52 > 0 and (v.last_price - low52) / low52 * 100 <= THRESHOLDS.near_52w_pct:
        v.reasons.append("Trading within striking distance of its 52-week low")
        v.score -= 1

    if v.score >= 2:
        v.label = "Bullish"
    elif v.score <= -2:
        v.label = "Bearish"
    else:
        v.label = "Neutral"
    return v
