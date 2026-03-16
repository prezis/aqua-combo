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

Five `ultrathink` checkpoints (Claude Code's high-effort reasoning keyword) ensure deep analysis at critical gates.

---

## Modes

| Mode | Phases | When |
|------|--------|------|
| **SCOUT** | P1 (quick) + plan | Simple task, known pattern, <50 LOC |
| **STANDARD** | P1 → P2 → P4 → P5 | New feature, moderate complexity |
| **FULL** | All P1 through P6 | Architecture, high stakes, production |

Override: `/aqua-combo --mode full "redesign the auth system"`

---

## How it uses Claude Code

aqua-combo builds on Claude Code's native capabilities:

- **Plan Mode** (P4) — `Shift+Tab` for read-only exploration and planning. `Ctrl+G` to edit plans in your editor.
- **Subagents** (P5-P6) — dispatched with `isolation: worktree` so each agent works in its own branch. No file conflicts, clean rollback.
- **`ultrathink` keyword** — triggers high-effort reasoning at 5 decision gates (Opus 4.6 / Sonnet 4.6).
- **Context management** — `/compact` between phases to prevent context window degradation.
- **Skill routing** — automatically uses installed skills (`/code-review`, `/security-review`, `/tdd`) when available.

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

Built by the community. Plan deeply, build once.
