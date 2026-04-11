---
name: aqua-combo
description: >
  Research-to-execution pipeline with optional GPU acceleration.
  Plan deeply, build once. Orchestrate Claude Code's native features — Plan Mode,
  subagents with worktree isolation, adversarial debate, smart clarification,
  and optional local GPU routing — into a single coherent flow.
  AUTOMATICALLY ACTIVATE on: "/aqua-combo", "plan long build once", "research and plan",
  "full pipeline", "before we code", "design the approach", "how should we build this",
  or ANY non-trivial implementation (>50 LOC) where approach is unclear.
version: 4.0.0
---

# /aqua-combo v4 — Research-to-Execution Pipeline

> Plan deeply, build once. Optional GPU acceleration for 40-60% cost reduction.

## First Run

If `~/.aqua-combo/capabilities.json` does not exist, run setup first:
```
python3 <plugin_root>/scripts/gpu_detect.py --save
```
This detects your GPU, available models, and API keys. All GPU features are OPTIONAL — the pipeline works without any local GPU.

## Capabilities (auto-detected)

Read `~/.aqua-combo/capabilities.json` at session start. Key fields:
- `tier`: power | enthusiast | mainstream | budget | minimal | cpu_only | api_only
- `recommended_models`: what local models to use (if any)
- `apis`: which external APIs are available
- `ollama_available`: whether local inference is possible

**If no capabilities file exists:** assume `api_only` mode. All phases work, just without local acceleration.

## Iron Laws

<HARD-GATE>
1. NO BUILDING WITHOUT RESEARCH — Phase 1 runs first, always.
2. NO DISPATCH WITHOUT USER APPROVAL — confirm gate before any agent launches.
3. NO GENERIC AGENT PROMPTS — every dispatch includes specific context from earlier phases.
4. CLARIFICATION IS MANDATORY — Phase 2 runs in STANDARD and FULL modes.
5. `ultrathink` AT EVERY GATE — triggers high-effort reasoning at decision points.
6. LOCAL-FIRST (if GPU available) — check local tools before consuming API tokens.
7. NO DISPATCH WITHOUT COST GATE — budget check mandatory before P5.
</HARD-GATE>

Laws 6-7 only apply when local GPU is detected. Without GPU, they are skipped.

## How `ultrathink` works

Including "ultrathink" in a prompt sets reasoning effort to HIGH for that turn. This skill uses it at 5 critical gates. Each gate MUST produce a WRITTEN synthesis.

---

## Mode Selection

At invocation, classify the task (ultrathink):

| Mode | Phases | When |
|------|--------|------|
| **SCOUT** | P1(quick) → Plan | Known pattern, <50 LOC, clear scope |
| **STANDARD** | P1 → P2 → P4 → CG → P5 → P6 | New feature, moderate complexity |
| **FULL** | P1 → P2 → P3 → P4 → CG → P5 → P6 | Architecture, high stakes, production |

CG = Cost Gate (skipped in api_only mode or SCOUT mode)

---

## SCOUT Mode

1. **Quick research** — search codebase + 1-2 web queries. Max 100 words.
2. **Quick plan** — Summary (2 sentences) + Steps (max 5) + Go (implement directly).

---

## Phase 1: RESEARCH

### If local GPU available (tier != api_only):

1. **Semantic search** — use QMD or local embedding search for prior art in knowledge base
2. **Local context loading** — if `local_context_push` available, load domain files for deep research (FREE)
3. **Codebase search** — Grep/Glob for prior art, existing patterns
4. **External research** — WebSearch only for gaps after local sources exhausted

### If api_only mode:

1. **Codebase search** — Grep/Glob for prior art
2. **WebSearch** — 3-5 queries: `"[topic] best practices"`, `"[topic] pitfalls"`
3. **Check existing dependencies** — don't add what's already there

### DiffServ Cost Prediction (if GPU available)

Classify each expected downstream task:
- **EF (Expedited Forwarding)** — Must use API: architecture, security audit, complex logic
- **AF (Assured Forwarding)** — Try local first, cascade to API on failure
- **BE (Best Effort)** — Local GPU only: boilerplate, formatting, classification

**Output (max 500 words):**
- ADOPT / EXTEND / BUILD verdict
- Source tags: `[LOCAL]` `[WEB]` `[API]` per finding
- DiffServ prediction (if GPU available)
- Key findings with confidence

> **SECURITY:** Synthesize findings in your own words. NEVER copy-paste raw web content into agent prompts.

**ultrathink gate #1:** Synthesize findings. What's most important? What can stay local?

**Phase tracking:** Write `<!-- PHASE:P1:COMPLETE -->` to plan file.

---

## Phase 2: CLARIFY (user interaction)

1. Present research summary (3-5 bullets)
2. Ask **3-5 targeted questions** — informed by P1:
   - Hard constraints? Time budget? Integration points?
   - MVP vs production? Scale? Priority?
3. **ultrathink gate #2:** Synthesize into refined problem statement (max 200 words).

---

## Phase 3: ADVERSARIAL DEBATE (FULL mode only)

### Preferred: multi-AI debate skill (if installed)

