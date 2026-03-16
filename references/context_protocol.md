# Context Management Protocol

Context is your most important resource. Claude Code performance degrades as context fills. This protocol prevents the aqua-combo pipeline from eating your entire context window.

---

## Context Cleanup Schedule

| After Phase | Action | Command | Why |
|-------------|--------|---------|-----|
| P1 Research | Compact | `/compact Focus on research conclusions, verdict, and key findings` | Raw search results are verbose |
| P3 Debate | Compact | `/compact Focus on debate direction, risks, and adjusted approach` | Debate transcript is long |
| Before P5 | Compact | `/compact Focus on the plan and execution steps` | Free max context for dispatch |
| Between unrelated tasks | Clear | `/clear` | Fresh context = better output |

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
