---
name: openmontage
description: "Agentic video production system — 12 production pipelines, 100+ tools, 700+ skill files. Turn any AI coding assistant into a full video production studio. Source: https://github.com/calesthio/OpenMontage (42K stars, AGPL-3.0, Python)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [video, production, agentic, ai-video, remotion, ffmpeg, animation, documentary, cinematic, narration, subtitles]
source: https://github.com/calesthio/OpenMontage
---

# OpenMontage

The first open-source, agentic video production system. Describe what you want in plain language — the agent handles research, scripting, asset generation, editing, and final composition.

## Install

```bash
# Prerequisites: Python 3.10+, FFmpeg, Node.js 18+
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Linux

# Clone and setup
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage
make setup

# Add API keys to .env (optional — more keys = more tools)
# Image + video gateway, TTS, music providers
cp .env.example .env
```

**Requirements:**
- Python 3.10+
- FFmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)
- Node.js 18+
- An AI coding assistant (Claude Code, Cursor, Copilot, Windsurf, Codex — or Hermes)

---

## Core Concept

OpenMontage is **pipeline-driven**. Every video request is a pipeline selection problem:

```
research -> proposal -> script -> scene_plan -> assets -> edit -> compose
```

Each stage has a dedicated **director skill** — a markdown file teaching the agent how to execute that stage. The agent reads the skill, uses the tools, self-reviews, checkpoints state, and asks for human approval at creative decision points.

## 12 Production Pipelines

| Pipeline | Produces | Best For |
|----------|----------|----------|
| Animated Explainer | AI explainer with research, narration, visuals, music | Education, tutorials |
| Animation | Motion graphics, kinetic typography | Social media, product demos |
| Avatar Spokesperson | Avatar-driven presenter videos | Corporate comms, training |
| Cinematic | Trailer, teaser, mood-driven edits | Brand films, promos |
| Clip Factory | Batch short-form clips from long source | Repurposing content |
| Documentary Montage | Thematic montage from free stock footage | Video essays, real-footage B-roll |
| Hybrid | Source footage + AI support visuals | Enhancing existing footage |
| Localization & Dub | Subtitle, dub, translate | Multi-language distribution |
| Podcast Repurpose | Podcast highlights to video | Podcast marketing |
| Screen Demo | Polished software screen recordings | Product demos, docs |
| Talking Head | Footage-led speaker videos | Presentations, vlogs |

## Two Composition Modes

1. **Pipeline mode** — structured 7-stage flow, reusable components
2. **Atelier (bespoke) mode** — hand-crafted scenes from scratch, no shared components

## Usage

Open the project in your AI coding assistant and describe what you want:

```
"Make a 60-second animated explainer about how neural networks learn"
```

Or start from a reference video:

```
"Here's a YouTube Short I love. Make me something like this, but about quantum computing."
```

The agent will:
1. Research the topic with live web search
2. Generate AI images / source stock footage
3. Write and narrate the script with voice direction
4. Find royalty-free background music automatically
5. Burn in word-level subtitles
6. Render the final video via Remotion

## Agent Integration (OpenClaw / Hermes)

If you're an agentic reader, the shortest path to becoming useful:

1. Read `AGENT_GUIDE.md`, then `PROJECT_CONTEXT.md`
2. Do NOT improvise the production workflow — go through `pipeline_defs/` + stage director skills in `skills/pipelines/`
3. Check capability envelope:
   ```bash
   python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.support_envelope(), indent=2))"
   python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.provider_menu(), indent=2))"
   ```
4. Treat every video request as a pipeline selection problem

## Pitfalls

1. **Web research is a first-class stage** — agent searches YouTube, Reddit, HN, news, academic sources before writing script
2. **Self-review before output** — ffprobe validation, frame sampling, audio levels, delivery promise verification, subtitle checks
3. **Provider selection scored across 7 dimensions** with auditable decision log
4. **Every creative decision gets human approval** — checkpoints, not fire-and-forget
5. **Real footage vs image-based** — Documentary Montage uses actual motion clips from free archives, not animated stills