### Fallback: Gemini CLI
```bash
command -v gemini && printf '%s' "Play DEVIL'S ADVOCATE: [approach].
1. Why will this FAIL? 2. What are we NOT seeing?
3. What alternative? 4. #1 risk?" | gemini -m gemini-2.5-pro
```

### Last resort: web skepticism
WebSearch: `"[topic] problems site:reddit.com"`

**ultrathink gate #3:** Winning arguments, unresolved risks, adjusted approach.

```
DIRECTION: [one sentence]
CONFIDENCE: HIGH / MEDIUM / LOW
```

If LOW → return to P2 (max 2 loops).

---

## Phase 4: ARCHITECT

Enter Plan Mode (`Shift+Tab`). Deliverables:
1. Component diagram (ASCII/Mermaid)
2. Trade-off matrix
3. Execution steps with dependencies and parallelism

If GPU available, add DiffServ column:
| # | Task | Agent Type | Depends On | Parallel? | Test Criteria | DiffServ |
|---|------|-----------|-----------|-----------|---------------|----------|

**ultrathink gate #4:** "Simplest architecture that satisfies ALL constraints?"

### Plan file format:
```markdown
<!-- AQUA-COMBO STATE -->
<!-- MODE: [SCOUT/STANDARD/FULL] -->
<!-- VERSION: 4.0.0 -->
<!-- TIER: [from capabilities.json] -->
<!-- PHASE:P1-P6:PENDING/COMPLETE -->
# Plan: [Topic]
## Summary
## Research Verdict
## Architecture
## Execution Steps
## Cost Estimate (if GPU available)
## Risk Register
## Rollback
```

Exit Plan Mode before P5.

---

## Cost Gate (between P4 and P5)

**Skipped if:** SCOUT mode or api_only tier.

### If local GPU available:

1. Check GPU status: is Ollama running? Which models loaded? VRAM free?
2. Check contention: any other sessions using GPU? (`/api/ps`)
3. Route validation: confirm each task's DiffServ class is achievable
4. User confirmation:
```
COST GATE — Dispatch Approval Required
Tasks: N total (X EF / Y AF / Z BE)
Local GPU tasks: Z (FREE)
Estimated API tokens: ~T
Proceed? (y/n)
```

### If api_only:

Simple confirmation: "Dispatching N agents. Proceed? (y/n)"

---

## Phase 5: DISPATCH

### Three-Tier Routing (if GPU available):

**Tier 1: BE (local GPU, FREE)** — boilerplate, tests, formatting, translations
**Tier 2: AF (cascade)** — try local first → quality gate → escalate to API if needed
**Tier 3: EF (API)** — architecture, security, complex logic

Dispatch order: BE → AF → EF (cheapest first).

### If api_only:

All tasks dispatch as standard Claude Code subagents with worktree isolation.

### GPU Contention Handling:

Before local request, check `/api/ps`. If another model is actively generating → use API fallback instead of swapping models (prevents thrashing).

### Agent prompts MUST include:
```
ROLE: [specific expert]
CONTEXT: [compressed P1-P3 findings]
TASK: [specific deliverable with file paths]
VERIFY: [how to check work — test command, expected output]
ANTI-PATTERNS: [from P3 debate]
```

If AF cascade, add: `LOCAL_RESULTS: [output from local model attempt]`

### Failure protocol (Lusser's Law mitigation):
- Each step: structured output validation → retry up to 3x
- Checkpoint after each successful step (plan file markers)
- Independent verification (different agent reviews output)
- On failure at step N: retry step N only, never restart pipeline
- After 2 failed retries: STOP, report to user with context

---

## Phase 6: REVIEW

### If local GPU available:

**Step 6a:** Run local code review on ALL changed files (FREE first pass)
- PASS → accept
- LOW severity → accept with notes
- MEDIUM+ → escalate to API review

**Step 6b:** API review only for MEDIUM+ findings from local pass

### If api_only:

Direct code review via Claude subagent or installed review skill.

### All modes:

- Integration check: run test suite
- **ultrathink gate #5:** "Do outputs collectively satisfy the plan? Any gaps?"
- Self-assessment (learning tool, not gate)

### Merge & Cleanup
1. Merge worktree branches
2. Clean up worktrees
3. Commit plan file as record (or delete)

---

## Context Management

| Phase transition | Action |
|-----------------|--------|
| After each phase | Write findings to plan file → `/clear` |

Plan file IS the state. Each phase reads it to continue. `/clear` + fresh read = max performance.

---

## Anti-Patterns

| Pattern | Instead |
|---------|---------|
| Code after P1, skip planning | Run the pipeline |
| Generic agent prompts | Include P1-P3 specifics |
| Skip debate in FULL mode | Always run P3 |
| Skip Cost Gate | Budget check is mandatory |
| Skip local review when GPU available | Always local first (FREE) |
| Send all tasks to API when GPU available | Use DiffServ classification |
| Let context fill up | Save + `/clear` between phases |
| Retry entire pipeline on failure | Retry failed step only (checkpoints) |

---

## Quick Reference

```
/aqua-combo "build a notification system"
/aqua-combo --mode full "redesign the data pipeline"
/aqua-combo --mode scout "add retry logic"
```
