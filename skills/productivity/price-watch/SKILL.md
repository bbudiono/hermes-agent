---
name: price-watch
description: "Use when setting up automated price drop monitoring for hardware (GPUs, CPUs, etc.) and triggering Telegram alerts when thresholds are met."
version: 0.1.0
author: Hermes Agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [price-watch, cron, telegram-alert, hardware-monitoring, microcenter, bestbuy, nvidia]
    source: youtube/eHZ14afnDZ0
    related_skills: [cronjob, platform-messaging-ops]
---

# Price Watch — Hardware Price Drop Monitor

## Overview

Hermes acts as a 24/7 price watchdog for scarce hardware (GPUs, CPUs, pre-built machines). Cron jobs poll retail sites daily, and when a price drop or availability change is detected, Hermes sends a Telegram alert.

**Primary use case**: Microcenter and Best Buy for NVIDIA RTX 5090 / RTX 5080 / high-demand GPUs, plus any other hardware the user wants to track.

## When to Use

- User wants to track a specific product for price drops or back-in-stock alerts
- User wants a recurring cron job to check retailer sites automatically
- User wants Telegram push notifications when a deal is found
- **Trigger phrase**: "watch for price drops", "notify me when RTX is in stock", "track GPU prices"

## Workflow

### Step 1 — Identify the Product URL

Provide Hermes with the exact product page URL from the retailer. Example targets:
- Microcenter: `https://www.microcenter.com/product/[sku]`
- Best Buy: `https://www.bestbuy.com/site/[slug]`
- Newegg: `https://www.newegg.com/p/[id]`

### Step 2 — Create the Cron Job

Use the `cronjob` tool with a script that:
1. Fetches the product page
2. Extracts current price and stock status
3. Compares against last known state
4. If changed, sends Telegram message

Example cron prompt (inline script mode):
```
Every day at 09:00, check Microcenter for RTX 5090 price. If price dropped below $X OR item is back in stock, send a Telegram alert to Home channel with the current price and product URL.
```

### Step 3 — Script Implementation Pattern

```python
# price_watch.py — runs as no_agent cron script
import urllib.request
import json
import os
import sys

PRODUCT_URL = "https://www.microcenter.com/product/..."
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_HOME_CHAT_ID")
PRICE_FILE = os.path.expanduser("~/.minerva/data/price_watch_rtx5090.json")

def get_price(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        # Parse HTML for price; use re or BeautifulSoup
        ...

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def main():
    price, in_stock = get_price(PRODUCT_URL)
    prev = {}
    if os.path.exists(PRICE_FILE):
        prev = json.load(open(PRICE_FILE))
    
    changed = prev.get("price") != price or prev.get("in_stock") != in_stock
    if changed:
        msg = f"🚨 RTX 5090 Update\nPrice: ${price}\nIn Stock: {in_stock}\nURL: {PRODUCT_URL}"
        send_telegram(msg)
    
    json.dump({"price": price, "in_stock": in_stock}, open(PRICE_FILE, "w"))

if __name__ == "__main__":
    main()
```

### Step 4 — Deploy

```bash
hermes cron create \
  --name "RTX 5090 Price Watch" \
  --script ~/.minerva/scripts/price_watch.py \
  --schedule "0 9 * * *" \
  --no-agent \
  --deliver origin
```

## Supported Retailers

| Retailer | Notes |
|----------|-------|
| Microcenter | Best for GPUs in-store + online; often has stock before others |
| Best Buy | US-wide online; good for RTX Founder Edition cards |
| Newegg | Often has third-party cards; better availability during shortages |
| B&H Photo | Good for workstation GPUs (RTX 6000, Ada) |
| Amazon | Higher prices but reliable fulfillment |

## Threshold Strategy

- **Price drop**: Set a target price (e.g., RTX 5090 at $1,599 instead of $1,999 MSRP)
- **Back-in-stock**: Alert on any stock change regardless of price
- **Historical low**: Alert if price is 10%+ below 30-day average

## Common Pitfalls

1. **Retailer blocks scraping**: Use Cloudflare-scraping workarounds or Firecrawl if direct HTTP fails
2. **No persistent state**: Always store last known price in a file or Nexus memory to detect changes
3. **Too many alerts**: Rate-limit to once per day; don't spam if price oscillates around threshold
4. **Chat ID changes**: Use the canonical Home channel chat ID from the user's config, not hardcoded

## Telegram Integration

See `platform-messaging-ops` skill for how to send Telegram messages from cron scripts. The canonical pattern uses the bot token + chat ID via the Bot API `sendMessage` endpoint.

## Nexus Persistence

- Log each alert to a Nexus Memory artifact for the user's price watch history
- Include: date, product, price, retailer, URL, stock status
