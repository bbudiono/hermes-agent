---
name: browser-use
description: "Use Browser Use to command an AI agent to navigate and use any website — fill forms, shop, make bookings, scrape data on demand. Source: https://github.com/browser-use/browser-use (105K GitHub stars)"
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
tags: [browser, automation, web, scraping, ai-agent]
source: https://github.com/browser-use/browser-use
install: pip install browser-use
---

# Browser Use

Browser Use lets an AI agent use a web browser the same way a human does — it opens pages, clicks buttons, types, and fills forms. You describe the task in natural language, and it completes it autonomously.

**Key stats:** 9.5M downloads/week, 105K GitHub stars

## Core Use Cases

- **Form filling** — automate login, registration, data entry
- **Web scraping** — extract structured data from any website on demand
- **Booking** — flight, hotel, appointment booking automation
- **Shopping** — price monitoring, cart automation
- **Research** — navigate multiple pages, extract key info, compile report

## Installation

```bash
pip install browser-use
```

Requires Python 3.10+ and Chrome/Chromium installed.

## Basic Usage

```python
from browser_use import Agent
from langchain_openai import ChatOpenAI

agent = Agent(
    task="Go to example.com, find the contact form, and fill it with name=test, email=test@example.com",
    llm=ChatOpenAI(model="gpt-4o"),
)
agent.run()
```

## With Ollama (local models)

```python
from browser_use import Agent
from langchain_ollama import ChatOllama

agent = Agent(
    task="Find the cheapest flight from Sydney to Melbourne next Friday",
    llm=ChatOllama(model="llama3.3"),
)
agent.run()
```

## With Claude via Anthropic API

```python
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

agent = Agent(
    task="Log into stake.com.au and check my account balance",
    llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
)
agent.run()
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| `task` | Natural language description of what to do |
| `llm` | LangChain LLM instance (OpenAI, Anthropic, Ollama, etc.) |
| `browser` | Optional browser config (headless, viewport, etc.) |
| `max_steps` | Max steps before stopping (default: auto) |

## Verification

```bash
python3 -c "from browser_use import Agent; print('browser-use OK')"
```

## Integration with Hermes Ecosystem

Browser Use complements the existing `computer-use` skill:

- `computer-use` — drives the **local macOS desktop** in background (cua-driver)
- `browser-use` — drives a **headless browser** on any website autonomously

Browser Use can handle websites that require JS rendering, form submissions, and multi-step flows that static scraping cannot.

## Pitfalls

1. **Requires Chrome/Chromium** — install via `brew install chromium` or download from google.com/chrome
2. **API costs** — if using OpenAI/Anthropic API, costs accrue per page/click. Use Ollama for free local inference
3. **Anti-bot detection** — some sites (Cloudflare, CAPTCHAs) will block automated browsers
4. **Headless by default** — set `headless=False` for debugging to watch the browser work

## Related Skills

- `computer-use` — local macOS desktop automation (cua-driver)
- `crawl4ai` — LLM-optimized web crawler for bulk scraping
