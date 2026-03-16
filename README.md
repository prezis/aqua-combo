# aqua-combo

**Plan long, build once.** A research-to-execution pipeline skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

aqua-combo replaces the manual cycle of research, debate, architecture review, and implementation with a single command. It runs a 10-phase pipeline that researches your problem, stress-tests the approach through adversarial debate, designs the architecture, crafts context-rich prompts for sub-agents, simulates execution, and dispatches the work -- all automatically.

```
/aqua-combo "build a notification system with WebSocket + queue"
```

---

## Pipeline Overview

```
+---------------------------------------------------------+
|                     /aqua-combo                         |
|                                                         |
|  +---------+   +----------+   +----------+              |
|  | SCOUT   |   | STANDARD |   | FULL     |              |
|  | MODE    |   | MODE     |   | MODE     |              |
|  | <10 min |   | 10-30 min|   | 30+ min  |              |
|  +----+----+   +----+-----+   +----+-----+              |
|       |              |              |                    |
|  P1(Q)->P8(mini) P1->P2->P5->  ALL P1-P10              |
|                  P6->P7L->P8->P10                       |
|                                                         |
|  Phases:                                                |
|  P1 Research -> P2 Clarification -> P3 Adversarial      |
|  -> P4 Cross-Validation -> P5 Architecture -> P6 Prompts|
|  -> P7 Simulation -> P8 Final Plan -> P9 Learning       |
|  -> P10 Auto-Dispatch                                   |
+---------------------------------------------------------+
```

---

## Modes

| Mode | Phases | When to use |
|------|--------|-------------|
| **SCOUT** | P1 (quick) -> P8 (mini) | Simple task, known pattern, <50 LOC |
| **STANDARD** | P1 -> P2 -> P5 -> P6 -> P7(lite) -> P8 -> P10 | New feature, moderate complexity |
| **FULL** | All P1 through P10 | Architecture decisions, high stakes, multi-agent, production |

The mode is auto-detected based on complexity, but you can override it:

```
/aqua-combo --mode full "redesign the data pipeline architecture"
/aqua-combo --mode scout "add retry logic to API calls"
```

---

## The 10 Phases

| Phase | Name | What it does |
|-------|------|-------------|
| **P1** | Research | Deep multi-source research on the problem space |
| **P2** | Clarification | 3-5 targeted questions to align research with your actual needs |
| **P3** | Adversarial Debate | Stress-test the approach (Gemini devil's advocate or web skepticism) |
| **P4** | Cross-Validation | Catch contradictions between research, user input, and debate |
| **P5** | Architecture | Design the simplest architecture that satisfies all constraints |
| **P6** | Prompt Engineering | Craft context-rich prompts for each sub-agent task |
| **P7** | Simulation | Mental dry-run: failure modes, time estimates, resource budget |
| **P8** | Final Plan | Single actionable document combining all phases |
| **P9** | Learning Loop | Capture what worked for future runs |
| **P10** | Auto-Dispatch | Launch sub-agents with two-stage review and conflict detection |

Each phase builds on the previous. Six mandatory ULTRATHINK checkpoints ensure deep reasoning at critical gates.

> **What is ULTRATHINK?** A structured deep-reasoning step where the AI pauses to think thoroughly before proceeding. Each ULTRATHINK checkpoint produces a written output — not just "I thought about it" but a concrete synthesis, decision, or analysis that subsequent phases build on.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/prezis/aqua-combo.git

# Copy to your Claude Code skills directory
cp -r aqua-combo ~/.claude/skills/
```

Or manually:

```bash
mkdir -p ~/.claude/skills/aqua-combo/references
# Copy SKILL.md and the references/ folder into the above directory
```

---

## Usage

Once installed, invoke it in Claude Code:

```
/aqua-combo "build a notification system with WebSocket + queue"
```

It also auto-activates on phrases like:
- "plan long build once"
- "research and plan"
- "full pipeline"
- "before we code"
- "design the approach"
- "how should we build this"

---

## What's Inside

```
aqua-combo/
  SKILL.md                              # Main skill definition (10 phases + iron laws)
  references/
    architecture_checklist.md            # Full checklist for P5 architecture review
    prompt_templates.md                  # Domain-specific templates for sub-agent prompts
    simulation_protocol.md               # Resource limits, timing, failure mode catalog
```

---

## Key Principles

- **No building without the full pipeline** -- if mode is FULL, all phases run, no shortcuts.
- **No dispatch without simulation** -- P7 must complete before P10 launches agents.
- **No generic prompts** -- every sub-agent prompt includes specific context from P1-P5.
- **Simplest architecture wins** -- complexity is not a feature.
- **Two-stage review** -- every agent output is reviewed for spec compliance, then code quality.

---

## Important Notes

**Agent dispatch (P10):** In STANDARD and FULL modes, the pipeline dispatches sub-agents that create and modify files in your project. Before dispatch, the skill presents a confirmation gate listing all tasks and asking for your approval. Agents run in default permission mode unless you explicitly opt in to `bypassPermissions` at the confirmation gate.

**Skill integration:** P6 and P10 automatically leverage installed Claude Code skills when available (e.g., `/code-review`, `/security-review`, `/tdd`). If no specialized skills are installed, it falls back to generic reviewer agents using the templates in `references/prompt_templates.md`.

**Web research safety:** P1 research may pull content from web sources. The skill includes guidance to summarize and paraphrase web content rather than copy-pasting raw text into agent prompts, reducing prompt injection risk.

---

## Prerequisites

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** -- the skill runs inside Claude Code's skill system.
- **Gemini CLI** (optional) -- used in P3 for adversarial debate. If unavailable, the skill falls back to web search for community skepticism.

---

## Contributing

Found a way to improve the pipeline? Open an issue or PR. Ideas welcome:
- New prompt templates for specific domains
- Better simulation heuristics
- Additional adversarial debate strategies

---

## License

[MIT](LICENSE)

---

Built by the community. Plan long, build once.
