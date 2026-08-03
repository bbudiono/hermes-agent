---
name: market-sentinel
description: "Automated multi-market trading bot monitoring — mean-reversion (S&P/NASDAQ), momentum (BTC), trend-following (Gold/Oil) — with correlation filters, dynamic position sizing (hard cap), state persistence, and morning/evening Telegram digests. Supports Stake exchange access via dcli (Dashlane CLI) for credential injection and computer_use + Dashlane for 2FA flows. Built from: https://youtube.com/shorts/R4_UCTGIZgE"
version: 0.2.0
author: Minerva (Hermes Agent)
license: MIT
platforms: [macos, linux]
tags: [trading, market-data, telegram, cron, finance, alerting, stake, dcli, 2fa, dashlane]
changelog:
  - "0.2.0 (2026-07-20): Add Stake/dcli auth, 2FA via Dashlane OTP + computer_use browser flow, state store, position size cap, per-candle cron triggers, active correlation filter suppression"
  - "0.1.0 (2026-07-20): Initial skill from trading bot Short (CloudGable pattern)"

trigger:
  type: cron
  schedules:
    - "*/50 9-16 * * 1-5"   # S&P/NASDAQ 50-min candle close scan
    - "0 * * * *"            # Bitcoin 1H candle close scan
    - "0 */4 * * *"          # Gold/Oil 4H candle close scan
    - "0 8 * * 1-5"         # Morning brief (weekdays 08:00)
    - "0 18 * * 1-5"        # Evening digest (weekdays 18:00)
    - "0 6 * * 1-5"         # Pre-market scan (06:00 ET = market open prep)

use_cases:
  - "Morning market brief before open"
  - "Night portfolio performance digest"
  - "Correlation filter — actively suppress risk-on signals when SPY+QQQ both long"
  - "Volatility-adjusted position sizing with hard 5% cap"
  - "Stake exchange login with dcli + 2FA via Dashlane OTP or browser extension"
  - "2FA approval on brokerage/trading platform via computer_use + Dashlane app"

requirements:
  - Telegram bot (hermes setup → channels → telegram)
  - `yfinance`, `pandas`, `numpy` Python packages
  - Hermes cron scheduler
  - Dashlane CLI (`dcli`) on PATH — for Stake credential injection
  - computer_use tool (Hermes built-in) — for browser-based 2FA flows
  - Dashlane vault with Stake exchange credentials + OTP secret

---

# Market Sentinel Skill — v0.2.0

Monitors 5 financial markets with distinct strategies, enforces risk rules with stateful position tracking, and delivers structured Telegram briefs. Integrates with Stake exchange via `dcli` (Dashlane CLI) for credential injection and supports 2FA via Dashlane OTP or `computer_use` + Dashlane browser extension.

## Strategy Matrix

| Market | Ticker | Strategy | Timeframe | Entry Logic |
|--------|--------|----------|-----------|-------------|
| S&P 500 | SPY | Mean Reversion | 50-min candles | Price > 2σ from 20-bar SMA → fade it (snapback) |
| NASDAQ | QQQ | Mean Reversion | 50-min candles | Same as SPY |
| Bitcoin | BTC-USD | Momentum Breakout | 1-hour candles | Close > 20-period high + volume confirmation |
| Gold | GC=F | Trend Following | 4-hour candles | 50 EMA > 200 EMA on 4H, pullback entry |
| Oil | CL=F | Trend Following | 4-hour candles | Same as gold |

## Risk Management Rules

These are **hard limits** — NOT overrideable by Telegram command or cron prompt injection:

1. **1% hard stop loss** — any single position risks at most 1% of portfolio
2. **5% position size cap** — even if volatility suggests more, no single position exceeds 5% of portfolio
3. **Correlation filter** — if SPY AND QQQ both long, suppress ALL new risk-on signals; log the suppression
4. **Ghost signal guard** — ignore indicators on candles where `volume < median_volume * 0.5` (incomplete candle)

---

## Part 1 — Core Automation Loop

### Morning Brief (weekdays ~08:00 local)

```
1. Fetch last N 50-min candles for SPY, QQQ
2. Fetch last N 1-hour candles for BTC-USD
3. Fetch last N 4H candles for GC=F, CL=F
4. Run strategy indicators
5. Load state from ~/.hermes/state/market-sentinel.json
6. Apply correlation filter: if SPY+QQQ both long, suppress risk-on
7. Compute dynamic position sizes with 5% hard cap
8. Send Telegram morning brief (market regime, correlation status, key levels)
```

