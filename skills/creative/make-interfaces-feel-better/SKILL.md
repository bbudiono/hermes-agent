---
name: make-interfaces-feel-better
description: "Design engineering principles for making interfaces feel polished. Use when building UI components, reviewing frontend code, implementing animations, hover states, shadows, borders, typography, icons, micro-interactions, or any visual detail work. Supports quick and full review modes. Source: https://github.com/jakubkrehel/make-interfaces-feel-better (2.5K stars, MIT)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [ui, design, frontend, animations, typography, icons, polish, review, css, tailwind, framer-motion]
source: https://github.com/jakubkrehel/make-interfaces-feel-better
---

# Make Interfaces Feel Better

An agent skill focused on the small details that make interfaces feel polished. Covers animations, typography, icons, hover states, optical alignment, concentric border radius, shadows, hit areas, and other interface details.

## Install

**Source install** (recommended for Hermes):

```bash
# Clone and copy the skill directory
git clone https://github.com/jakubkrehel/make-interfaces-feel-better.git /tmp/make-interfaces-feel-better
cp -r /tmp/make-interfaces-feel-better/skills/make-interfaces-feel-better ~/.minerva/skills/creative/
```

**Keep the directory intact** — `SKILL.md` links to `references/typography.md`, `references/surfaces.md`, `references/animations.md`, `references/icons.md`, and `references/performance.md` with relative paths. Copying only `SKILL.md` drops the detailed guidance.

---

## Quick Reference

| Category | When to Use |
| --- | --- |
| [Typography](references/typography.md) | Text wrapping, font smoothing, tabular numbers |
| [Surfaces](references/surfaces.md) | Border radius, optical alignment, shadows, image outlines, hit areas |
| [Animations](references/animations.md) | Interruptible animations, enter/exit transitions, icon animations, scale on press, motion restraint |
| [Icons](references/icons.md) | Icon stroke weight, states via `currentColor`, outline vs fill, sizing, RTL flipping |
| [Performance](references/performance.md) | Transition specificity, `will-change` usage |

## Review Modes

```
skill_view("creative/make-interfaces-feel-better")
/make-interfaces-feel-better          # full review
/make-interfaces-feel-better quick   # shorter review
/make-interfaces-feel-better full pricing page
```

Reviews return prioritized findings with exact locations, proposed changes, reasoning, verification, rejected candidates, and an explicit verdict.

## 14 Core Principles

1. **Concentric Border Radius** — Outer radius = inner radius + padding
2. **Optical Over Geometric Alignment** — Manual adjustment for asymmetric elements
3. **Shadows for Elevation, Borders for Structure** — Layered box-shadow over borders for depth
4. **Interruptible Animations** — CSS transitions for state changes, keyframes for one-shot sequences
5. **Split and Stagger Enter Animations** — ~100ms stagger between semantic chunks
6. **Subtle Exit Animations** — Small fixed translateY, softer than enters, ease-out
7. **Contextual Icon Animations** — scale(0.25→1), opacity(0→1), blur(4px→0); use framer-motion when available, CSS transitions otherwise
8. **Font Smoothing** — `-webkit-font-smoothing: antialiased` on macOS
9. **Tabular Numbers** — `font-variant-numeric: tabular-nums` for dynamically updating numbers
10. **Text Wrapping** — `text-wrap: balance` on headings, `text-wrap: pretty` on body
11. **Image Outlines** — 1px `oklch(0 0 0 / 0.1)` light / `oklch(1 0 0 / 0.1)` dark; pure black/white only
12. **Scale on Press** — `scale(0.96)` on click; never smaller than 0.95
13. **Skip Animation on Page Load** — `initial={false}` on AnimatePresence
14. **Never Use `transition: all`** — Always specify exact properties

## Key Rules

- **Match the project's existing styling system** — Tailwind in Tailwind projects, plain CSS in CSS projects, established CSS-in-JS approach
- **Slow the interface down** — Replay motion at 10% speed in browser Animations panel; walk every state: hover, focus, active, loading, empty
- **Motion restraint** — Don't stagger routine, high-frequency interactions
- **Bounce = 0** — Always set `bounce: 0` when using framer-motion spring animations

## Pitfalls

1. **Never introduce a second styling system** to apply a polish fix
2. **Tinted image outlines pick up surface color** — Only pure black/white work correctly
3. **Keyframes vs transitions** — Transitions can be interrupted mid-animation; keyframes cannot
4. **Verify `initial={false}`** doesn't break intentional entrance animations on first render
5. **framer-motion vs CSS** — Use the project's existing motion library; CSS-only when none is installed
