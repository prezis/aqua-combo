# Prompt Templates for Sub-Agent Tasks

## Template Structure

Every sub-agent prompt MUST follow this structure. Missing sections = worse output.

```
ROLE: [Specific expert — not generic "developer" but "Python backend engineer specializing in async WebSocket handlers"]
CONTEXT_BLOCK:
  Project: [from research]
  Current state: [what exists]
  Goal: [what we're building]
  Constraints: [from user clarification]
TASK: [Specific, measurable deliverable]
CONSTRAINTS:
  - [Hard constraint 1]
  - [Hard constraint 2]
VERIFICATION:
  - [How to check output is correct]
  - [Test command to run]
ANTI-PATTERNS:
  - [From debate: what NOT to do]
  - [Common mistake for this type of task]
OUTPUT FORMAT:
  - [What files to create/modify]
  - [Code style requirements]
FEW-SHOT EXAMPLE:
  [If available from research — concrete example of desired output]
```

---

## Role Templates

### 1. Backend Developer (Python, async, DB)

```
ROLE: Python backend engineer specializing in {domain — e.g., async/await patterns, REST APIs, data processing}.
CONTEXT_BLOCK:
  Project: {project_name} — {one-line description}
  Current state: {existing modules, DB schema, entry points}
  Goal: {what the new code must do, with measurable outcome}
  Constraints: {project-specific constraints — e.g., max memory, API rate limits}
TASK: Implement {module_name} that {specific behavior}. Must handle {edge cases}.
CONSTRAINTS:
  - {DB access pattern — e.g., async with aiosqlite, SQLAlchemy session, Prisma client}
  - {Numeric precision — e.g., Decimal(str(value)) for financial data, or float if precision is not critical}
  - No global mutable state — pass config via dataclass or dict
  - {Async pattern if applicable — e.g., async def for I/O-bound functions}
VERIFICATION:
  - python -m py_compile {file} — zero errors
  - pytest {test_file} -v — all green
  - Manual: call main function with sample input, check expected output
ANTI-PATTERNS:
  - NEVER swallow exceptions with bare `except:`
  - NEVER hardcode API keys — read from .env or config
  - {Domain-specific: e.g., NEVER use float for financial values}
  - {Async-specific: e.g., NEVER use time.sleep() in async code}
OUTPUT FORMAT:
  - Single file: {path}
  - Type hints on all function signatures
  - Docstring on public functions (one-liner is fine)
FEW-SHOT EXAMPLE:
  {paste a similar function from the codebase if available}
```

### 2. Test Writer (pytest, TDD)

```
ROLE: QA engineer writing pytest tests for Python async code with aiosqlite and httpx.
CONTEXT_BLOCK:
  Project: {project_name}
  Module under test: {path to module}
  Key functions: {list of functions to test}
  Dependencies: {what needs mocking — APIs, DB, filesystem}
TASK: Write comprehensive tests for {module}. Cover: happy path, edge cases, error handling.
CONSTRAINTS:
  - Use pytest + pytest-asyncio for async tests
  - Mock ALL external API calls — no real network in tests
  - Use tmp_path fixture for any file I/O
  - Each test function tests ONE behavior — name it test_{behavior}_{scenario}
VERIFICATION:
  - pytest {test_file} -v — all pass
  - pytest {test_file} --tb=short — no warnings
  - Coverage: every public function has at least 2 tests (happy + error)
ANTI-PATTERNS:
  - NEVER call real APIs in tests
  - NEVER test implementation details — test behavior
  - NEVER write tests that depend on execution order
  - NEVER skip writing error-case tests
OUTPUT FORMAT:
  - File: tests/test_{module_name}.py
  - Fixtures at top, tests grouped by function
```

### 3. Architecture Reviewer

```
ROLE: Senior software architect reviewing Python backend systems for simplicity, correctness, and maintainability.
CONTEXT_BLOCK:
  Project: {project_name}
  Architecture doc: {summary of planned architecture from P5}
  Constraints: {RAM limit, API limits, concurrency limits}
  Existing code: {key existing modules and their responsibilities}
TASK: Review the proposed architecture. Identify: over-abstraction, missing error handling, circular dependencies, unnecessary complexity. Produce a verdict: APPROVE / SIMPLIFY / REDESIGN.
CONSTRAINTS:
  - Focus on SIMPLICITY — fewest components that satisfy all requirements
  - Every component must have a clear single responsibility
  - Flag any component that could be merged with another
  - Check for reuse of existing codebase functions
VERIFICATION:
  - Every flagged issue has a concrete fix suggestion
  - Verdict includes specific action items, not vague advice
ANTI-PATTERNS:
  - NEVER approve "just because it looks reasonable"
  - NEVER suggest adding more abstraction layers
  - NEVER ignore resource constraints (RAM, API limits)
OUTPUT FORMAT:
  - Markdown report: VERDICT, ISSUES (numbered), ACTION ITEMS
```

### 4. Security Auditor

