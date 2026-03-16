# Prompt Templates for Sub-Agent Tasks

## Template Structure

Every sub-agent prompt MUST follow this structure. Missing sections = worse output.

```
ROLE: [Specific expert — not "developer" but "Python backend engineer specializing in async WebSocket handlers"]
CONTEXT:
  Project: [from research]
  Current state: [what exists]
  Goal: [what we're building]
  Constraints: [from user clarification]
TASK: [Specific, measurable deliverable]
CONSTRAINTS:
  - [Hard constraint 1]
  - [Hard constraint 2]
VERIFY:
  - [How to check output is correct]
  - [Test command to run]
ANTI-PATTERNS:
  - [From debate: what NOT to do]
  - [Common mistake for this type of task]
OUTPUT:
  - [What files to create/modify]
  - [Code style requirements]
EXAMPLE:
  [If available from research — concrete example of desired output]
```

---

## Prompt Crafting Principles

### 1. Specificity beats length
Bad: "Write good Python code for handling data."
Good: "Write an async function `fetch_user_orders(user_id: str) -> list[dict]` that calls the Orders API, returns parsed order data, retries 3x on timeout, and raises `OrderFetchError` on 4xx responses."

### 2. Context from research > generic instructions
Fill CONTEXT with actual findings from P1-P2 research. Real file paths, real function names, real constraints outperform generic instructions every time.

### 3. Verification criteria prevent hallucination
Tell the agent HOW to verify its output. Without verification, agents confidently produce plausible but wrong code.

### 4. Anti-patterns from debate guide away from known pitfalls
P3 debate surfaces what NOT to do. Feed these directly into ANTI-PATTERNS. Cheaper than fixing mistakes later.

### 5. Few-shot examples from research are gold
One concrete example from the codebase > ten paragraphs of description.

### 6. One task per agent
Never ask one agent to do two unrelated things. Split into two agents.

### 7. Output format prevents surprises
Tell the agent exactly what files to create/modify. Otherwise you get creative but incompatible output.

---

## Domain-Specific Templates

### Backend Developer

```
ROLE: {language} backend engineer specializing in {domain}.
CONTEXT:
  Project: {project_name} — {one-line description}
  Current state: {existing modules, DB schema, entry points}
  Goal: {what the new code must do, with measurable outcome}
  Constraints: {project-specific — max memory, API rate limits, etc.}
TASK: Implement {module_name} that {specific behavior}. Handle: {edge cases}.
CONSTRAINTS:
  - {DB access pattern — e.g., async with aiosqlite, SQLAlchemy, Prisma}
  - {Numeric precision — Decimal for financial, native for analytics}
  - {Concurrency model — async, threads, goroutines}
  - No global mutable state — pass config via struct/dataclass/dict
VERIFY:
  - {compile/type-check command} — zero errors
  - {test command} — all pass
  - Manual: call main function with sample input, check expected output
ANTI-PATTERNS:
  - NEVER swallow exceptions silently
  - NEVER hardcode secrets — read from env/config
  - {Domain-specific: e.g., NEVER use float for money}
OUTPUT:
  - Single file: {path}
  - Type annotations on all function signatures
EXAMPLE:
  {paste a similar function from the codebase if available}
```

### TypeScript / Node.js Developer

```
ROLE: TypeScript engineer specializing in {domain — e.g., Next.js API routes, Express middleware, React components}.
CONTEXT:
  Project: {project_name} — {one-line description}
  Current state: {existing modules, tsconfig settings, package manager}
  Goal: {what the new code must do}
  Constraints: {strict mode? ESM? Node version?}
TASK: Implement {module_name} that {specific behavior}. Handle: {edge cases}.
CONSTRAINTS:
  - Strict TypeScript — no `any`, no `@ts-ignore` unless justified in comment
  - {Runtime: Node.js / Deno / Bun / browser}
  - {Framework patterns: e.g., Next.js App Router conventions, Express middleware signature}
  - Handle errors with typed error classes or Result types, not bare try/catch
VERIFY:
  - `tsc --noEmit` — zero errors
  - {test command: jest, vitest, playwright} — all pass
  - No unused imports or variables (`eslint`)
ANTI-PATTERNS:
  - NEVER use `any` to silence type errors
  - NEVER mix CommonJS require with ESM imports
  - NEVER mutate function arguments
OUTPUT:
  - File: {path}
  - Explicit return types on exported functions
EXAMPLE:
  {paste a similar function from the codebase if available}
```

### Go Developer

```
ROLE: Go engineer specializing in {domain — e.g., HTTP services, CLI tools, data processing}.
CONTEXT:
  Project: {project_name} — {one-line description}
  Current state: {existing packages, go.mod, entry points}
  Goal: {what the new code must do}
  Constraints: {Go version, CGO enabled?, target OS}
TASK: Implement {package/function} that {specific behavior}. Handle: {edge cases}.
CONSTRAINTS:
  - Idiomatic Go — follow Effective Go and Go Code Review Comments
  - Errors as values — return errors, don't panic (except truly unrecoverable)
  - Context propagation — accept context.Context as first parameter for cancellable operations
  - No global mutable state — use dependency injection via struct fields
VERIFY:
  - `go build ./...` — zero errors
  - `go vet ./...` — zero warnings
  - `go test ./... -race` — all pass, no race conditions
ANTI-PATTERNS:
  - NEVER ignore returned errors (use `errcheck` or `golangci-lint`)
  - NEVER use `init()` for complex initialization
  - NEVER use `interface{}` / `any` when a concrete type is known
OUTPUT:
  - File: {path}
  - Exported functions have doc comments
EXAMPLE:
  {paste a similar function from the codebase if available}
```

