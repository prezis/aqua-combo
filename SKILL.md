---
name: aqua-combo
description: >
  Ultimate research-to-execution pipeline. Combines deep research (aqua-search),
  adversarial debate (Gemini/web), architecture review, prompt engineering for sub-agents,
  step-by-step simulation, and auto-dispatch — all in ONE command.
  AUTOMATICALLY ACTIVATE on: "/aqua-combo", "plan long build once", "research and plan",
  "full pipeline", "before we code", "design the approach", "how should we build this",
  or ANY non-trivial implementation (>50 LOC) where approach is unclear.
  Philosophy: plan deeply, build once. Replace manual cycle of aqua-search + debate + plan + architect.
version: 1.0.0
---

# /aqua-combo — Research-to-Execution Pipeline v1

> "Plan long, build once." — Replace the manual cycle of research + debate + plan + architect
> with a single command that does ALL of it.

## The Iron Laws

<HARD-GATE>
1. NO BUILDING WITHOUT FULL PIPELINE — if mode=FULL, ALL phases run. No shortcuts.
2. NO DISPATCH WITHOUT SIMULATION — P7 must complete before P10 launches agents.
3. NO GENERIC PROMPTS — P6 prompts MUST include specific context from P1-P5.
4. CLARIFICATION IS MANDATORY — P2 always runs in STANDARD and FULL modes.
5. ULTRATHINK AT EVERY GATE — 5 mandatory ULTRATHINK triggers, never skip.
</HARD-GATE>

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      /aqua-combo                            │
│                                                             │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐                 │
│  │ SCOUT   │   │ STANDARD │   │ FULL     │                 │
│  │ MODE    │   │ MODE     │   │ MODE     │                 │
│  │ <10 min │   │ 10-30 min│   │ 30+ min  │                 │
│  └────┬────┘   └────┬─────┘   └────┬─────┘                 │
│       │              │              │                        │
│  P1(Q)→P8(mini) P1→P2→P5→     ALL P1-P10                   │
│                 P6→P8→P10                                   │
│                                                             │
│  Phases:                                                    │
│  P1 Research → P2 Clarification → P3 Adversarial Debate    │
│  → P4 Cross-Validation → P5 Architecture → P6 Prompts      │
│  → P7 Simulation → P8 Final Plan → P9 Learning → P10 Go    │
└─────────────────────────────────────────────────────────────┘
```

---

## Mode Selection (auto-detect or override)

At invocation, ULTRATHINK to classify:

| Mode | Phases | Auto-detect when |
|------|--------|------------------|
| SCOUT | P1(QUICK) → P8(mini) | Simple task, known pattern, <50 LOC |
| STANDARD | P1(STD) → P2 → P5 → P6 → P8 → P10 | New feature, moderate complexity |
| FULL | All P1-P10 | Architecture, high stakes, multi-agent, production |

**Auto-detect rules:**
- >3 unknowns = FULL
- >200 LOC estimated = FULL
- Multi-agent coordination needed = FULL
- Production / money involved = FULL
- Otherwise = STANDARD

**Manual override:** `/aqua-combo --mode full "topic"`

---

## P1: RESEARCH (delegate to /aqua-search)

Invoke `/aqua-search` in DEEP mode with the topic. aqua-search handles its own pipeline:
- Context Assembly, Prior Art, Step-Back Abstraction (ULTRATHINK)
- Multi-Source Search, Re-rank, CoVe
- Failure Mode Analysis, Synthesis, Decision Gate

**Output consumed by P2:**
- Compressed research summary (max 500 words)
- ADOPT / EXTEND / BUILD verdict
- Key findings with confidence tags
- Relevant code references / libraries discovered

**If aqua-search skill unavailable:** fall back to manual research:
1. WebSearch 3-5 queries covering: "[topic] best practices", "[topic] library", "[topic] pitfalls"
2. Check existing codebase with Grep/Glob for prior art
3. Summarize findings manually

---

## P2: CLARIFICATION GATE (user interaction)

**Purpose:** Align research findings with user's actual needs before investing in architecture.

### Steps:
1. **Present** research summary from P1 (3-5 bullet points, not a wall of text)
2. **Ask 3-5 targeted questions** using conversation (adapt to topic):

Pick the most relevant from:
- Hard constraints — what CANNOT change?
- Time budget — hours/days for implementation?
- Integration requirements — what existing code/systems must it connect to?
- "Good enough" vs ideal — MVP or production-grade?
- What already tried/considered — avoid re-treading?
- Scale requirements — users, data volume, concurrent processes?
- Priority ranking — speed vs quality vs cost?

**Questions MUST be SMART** — informed by P1 research findings, not generic.

3. **ULTRATHINK #1:** Synthesize user answers + research into refined problem statement

**Output:** Refined problem statement (max 200 words) that ALL subsequent phases use.

---

## P3: ADVERSARIAL DEBATE

**Purpose:** Stress-test the proposed approach before committing to architecture.

### Gemini Path (preferred):
```bash
# Check availability
command -v gemini

