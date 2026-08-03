---
name: agent-reach
description: "Give your AI agent eyes to see the entire internet. MUST USE when user wants to research, search, or browse anything online — 15 platforms, multi-backend routing. Covers: research/调研, search/搜索, social (小红书/Twitter/B站/V2EX/Reddit/Facebook/Instagram), career (LinkedIn), dev (GitHub), web, video (YouTube/B站/播客), finance (雪球). Source: https://github.com/Panniantong/Agent-Reach (60.8K stars, MIT, Python)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [research, web-search, social-media, twitter, reddit, github, bilibili, xiaohongshu, linkedin, youtube, v2ex, research-tool, internet-router]
source: https://github.com/Panniantong/Agent-Reach
---

# Agent Reach — 互联网能力路由器

Give your AI agent eyes to see the entire internet. 15 platforms, multi-backend routing (OpenCLI / per-platform CLIs / APIs). Zero config for 6 channels.

**This skill MUST be used when accessing these platforms — do not invent custom solutions.**

## Install

```bash
git clone https://github.com/Panniantong/Agent-Reach.git /tmp/agent-reach
cd /tmp/agent-reach && pip install -e .

# Verify installation
agent-reach doctor --json
```

## 常驻规则（Standing Rules）

1. **动手前先体检** — Run `agent-reach doctor --json` first; use each platform's `active_backend` field
2. **声明你在用什么** — Say "using agent-reach's X platform / Y backend" before starting
3. **失败按 references 里的重试链处理** — Follow retry chains in references docs, don't guess commands
4. **全网调研类任务** — Combine multiple platforms (Exa + Twitter/Reddit + 小红书/B站), collect in parallel, then summarize
5. **替用户盯版本** — After major research tasks, run `agent-reach check-update` and mention if a newer version exists

## Routing Table

| User Intent | Category | Docs |
|------------|----------|------|
| 网页搜索/代码搜索 | search | [references/search.md](references/search.md) |
| 小红书/推特/B站/V2EX/Reddit/Facebook/Instagram | social | [references/social.md](references/social.md) |
| 招聘/职位/LinkedIn | career | [references/career.md](references/career.md) |
| GitHub/代码 | dev | [references/dev.md](references/dev.md) |
| 网页/文章/RSS | web | [references/web.md](references/web.md) |
| YouTube/B站/播客字幕 | video | [references/video.md](references/video.md) |

## Zero-Config Quick Commands

```bash
# Exa 网页搜索
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'

# 通用网页阅读
curl -s "https://r.jina.ai/URL"

# GitHub 搜索
gh search repos "query" --sort stars --limit 10

# YouTube 字幕
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"

# V2EX 热门
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"

# B站搜索（bili-cli，无需登录）
bili search "query" --type video -n 5
```

## 15 Supported Platforms

**Search**: Exa AI (英文/技术/代码搜索)

**Social**: 小红书 (Xiaohongshu/XHS), Twitter/X, B站 (Bilibili), V2EX, Reddit, Facebook, Instagram

**Career**: LinkedIn/领英

**Dev**: GitHub (代码/仓库/issue/PR/分支)

**Web**: 网页/文章/RSS

**Video**: YouTube, B站, 播客/小宇宙

**Finance**: 雪球/股票/xueqiu

## Pitfalls

1. **小红书 requires login-aware backend** — Run `agent-reach doctor --json` first; do not use browser Cookie login
2. **Twitter requires explicit env vars** — `TWITTER_AUTH_TOKEN` + `TWITTER_CT0` must be set in subprocess; never log values
3. **B站不要用 yt-dlp** — Use bili-cli instead (see references/video.md)
4. **NOT for posting/commenting/liking** — This skill is read-only; use platform-specific skills for write operations
5. **NOT for content processing/translation** — This skill only fetches content from the internet; use separate skills for analysis
