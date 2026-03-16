---
name: aqua-combo
description: >
  Research-to-execution pipeline that orchestrates Claude Code's native features:
  Plan Mode, subagents with worktree isolation, adversarial debate, and smart
  clarification — into a single coherent flow. Forces you to research before coding,
  debate before committing, and verify before shipping.
  AUTOMATICALLY ACTIVATE on: "/aqua-combo", "plan long build once", "research and plan",
  "full pipeline", "before we code", "design the approach", "how should we build this",
  or ANY non-trivial implementation (>50 LOC) where approach is unclear.
  Philosophy: plan deeply, build once.
version: 2.0.0
---

# /aqua-combo v2 — Research-to-Execution Pipeline

> Plan deeply, build once. Orchestrate Claude Code's native features into one flow.

## Iron Laws

<HARD-GATE>
1. NO BUILDING WITHOUT RESEARCH — Phase 1 runs first, always.
2. NO DISPATCH WITHOUT USER APPROVAL — confirm gate before any agent launches.
3. NO GENERIC AGENT PROMPTS — every dispatch includes specific context from earlier phases.
4. CLARIFICATION IS MANDATORY — Phase 2 runs in STANDARD and FULL modes.
5. `ultrathink` AT EVERY GATE — the word "ultrathink" triggers Claude Code's high-effort reasoning. Use it at every decision point.
</HARD-GATE>

---

## How `ultrathink` works

In Claude Code, including the word "ultrathink" in a prompt sets reasoning effort to HIGH for that turn (Opus 4.6 / Sonnet 4.6). This skill uses it at 5 critical gates. Each gate MUST produce a WRITTEN synthesis — not just "I thought about it."

---

## Mode Selection

At invocation, classify the task (ultrathink):

| Mode | Phases | When |
|------|--------|------|
| **SCOUT** | P1(quick) → Plan | Known pattern, <50 LOC, clear scope |
| **STANDARD** | P1 → P2 → P4 → P5 | New feature, moderate complexity |
| **FULL** | P1 → P2 → P3 → P4 → P5 → P6 | Architecture, high stakes, production, multi-agent |

**Auto-detect:** >3 unknowns or >200 LOC or money involved → FULL. Otherwise → STANDARD.

**Override:** `/aqua-combo --mode full "topic"`

---

## SCOUT Mode

For simple tasks where you know HOW, just need to organize:

1. **Quick research** — 1-2 searches + check codebase for prior art. No formal verdict, just "what exists" (max 100 words).
2. **Quick plan** — Summary (2 sentences) + Steps (max 5) + Go (implement directly, no agent dispatch).

---

## Phase 1: RESEARCH

Delegate to `/aqua-search` if available. Otherwise:

1. WebSearch 3-5 queries: `"[topic] best practices"`, `"[topic] library"`, `"[topic] pitfalls"`
2. Grep/Glob codebase for prior art
3. Check existing dependencies — don't add what's already there

**Output (max 500 words):**
- ADOPT (use existing solution) / EXTEND (modify existing) / BUILD (from scratch)
- Key findings with confidence
- Libraries/patterns discovered

**ultrathink gate #1:** Synthesize findings. What's the most important thing we learned?

**Context cleanup:** After summarizing, run `/compact Focus on research conclusions` to free context from raw search results.

---

## Phase 2: CLARIFY (user interaction)

This is the "interview me" pattern from Claude Code best practices. Don't just ask what the user wants — ask what they HAVEN'T thought of.

1. Present research summary (3-5 bullets, not a wall)
2. Ask **3-5 targeted questions** — SMART, informed by P1 findings:

Pick from:
- Hard constraints — what CANNOT change?
- Time budget — hours or days?
- Integration — what existing code must it connect to?
- MVP vs production-grade?
- Scale — users, data volume, concurrency?
- Priority — speed vs quality vs cost?
- What already tried — avoid retreading?

**Questions MUST be surprising** — things the user wouldn't think to mention but that will determine the approach. Generic questions waste time.

3. **ultrathink gate #2:** Synthesize user answers + research into a refined problem statement (max 200 words). ALL subsequent phases reference this.

---

## Phase 3: ADVERSARIAL DEBATE (FULL mode only)

Stress-test the approach before committing.