# Build context-rich prompt
PROMPT="You are a senior engineer reviewing a proposed approach.
CONTEXT: [P1 research summary]
USER CONSTRAINTS: [P2 refined problem]
PROPOSED APPROACH: [current best direction]

Play DEVIL'S ADVOCATE:
1. Why will this approach FAIL?
2. What are we NOT seeing?
3. What alternative would YOU choose and why?
4. What's the #1 risk we're underestimating?"

# Execute
printf '%s' "$PROMPT" | gemini -m gemini-2.5-pro -p "" -o text --approval-mode yolo
```

### Fallback Path (no Gemini):
Run WebSearch queries for real community skepticism:
- `"[topic] problems site:reddit.com"`
- `"[topic] pitfalls site:news.ycombinator.com"`
- `"[topic] alternative approach site:stackoverflow.com"`
- `"[topic] issues site:github.com"`

### 3-Perspective Synthesis:
Regardless of path, synthesize three perspectives:

| Perspective | Question |
|-------------|----------|
| ADVOCATE | Best case for proposed approach — why it works |
| DEVIL'S ADVOCATE | Why this will fail, what's missing |
| PARADOX HUNTER | What if this works BECAUSE it violates convention? Counterintuitive strengths? |
| PRAGMATIST | What's realistic given constraints from P2 |

**ULTRATHINK #2:** Identify winning arguments, unresolved risks, blind spots.

**Output:** Debate summary with:
- Strongest argument FOR (1 sentence)
- Strongest argument AGAINST (1 sentence)
- Unresolved risks (bullet list)
- Approach adjustment if needed

---

## P4: CROSS-VALIDATION

**Purpose:** Catch contradictions between research, user input, and debate.

### Validation checks:
1. **Research vs Debate:** Did debate reveal anything research missed?
2. **User vs Research:** Do P2 constraints invalidate any P1 findings?
3. **Source vs Source:** Are there contradictions between different sources?
4. **Feasibility:** Given ALL inputs, is the direction actually achievable?

**ULTRATHINK #3:** Reconcile ALL inputs (research + user + debate) into single coherent direction.

**Output:**
```
DIRECTION: [one sentence]
CONFIDENCE: HIGH / MEDIUM / LOW
UNRESOLVED: [list anything still uncertain]
ADJUSTED FROM ORIGINAL: [yes/no + what changed]
```

If CONFIDENCE = LOW → loop back to P2 with specific follow-up questions.

---

## P5: ARCHITECTURE REVIEW

**Purpose:** Design the simplest architecture that satisfies ALL constraints.

### Deliverables:

**1. Component Diagram** (ASCII or Mermaid):
```
[Component A] --depends--> [Component B]
                           [Component B] --calls--> [External API]
[Component C] --parallel-- [Component D]
```

**2. Dependency Analysis:**
- What depends on what?
- Circular dependencies? (REJECT if found)
- External dependencies: version pinned? Maintained?

**3. Trade-off Matrix:**
| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| ... | Pro/Con | Pro/Con | ... | ... |

**4. Failure Points:**
- What breaks if X fails? Recovery plan?
- Single points of failure?

**5. Integration Points:**
- How does this connect to existing code?
- Read existing codebase files to verify interfaces

**Reference:** See `references/architecture_checklist.md` for full checklist.

**ULTRATHINK #4:** "What is the SIMPLEST architecture that satisfies ALL constraints?"

**Output:** Architecture document with diagram, trade-offs, and integration plan.

### P5.5: Context Curation Loop (iterative-retrieval pattern)

Before crafting prompts, curate the RIGHT context per component:

```
FOR each component in architecture:
  1. Glob+Grep for existing implementations in codebase
  2. Score relevance of each found file (0-1)
  3. If gaps found → refine search terms, repeat (max 3 cycles)
  4. Bundle top 3-5 high-relevance files per component
  5. Attach to corresponding P6 agent prompt
```

This prevents agents asking "what about file X?" mid-implementation.

---

## P6: PROMPT ENGINEERING (for sub-agents)

**Purpose:** Craft context-rich prompts for each sub-agent task identified in P5.

### Context Sufficiency Check (before dispatch):
After curating each prompt, ask: "Does this context contain everything the agent needs?"
If uncertain → 1-2 retrieval cycles: agent reads context, identifies gaps, re-search, re-curate.
Max 2 cycles — don't get stuck in loop.

### Prompt Template per Agent:

```
ROLE: [specific expert for this sub-task]

