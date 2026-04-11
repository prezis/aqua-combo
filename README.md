<div align="center">

# aqua-combo

**Research-to-execution pipeline for Claude Code with optional GPU acceleration**

Plan deeply, build once.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-17%20passed-brightgreen)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-purple)]()
[![GPU Optional](https://img.shields.io/badge/GPU-optional-orange)]()

[Install](#install) | [How It Works](#how-it-works) | [GPU Setup](#gpu-acceleration) | [Modes](#modes) | [Contributing](#contributing)

</div>

---

## What It Does

aqua-combo turns vague ideas into shipped code through a structured 6-phase pipeline:

| Without aqua-combo | With aqua-combo |
|---|---|
| Jump to code, hit unknowns, rewrite | Research first, build once |
| Generic agent prompts, bad output | Context-rich prompts from prior phases |
| Whole pipeline fails, restart | Per-step retry + checkpoint resume |
| All tasks → expensive API | Local GPU handles 40-60% of tasks FREE |

## Install

```bash
# Register the marketplace
claude plugin marketplace add prezis/aqua-combo

# Install
claude plugin install aqua-combo@aqua-pipeline
```

Then in any Claude Code session:
```
/aqua-combo "build a notification system with WebSocket"
```

## How It Works

```
P1 RESEARCH → P2 CLARIFY → P3 DEBATE → P4 ARCHITECT → COST GATE → P5 DISPATCH → P6 REVIEW
     │             │            │            │              │            │            │
  Search local   Interview    Devil's    Plan Mode      Budget      3-tier       Local-first
  knowledge      user for     advocate   + trade-off    check       routing      code review
  base first     constraints  stress     matrix         (if GPU)    BE→AF→EF     (FREE)
```

### Three Modes

| Mode | Phases | When |
|------|--------|------|
| **SCOUT** | P1 → Plan → Build | Known pattern, <50 LOC |
| **STANDARD** | P1 → P2 → P4 → P5 → P6 | Typical feature |
| **FULL** | P1 → P2 → P3 → P4 → P5 → P6 | Architecture, high stakes |

### Reliability (Lusser's Law Mitigation)

Raw agent chains have compound probability: 0.80^5 = 33%. aqua-combo beats this with:

1. **Deterministic wrapper** — code controls flow, LLM fills blanks (reduces N)
2. **Per-step retry** — 3 retries transforms 85% → 99.7% per step
3. **Checkpoint/resume** — never restart, retry only the failed step
4. **Independent verification** — separate reviewer catches silent failures
5. **Structured output** — schema validation catches format errors before they compound

Result: **~98% pipeline reliability** instead of 33%.

## GPU Acceleration

**GPU is optional.** aqua-combo works perfectly without any local GPU — it just uses API calls. But if you have a GPU + Ollama, it can route 40-60% of tasks locally for FREE.

### Auto-Detection

On first run, aqua-combo detects your hardware:

```bash
python3 <plugin_root>/scripts/gpu_detect.py --save
```

| Your GPU | Tier | What Runs Locally |
|----------|------|-------------------|
| RTX 4090/5090 (24GB+) | **power** | Everything: reasoning, code review, embeddings |
| RTX 3060-4070 (12-23GB) | **enthusiast** | 14B reasoning + fast classifier + embeddings |
| RTX 3050, M1 (6-11GB) | **mainstream** | 8B reasoning + embeddings |
| GTX 1650, old GPU (4-5GB) | **budget** | 4B classifier + embeddings |
| iGPU, 2-3GB | **minimal** | Embeddings + tiny classifier only |
| No GPU | **api_only** | All tasks via API (still works!) |

### DiffServ Routing

Tasks are classified into three service classes:

- **BE (Best Effort)** — local GPU only: formatting, classification, boilerplate → FREE
- **AF (Assured Forwarding)** — try local first, escalate to API if quality insufficient
- **EF (Expedited Forwarding)** — API only: architecture, security, complex reasoning

### Multi-Session GPU Contention

When multiple Claude Code sessions request the GPU simultaneously, aqua-combo checks `/api/ps` before each request. If another model is actively generating → falls back to API instead of causing swap thrashing.

## Configuration

After setup, capabilities are saved to `~/.aqua-combo/capabilities.json`:

```json
{
  "gpu": { "vendor": "nvidia", "name": "RTX 4070", "vram_total_mb": 16384 },
  "tier": "enthusiast",
  "recommended_models": [...],
  "apis": { "anthropic": true, "openai": false, "gemini": true }
}
```

## Project Structure

```
aqua-combo/
├── .claude-plugin/           # Plugin manifest
├── skills/aqua-combo/        # Main pipeline SKILL.md
├── agents/                   # Specialized agent personas
├── scripts/gpu_detect.py     # Cross-platform GPU detection
├── tests/                    # 17 tests (GPU tiers + skill validation)
├── examples/                 # Config examples per hardware tier
└── docs/                     # Detailed documentation
```

## Contributing

1. Fork the repo
2. Make your change (edit SKILL.md or scripts)
3. Run tests: `python3 -m pytest tests/ -v`
4. Submit a PR with before/after showing the improvement

## License

MIT
