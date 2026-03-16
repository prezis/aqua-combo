# Architecture Review Checklist (Phase 5)

Use this checklist during P5 to evaluate the proposed architecture BEFORE any code is written.

---

## Component Analysis

- [ ] List ALL components (modules, classes, scripts) in the architecture
- [ ] What is each component's single responsibility? (one sentence max)
- [ ] Can any two components be merged without losing clarity?
  - If YES: merge them. Over-abstraction is a bigger risk than under-abstraction.
- [ ] Are there missing components? (something the requirements need but architecture doesn't cover)
- [ ] Does every component have a clear owner (which agent will build it)?
- [ ] For each component: what happens if you DELETE it? If nothing breaks, it's unnecessary.

## Dependency Analysis

- [ ] Draw the dependency graph: which module imports/calls which
  ```
  A --> B --> C
  A --> D
  B --> D
  ```
- [ ] Are there circular dependencies? (A->B->A)
  - If YES: extract shared logic into a new module, or merge A and B
- [ ] Coupling level for each pair:
  - TIGHT: shares internal state, calls private methods
  - MODERATE: uses public API, passes data objects
  - LOOSE: communicates via files, DB, or message queue
- [ ] What happens if component X fails?
  - Does the whole system crash? (bad)
  - Does it degrade gracefully? (good)
  - Is there a retry/recovery path? (required)

## Trade-off Matrix

For every non-obvious design decision, fill this table:

```
| Decision           | Option A        | Option B         | Chosen | Why                          |
|--------------------|-----------------|------------------|--------|------------------------------|
| DB engine          | SQLite + WAL    | PostgreSQL       | A      | Single machine, no server    |
| HTTP client        | httpx           | aiohttp          | A      | Simpler API, built-in async  |
| Config format      | .env + dotenv   | YAML config file | A      | Already used in project      |
| Scheduling         | asyncio.sleep   | APScheduler      | A      | No extra dependency          |
| Error reporting    | Telegram alert  | Log file only    | A      | Immediate visibility         |
```

Keep this table in the architecture doc. Future-you will thank present-you.

## Integration Points

- [ ] How does this connect to the EXISTING codebase?
  - List every existing file that will be imported/modified
- [ ] What existing functions/classes can be REUSED?
  - Search the repo before writing new code. Duplication = bugs.
- [ ] What needs to be MODIFIED vs CREATED NEW?
  - Prefer modification. New files = new things to maintain.
- [ ] What's the blast radius of changes?
  - If you modify module X, what else breaks?
  - Run: grep -r "import X" to find all consumers
- [ ] Are there shared resources (DB tables, API keys, config files)?
  - Who owns each? What's the access pattern? (read-only vs read-write)

## Scalability Questions

- [ ] What's the current bottleneck? (CPU, memory, API rate, disk I/O)
- [ ] How does this scale to 10x current load?
  - 10x more API calls: do we hit rate limits?
  - 10x more DB rows: do queries slow down? (add indexes)
  - 10x more agents: do we exceed available RAM?
- [ ] Caching strategy:
  - What data can be cached? For how long?
  - Where: memory dict, file, DB table?
  - Invalidation: time-based, event-based, manual?
- [ ] Failure recovery:
  - Can the system restart mid-operation without data loss?
  - Are there checkpoints? (critical for long pipelines)
  - Is there idempotency? (running twice = same result as once)

## API and Resource Budget

- [ ] List every external API call with: endpoint, rate limit, cost
- [ ] Total API calls per run — does it fit within limits?
- [ ] Max concurrent heavy API agents: 1 at a time (avoid rate limit contention)
- [ ] Memory per component estimate:
  - Agent context: ~200K tokens each
  - Data in memory: estimate from expected volume
  - Total must fit in available RAM with OS overhead

## Simplicity Gate

**ULTRATHINK before finalizing:**

> "Can I remove any component and still satisfy ALL constraints from P2?"

If YES: remove it. Do not keep "nice to have" components.

> "Can I replace any custom code with a standard library call?"

If YES: replace it. Less code = fewer bugs.

> "Is there a simpler architecture that a junior dev could understand in 5 minutes?"

If YES: use the simpler one. Complexity is not a feature.

**The simplest architecture that satisfies all constraints WINS. Always.**

---

## Output: Architecture Decision Record

After completing this checklist, produce:

```
ARCHITECTURE: {name}
COMPONENTS: {count} modules
VERDICT: APPROVE / SIMPLIFY (remove X, Y) / REDESIGN (reason)

COMPONENT LIST:
  1. {name} — {responsibility} — {file path}
  2. ...

DEPENDENCY GRAPH:
  {text diagram}

TRADE-OFFS:
  {table}

RISKS:
  1. {risk} — mitigation: {how}

EXECUTION ORDER:
  1. Build {X} first (no dependencies)
  2. Build {Y} (depends on X)
  3. ...
```