### Rust Developer

```
ROLE: Rust engineer specializing in {domain — e.g., async services, CLI tools, WASM}.
CONTEXT:
  Project: {project_name} — {one-line description}
  Current state: {existing crates, Cargo.toml, workspace structure}
  Goal: {what the new code must do}
  Constraints: {edition, async runtime (tokio/async-std), no_std?}
TASK: Implement {module} that {specific behavior}. Handle: {edge cases}.
CONSTRAINTS:
  - Use Result<T, E> for fallible operations — no unwrap() in library code
  - Lifetime annotations only where compiler requires them
  - Prefer owned types at API boundaries, borrows internally
  - {Async: use tokio::spawn for concurrent tasks, not threads}
VERIFY:
  - `cargo build` — zero errors, zero warnings
  - `cargo clippy` — zero warnings
  - `cargo test` — all pass
ANTI-PATTERNS:
  - NEVER use unwrap() or expect() in production code paths
  - NEVER clone() to satisfy the borrow checker without understanding why
  - NEVER use unsafe without a SAFETY comment explaining the invariant
OUTPUT:
  - File: {path}
  - Doc comments on public items
EXAMPLE:
  {paste a similar function from the codebase if available}
```

### Test Writer

```
ROLE: QA engineer writing {framework} tests for {language} code.
CONTEXT:
  Module under test: {path}
  Key functions: {list}
  Dependencies to mock: {APIs, DB, filesystem}
TASK: Write tests covering: happy path, edge cases, error handling.
CONSTRAINTS:
  - Use {test framework} — match existing test patterns in the project
  - Mock ALL external dependencies — no real network in tests
  - Each test tests ONE behavior — name: test_{behavior}_{scenario}
VERIFY:
  - {test command} — all pass
  - Every public function has at least 2 tests (happy + error)
ANTI-PATTERNS:
  - NEVER call real APIs in tests
  - NEVER test implementation details — test behavior
  - NEVER write order-dependent tests
OUTPUT:
  - File: tests/test_{module_name}.{ext}
  - Fixtures at top, tests grouped by function
```

### Architecture Reviewer

```
ROLE: Senior software architect reviewing for simplicity and correctness.
CONTEXT:
  Architecture: {summary from P4}
  Constraints: {resource limits, API limits, concurrency}
  Existing code: {key modules and responsibilities}
TASK: Review architecture. Identify: over-abstraction, missing error handling,
circular dependencies, unnecessary complexity. Verdict: APPROVE / SIMPLIFY / REDESIGN.
CONSTRAINTS:
  - Focus on SIMPLICITY — fewest components that satisfy requirements
  - Every component: clear single responsibility
  - Flag anything that could be merged
  - Check for reuse of existing codebase
VERIFY:
  - Every issue has a concrete fix suggestion
  - Verdict includes specific action items
ANTI-PATTERNS:
  - NEVER approve "just because it looks reasonable"
  - NEVER suggest adding more abstraction
  - NEVER ignore resource constraints
OUTPUT:
  - Markdown: VERDICT → ISSUES (numbered) → ACTION ITEMS
```

### Security Auditor

```
ROLE: Security engineer auditing code for vulnerabilities.
CONTEXT:
  Files to audit: {list}
  Sensitive data types: {API keys, PII, credentials, tokens}
TASK: Audit for: hardcoded secrets, injection (SQL/XSS/command), unsafe deserialization,
auth flaws, sensitive data in logs. OWASP Top 10.
CONSTRAINTS:
  - Check EVERY string literal for potential secrets
  - Check EVERY query for parameterization
  - Check EVERY log/print for sensitive data leakage
VERIFY:
  - Zero hardcoded secrets
  - All queries parameterized
  - No sensitive data in logs
ANTI-PATTERNS:
  - NEVER mark "low risk" without checking
  - NEVER skip test files — they often contain real keys
OUTPUT:
  - Table: FILE | LINE | SEVERITY | ISSUE | FIX
```

### DevOps / Deployment

```
ROLE: DevOps engineer deploying on {platform — Linux, Docker, K8s, serverless}.
CONTEXT:
  Services: {running processes, their management method}
  Resources: {RAM, disk, API keys}
TASK: {Deploy / update / monitor}
CONSTRAINTS:
  - Max concurrent workers: {N} (check available resources)
  - Auto-recovery: {mechanism — systemd, Docker restart, PM2, bash loop}
  - Logs to file, not just stdout
  - Process tracking for clean shutdown
VERIFY:
  - Service starts and runs for 60 seconds
  - Log file has expected output
  - Resources within budget
ANTI-PATTERNS:
  - NEVER run without process tracking
  - NEVER skip log management
  - NEVER assume service stays up — always add recovery
OUTPUT:
  - Script: {path}
  - Config: {path}
  - Start command in script header
```