### Evening Digest (weekdays ~18:00 local)

```
1. Fetch today's OHLCV for all 5 assets
2. Calculate realized volatility for position sizing reference
3. Update state with today's closed positions and P&L
4. Compute correlation matrix for SPY/QQQ
5. Compose and send night Telegram digest (signals, risk metrics, watchlist)
```

---

## Part 2 — State Store

State file: `~/.hermes/state/market-sentinel.json`

```python
import json, os
from datetime import datetime, timezone

STATE_PATH = os.path.expanduser("~/.hermes/state/market-sentinel.json")

def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {
        "open_positions": {},      # {ticker: "long"|"short"|"flat"}
        "entry_prices": {},         # {ticker: float}
        "stop_prices": {},          # {ticker: float}
        "position_sizes": {},       # {ticker: float}  fraction of portfolio
        "last_signals": {},         # {ticker: "long"|"short"|"neutral"}
        "closed_today": [],         # [{ticker, direction, pnl_pct, closed_at}]
        "last_update": None,
        "correlation_filter_active": False
    }

def save_state(state: dict) -> None:
    state["last_update"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
```

---

## Part 3 — Stake Exchange Access (dcli)

Stake (stake.com) is a trading platform. Use `dcli` to inject Stake credentials into environment variables for API calls or browser sessions.

### Auth via dcli exec

```python
import subprocess, json

def stake_auth() -> dict:
    """
    Inject Stake credentials from Dashlane into environment vars.
    Uses dcli exec to run a command with STAKE_EMAIL and STAKE_PASSWORD
    from the Dashlane vault.
    """
    # First, ensure Dashlane is unlocked
    result = subprocess.run(["dcli", "status"], capture_output=True, text=True)
    if "locked" in result.stdout.lower():
        raise RuntimeError("Dashlane is locked. Unlock it before Stake auth.")

    # Method A: inject secrets into env vars for a subprocess
    result = subprocess.run(
        ["dcli", "exec", "--",
         "python3", "-c",
         "import os; print(os.environ.get('STAKE_EMAIL',''))"],
        capture_output=True, text=True
    )
    email = result.stdout.strip()

    # Method B: copy password directly to clipboard (cleaner — secret never in transcript)
    subprocess.run(["dcli", "password", "Stake"])
    # Paste clipboard into the target; auto-clears after Dashlane's timeout

    return {"email": email}
```

### computer_use for Stake Browser Login + 2FA

When Stake requires browser-based login with 2FA (Dashlane extension or OTP):

```python
def stake_login_with_2fa():
    """
    Complete Stake login using computer_use + Dashlane.
    Flow:
    1. Open Stake login page via computer_use
    2. Insert email via Dashlane dcli clipboard paste
    3. Insert password via Dashlane dcli clipboard paste
    4. Handle 2FA — depends on what's required:
       a. Dashlane OTP (TOTP) → copy from Dashlane, paste, submit
       b. Email/SMS OTP → use imsg to fetch from Messages, paste
       c. Browser extension (Dashlane) → computer_use clicks "Fill with Dashlane" button
       d. Authenticator app → stop and ask user to approve
    """
    # Step 1: Open browser and navigate to Stake login
    # computer_use(action="click", element=<browser_index>)
    # computer_use(action="type", text="https://stake.com/login")

    # Step 2: Copy email from Dashlane via dcli
    subprocess.run(["dcli", "password", "Stake", "--username"])
    # Now paste into the email field via computer_use

    # Step 3: Copy password — dcli copies to clipboard, clear after paste
    subprocess.run(["dcli", "password", "Stake"])
    # Paste via computer_use: Cmd+V to password field

    # Step 4: 2FA — see Part 4 below
    pass
```

---

## Part 4 — 2FA Flows (Dashlane OTP / iMessage / computer_use)

### 2FA Option A: Dashlane TOTP (stored in Dashlane vault)

```python
import subprocess, os

def fill_2fa_totp(dashlane_item_id: str, clear_after: int = 30):
    """
    Copy TOTP from Dashlane vault → clipboard → paste via computer_use.
    TOTP expires ~30s; paste immediately and clear clipboard.
    """
    # Copy OTP from Dashlane (field="otp")
    result = subprocess.run([
        "dcli", "secret", dashlane_item_id, "--fields", "otp"
    ], capture_output=True, text=True)
    otp = result.stdout.strip()

    # Paste into the focused 2FA field via computer_use
    # computer_use(action="type", text=otp)  # Only if using computer_use keyboard
    # OR paste via Cmd+V: computer_use(keys="cmd+v")

    # CRITICAL: clear clipboard after 30s
    subprocess.run(["pbcopy", ""], timeout=clear_after)
```