CONTEXT_BLOCK:
[Compressed relevant findings from P1 research]
[User constraints from P2]
[Risks to avoid from P3 debate]
[Relevant files from P5.5 context curation]

TASK:
[Specific component from P5 architecture]
[Exact files to create/modify]
[Exact interfaces to implement]

CONSTRAINTS:
[From P2 user clarification]
[From P4 cross-validation]

VERIFICATION:
[How to check work — from P7 simulation]
[Test criteria — specific, measurable]

ANTI-PATTERNS:
[What NOT to do — from P3 debate]
[Known failure modes from P1 research]

FEW-SHOT:
[Examples from research if available]
[Similar patterns in existing codebase]
```

**Reference:** See `references/prompt_templates.md` for domain-specific templates.

### Rules:
- NEVER use generic prompts like "write tests for X" — include WHAT to test and WHY
- Each prompt MUST reference specific findings from P1-P5
- Include file paths, function signatures, expected inputs/outputs
- If agent needs to read files first, specify WHICH files

**Output:** N ready-to-dispatch agent prompts (where N = number of components from P5).

---

## P7: EXECUTION SIMULATION

**Purpose:** Mental dry-run before committing resources.

**ULTRATHINK #5:** Walk through execution step by step:

### Per step, evaluate:
| Aspect | Check |
|--------|-------|
| Failure mode | What could go wrong? Recovery? |
| Time estimate | Minutes/hours for this step? |
| Resources | API calls, RAM, concurrent agents? |
| Dependencies | What must complete first? |
| Verification | How do we KNOW this step succeeded? |

### Parallelization Plan:
```
SERIAL:   [Step 1] → [Step 2] → [Step 5]
PARALLEL: [Step 3] ║ [Step 4]  (after Step 2)
SERIAL:   [Step 5] → [Step 6]
```

### Resource Budget:
- Max concurrent agents: 3-4 (check available RAM with `free -h`)
- Max 1 heavy rate-limited API agent at a time
- API rate limits: check .env for key count and provider limits

**Reference:** See `references/simulation_protocol.md` for resource limits.

**Output:** Ordered execution plan with time estimates and parallelization map.

---

## P8: FINAL PLAN

**Purpose:** Single document combining all phases into actionable plan.

### Structure:
```markdown
# Plan: [Topic]

