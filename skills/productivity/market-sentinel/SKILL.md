---
name: market-sentinel
description: "Automated market monitoring, multi-market strategy tracking, and portfolio pulse alerts. Runs mean-reversion (S&P/NASDAQ 50-min candles), momentum (BTC 1H), and trend-following (GOLD/OIL 4H) market scans on a schedule, enforces correlation filters, and delivers morning market briefs + night performance reports via Telegram. Built from: https://youtube.com/shorts/R4_UCTGIZgE"
version: 0.1.0
author: Minerva (Hermes Agent)
license: MIT
platforms: [macos, linux]
tags: [trading, market-data, telegram, cron, finance, alerting]
changelog:
  - "0.1.0 (2026-07-20): Initial skill from trading bot Short (CloudGable pattern)"

trigger:
  type: cron
  schedule: "0 8 * * 1-5"   # Weekday mornings — market open prep
  second_job: "0 18 * * 1-5" # Weekday evenings — performance digest

use_cases:
  - "Morning market brief before open"
  - "Night portfolio performance digest"
  - "Correlation filter alerts (S&P + NASDAQ long bias warning)"
  - "Volatility-adjusted position sizing alerts"

requirements:
  - Telegram bot configured (hermes setup → channels → telegram)
  - Market data API key (see §2)
  - `yfinance` Python package for market data
  - Hermes cron job scheduler

---

# Market Sentinel Skill

Monitors multiple financial markets using distinct strategies per asset class, enforces correlation filters, and delivers structured Telegram briefs.

## Strategy Matrix

| Market | Strategy | Timeframe | Logic |
|--------|----------|-----------|-------|
| S&P 500 (SPY) | Mean Reversion | 50-min candles | Price snaps back when too far from mean |
| NASDAQ (QQQ) | Mean Reversion | 50-min candles | Same as S&P 500 |
| Bitcoin (BTC-USD) | Momentum Breakout | 1-hour candles | Trend continuation after threshold break |
| Gold (GC=F) | Trend Following | 4-hour candles | Cleaner waves, less intraday noise |
| Oil (CL=F) | Trend Following | 4-hour candles | Same as gold |

## Core Automation Loop

### Morning Brief (weekdays ~08:00 local)

```
1. Fetch last N 50-min candles for SPY, QQQ
2. Fetch last N 1-hour candles for BTC-USD
3. Fetch last N 4-hour candles for GC=F, CL=F
4. Run strategy indicators per table above
5. Check correlation filter: if SPY+QQQ both in long position, warn about risk-on concentration
6. Compose morning Telegram message:
   - Market regime summary (which strategies are signalling)
   - Correlation filter status
   - Key levels to watch today
```

### Evening Digest (weekdays ~18:00 local)

```
1. Fetch today's OHLCV for all 5 assets
2. Calculate realized volatility for dynamic position sizing reference
3. Compute correlation matrix for SPY/QQQ
4. Compose night Telegram message:
   - Strategy signal status for each market
   - Portfolio risk metrics (volatility-adjusted)
   - Any correlation filter triggers
   - Next-day watchlist
```

## Risk Management Rules

These are encoded as hard limits in the skill logic — NOT overrideable by Telegram command:

1. **1% hard stop loss** — any single trade signals at most 1% portfolio risk
2. **Dynamic position sizing** — `position_size = base_risk / ATR(14)` per asset
3. **Correlation filter** — if SPY AND QQQ both long, suppress additional risk-on signals

## Setup Steps

### 1. Install dependencies

```bash
pip install yfinance pandas numpy
```

### 2. Configure market data API (optional)

`yfinance` works without an API key for basic use. For higher rate limits, add `YF_API_KEY` to your `.env`:

```
YF_API_KEY=your_alpha_vantage_or_polygon_key
```

### 3. Register Telegram bot

```bash
hermes setup channels telegram
```

### 4. Create the cron jobs

```bash
# Morning brief
hermes cron create \
  --name "market-sentinel-morning" \
  --schedule "0 8 * * 1-5" \
  --skill market-sentinel \
  --prompt "Run morning brief for market-sentinel. Send Telegram alert with today's market regime summary, correlation filter status, and key levels."

# Evening digest
hermes cron create \
  --name "market-sentinel-evening" \
  --schedule "0 18 * * 1-5" \
  --skill market-sentinel \
  --prompt "Run evening digest for market-sentinel. Send Telegram alert with today's strategy signal status, portfolio risk metrics, and next-day watchlist."
```

### 5. Test the skill

```bash
hermes run skill market-sentinel --mode dry-run --targets SPY,QQQ,BTC-USD
```

## Send Telegram Alert (Python)

```python
import subprocess, os

def send_telegram_alert(message: str) -> bool:
    """Send formatted market alert via Hermes Telegram integration."""
    result = subprocess.run(
        ["hermes", "send", "--platform", "telegram", "--chat", os.environ.get("TELEGRAM_MARKET_CHAT_ID", "")],
        input=message.encode(),
        capture_output=True
    )
    return result.returncode == 0
```

## Market Regime Detection (Python core)