### Gemini path (preferred):
```bash
command -v gemini && printf '%s' "You are a senior engineer reviewing a proposed approach.
CONTEXT: [P1 research summary]
USER CONSTRAINTS: [P2 refined problem]
PROPOSED: [current best direction]

Play DEVIL'S ADVOCATE:
1. Why will this approach FAIL?
2. What are we NOT seeing?
3. What alternative would YOU choose and why?
4. What's the #1 risk we're underestimating?" | gemini -m gemini-2.5-pro -p "" -o text
```

### Fallback (no Gemini):
WebSearch: `"[topic] problems site:reddit.com"`, `"[topic] pitfalls site:news.ycombinator.com"`

### 4-Perspective Synthesis:

| Perspective | Question |
|-------------|----------|
| ADVOCATE | Best case — why this works |
| DEVIL'S ADVOCATE | Why this fails, what's missing |
| PARADOX HUNTER | Counterintuitive strengths? |
| PRAGMATIST | What's realistic given P2 constraints |

### Cross-validate:
- Did debate reveal anything research missed?
- Do P2 constraints invalidate any P1 findings?
- Contradictions between sources?

**ultrathink gate #3:** Winning arguments, unresolved risks, approach adjustment if needed.

**Output:**
```
DIRECTION: [one sentence]
CONFIDENCE: HIGH / MEDIUM / LOW
UNRESOLVED: [list]
ADJUSTED: [what changed from original]
```

If CONFIDENCE = LOW → return to P2 with follow-up questions (max 2 loops, then STOP and report to user).

---

## Phase 4: ARCHITECT

**Enter Plan Mode** — use `Shift+Tab` or `--permission-mode plan`. In Plan Mode, Claude reads and plans without making changes.

### Deliverables:
1. **Component diagram** (ASCII or Mermaid)
2. **Trade-off matrix** for non-obvious decisions
3. **Integration points** — which existing files are modified vs created
4. **Execution steps** — ordered, with dependencies and parallelism

### Simplicity gate:

**ultrathink gate #4:** "What is the SIMPLEST architecture that satisfies ALL constraints from P2?"

- Can I remove any component and still satisfy requirements? → remove it
- Can I replace custom code with a standard library? → replace it
- Would a junior dev understand this in 5 minutes? → if not, simplify

### Plan output:

Write plan to `aqua-combo-plan-{topic-slug}.md`. Use `Ctrl+G` to open in editor for user review.

```markdown
# Plan: [Topic]
## Summary — 2-3 sentences
## Research Verdict — ADOPT/EXTEND/BUILD + key finding
## Architecture — diagram + trade-offs
## Execution Steps
| # | Task | Agent Type | Depends On | Parallel? | Test Criteria |
## Risk Register
| Risk | Impact | Mitigation |
## Rollback — how to undo (git checkout/stash/worktree remove)
```

**Context cleanup:** `/compact Focus on the plan and execution steps` before dispatch.

---

## Phase 5: DISPATCH

### User confirmation gate (MANDATORY):

> "About to dispatch N agents (M parallel, K serial).
> Each runs in an isolated worktree (own branch, own files).
> Tasks: [numbered list].
> Permission mode: default (you approve operations).
> Proceed? (y/n)"

**Only proceed after explicit "yes".**

### Dispatch using Claude Code's native subagent system:

For each task from the plan:

```
Agent tool call:
  - subagent_type: [matching agent — see Skill Routing below]
  - isolation: worktree  ← CRITICAL: each agent gets own copy of repo
  - mode: default  ← user approves operations (or acceptEdits if user opted in)
  - prompt: [context-rich prompt built from P1-P3 findings]
```

### Skill Routing — use the best tool for the job:

| Task Type | Best Agent/Skill | Fallback |
|-----------|-----------------|----------|
| Implementation | `general-purpose` agent | — |
| Code review | `/code-review` or `code-reviewer` agent | see `references/subagent_definitions.md` |
| Security audit | `/security-review` or `security-reviewer` agent | see `references/subagent_definitions.md` |
| Testing | `/tdd` or `tdd-guide` agent | generic test writer |
| Architecture review | `Plan` agent in plan mode | — |
| Debugging | `/octo-debug` or `debugger` agent | — |
| Research subtask | `Explore` agent (built-in, uses Haiku) | — |

**To discover installed skills:** check `/` menu or ask "what skills are available?"

### Prompt engineering for dispatched agents:

