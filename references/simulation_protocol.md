# Simulation Protocol (Phase 7)

Dry-run the entire execution plan mentally before launching any agents.

---

## Pre-Simulation Setup

1. **List all execution steps** from the P5 architecture, in order
2. **For each step, define:**
   - Inputs: what data/files this step needs
   - Outputs: what data/files this step produces
   - Dependencies: which prior steps must complete first
3. **Identify parallelism:**
   - Steps with no shared dependencies can run in parallel
   - Steps sharing DB write access must be serialized
   - Steps sharing API keys: max 1 heavy caller at a time

---

## Mental Walkthrough Template

For each step, fill out:

```
STEP N: [Description]
  INPUT: [What this step receives — files, data, config]
  ACTION: [What happens — API call, DB write, code generation]
  OUTPUT: [What this step produces — files, DB rows, artifacts]
  COULD FAIL IF:
    - [Failure scenario 1]
    - [Failure scenario 2]
  RECOVERY:
    - [What to do if failure 1 occurs]
    - [What to do if failure 2 occurs]
  TIME ESTIMATE: [X minutes]
  RESOURCES: [API calls count, memory, disk writes]
  PARALLEL WITH: [Other step numbers, or NONE]
```

Walk through ALL steps sequentially. At each step, ask:
- Do I have the inputs? (check outputs of prior steps)
- Can this actually fail? (assume it WILL fail — what then?)
- Is the time estimate realistic? (double it for safety)

---

## Failure Mode Catalog

### API Failures
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Rate limit (429) | HTTP status code | Exponential backoff + retry 3x + rotate API key |
| Timeout | No response in 30s | Retry with longer timeout, then skip + log |
| Auth error (401/403) | HTTP status code | Check .env key validity, switch to backup key |
| Data format changed | KeyError / parse fail | Log raw response, alert, fail gracefully |

### Database Failures
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| DB locked | sqlite3.OperationalError | WAL mode + busy_timeout=5000 + retry |
| Disk full | OSError | Check disk space before write, alert if <500MB |
| Schema mismatch | Column not found | Run migration check before operations |
| Corruption | Integrity check fail | Keep daily backup, restore from last good |

### Agent Failures
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Wrong output | Verification criteria fail | Retry with more specific prompt + error feedback |
| Context exceeded | Token limit error | Split task into smaller chunks, compress context |
| Hangs / no response | Timeout >10min | Kill agent, restart with same task |
| Produces extra files | File count check | Delete unexpected files, re-run with stricter OUTPUT FORMAT |

### System Failures
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| OOM (out of memory) | Process killed | Reduce concurrent agents (check available RAM) |
| Dependency missing | ImportError / ModuleNotFoundError | Check requirements before run |
| File conflict | Git merge conflict | git stash before, verify after, manual resolve |
| Process manager lost | Session/container gone | Auto-recovery via process manager restart policy |

---

## Time Estimation Rules

| Task Type | Optimistic | Realistic | Pessimistic |
|-----------|-----------|-----------|-------------|
| API data fetch (small) | 1 min | 3 min | 10 min |
| API data fetch (large/paginated) | 10 min | 30 min | 60 min |
| Code generation (single module) | 2 min | 5 min | 10 min |
| Test writing (per test file) | 3 min | 8 min | 15 min |
| Architecture review | 5 min | 10 min | 15 min |
| Integration + debug | 5 min | 15 min | 30 min |
| Full pipeline (small project) | 20 min | 45 min | 90 min |

**Rules:**
- Use REALISTIC estimate for planning
- Total time = sum of the SERIAL critical path (parallel steps don't add)
- Add 20% buffer for unexpected issues
- If total > 60 min, consider splitting into multiple sessions

---

## Resource Budget

| Resource | Limit | Check Command |
|----------|-------|---------------|
| RAM | Check available memory | Linux: `free -h`, macOS: `vm_stat`, Windows/WSL: `free -h` |
| Concurrent agents | 3-4 max (OS overhead) | `ps aux \| grep agent` |
| Heavy API agents | 1 rate-limited agent at a time | Track in session state |
| Context window per agent | ~200K tokens | Monitor prompt size |
| Disk space | Check before large writes | `df -h` |
| API keys | Check .env for key count + rate limits | Round-robin in code |

---

## Simulation Verdict

After walking through all steps, answer:

1. **Can every step get its required inputs?** If NO: fix the dependency chain.
2. **Is every failure mode covered?** If NO: add recovery logic before starting.
3. **Does total time fit the session?** If NO: cut scope or split into phases.
4. **Does resource usage fit the budget?** If NO: reduce parallelism or batch size.

```
SIMULATION RESULT: PASS / FAIL
  Issues found: {count}
  Fixes applied: {list}
  Estimated time: {X} minutes (serial path)
  Resource usage: {agents} agents, {API calls} API calls, {memory} MB RAM
  GO / NO-GO: {decision}
```

Only proceed to P8 (Final Plan) when simulation result is PASS.