```python
import yfinance as yf
import pandas as pd
import numpy as np

def fetch_candles(ticker: str, interval: str, period: str = "5d") -> pd.DataFrame:
    """Fetch candles via yfinance."""
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    return data

def mean_reversion_signal(prices: pd.Series, lookback: int = 20, threshold: float = 2.0) -> dict:
    """Mean reversion on 50-min candles. Returns: {signal: 'long'|'short'|'neutral', z_score: float}"""
    ma = prices.rolling(lookback).mean()
    std = prices.rolling(lookback).std()
    z = (prices - ma) / std
    latest_z = z.iloc[-1]
    if latest_z > threshold:
        return {"signal": "short", "z_score": round(latest_z, 3)}  # Price too far above mean
    elif latest_z < -threshold:
        return {"signal": "long", "z_score": round(latest_z, 3)}   # Price too far below mean
    return {"signal": "neutral", "z_score": round(latest_z, 3)}

def momentum_breakout(prices: pd.Series, lookback: int = 20, threshold_pct: float = 0.01) -> dict:
    """Momentum breakout on 1H candles. Returns: {signal: 'long'|'short'|'neutral', momentum_pct: float}"""
    ret = prices.pct_change(lookback)
    latest_ret = ret.iloc[-1]
    if latest_ret > threshold_pct:
        return {"signal": "long", "momentum_pct": round(latest_ret * 100, 3)}
    elif latest_ret < -threshold_pct:
        return {"signal": "short", "momentum_pct": round(latest_ret * 100, 3)}
    return {"signal": "neutral", "momentum_pct": round(latest_ret * 100, 3)}

def trend_following(prices: pd.Series, fast: int = 50, slow: int = 200) -> dict:
    """Trend following on 4H candles. Returns: {signal: 'long'|'short'|'neutral', edge_pct: float}."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    edge = (ema_fast - ema_slow) / ema_slow * 100
    latest = edge.iloc[-1]
    return {"signal": "long" if latest > 0 else "short", "edge_pct": round(latest, 4)} if abs(latest) > 0.5 else {"signal": "neutral", "edge_pct": round(latest, 4)}

def correlation_filter(spy_signal: str, qqq_signal: str) -> dict:
    """Correlation filter: suppress risk-on if both SPY and QQQ are long."""
    risk_on = spy_signal == "long" and qqq_signal == "long"
    return {
        "suppress_risk_on": risk_on,
        "reason": "SPY+QQQ both long — doubling exposure" if risk_on else "no filter triggered"
    }

def volatility_position_size(base_risk_pct: float = 1.0, atr: float = None) -> float:
    """Dynamic position sizing: base_risk / ATR. Returns position size as fraction of portfolio."""
    if atr is None or atr == 0:
        return base_risk_pct  # fallback to flat 1%
    return round(base_risk_pct / atr, 4)
```

## Integration with CloudGable / CloudCoworks

This skill is a **monitoring and alerting layer** — it does NOT replace the trading execution layer (CloudGable). The integration points are:

| External Service | What Hermes Does | What External Service Does |
|-----------------|-----------------|---------------------------|
| CloudGable | Monitors market conditions; alerts if strategy signals change | Executes actual trades |
| CloudCoworks | Feeds Hermes market data to CloudCoworks morning/night API | Sends Telegram briefings |
| Tradingview / Alert Webhooks | Receives Hermes alerts as webhook triggers | Triggers CloudGable automations |

To wire up CloudCoworks messaging:
```bash
# Night performance update via CloudCoworks API
curl -X POST "https://api.cloudcoworks.io/hermes/night-report" \
  -H "Authorization: Bearer $CLOUDCOWORKS_API_KEY" \
  -d "$(python3 market_sentinel_report.py --format json)"
```

## Limitations & Disclaimers

- **Not financial advice.** This skill is an informational monitoring tool only.
- yfinance data is non-realtime (15-min delay for US markets).
- Hard stop loss and position sizing rules are **informational alerts only** — Hermes cannot enforce these on the actual brokerage account.
- CloudGable/CloudCoworks API integration requires their respective accounts and API keys.

## Pitfalls

1. **yfinance rate limits** — Don't run the full strategy scan more than once per 15 minutes per ticker. Use `time.sleep(1)` between tickers.
2. **Wrong timezone** — Cron at `0 8 * * 1-5` runs in the server's local timezone. Market open is 09:30 ET — schedule for 08:00 ET (13:00 UTC) to pre-market.
3. **Correlation filter is one-way** — It only suppresses when BOTH SPY+QQQ are long. It does NOT protect against both being short simultaneously.
4. **Ghost signals** — If a candle is still forming (incomplete), the indicator may give false signals. Always check `volume` on the latest candle before acting.
5. **Holiday gaps** — US market holidays mean no 50-min candle data. The skill should skip SPY/QQQ on NYSE holidays.

## Verification

```bash
# Dry-run: verify all 5 tickers resolve and produce signals
python3 - << 'PYEOF'
import yfinance as yf, sys
tickers = ["SPY", "QQQ", "BTC-USD", "GC=F", "CL=F"]
for t in tickers:
    try:
        d = yf.download(t, period="5d", interval="1h", auto_adjust=True, progress=False)
        print(f"OK  {t}: {len(d)} candles, last close {d['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"ERR {t}: {e}")
        sys.exit(1)
print("All tickers OK")
PYEOF
```
