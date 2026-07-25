---
name: defuddle
description: "Extract the main content of any web page as clean Markdown or HTML. Strips clutter like ads, sidebars, headers, footers, and nav. Built by kepano (Obsidian Web Clipper author). Source: https://github.com/kepano/defuddle (8.5K stars)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows, browser, node]
tags: [web, scraping, content-extraction, markdown, readability]
source: https://github.com/kepano/defuddle
---

# Defuddle

## Install

```bash
# Node.js / npm
npm install defuddle

# Or clone for development
git clone https://github.com/kepano/defuddle.git && cd defuddle && npm install
```

**Requirements:** Node.js 18+ (for ESM support)

**Python wrapper (via subprocess):** `pip install readability` as fallback for Python environments.

---

Defuddle extracts the **main content** of any web page as clean Markdown or HTML — removing all the clutter (ads, sidebars, headers, footers, nav, comments) that makes web scraping messy.

It was built for the [Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper) but runs in any environment: browser, Node.js, or via CLI.

## Usage

### JavaScript (Node.js with JSDOM)

```javascript
import { JSDOM } from 'jsdom';
import { Defuddle } from 'defuddle/node';

const dom = new JSDOM(html, { url: 'https://example.com/article' });
const result = await Defuddle(dom.window.document, 'https://example.com/article', {
  markdown: true
});

console.log(result.content);   // Clean Markdown
console.log(result.title);     // Page title
console.log(result.author);    // Author (if detected)
console.log(result.excerpt);   // Meta description
```

### JavaScript (Browser)

```javascript
import Defuddle from 'defuddle';

const defuddle = new Defuddle(document);
const result = defuddle.parse();

console.log(result.content);  // Clean HTML
console.log(result.title);   // Page title
```

### CLI

```bash
npx defuddle https://example.com/article --markdown
```

## Key Features

- **Clean Markdown output** — ready for LLM consumption or Obsidian import
- **Metadata extraction** — title, author, date, excerpt, Open Graph data
- **Schema.org support** — Article, Product, Recipe, Event, etc.
- **Footnotes, math, code blocks** — preserved in consistent format
- **Mobile-first** — uses mobile styles to identify essential content
- **Mozilla Readability alternative** — more forgiving, removes fewer uncertain elements

## Comparison with alternatives

| Feature | Defuddle | Mozilla Readability |
|---------|----------|-------------------|
| Markdown output | ✅ | ❌ (HTML only) |
| Metadata extraction | ✅ title, author, date, OG | title + excerpt |
| Schema.org support | ✅ | ❌ |
| Math/KaTeX | ✅ | ❌ |
| Footnotes | ✅ | ❌ |

## Pitfalls

1. **WIP** — Defuddle is marked as "work in progress" by the author
2. **Node ESM** — requires Node 18+ for ES module support
3. **URL required** — pass the page URL for best extraction accuracy
4. **No Python native** — use `readability` (Mozilla) or `trafilatura` as Python alternatives
