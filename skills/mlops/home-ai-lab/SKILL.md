---
name: home-ai-lab
description: "Use when setting up, expanding, or managing a Home AI Lab: hardware audit, local model discovery on Hugging Face, MLX/Ollama model loading, and a local AI control panel dashboard."
version: 0.1.0
author: Hermes Agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [local-ai, home-lab, huggingface, mlx, ollama, unity, game-studio]
    source: youtube/eHZ14afnDZ0
    related_skills: [mlx-local-inference, gaming-automation-ops]
---

# Home AI Lab

## Overview

A Home AI Lab is a personal infrastructure layer: one or more Macs/Linux machines running local AI models 24/7, accessible via a unified control panel. Hermes (powered by GPT-5.6 Soul) acts as the conductor — auditing hardware, discovering models, loading them, and managing workloads across machines.

**Core principle**: Every device can run local AI. Hardware constraints determine which model, not whether it's possible.

## When to Use

- User wants to find the best local model for their hardware (Mac Studio, Mac Mini, old laptop, etc.)
- User wants a unified dashboard showing all running local models across their machines
- User wants to assign jobs to local models (coding, inference, testing) from Hermes
- User wants to build custom front-ends (ChatGPT-like UI, Codex clone) on top of local models
- **Trigger phrase**: "set up my home AI lab", "find models for my Mac", "run local AI at home"

## Workflow

### Step 1 — Hardware Audit

Have Hermes run:
```bash
# macOS
system_profiler SPHardwareDataType SPDisplaysDataType SPMemoryDataType | grep -E "Chip|RAM|Graphics|Memory"

# Linux
lscpu | grep -E "Model name|CPU\(s\)|Thread"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv 2>/dev/null
free -h
```

Or delegate to the `mlx-local-inference` skill to benchmark existing models.

### Step 2 — Hugging Face Model Discovery

Use the `mlx-local-inference` skill for Apple Silicon. For general Linux/GPU hardware, search HF programmatically:
```bash
# Find models by hardware tag (example: RTX 5090 / CUDA / Linux)
curl -s "https://huggingface.co/api/models?tags=llama,text-generation&sort=downloads&direction=-1&limit=10" | jq '.[].id'
```

The recommended prompt to send to Hermes (GPT-5.6 Soul) is:
> "Check out the hardware and specs on my computer, then go through Hugging Face and find the best local AI model I can run on it. Then list the use cases I can do with that model."

### Step 3 — Load and Run Models

Use the appropriate runtime:
- **Apple Silicon** → `mlx-community` models via `mlx_local.py` or `mlx-lm`
- **NVIDIA GPU** → `ollama` or `vLLM` for inference serving
- **CPU-only** → `llama.cpp` quantised GGUF models via `ollama`

### Step 4 — Control Panel UI

Build a lightweight web UI for monitoring:
```python
# Example: Flask + SSE dashboard
# Shows: model name, status (idle/running), tokens/sec, assigned jobs
# Hermes feeds job assignments to the panel via cron or pub/sub
```

The control panel lets you:
- See all computers and their running models
- Test any model with a direct prompt
- Assign batch jobs (e.g., code generation, document processing)
- Monitor throughput and health

## Hardware Compatibility Quick Reference

| Hardware | Recommended Model Type | Runtime |
|----------|----------------------|---------|
| Mac Studio 128GB | Llama 3.3 70B Q4, Mistral Q5 | MLX 4-bit |
| Mac Mini 16GB | Llama 3.2 3B Q4, Gemma 2B | MLX 4-bit |
| MacBook Air 8GB | Phi-3.5 mini Q4, Gemma 2B | MLX 4-bit |
| Linux + RTX 4090 | Llama 3.1 70B Q4, Mistral 7B Q5 | vLLM / Ollama |
| Linux + RTX 5090 | Llama 3.3 70B Q4, Mistral 8x7B | vLLM |
| CPU-only old laptop | TinyLlama 1B, Phi-2 Q5 | llama.cpp GGUF |

## Common Pitfalls

1. **Starting too large**: Begin with a model confirmed to fit in memory, not the biggest model available.
2. **No benchmark**: Always measure tokens/sec and output cleanliness before committing to a model for production use.
3. **Single model per machine**: Use `ollama` with multiple model instances or `vLLM` for multi-tenant serving.
4. **No job queue**: Set up a simple job queue (Redis, SQLite, or even a file-based queue) so idle models get work.

## Nexus Persistence

After building a lab:
- Write a Guide documenting the hardware config, model choices, and control panel URL
- Write a Memory artifact recording what was learned about the hardware/model combination