## Summary
[2-3 sentences — what we're building and why this approach]

## Research Verdict
- Decision: ADOPT / EXTEND / BUILD
- Confidence: HIGH / MEDIUM / LOW
- Key finding: [most important discovery from P1]

## Architecture
[Diagram from P5]
[Trade-offs accepted and why]

## Execution Steps
| # | Task | Agent | Depends On | Time Est | Test Criteria |
|---|------|-------|------------|----------|---------------|
| 1 | ... | ... | - | Xm | ... |
| 2 | ... | ... | #1 | Xm | ... |

## Risk Register
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ... | H/M/L | H/M/L | ... |

## Rollback Plan
[How to undo if things go wrong]

## Agent Prompts
[Ready-to-paste prompts from P6]
```

**Output:** Complete plan written to a file if >20 lines. Display summary to user.

---

## P9: LEARNING LOOP

**Purpose:** Capture what worked for future runs.

Append to aqua-search `knowledge_bank.md`:
- Effective search queries from P1
- Novel findings from P3 debate
- Patterns recognized
- What worked / didn't work
- Time taken vs estimated

Keep entries compact (max 5 lines per run).

---

## P10: AUTO-DISPATCH (Subagent-Driven Execution)

**Purpose:** Launch agents with prompts from P6, respecting order from P7.
**Pattern:** Fresh subagent per task + two-stage review + conflict detection.

### 10.1 Pre-Dispatch Setup
- Extract all tasks from P8 plan into ordered list
- For each task: curate EXACT context (don't let agent read plan — provide full text)
- Classify: PARALLEL (no shared files) vs SERIAL (depends on previous)

### 10.2 Dispatch Loop (per task)

```
FOR each task in execution order:
  1. LAUNCH implementer agent (background if parallel-safe)
     - Prompt = P6 crafted prompt (ROLE + CONTEXT + TASK + CONSTRAINTS)
     - Mode: bypassPermissions (pre-approved by pipeline)
     - Include: "After implementation, run tests and self-review"

  2. WAIT for completion

  3. STAGE 1 REVIEW: Spec Compliance (fresh agent)
     - "Does this match the spec from the plan?"
     - If ISSUES → same implementer fixes → re-review (loop max 2x)

  4. STAGE 2 REVIEW: Code Quality (fresh agent)
     - "Is this well-built? Security, patterns, edge cases?"
     - If ISSUES → same implementer fixes → re-review (loop max 2x)

  5. Mark task COMPLETE
```

### 10.3 Parallel Dispatch Rules
- Launch ALL independent tasks simultaneously (from P7 analysis)
- Max concurrent: 3-4 agents (check available RAM)
- Each agent gets isolated scope (specific files only)
- NEVER dispatch parallel agents that edit SAME files
- After all parallel agents complete: CONFLICT CHECK
  - `git diff` — did any agent modify files another touched?
  - If conflict: resolve manually, don't auto-merge

### 10.4 Context Passing (Critical)
- Controller curates per-task context (agent never reads plan file)
- Include in prompt: scene-setting (where this fits in the bigger picture)
- Include: verification criteria (how to check own work)
- Include: anti-patterns from P3 debate (what NOT to do)
- Include: file paths from P5 architecture (exact, not vague)

### 10.5 Quality Gates
- Each task must pass BOTH review stages before marking complete
- Spec compliance FIRST, then code quality (order matters)
- If review finds issues: implementer fixes → reviewer re-reviews
- NO moving to next serial task while current has open issues

### 10.6 Progress Reporting
- After each task completes: brief status update to user (not a question, just info)
- Format: "Task 3/5 done: [component] — tests pass, moving to next"
- If task fails review 2x: STOP pipeline, report to user with context, wait for guidance
- NEVER auto-retry endlessly — 2 review loops max per task, then escalate

### 10.7 Failure Protocol
- Agent timeout (10 min): kill, retry once with same prompt
- Agent produces wrong output: send to review loop (max 2x)
- Review fails 2x: STOP, report exact issue + agent output + what was expected
- Multiple agents fail: STOP entire pipeline, ULTRATHINK — "Is the plan wrong?"
- Rollback: revert agent changes, report what was rolled back

### 10.8 Integration & Post-Dispatch
- ULTRATHINK #6: "Do agent outputs collectively satisfy the plan? Any gaps?"
- Run full test suite after all tasks complete
- Check for cross-agent conflicts (same file edits)
- If conflicts: resolve, don't auto-merge
- Report results with: files changed, tests status, review issues
- Run self-assessment (see below)
- NO user approval needed for dispatch — but STOP if things go wrong

---

## ULTRATHINK Triggers Summary

| # | Phase | Trigger | Purpose |
|---|-------|---------|---------|
| 1 | P2 | After user answers | Synthesize answers + research into refined problem |
| 2 | P3 | After debate | Winning arguments + unresolved risks |
| 3 | P4 | After cross-validation | Reconcile all inputs into coherent direction |
| 4 | P5 | After architecture | Simplest architecture for all constraints |
| 5 | P7 | After simulation | Mental walkthrough, failure modes, ordering |
| 6 | P10.8 | After all agents done | Do outputs collectively satisfy the plan? Gaps? |

**Rule:** Each ULTRATHINK must produce a WRITTEN output (not just "I thought about it").

---

## Anti-Patterns

| Pattern | Why it's wrong | Instead |
|---------|---------------|---------|
| Code after P1, skip P2-P7 | The whole point is PLANNING | Run full pipeline |
| Generic agent prompts | "write tests for X" has no context | Include P1-P5 specifics |
| Skip debate ("obvious approach") | Obvious to YOU, not adversarial | Always run P3 |
| Ask >5 questions in P2 | Wastes user time, diminishing returns | 3-5 targeted, research-informed |
| FULL mode for typo fix | Overkill wastes time | Auto-detect picks SCOUT |
| Skip simulation, dispatch immediately | Agents will collide or fail | P7 before P10, always |
| Amend P6 prompts post-dispatch | Inconsistent state | Re-run P6 → P7 → P10 |

---

## Self-Assessment (after P10)

After dispatch completes, score the run:

| Question | Score 0-10 |
|----------|------------|
| Did P1 research find something we wouldn't have known? | |
| Did P3 debate change our approach? | |
| Did P7 simulation prevent a mistake? | |
| Were P6 agent prompts better than generic? | |
| Overall pipeline value-add? | |

Append score + notes to P9 learning loop.

---

## Quick Reference: Invocation

```
/aqua-combo "build a notification system with WebSocket + queue"
/aqua-combo --mode full "redesign the data pipeline architecture"
/aqua-combo --mode scout "add retry logic to API calls"
```

**Auto-activation triggers:**
- "plan long build once"
- "research and plan"
- "full pipeline"
- "before we code"
- "design the approach"
- "how should we build this"
- Any non-trivial implementation (>50 LOC) where approach is unclear

---

## References (heavy content delegated)

- `references/architecture_checklist.md` — Full architecture review checklist
- `references/prompt_templates.md` — Domain-specific prompt templates for sub-agents
- `references/simulation_protocol.md` — Resource limits, timing, parallelization rules
