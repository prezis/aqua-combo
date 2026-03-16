#!/usr/bin/env python3
"""
aqua-combo-run.py — Enforced research-to-execution pipeline runner.

Transforms aqua-combo from a prompt-based skill into an actual engine
that enforces phase order, validates state, and manages context.

Usage:
    python3 aqua-combo-run.py "build a notification system"
    python3 aqua-combo-run.py "redesign auth" --mode full
    python3 aqua-combo-run.py "add retry logic" --mode scout
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

PHASE_TIMEOUT = 600  # 10 min per phase
MAX_TURNS_PER_PHASE = 50
MAX_BUDGET_PER_PHASE = 2.0  # USD

MODES = {
    "scout": ["P1"],
    "standard": ["P1", "P2", "P4", "P5", "P6"],
    "full": ["P1", "P2", "P3", "P4", "P5", "P6"],
}

PHASE_NAMES = {
    "P1": "Research",
    "P2": "Clarify",
    "P3": "Debate",
    "P4": "Architect",
    "P5": "Dispatch",
    "P6": "Review",
}

# Tools allowed per phase (read-only for research/planning, full for dispatch)
PHASE_TOOLS = {
    "P1": "Read,Glob,Grep,Bash,WebSearch,WebFetch",
    "P2": None,  # Interactive — no tool restriction
    "P3": "Read,Glob,Grep,Bash,WebSearch,WebFetch",
    "P4": "Read,Glob,Grep",  # Plan mode — read only
    "P5": "Read,Edit,Write,Bash,Glob,Grep,Agent",  # Full — dispatch agents
    "P6": "Read,Glob,Grep,Bash,Agent",  # Review — can dispatch reviewers
}

# ─── Plan File Management ────────────────────────────────────────────────────

PLAN_TEMPLATE = """<!-- AQUA-COMBO STATE -->
<!-- MODE: {mode} -->
<!-- TOPIC: {topic} -->
<!-- STARTED: {timestamp} -->
<!-- PHASE:P1:PENDING -->
<!-- PHASE:P2:PENDING -->
<!-- PHASE:P3:PENDING -->
<!-- PHASE:P4:PENDING -->
<!-- PHASE:P5:PENDING -->
<!-- PHASE:P6:PENDING -->

# Plan: {topic}

## Research Verdict
_Pending P1..._

## Refined Problem
_Pending P2..._

## Debate Conclusions
_Pending P3..._

## Architecture
_Pending P4..._

## Execution Steps
_Pending P4..._

## Risk Register
_Pending P4..._

## Dispatch Results
_Pending P5..._

## Review Results
_Pending P6..._
"""


def slugify(text: str) -> str:
    """Convert topic to filename-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")[:50]


def create_plan_file(topic: str, mode: str) -> Path:
    """Create initial plan file with state markers."""
    slug = slugify(topic)
    filename = f"aqua-combo-plan-{slug}.md"
    plan_path = Path(filename)

    content = PLAN_TEMPLATE.format(
        mode=mode.upper(),
        topic=topic,
        timestamp=datetime.now().isoformat(),
    )
    plan_path.write_text(content)
    print(f"  Plan file: {plan_path}")
    return plan_path


def read_plan(plan_path: Path) -> str:
    """Read plan file content."""
    return plan_path.read_text()


def update_plan_section(plan_path: Path, section: str, content: str):
    """Replace a section's placeholder with actual content."""
    plan = read_plan(plan_path)
    pattern = rf"(## {re.escape(section)}\n)_Pending.*?_"
    replacement = rf"\1{content}"
    updated = re.sub(pattern, replacement, plan, flags=re.DOTALL)
    plan_path.write_text(updated)


def mark_phase_complete(plan_path: Path, phase: str):
    """Update phase marker from PENDING to COMPLETE."""
    plan = read_plan(plan_path)
    updated = plan.replace(
        f"<!-- PHASE:{phase}:PENDING -->",
        f"<!-- PHASE:{phase}:COMPLETE -->"
    )
    plan_path.write_text(updated)