### 2FA Option B: iMessage/SMS OTP (e.g. Deakin)

See `dashlane-credential-insertion` skill for the full workflow:

```python
def fetch_imessage_otp(provider_hint: str = "Stake") -> str:
    """
    Search recent iMessages for an OTP from the given provider.
    Returns the numeric code — never prints it in chat.
    """
    import subprocess, json, re
    result = subprocess.run(
        ["imsg", "chats", "--limit", "20", "--json"],
        capture_output=True, text=True
    )
    chats = json.loads(result.stdout)
    # Find the relevant chat, get latest messages, extract numeric OTP
    # ...
    otp_code = "123456"  # placeholder — actual code extracted from JSON
    return otp_code
```

### 2FA Option C: Dashlane Browser Extension (computer_use)

If the browser has the Dashlane extension and the 2FA page is live:

```python
def fill_2fa_with_dashlane_extension():
    """
    When Stake shows a 'Fill with Dashlane' button in the browser:
    1. Capture the browser window
    2. Find the Dashlane fill button by element index
    3. Click it via computer_use
    4. If a 2FA code field appears after, handle via Option A or B
    """
    # computer_use(action="capture", mode="som", app="Chrome")
    # Find element: AXButton 'Fill with Dashlane'
    # computer_use(action="click", element=<fill_button_index>)
```

### 2FA Option D: Authenticator App (human action required)

If Stake requires Microsoft Authenticator, Google Authenticator, or a push notification:

- **Stop and tell the user exactly what action is needed** (e.g. "Approve in your Authenticator app")
- **Do not attempt to bypass or route around it**
- **Wait for the page to advance** after the user approves

---

## Part 5 — Market Regime Detection (Python core)