```
ROLE: Security engineer auditing Python code for credential leaks, injection, and unsafe patterns.
CONTEXT_BLOCK:
  Project: {project_name}
  Files to audit: {list of files}
  Sensitive data: API keys, secrets, credentials, DB connection strings
TASK: Audit for: hardcoded secrets, SQL injection, unsafe deserialization, exposed endpoints, logging of sensitive data.
CONSTRAINTS:
  - Check EVERY string literal for potential secrets
  - Check EVERY SQL query for parameterization
  - Check EVERY log/print statement for sensitive data leakage
VERIFICATION:
  - Zero hardcoded secrets (grep for patterns: key=, secret=, password=)
  - All SQL uses parameterized queries (? placeholders)
  - No private keys in logs
ANTI-PATTERNS:
  - NEVER mark "low risk" without checking — assume everything is high risk
  - NEVER skip checking test files — they often contain real keys
OUTPUT FORMAT:
  - Table: FILE | LINE | SEVERITY | ISSUE | FIX
```

### 5. Data Pipeline Builder

```
ROLE: Data engineer building ETL pipelines in Python with {transport — e.g., async HTTP, message queue, file reader} and {storage — e.g., PostgreSQL, SQLite, S3, BigQuery}.
CONTEXT_BLOCK:
  Project: {project_name}
  Data source: {API endpoint, format, rate limits}
  Target: {DB table schema, expected row format}
  Volume: {expected records per run}
TASK: Build pipeline that fetches from {source}, transforms to {schema}, loads into {table}. Must handle: pagination, rate limits, partial failures.
CONSTRAINTS:
  - Checkpoint progress — resumable after crash
  - {Numeric precision — e.g., Decimal(str(value)) for financial data, or native types if precision is not critical}
  - Respect rate limits: {X} requests per second max
  - Cache raw responses in {cache_dir}
VERIFICATION:
  - Dry run with limit=10 produces correct rows
  - Interrupt mid-run, restart — no duplicates, no data loss
  - {Precision check if applicable — e.g., verify no floating point artifacts}
ANTI-PATTERNS:
  - NEVER load all data into memory — stream/paginate
  - NEVER skip error handling on individual records — log and continue
  - {Domain-specific: e.g., NEVER use float for financial amounts}
OUTPUT FORMAT:
  - Single file: {path}
  - Functions: fetch(), transform(), load(), run_pipeline()
```

### 6. Frontend Developer

```
ROLE: Frontend developer building lightweight HTML/JS dashboards or Telegram bot interfaces.
CONTEXT_BLOCK:
  Project: {project_name}
  Data source: {API or DB to read from}
  User: {who will use this — Telegram bot, web dashboard, CLI}
TASK: Build {interface} that displays {data} with {interactions}.
CONSTRAINTS:
  - Minimal dependencies — vanilla JS or single library max
  - Mobile-friendly if web
  - Refresh interval: {X} seconds
VERIFICATION:
  - Open in browser / send test message — visual check
  - Data matches DB/API source
ANTI-PATTERNS:
  - NEVER build SPA framework for simple dashboard
  - NEVER fetch data client-side if server can pre-render
OUTPUT FORMAT:
  - Files: {list}
  - No build step required
```

### 7. DevOps / Deployment

```
ROLE: DevOps engineer deploying services on {platform — e.g., Linux server, Docker, Kubernetes, serverless}.
CONTEXT_BLOCK:
  Project: {project_name}
  Services: {list of running processes and their management — e.g., tmux windows, Docker containers, systemd units, PM2 apps}
  Resources: {current RAM usage, disk, API key count}
TASK: {Deploy new service / update existing / set up monitoring}
CONSTRAINTS:
  - Max concurrent workers: {N} (check available RAM: `free -h` on Linux, `vm_stat` on macOS)
  - Services must auto-recover ({mechanism — e.g., systemd restart, Docker restart policy, PM2 watch, bash loop})
  - Logs to file, not just stdout
  - Process tracking for clean shutdown ({PID files, Docker container names, PM2 IDs})
VERIFICATION:
  - Service starts and stays running for 60 seconds
  - Log file populated with expected output
  - Resource usage within budget
ANTI-PATTERNS:
  - NEVER run without process tracking — orphan processes are invisible
  - NEVER skip log rotation — disk fills up
  - NEVER assume service will stay up — always add restart/recovery mechanism
OUTPUT FORMAT:
  - Script: {path}
  - Config: {path}
  - Start command documented in script header
```

---

## Prompt Crafting Principles

### 1. Specificity beats length
Bad: "Write good Python code for handling data."
Good: "Write an async function `fetch_user_orders(user_id: str) -> list[dict]` that calls the Orders API, returns parsed order data, retries 3x on timeout, and raises `OrderFetchError` on 4xx responses."

### 2. Context from research > generic instructions
Fill CONTEXT_BLOCK with actual findings from P1-P2 research. A prompt with real file paths, real function names, and real constraints outperforms a generic one every time.

### 3. Verification criteria prevent hallucination
If you tell the agent HOW to verify its output, it self-corrects. Without verification, agents confidently produce plausible but wrong code.

### 4. Anti-patterns from debate guide away from known pitfalls
The P3 debate surfaces what NOT to do. Feed these directly into ANTI-PATTERNS. This is cheaper than fixing mistakes after the fact.

### 5. Few-shot examples from research are gold
If P1 research found a working example (from the codebase, docs, or web), paste it into FEW-SHOT EXAMPLE. One concrete example > ten paragraphs of description.

### 6. One task per agent
Never ask one agent to do two unrelated things. Split into two agents. Focused agents produce better output and are easier to verify.

### 7. Output format prevents surprises
Tell the agent exactly what files to create/modify and what style to use. Otherwise you get creative but incompatible output.
