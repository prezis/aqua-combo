# aqua-combo v2

**Plan deeply, build once.** A research-to-execution pipeline skill for [Claude Code](https://code.claude.com).

[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://code.claude.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

aqua-combo orchestrates Claude Code's native features — Plan Mode, subagents with worktree isolation, adversarial debate, and smart clarification — into a single pipeline. It forces you to research before coding, debate before committing, and verify before shipping.

```
/aqua-combo "build a notification system with WebSocket + queue"
```

---

## What it does

| Phase | Name | What happens |
|-------|------|-------------|
| **P1** | Research | Deep multi-source research on the problem |
| **P2** | Clarify | 3-5 targeted questions you didn't think to ask |
| **P3** | Debate | Adversarial stress-test via Gemini or web skepticism |
| **P4** | Architect | Design simplest architecture using Plan Mode |
| **P5** | Dispatch | Launch subagents in isolated worktrees with crafted prompts |
| **P6** | Review | Code review + security audit via specialized subagents |

`ultrathink` checkpoints (Claude Code's high-effort reasoning keyword) at each decision gate ensure deep analysis. The number of gates depends on the selected mode — FULL mode uses all five numbered gates plus mode selection.

---

## Modes

| Mode | Phases | When |
|------|--------|------|
| **SCOUT** | P1 (quick) + plan | Simple task, known pattern, <50 LOC |
| **STANDARD** | P1 → P2 → P4 → P5 → P6 | New feature, moderate complexity |
| **FULL** | All P1 through P6 | Architecture, high stakes, production, multi-agent |

Override: `/aqua-combo --mode full "redesign the auth system"`

---

## How it uses Claude Code

aqua-combo orchestrates Claude Code's native features AND installed skills:

**Native features:**
- **Plan Mode** (P4) — `Shift+Tab` for read-only architecture planning
- **Subagents with worktree isolation** (P5) — each agent works in its own git branch
- **`ultrathink` keyword** — triggers high-effort reasoning at 5 decision gates
- **Save-state + `/clear`** — fresh context between phases for maximum quality
- **Skill routing** — automatically picks the best tool per task

**Skill delegation (auto-detected, fallbacks if not installed):**
- **`/octo-debate`** in P3 — 3-way AI debate (Claude+Gemini+Codex) instead of Gemini-only
- **`/octo-plan`** in P4 — multi-AI consensus architecture instead of single-AI
- **`/octo-deliver`** in P6 — structured multi-AI QA instead of manual review
- **`/aqua-search`** in P1 — deep research with verification instead of basic search

aqua-combo works standalone with built-in fallbacks for every phase. Installing the recommended skills makes each phase significantly stronger.

---

## Optional: hooks for hard gates

aqua-combo's quality gates are LLM-enforced by default. For production use, add deterministic hooks that make gates unbypassable:

- **Notification hook** — desktop alert when pipeline needs your input (long phases)
- **Stop hook** — verify all required phases ran before declaring complete
- **PreToolUse hook** — block file edits until a plan file exists (Iron Law #1)
- **SubagentStop hook** — auto-notify when dispatched agents finish

See `references/context_protocol.md` for ready-to-paste hook configurations.

---

## Important notes

**Agent dispatch (P5):** Before launching agents, the skill presents a confirmation gate listing all tasks. Agents run in default permission mode unless you explicitly opt in to auto-accept.

**Worktree isolation:** Each dispatched agent gets its own copy of the repo via git worktree. If an agent's work fails review, `git worktree remove` discards it cleanly. No mess in your working directory.

**Web research safety:** P1 research may pull web content. The skill summarizes and paraphrases rather than copy-pasting raw content into agent prompts, reducing prompt injection risk.

---

## Installation

```bash
git clone https://github.com/prezis/aqua-combo.git
cp -r aqua-combo/SKILL.md aqua-combo/references ~/.claude/skills/aqua-combo/
```

Or manually:
```bash
mkdir -p ~/.claude/skills/aqua-combo/references
# Copy SKILL.md and references/ into the above directory
```

Optional — install the provided subagent definitions for better review:
```bash
mkdir -p .claude/agents
cp aqua-combo/references/subagent_definitions.md .claude/agents/README.md
# Then copy individual agent definitions from that file into .claude/agents/
```

---

## What's inside

```
aqua-combo/
  SKILL.md                              # Main skill (6 phases + iron laws)
  references/
    subagent_definitions.md             # Ready-to-use .claude/agents/ definitions
    prompt_templates.md                 # Domain-specific templates for agent prompts
    context_protocol.md                 # Context management, resource budgets, failure modes
```

---

## Prerequisites

- **[Claude Code](https://code.claude.com)** — the skill runs inside Claude Code's skill system
- **Gemini CLI** (optional) — used in P3 for adversarial debate. Falls back to web search if unavailable.

---

## Contributing

Found a way to improve the pipeline? Open an issue or PR. Ideas:
- New subagent definitions for specific domains
- Better prompt templates
- Additional adversarial debate strategies
- Context management improvements

---

## License

[MIT](LICENSE)

---

Plan deeply, build once.
