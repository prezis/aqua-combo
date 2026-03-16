# Context Management Protocol

Context is your most important resource. Claude Code performance degrades as context fills. This protocol prevents the aqua-combo pipeline from eating your entire context window.

---

## Context Strategy: Save-State + /clear > /compact

The official Claude Code docs say performance degrades as context fills. For a multi-phase pipeline, the optimal strategy is:

### Between major phases: save state to plan file → /clear

Each phase produces a concrete artifact. The next phase only needs that artifact, not the full conversation history. A fresh context window gives maximum quality.

| Phase transition | Action | State preserved in |
|-----------------|--------|-------------------|
| After P1 Research | Write findings to plan file → `/clear` | `aqua-combo-plan-*.md` (Research Verdict section) |
| After P2 Clarify | Append refined problem to plan file → `/clear` | Plan file (Summary + Constraints section) |
| After P3 Debate | Append debate conclusions to plan file → `/clear` | Plan file (Risk Register + Direction section) |
| After P4 Architect | Plan file is now complete → `/clear` | Plan file IS the state — it has everything P5 needs |
| After P5 Dispatch | Agent outputs in worktrees → `/clear` | Worktree branches + plan file |
| After P6 Review | Final result | Merged code + plan file as record |

### Why /clear beats /compact for pipelines:

- **`/compact`**: compresses context but keeps conversation going. Good for single-task sessions. Risk: compression loses important details, especially code snippets and exact findings.
- **`/clear`**: completely fresh context. Perfect when state is externalized to a file. Each phase starts at 0% context usage = maximum model performance.
- **Save-state + `/clear`**: write phase output to plan file, clear context, read plan file at start of next phase. Zero compression artifacts.

### When to use /compact instead:

- Within a single phase that's running long (e.g., P1 research reading many files)
- When you don't want to break the conversation flow
- For SCOUT mode (too short to warrant /clear)

### Emergency: context at 70-80%

If context reaches 70-80% during any phase:
1. Save current progress to plan file
2. `/clear`
3. Read plan file to resume
4. Continue the current phase

Don't wait for auto-compaction at 95% — by then performance has already degraded.

## Why Subagents + Worktrees Matter for Context

Each dispatched agent runs in its **own context window** and its **own worktree** (git branch):

- Agent reads files → those tokens are in the AGENT's context, not yours
- Agent generates code → in the agent's worktree, not your working directory
- Agent returns → only a summary enters your context
- Agent's worktree → merged only if work passes review

This is why `isolation: worktree` in Phase 5 is critical. Without it, every agent's file reads and writes pollute your main context.

---

## Resource Budget

| Resource | Limit | How to Check |
|----------|-------|-------------|
| RAM | Varies by machine | Linux: `free -h`, macOS: `vm_stat` |
| Concurrent agents | 3-4 max | `ps aux \| grep claude` |
| Heavy API agents | 1 rate-limited at a time | Track manually |
| Context per agent | ~200K tokens | Monitor prompt size |
| Disk space | Check before large writes | `df -h` |

---

## Failure Mode Catalog

### Agent Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Wrong output | Verification criteria fail | Retry with more specific prompt + error feedback (max 2x) |
| Context exceeded | Token limit error | Split task into smaller chunks |
| Hangs >10 min | No response | Kill agent, retry once |
| Extra files created | File count check | Delete unexpected files, re-run with stricter output spec |

### API Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Rate limit (429) | HTTP status | Backoff + retry 3x + rotate key |
| Timeout | No response 30s | Retry with longer timeout, then skip + log |
| Auth error (401/403) | HTTP status | Check key validity, try backup |
| Data format changed | Parse error | Log raw response, alert, fail gracefully |

### System Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| OOM | Process killed | Reduce concurrent agents |
| Dependency missing | ImportError | Check requirements before run |
| File conflict | Git merge conflict | Worktree isolation prevents this; if manual, stash + resolve |
| Worktree cleanup failed | `git worktree list` shows stale | `git worktree remove <path>` |

---

## Time Estimation

| Task Type | Realistic Estimate |
|-----------|-------------------|
| Quick research (P1 SCOUT) | 2-3 min |
| Deep research (P1 FULL) | 5-10 min |
| Clarification (P2) | 3-5 min (depends on user) |
| Adversarial debate (P3) | 5-10 min |
| Architecture + plan (P4) | 5-15 min |
| Agent dispatch + completion (P5) | 5-30 min (depends on task count) |
| Review (P6) | 5-10 min |
| **Full pipeline** | **30-60 min** |
| **Standard pipeline** | **15-30 min** |
| **Scout** | **5-10 min** |

Add 20% buffer. If total >60 min, consider splitting into sessions.

---

## Worktree Lifecycle

```
1. Agent dispatched with isolation: worktree
   → Claude creates .claude/worktrees/<agent-name>/ with new branch

2. Agent works in its own copy of the repo
   → No conflicts with other agents or your working directory

3. Agent completes
   → If no changes: worktree auto-cleaned
   → If changes: worktree preserved for review

4. After review passes
   → Merge worktree branch into main
   → git worktree remove <path>

5. If review fails
   → git worktree remove <path> discards everything cleanly
```

This is why worktree isolation is the single most important dispatch feature. It makes rollback free and conflict-free.