def check_phase_complete(plan_path: Path, phase: str) -> bool:
    """Check if a phase is marked COMPLETE."""
    plan = read_plan(plan_path)
    return f"<!-- PHASE:{phase}:COMPLETE -->" in plan


def validate_prerequisites(plan_path: Path, phase: str, mode: str) -> bool:
    """Check that all required prior phases are complete."""
    phases = MODES[mode]
    phase_idx = phases.index(phase) if phase in phases else -1
    for i in range(phase_idx):
        prior = phases[i]
        if not check_phase_complete(plan_path, prior):
            print(f"  ERROR: {prior} ({PHASE_NAMES[prior]}) not complete. Cannot start {phase}.")
            return False
    return True


# ─── Skill Detection ─────────────────────────────────────────────────────────

SKILL_LOCATIONS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".claude" / "commands",
    Path.home() / ".claude" / "plugins",
    Path(".claude") / "skills",
    Path(".claude") / "commands",
]


def skill_exists(name: str) -> bool:
    """Check if a skill/command exists in any location."""
    clean_name = name.lstrip("/").replace(":", "-").replace("--", "/")
    for loc in SKILL_LOCATIONS:
        if not loc.exists():
            continue
        # Check as directory with SKILL.md
        for pattern in [f"*{name.lstrip('/')}*", f"*{clean_name}*"]:
            matches = list(loc.glob(f"**/{pattern}"))
            if matches:
                return True
    return False


def detect_skills() -> dict:
    """Detect which recommended skills are available."""
    skills = {
        "aqua-search": skill_exists("aqua-search"),
        "octo-define": skill_exists("octo-define"),
        "octo-debate": skill_exists("octo-debate"),
        "octo--octopus-architecture": skill_exists("octo--octopus-architecture"),
        "octo--skill-code-review": skill_exists("octo--skill-code-review"),
        "verification-loop": skill_exists("verification-loop"),
        "thought-partner": skill_exists("octo--skill-thought-partner"),
        "writing-plans": skill_exists("superpowers--writing-plans"),
        "dispatching-parallel": skill_exists("superpowers--dispatching-parallel-agents"),
    }
    return skills


# ─── Phase Prompts ───────────────────────────────────────────────────────────

