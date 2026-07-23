---
name: crawl4ai
description: "Crawl4AI: LLM-friendly web crawler and scraper. Convert any website into clean data ready for AI models. Source: https://github.com/unclecode/crawl4ai (67.8K GitHub stars, 2M downloads/month)"
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
tags: [web, crawler, scraper, llm, ai, data-extraction]
source: https://github.com/unclecode/crawl4ai
install: pip install crawl4ai
---

# Crawl4AI

Crawl4AI is an open-source LLM-friendly web crawler and scraper. It converts any website into clean, structured data ready for AI models — handles JavaScript-heavy pages that most scrapers struggle with.

**Key stats:** 67.8K GitHub stars, 2M downloads/month

## Core Use Cases

- **LLM data preparation** — crawl and extract clean markdown/HTML for RAG pipelines
- **Research automation** — pull content from multiple sites for synthesis
- **Bulk scraping** — extract data from thousands of pages efficiently
- **JavaScript-heavy sites** — handles SPAs, dynamic content, lazy-loaded pages

## Installation

```bash
pip install crawl4ai
```

Or with Docker:
```bash
docker pull unclecode/crawl4ai
```

## Basic Usage

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.araw_crawl("https://example.com")
        print(result.markdown)  # Clean markdown output
        print(result.html)      # Cleaned HTML

asyncio.run(main())
```

## Key Features

| Feature | Description |
|---------|-------------|
| `markdown` | Returns clean markdown (best for LLMs) |
| `html` | Returns cleaned HTML |
| `metadata` | Returns page metadata |
| `js_content` | Execute JS before extracting (for SPAs) |

## Verification

```bash
python3 -c "from crawl4ai import AsyncWebCrawler; print('crawl4ai OK')"
```

## Integration with Hermes Ecosystem

Crawl4AI is a **free self-hosted alternative** to Firecrawl and Tavily. Use it for bulk research, RAG data preparation, and web extraction that doesn't need managed APIs.

## Pitfalls

1. **Infrastructure** — you manage your own crawler instances
2. **JS pages** — may need `js_code` parameter to wait for hydration
3. **Respect robots.txt** — check before bulk crawling
4. **Cloud API** — Crawl4AI Cloud in closed beta if you want managed option

## Related Skills

- `browser-use` — autonomous AI browser agent for interactive web tasks
- `firecrawl` or `web_search` — quick single-page lookups