Every agent prompt MUST include:
```
ROLE: [specific expert]
CONTEXT: [compressed P1 findings + P2 constraints + P3 risks]
TASK: [specific deliverable with file paths]
CONSTRAINTS: [from P2 + debate anti-patterns from P3]
VERIFY: [how to check work — test command, expected output]
ANTI-PATTERNS: [what NOT to do — from P3 debate]
```

See `references/prompt_templates.md` for domain-specific templates.

**Rules:**
- NEVER generic prompts ("write tests") — include WHAT, WHY, and HOW to verify
- Each prompt references specific findings from P1-P3
- Include exact file paths and function signatures
- One task per agent — focused agents produce better output

### Parallel dispatch:
- Tasks with no shared files → launch simultaneously (worktree isolation prevents conflicts)
- Tasks with dependencies → serial
- Max concurrent: 3-4 agents (check `free -h` / `vm_stat`)
- Max 1 heavy rate-limited API agent at a time

### Failure protocol:
- Agent timeout (10 min): kill, retry once
- Wrong output: send to review (max 2x)
- Review fails 2x: STOP, report to user with context
- Multiple agents fail: STOP — ultrathink "Is the plan wrong?"
- Rollback: `git worktree remove` (worktree isolation makes this clean)

### Progress:
- After each task: "Task 3/5 done: [component] — tests pass"
- Never auto-retry endlessly — 2 loops max, then escalate to user

---

## Phase 6: REVIEW (FULL mode, recommended for STANDARD)

After all agents complete:

1. **Spec compliance** — does output match the plan?
   - Use `/code-review` skill if installed
   - Or dispatch `code-reviewer` subagent (see `references/subagent_definitions.md`)

2. **Security + quality** — vulnerabilities, edge cases, code smells?
   - Use `/security-review` skill if installed
   - Or dispatch `security-reviewer` subagent

3. **Integration check** — run full test suite, check for cross-agent conflicts

**ultrathink gate #5:** "Do outputs collectively satisfy the plan? Any gaps?"

### Self-assessment:

| Question | Score 0-10 |
|----------|------------|
| Did P1 research find something we wouldn't have known? | |
| Did P3 debate change our approach? | |
| Were agent prompts better than generic? | |
| Did worktree isolation prevent conflicts? | |
| Overall pipeline value-add? | |

---

## Context Management Protocol

Context is your #1 resource. The official Claude Code docs say: "performance degrades as context fills." This pipeline is context-hungry — manage it aggressively.

| When | Action | Why |
|------|--------|-----|
| After P1 research | `/compact Focus on research conclusions` | Raw search results no longer needed |
| After P2 clarify | Nothing — user answers are small | — |
| After P3 debate | `/compact Focus on debate conclusions and direction` | Debate transcript is verbose |
| Before P5 dispatch | `/compact Focus on the plan and execution steps` | Free maximum context for agent management |
| Between unrelated tasks | `/clear` | Fresh context = better performance |

**Subagent context:** Each dispatched agent runs in its OWN context window + its own worktree. Their verbose output stays there — only summaries return to your main conversation.

---

## Anti-Patterns

| Pattern | Why it's wrong | Instead |
|---------|---------------|---------|
| Code after P1, skip planning | The whole point is PLANNING | Run the pipeline |
| Generic agent prompts | No context = bad output | Include P1-P3 specifics |
| Skip debate ("obvious approach") | Obvious to YOU | Always run P3 in FULL mode |
| Ask >5 questions in P2 | Diminishing returns | 3-5 targeted, research-informed |
| FULL mode for typo fix | Overkill | Auto-detect picks SCOUT |
| Skip user confirmation before dispatch | Agents modify your code | Always confirm at P5 gate |
| Let context fill up | Performance degrades | `/compact` between phases |
| Dispatch without worktree isolation | File conflicts | Always use `isolation: worktree` |

---

## Quick Reference

```
/aqua-combo "build a notification system with WebSocket + queue"
/aqua-combo --mode full "redesign the data pipeline architecture"
/aqua-combo --mode scout "add retry logic to API calls"
```

**Auto-triggers:** "plan long build once", "research and plan", "full pipeline", "before we code", "design the approach", "how should we build this", or any non-trivial implementation where approach is unclear.

---

## References

- `references/subagent_definitions.md` — Ready-to-use `.claude/agents/` definitions for reviewers, debuggers, and more
- `references/prompt_templates.md` — Domain-specific templates for sub-agent prompts
- `references/context_protocol.md` — Context management, resource budgets, failure modes
