---
name: ai-game-studio
description: "Use when building, generating, or iterating on 3D games autonomously with Hermes as the AI game director. Unity engine is the recommended backend."
version: 0.1.0
author: Hermes Agent
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [game-development, unity, 3d, ai-game-studio, game-engine, asset-generation]
    source: youtube/eHZ14afnDZ0
    related_skills: [home-ai-lab]
---

# AI Game Studio

## Overview

Hermes can act as a fully autonomous 3D game studio — generating assets, characters, environments, lighting, loot systems, and game logic by controlling the Unity engine front-to-back. The human sets the brief; Hermes builds the game.

**Recommended engine**: Unity (free tier; best AI compatibility per testing across Unity/Unreal/Three.js)

## When to Use

- User wants to generate a complete 3D game from a prompt
- User wants AI-generated game assets (textures, models, sounds) without external tools
- User wants Hermes to autonomously build a Unity project (C# scripts, scene setup, lighting, physics)
- User wants to prototype a game mechanic or world rapidly
- **Trigger phrase**: "build me a game", "create a 3D world", "generate a game with AI", "Unity game studio"

## Workflow

### Step 1 — Scaffold Unity Project

Hermes creates the project structure:
```bash
unity-helper create --name "MyGame" --template 3D
# Or use Unity Hub CLI to create project
```

### Step 2 — Generate Assets with Hermes

Feed Hermes a detailed prompt:
> "Build a 3D extraction shooter in Unity. Full loot system, enemy AI with pathfinding, complex 3D lighting. Include: player spawn, 3 enemy types, loot tables, day/night lighting cycle, and extraction zone."

Hermes will:
1. Generate C# scripts for game logic
2. Create scene hierarchy in Unity
3. Configure lighting (Volumetric, HDRP/URP)
4. Set up NavMesh for enemy AI
5. Define loot table JSON and spawn logic

### Step 3 — Key Unity Packages for AI Compatibility

Ensure these are installed in Unity:
- **Unity ProGrids** — snapping for procedural generation
- **Unity Visual Scripting** — optional node-based scripting for non-coders
- **TextMeshPro** — UI text
- **Newtonsoft JSON** — loot/inventory serialization
- **Unity UI (uGUI)** — standard UI

### Step 4 — Build and Test

```bash
# Hermes drives the build
unity-helper build --platform macOS --output ./build/MyGame.app
```

### Step 5 — Iterate via Natural Language

The user refines the game via chat:
- "Add a fourth enemy type with ranged attacks"
- "Make the lighting moodier — darker, more contrast"
- "Add a loot rarity system with 5 tiers"

## What Hermes Can Generate Autonomously

| Category | Capability |
|----------|-----------|
| Geometry | Procedural room/corridor generation, terrain |
| Characters | Basic humanoid rigs, enemy types, NPCs |
| Textures/Materials | Procedural PBR materials, normal maps |
| Lighting | Dynamic day/night, volumetric, global illumination |
| Audio | Basic ambient loops, trigger-based sound effects |
| Game Logic | Player movement, health, inventory, enemy AI, loot |
| UI | HUD, inventory screens, main menu |

## Limitations

- Hermes generates **prototypes**, not polished shipped games
- Complex physics (ragdolls, fluid simulation) still require manual tuning
- Asset quality depends on prompt specificity
- Unity personal edition has platform build restrictions

## Common Pitfalls

1. **Overly complex first prompt**: Start with a single mechanic (e.g., "just player movement + one enemy + extraction zone"), then expand.
2. **No build testing**: Always verify the Unity build works on target platform before adding more complexity.
3. **Missing error handling**: Hermes-generated C# may not handle null references or edge cases — review scripts before adding to scene.
4. **Large project syndrome**: Keep scenes small and modular; Hermes works better on focused tasks than monolithic scenes.

## Skill Integration

- `home-ai-lab`: Local models can be used to generate textures and audio locally (Stable Diffusion for textures, AudioCraft for sound)
- `mlx-local-inference`: For local asset generation pipelines without cloud dependency