def build_phase_prompt(phase: str, topic: str, plan_content: str, skills: dict, mode: str) -> str:
    """Build the prompt for each phase, incorporating plan state and available skills."""

    base_context = f"""You are executing phase {phase} ({PHASE_NAMES[phase]}) of the aqua-combo pipeline.
Topic: {topic}
Mode: {mode.upper()}

Current plan file state:
{plan_content}

IMPORTANT: After completing this phase, output your findings in a structured way.
Start your output with "=== {phase} OUTPUT ===" and end with "=== {phase} DONE ==="."""

    if phase == "P1":
        skill_hint = 'Use /aqua-search for deep research.' if skills.get("aqua-search") else ''
        return f"""{base_context}

PHASE 1: RESEARCH
{skill_hint}
Research the topic thoroughly:
1. Search for best practices, libraries, pitfalls
2. Check the existing codebase for prior art (grep/glob)
3. Check existing dependencies

Output format:
- VERDICT: ADOPT / EXTEND / BUILD
- KEY FINDINGS: (3-5 bullet points)
- LIBRARIES/PATTERNS: (what exists)
- CONFIDENCE: HIGH / MEDIUM / LOW

ultrathink: What is the most important thing we learned?"""

    elif phase == "P2":
        skill_hint = 'Use /octo-define for multi-AI consensus on requirements.' if skills.get("octo-define") else ''
        thought_hint = 'First use /octo--skill-thought-partner to discover hidden assumptions.' if (mode == "full" and skills.get("thought-partner")) else ''
        return f"""{base_context}

PHASE 2: CLARIFY
{thought_hint}
{skill_hint}
Based on the research findings, ask the user 3-5 targeted questions they haven't thought of:
- Hard constraints — what CANNOT change?
- Integration requirements — what must it connect to?
- Scale — users, data volume, concurrency?
- Priority — speed vs quality vs cost?
- What already tried?

Questions MUST be informed by P1 research — not generic.

ultrathink: Synthesize user answers + research into a refined problem statement (max 200 words)."""

    elif phase == "P3":
        skill_hint = 'Use /octo-debate for 3-way AI debate.' if skills.get("octo-debate") else 'Use Gemini CLI if available, otherwise WebSearch for community skepticism.'
        return f"""{base_context}

PHASE 3: ADVERSARIAL DEBATE
{skill_hint}
Stress-test the proposed approach:
1. Why will this approach FAIL?
2. What are we NOT seeing?
3. What alternative would be better?
4. What's the #1 underestimated risk?

Synthesize 4 perspectives: Advocate, Devil's Advocate, Paradox Hunter, Pragmatist.

Cross-validate: research vs debate vs user constraints.

Output:
- DIRECTION: (one sentence)
- CONFIDENCE: HIGH / MEDIUM / LOW
- UNRESOLVED: (list)
- ADJUSTED FROM ORIGINAL: (what changed)

ultrathink: Winning arguments, unresolved risks, approach adjustment."""

    elif phase == "P4":
        arch_hint = 'Use /octo--octopus-architecture for multi-AI design.' if skills.get("octo--octopus-architecture") else ''
        plan_hint = 'Then use /superpowers--writing-plans to convert design into TDD tasks.' if skills.get("writing-plans") else ''
        return f"""{base_context}

PHASE 4: ARCHITECT
{arch_hint}
{plan_hint}
Design the SIMPLEST architecture that satisfies all constraints:
1. Component diagram (ASCII)
2. Trade-off matrix for non-obvious decisions
3. Integration points — which files modified vs created
4. Execution steps — ordered, with dependencies and parallelism

ultrathink: What is the SIMPLEST architecture that satisfies ALL constraints?
- Can I remove any component? → remove it
- Can I replace custom code with stdlib? → replace it
- Would a junior dev understand in 5 min? → if not, simplify

Output the full plan with execution steps table."""

    elif phase == "P5":
        dispatch_hint = 'Use /superpowers--dispatching-parallel-agents for parallel tasks.' if skills.get("dispatching-parallel") else ''
        return f"""{base_context}

PHASE 5: DISPATCH
{dispatch_hint}
Execute the plan from P4:
1. Present the task list to the user for confirmation
2. Dispatch agents with worktree isolation for each task
3. Each agent gets: context from P1-P3, specific task, verification criteria
4. Report progress after each task

For each task, tell Claude:
"Dispatch [task] using a subagent with worktree isolation.
Context: [findings]. Verify by: [test criteria from plan]."

Report: "Task N/M done: [component] — [status]"."""

    elif phase == "P6":
        review_hint = 'Use /octo--skill-code-review for multi-AI review.' if skills.get("octo--skill-code-review") else ''
        verify_hint = 'Use /verification-loop for automated gates.' if skills.get("verification-loop") else ''
        return f"""{base_context}

PHASE 6: REVIEW
{review_hint}
{verify_hint}
Review all agent outputs:
1. Spec compliance — does each output match the plan's test criteria?
2. Security + quality — vulnerabilities, edge cases, code smells?
3. Integration — run the project's test suite

ultrathink: Do outputs collectively satisfy the plan? Any gaps?

Self-assessment (score 0-10):
- Did P1 research find something we wouldn't have known?
- Did P3 debate change our approach?
- Were agent prompts better than generic?
- Overall pipeline value-add?

Then: merge worktree branches and clean up."""

    return base_context


# ─── Claude Execution ────────────────────────────────────────────────────────