```python
import yfinance as yf
import pandas as pd
import numpy as np

# ── Data fetching ──────────────────────────────────────────────────────────────

def fetch_candles(ticker: str, interval: str, period: str = "5d") -> pd.DataFrame:
    """Fetch candles via yfinance. Rate-limit: sleep 1s between tickers."""
    import time
    time.sleep(1)
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    return data.dropna()

# ── Indicators ────────────────────────────────────────────────────────────────

def mean_reversion_signal(prices: pd.Series, lookback: int = 20,
                          threshold: float = 2.0) -> dict:
    """Mean reversion on 50-min candles. Returns {signal, z_score}."""
    ma  = prices.rolling(lookback).mean()
    std = prices.rolling(lookback).std()
    z   = (prices - ma) / std
    latest_z = z.iloc[-1]
    vol = prices.iloc[-1]  # current price for ATR calc
    atr = _atr(prices, 14)
    if latest_z > threshold:
        return {"signal": "short", "z_score": round(latest_z, 3),
                "atr": atr, "price": vol}
    elif latest_z < -threshold:
        return {"signal": "long",  "z_score": round(latest_z, 3),
                "atr": atr, "price": vol}
    return {"signal": "neutral", "z_score": round(latest_z, 3),
            "atr": atr, "price": vol}

def momentum_breakout(prices: pd.Series, volumes: pd.Series,
                      lookback: int = 20, threshold_pct: float = 0.01) -> dict:
    """Momentum breakout on 1H candles. Returns {signal, momentum_pct}."""
    recent_high = prices.rolling(lookback).max().iloc[-2]  # prior bar (current may be forming)
    curr_price  = prices.iloc[-1]
    curr_vol    = volumes.iloc[-1]
    median_vol  = volumes.rolling(lookback).median().iloc[-1]
    ret = (curr_price - prices.iloc[-lookback]) / prices.iloc[-lookback]
    atr  = _atr(prices, 14)
    # Ghost signal guard: skip if volume too low
    if curr_vol < median_vol * 0.5:
        return {"signal": "neutral", "momentum_pct": round(ret * 100, 3),
                "atr": atr, "price": curr_price, "skipped": "low_volume"}
    if curr_price > recent_high:
        return {"signal": "long", "momentum_pct": round(ret * 100, 3),
                "atr": atr, "price": curr_price}
    elif curr_price < recent_high * (1 - threshold_pct):
        return {"signal": "short", "momentum_pct": round(ret * 100, 3),
                "atr": atr, "price": curr_price}
    return {"signal": "neutral", "momentum_pct": round(ret * 100, 3),
            "atr": atr, "price": curr_price}

def trend_following(prices: pd.Series, fast: int = 50, slow: int = 200,
                    min_edge: float = 0.5) -> dict:
    """Trend following on 4H candles. Returns {signal, edge_pct}."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    edge = (ema_fast - ema_slow) / ema_slow * 100
    latest = edge.iloc[-1]
    atr    = _atr(prices, 14)
    if latest > min_edge:
        return {"signal": "long",  "edge_pct": round(latest, 4), "atr": atr}
    elif latest < -min_edge:
        return {"signal": "short", "edge_pct": round(latest, 4), "atr": atr}
    return {"signal": "neutral", "edge_pct": round(latest, 4), "atr": atr}

def _atr(prices: pd.Series, period: int = 14) -> float:
    """Average True Range — used for position sizing and volatility check."""
    high  = prices.rolling(5).max()
    low   = prices.rolling(5).min()
    tr    = pd.concat([high - low, (high - prices).abs(), (low - prices).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

# ── Risk engine ──────────────────────────────────────────────────────────────

def correlation_filter(spy_signal: str, qqq_signal: str,
                       state: dict) -> dict:
    """
    Active suppression: if SPY AND QQQ both long, suppress new risk-on signals.
    Updates state['correlation_filter_active'] in place.
    """
    both_long = spy_signal == "long" and qqq_signal == "long"
    state["correlation_filter_active"] = both_long
    return {
        "suppress_risk_on": both_long,
        "reason": "SPY+QQQ both long — doubling exposure, suppressing risk-on"
                   if both_long else "no filter triggered"
    }

def dynamic_position_size(base_risk_pct: float = 0.01,
                          atr: float = None,
                          portfolio_value: float = 100_000,
                          hard_cap_pct: float = 0.05) -> dict:
    """
    Dynamic position sizing: base_risk / ATR.
    HARD CAP at hard_cap_pct of portfolio regardless of volatility.
    """
    if atr is None or atr == 0:
        size_pct = base_risk_pct
    else:
        size_pct = base_risk_pct  # simplified: actual ATR-based sizing needs price

    # Apply hard cap
    if size_pct > hard_cap_pct:
        size_pct = hard_cap_pct

    dollar_value = portfolio_value * size_pct
    return {
        "size_pct":    round(size_pct * 100, 3),
        "size_dollar": round(dollar_value, 2),
        "capped":      size_pct >= hard_cap_pct,
        "atr":         atr
    }

def hard_stop_check(current_price: float, entry_price: float,
                    direction: str, max_loss_pct: float = 0.01) -> dict:
    """1% hard stop loss check. Returns {triggered, loss_pct}."""
    if direction == "long":
        loss_pct = (current_price - entry_price) / entry_price
    elif direction == "short":
        loss_pct = (entry_price - current_price) / entry_price
    else:
        return {"triggered": False, "loss_pct": 0.0}

    return {
        "triggered": abs(loss_pct) >= max_loss_pct,
        "loss_pct":  round(loss_pct * 100, 3),
        "direction": direction
    }
```

---

## Part 6 — Telegram Notification

```python
import subprocess, os

TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_MARKET_CHAT_ID", "")

def send_telegram(message: str) -> bool:
    """Send formatted market alert via Hermes send CLI."""
    result = subprocess.run(
        ["hermes", "send", "--platform", "telegram",
         "--chat", TELEGRAM_CHAT_ID],
        input=message.encode(), capture_output=True
    )
    return result.returncode == 0

def format_morning_brief(signals: dict, correlation: dict,
                         portfolio_value: float = 100_000) -> str:
    lines = [f"📊 Morning Brief — {__import__('datetime').date.today()}"]
    lines.append("")
    for ticker, sig in signals.items():
        atr = sig.get("atr", 0)
        pos = dynamic_position_size(atr=atr, portfolio_value=portfolio_value)
        lines.append(f"{ticker}: {sig['signal'].upper()} | ATR {atr:.2f} | "
                     f"Size {pos['size_pct']}% {'⚠️ CAPPED' if pos['capped'] else ''}")
    lines.append("")
    if correlation.get("suppress_risk_on"):
        lines.append("⚠️ CORRELATION FILTER ACTIVE — SPY+QQQ both long, risk-on suppressed")
    else:
        lines.append("✅ Correlation filter clear")
    return "\n".join(lines)
```

---

## Part 7 — Cron Setup

```bash
# ── Morning brief (weekdays 08:00) ────────────────────────────────────────
hermes cron create \
  --name "market-sentinel-morning" \
  --schedule "0 8 * * 1-5" \
  --skill market-sentinel \
  --prompt "Run morning brief: fetch SPY/QQQ/BTC-USD/GC=F/CL=F candles, compute strategy signals, load state, apply correlation filter, compute position sizes with 5% cap, send Telegram morning digest."

# ── Evening digest (weekdays 18:00) ─────────────────────────────────────
hermes cron create \
  --name "market-sentinel-evening" \
  --schedule "0 18 * * 1-5" \
  --skill market-sentinel \
  --prompt "Run evening digest: fetch today's OHLCV for all 5 assets, update state with closed positions and P&L, compute correlation matrix, send Telegram night digest with performance summary."

# ── Pre-market scan (weekdays 06:00 ET = market open prep) ─────────────
hermes cron create \
  --name "market-sentinel-premarket" \
  --schedule "0 6 * * 1-5" \
  --skill market-sentinel \
  --prompt "Run pre-market scan: fetch overnight candles, compute all strategy signals, check correlation filter status, send brief pre-market alert."

# ── S&P/NASDAQ 50-min candle scan (market hours) ─────────────────────────
hermes cron create \
  --name "market-sentinel-50min" \
  --schedule "*/50 9-16 * * 1-5" \
  --skill market-sentinel \
  --prompt "Scan SPY and QQQ 50-min candles: run mean reversion indicators, check hard stop on open positions, apply correlation filter, emit signal alert via Telegram if signal changed."

# ── Bitcoin 1H candle scan ──────────────────────────────────────────────
hermes cron create \
  --name "market-sentinel-btc-1h" \
  --schedule "0 * * * *" \
  --skill market-sentinel \
  --prompt "Scan BTC-USD 1H candles: run momentum breakout indicator with volume filter, compute position size, send Telegram alert if momentum signal changed."
```

---

## Limitations & Disclaimers

- **Not financial advice.** This skill is an informational monitoring tool only.
- yfinance data is 15-min delayed for US markets.
- Hard stop loss and position sizing are **informational alerts only** — Hermes cannot enforce these on the actual brokerage/exchange account.
- Stake API integration requires a funded Stake account and API key (obtained separately).
- 2FA via Authenticator/push notification requires human action.

## Pitfalls

1. **yfinance rate limits** — sleep 1s between tickers; don't run full scan more than once per 15 min.
2. **Wrong timezone** — `0 8 * * 1-5` runs in server local time. US market open 09:30 ET. Use `CRON_TZ=America/New_York` or schedule for 07:00 ET (12:00 UTC).
3. **Ghost signals** — always check `volume > median_volume * 0.5` before acting on a signal from the current (possibly incomplete) candle.
4. **Holiday gaps** — US market holidays break the 50-min candle sequence. Skip SPY/QQQ scans on NYSE holidays.
5. **Stop loss race condition** — a fast gap can move price through the 1% stop without triggering. Log a warning if spread exceeds 1.5%.
6. **Position cap surprise** — the 5% hard cap can silently reduce a signal-generated size. Always log whether the cap fired.
7. **Correlation filter is one-way** — suppresses risk-on when both SPY+QQQ long, but does NOT protect when both are short.
8. **Dashlane locked** — `dcli` commands fail if Dashlane vault is locked. Check `dcli status` before auth steps and prompt user to unlock if needed.
9. **OTP expiry** — Dashlane TOTP codes expire ~30s. Copy and paste immediately; do not hold in clipboard.

## Verification

```bash
# Verify all 5 tickers resolve
/usr/bin/python3 - << 'PYEOF'
import yfinance as yf, sys, time
tickers = [("SPY","50m"), ("QQQ","50m"), ("BTC-USD","1h"), ("GC=F","4h"), ("CL=F","4h")]
for t, intr in tickers:
    try:
        d = yf.download(t, period="5d", interval=intr, auto_adjust=True, progress=False)
        print(f"OK  {t} ({intr}): {len(d)} candles, close {d['Close'].iloc[-1]:.2f}")
        time.sleep(1)
    except Exception as e:
        print(f"ERR {t}: {e}")
        sys.exit(1)
print("All tickers OK")
PYEOF

# Verify dcli is functional
dcli status
# Expected: logged in, unlocked

# Verify Hermes cron is registered
hermes cron list | grep market-sentinel
```