def run_claude(prompt: str, tools: str = None, interactive: bool = False,
               session_id: str = None, timeout: int = PHASE_TIMEOUT) -> dict:
    """Execute a Claude Code invocation and return parsed result."""

    if interactive:
        # Interactive mode for P2 — user needs to answer questions
        cmd = ["claude"]
        if session_id:
            cmd += ["--resume", session_id]
        print("\n  Launching interactive Claude session for clarification...")
        print("  (Answer the questions, then type 'exit' or Ctrl+C when done)\n")
        result = subprocess.run(cmd, timeout=timeout * 2)
        return {"result": "(interactive session completed)", "session_id": session_id or "interactive"}

    cmd = ["claude", "-p", prompt, "--output-format", "json", "--effort", "high"]

    if tools:
        cmd += ["--allowedTools"] + tools.split(",")
    if session_id:
        cmd += ["--resume", session_id]

    cmd += ["--max-turns", str(MAX_TURNS_PER_PHASE)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            print(f"  WARNING: Claude exited with code {result.returncode}")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")

        # Parse JSON output
        if result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
                return parsed
            except json.JSONDecodeError:
                return {"result": result.stdout, "session_id": None}
        else:
            return {"result": "(no output)", "session_id": None}

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: Phase exceeded {timeout}s limit")
        return {"result": "(timeout)", "session_id": None}


def extract_phase_output(result_text: str, phase: str) -> str:
    """Extract structured output between === markers."""
    pattern = rf"=== {phase} OUTPUT ===(.*?)=== {phase} DONE ==="
    match = re.search(pattern, result_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: return full result if markers not found
    return result_text[:2000] if result_text else "(no output)"


# ─── Phase Section Mapping ───────────────────────────────────────────────────

PHASE_TO_SECTION = {
    "P1": "Research Verdict",
    "P2": "Refined Problem",
    "P3": "Debate Conclusions",
    "P4": "Architecture",
    "P5": "Dispatch Results",
    "P6": "Review Results",
}


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def run_pipeline(topic: str, mode: str):
    """Execute the aqua-combo pipeline."""

    phases = MODES[mode]
    total = len(phases)

    print(f"\n{'='*60}")
    print(f"  aqua-combo v2 — {mode.upper()} mode")
    print(f"  Topic: {topic}")
    print(f"  Phases: {' → '.join(phases)}")
    print(f"{'='*60}\n")

    # Detect available skills
    print("  Detecting installed skills...")
    skills = detect_skills()
    available = [k for k, v in skills.items() if v]
    missing = [k for k, v in skills.items() if not v]
    if available:
        print(f"  Found: {', '.join(available)}")
    if missing:
        print(f"  Not found (using fallbacks): {', '.join(missing)}")

    # Create plan file
    plan_path = create_plan_file(topic, mode)
    session_id = None

    # SCOUT mode: simplified — one shot, no plan file ceremony
    if mode == "scout":
        print(f"\n  [P1] Research (SCOUT — quick mode)...")
        prompt = f"""Quick research for: {topic}
1-2 searches + check codebase for prior art.
Output: what exists (max 100 words) + steps (max 5) to implement."""
        result = run_claude(prompt, tools=PHASE_TOOLS["P1"])
        output = result.get("result", "")
        print(f"\n{output}\n")
        mark_phase_complete(plan_path, "P1")
        update_plan_section(plan_path, "Research Verdict", output[:1000])
        print(f"\n  SCOUT complete. Plan: {plan_path}")
        return

    # STANDARD / FULL: run all phases
    for i, phase in enumerate(phases, 1):
        phase_name = PHASE_NAMES[phase]
        print(f"\n{'─'*60}")
        print(f"  [{phase}] {phase_name} ({i}/{total})")
        print(f"{'─'*60}")

        # Validate prerequisites
        if not validate_prerequisites(plan_path, phase, mode):
            print(f"\n  ABORT: Prerequisites not met for {phase}.")
            sys.exit(1)

        # Read current plan state
        plan_content = read_plan(plan_path)

        # Build phase prompt
        prompt = build_phase_prompt(phase, topic, plan_content, skills, mode)

        # Execute phase
        is_interactive = (phase == "P2")
        tools = PHASE_TOOLS.get(phase)

        if is_interactive:
            # P2: Interactive — append system prompt with plan context
            print(f"  P2 requires user interaction.")
            print(f"  Starting interactive session with plan context...")
            # Write a temp prompt file for the interactive session
            temp_prompt = Path("/tmp/aqua-combo-p2-prompt.md")
            temp_prompt.write_text(prompt)
            print(f"  Context written to {temp_prompt}")
            print(f"  Run: claude --append-system-prompt-file {temp_prompt}")
            print(f"  When done, press Enter to continue...")
            input()
            # User manually completed P2 — mark as complete
            # Ask user for the refined problem
            print("  Paste the refined problem statement (Ctrl+D when done):")
            try:
                refined = sys.stdin.read()
            except EOFError:
                refined = "(user completed P2 interactively)"
            update_plan_section(plan_path, PHASE_TO_SECTION[phase], refined[:2000])
            mark_phase_complete(plan_path, phase)
        else:
            start = time.time()
            result = run_claude(prompt, tools=tools, session_id=session_id)
            elapsed = time.time() - start

            session_id = result.get("session_id", session_id)
            output = result.get("result", "(no output)")

            # Extract and save phase output
            phase_output = extract_phase_output(output, phase)
            section = PHASE_TO_SECTION.get(phase, phase_name)
            update_plan_section(plan_path, section, phase_output[:3000])
            mark_phase_complete(plan_path, phase)

            print(f"  Completed in {elapsed:.0f}s")
            print(f"  Output preview: {phase_output[:200]}...")

            # Clear session between phases (fresh context)
            session_id = None

    # Final report
    print(f"\n{'='*60}")
    print(f"  aqua-combo COMPLETE — {mode.upper()} mode")
    print(f"  Plan file: {plan_path}")
    print(f"{'='*60}")

    # Validate all phases complete
    plan_content = read_plan(plan_path)
    all_complete = all(
        f"<!-- PHASE:{p}:COMPLETE -->" in plan_content
        for p in phases
    )
    if all_complete:
        print(f"  Status: ALL PHASES COMPLETE")
    else:
        incomplete = [p for p in phases if f"<!-- PHASE:{p}:COMPLETE -->" not in plan_content]
        print(f"  WARNING: Incomplete phases: {', '.join(incomplete)}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def auto_detect_mode(topic: str) -> str:
    """Auto-detect mode based on topic complexity heuristics."""
    words = topic.lower().split()
    complex_signals = ["architecture", "redesign", "migrate", "production", "security", "scale"]
    simple_signals = ["add", "fix", "update", "rename", "typo"]

    if any(s in words for s in complex_signals) or len(words) > 10:
        return "full"
    if any(s in words for s in simple_signals) and len(words) < 6:
        return "scout"
    return "standard"


def main():
    parser = argparse.ArgumentParser(
        description="aqua-combo — Enforced research-to-execution pipeline",
        epilog="Examples:\n"
               "  aqua-combo-run 'build WebSocket notification system'\n"
               "  aqua-combo-run 'add retry logic' --mode scout\n"
               "  aqua-combo-run 'redesign auth system' --mode full",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topic", help="What to build/research/plan")
    parser.add_argument("--mode", choices=["scout", "standard", "full"],
                        help="Pipeline mode (auto-detected if omitted)")
    parser.add_argument("--timeout", type=int, default=PHASE_TIMEOUT,
                        help=f"Timeout per phase in seconds (default: {PHASE_TIMEOUT})")
    parser.add_argument("--max-budget", type=float, default=MAX_BUDGET_PER_PHASE,
                        help=f"Max USD per phase (default: {MAX_BUDGET_PER_PHASE})")

    args = parser.parse_args()

    global PHASE_TIMEOUT, MAX_BUDGET_PER_PHASE
    PHASE_TIMEOUT = args.timeout
    MAX_BUDGET_PER_PHASE = args.max_budget

    mode = args.mode or auto_detect_mode(args.topic)
    print(f"  Auto-detected mode: {mode.upper()}" if not args.mode else "")

    run_pipeline(args.topic, mode)


if __name__ == "__main__":
    main()
