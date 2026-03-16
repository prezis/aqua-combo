#!/usr/bin/env python3
"""
aqua-combo-run.py — Enforced research-to-execution pipeline runner.

Transforms aqua-combo from a prompt-based skill into an actual engine
that enforces phase order, validates output, and manages context.

Usage:
    python3 aqua-combo-run.py "build a notification system"
    python3 aqua-combo-run.py "redesign auth" --mode full
    python3 aqua-combo-run.py "add retry logic" --mode scout
    python3 aqua-combo-run.py --resume  # resume from existing plan file

Exit codes: 0=success, 1=phase failed, 2=plan corruption, 3=claude not found,
            4=user abort, 5=timeout, 6=low confidence abort
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────

PHASE_TIMEOUT = 600
MAX_TURNS = 50

MODES = {
    "scout": ["P1"],
    "standard": ["P1", "P2", "P4", "P5", "P6"],
    "full": ["P1", "P2", "P3", "P4", "P5", "P6"],
}

PHASE_NAMES = {
    "P1": "Research", "P2": "Clarify", "P3": "Debate",
    "P4": "Architect", "P5": "Dispatch", "P6": "Review",
}

PHASE_TOOLS = {
    "P1": ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"],
    "P2": None,  # Interactive
    "P3": ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"],
    "P4": ["Read", "Glob", "Grep"],
    "P5": ["Read", "Edit", "Write", "Bash", "Glob", "Grep", "Agent"],
    "P6": ["Read", "Glob", "Grep", "Bash", "Agent"],
}


# ─── Data Structures ────────────────────────────────────────────────────────

class PhaseStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class PhaseResult:
    phase: str
    success: bool
    output: str = ""
    duration: float = 0.0
    error: str | None = None
    retries: int = 0


# ─── Validation Rules ───────────────────────────────────────────────────────

PHASE_VALIDATION = {
    "P1": {
        "required_keywords": ["ADOPT", "EXTEND", "BUILD"],
        "min_length": 100,
        "section": "Research Verdict",
    },
    "P2": {
        "min_length": 50,
        "section": "Refined Problem",
    },
    "P3": {
        "required_keywords": ["DIRECTION", "CONFIDENCE"],
        "min_length": 100,
        "section": "Debate Conclusions",
    },
    "P4": {
        "min_length": 200,
        "section": "Architecture",
    },
    "P5": {
        "min_length": 50,
        "section": "Dispatch Results",
    },
    "P6": {
        "min_length": 50,
        "section": "Review Results",
    },
}


def validate_phase_output(phase: str, output: str) -> list[str]:
    """Validate phase output against rules. Returns list of issues."""
    rules = PHASE_VALIDATION.get(phase, {})
    issues = []

    if not output or output.strip() in ("(no output)", "(timeout)"):
        issues.append(f"{phase}: No output produced")
        return issues

    min_len = rules.get("min_length", 0)
    if len(output) < min_len:
        issues.append(f"{phase}: Output too short ({len(output)} chars, need {min_len})")

    keywords = rules.get("required_keywords", [])
    if keywords:
        found = any(kw in output.upper() for kw in keywords)
        if not found:
            issues.append(f"{phase}: Missing required keyword (one of: {', '.join(keywords)})")

    return issues


# ─── Plan File ───────────────────────────────────────────────────────────────

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

SECTION_MAP = {
    "P1": "Research Verdict",
    "P2": "Refined Problem",
    "P3": "Debate Conclusions",
    "P4": "Architecture",
    "P5": "Dispatch Results",
    "P6": "Review Results",
}


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")[:50]


def plan_path_for(topic: str) -> Path:
    return Path(f"aqua-combo-plan-{slugify(topic)}.md")


def create_plan(topic: str, mode: str) -> Path:
    path = plan_path_for(topic)
    path.write_text(PLAN_TEMPLATE.format(
        mode=mode.upper(), topic=topic, timestamp=datetime.now().isoformat(),
    ))
    return path


def find_existing_plan(topic: str) -> Path | None:
    path = plan_path_for(topic)
    if path.exists():
        return path
    # Also check for any aqua-combo-plan-*.md
    plans = list(Path(".").glob("aqua-combo-plan-*.md"))
    return plans[0] if len(plans) == 1 else None


def read_plan(path: Path) -> str:
    return path.read_text()


def get_phase_status(path: Path, phase: str) -> PhaseStatus:
    content = read_plan(path)
    for status in PhaseStatus:
        if f"<!-- PHASE:{phase}:{status.value} -->" in content:
            return status
    return PhaseStatus.PENDING


def mark_phase(path: Path, phase: str, status: PhaseStatus):
    content = read_plan(path)
    for s in PhaseStatus:
        content = content.replace(
            f"<!-- PHASE:{phase}:{s.value} -->",
            f"<!-- PHASE:{phase}:{status.value} -->"
        )
    path.write_text(content)


def update_section(path: Path, section: str, new_content: str):
    content = read_plan(path)
    pattern = rf"(## {re.escape(section)}\n)_Pending.*?_"
    # Also handle already-written sections (replace everything until next ##)
    if re.search(pattern, content):
        updated = re.sub(pattern, rf"\1{new_content}", content, flags=re.DOTALL)
    else:
        # Section already has content — replace between this ## and next ##
        pattern2 = rf"(## {re.escape(section)}\n)(.+?)(\n## |\Z)"
        updated = re.sub(pattern2, rf"\1{new_content}\n\3", content, flags=re.DOTALL)
    path.write_text(updated)


def validate_prerequisites(path: Path, phase: str, mode: str) -> bool:
    phases = MODES[mode]
    if phase not in phases:
        return True
    idx = phases.index(phase)
    for i in range(idx):
        prior = phases[i]
        if get_phase_status(path, prior) != PhaseStatus.COMPLETE:
            print(f"  BLOCKED: {prior} ({PHASE_NAMES[prior]}) not complete")
            return False
    return True


def get_completed_context(path: Path) -> str:
    """Extract all completed sections from plan file."""
    content = read_plan(path)
    # Remove state markers, return clean content
    clean = re.sub(r"<!--.*?-->", "", content).strip()
    return clean


# ─── Skill Detection ────────────────────────────────────────────────────────

SKILL_DIRS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".claude" / "commands",
    Path.home() / ".claude" / "agents",
    Path.home() / ".claude" / "plugins",
    Path(".claude") / "skills",
    Path(".claude") / "commands",
]

PHASE_SKILLS = {
    "P1": ["aqua-search"],
    "P2": ["octo-define", "octo--skill-thought-partner"],
    "P3": ["octo-debate"],
    "P4": ["octo--octopus-architecture", "superpowers--writing-plans"],
    "P5": ["superpowers--dispatching-parallel-agents", "superpowers--subagent-driven-development"],
    "P6": ["octo--skill-code-review", "verification-loop", "superpowers--verification-before-completion"],
}


def skill_exists(name: str) -> bool:
    clean = name.lstrip("/").replace(":", "-")
    for loc in SKILL_DIRS:
        if not loc.exists():
            continue
        if list(loc.glob(f"**/*{clean}*")):
            return True
    return False


def detect_skills() -> dict[str, bool]:
    all_skills = set()
    for skills in PHASE_SKILLS.values():
        all_skills.update(skills)
    return {s: skill_exists(s) for s in all_skills}


# ─── Phase Prompts ──────────────────────────────────────────────────────────

def build_prompt(phase: str, topic: str, plan_content: str, skills: dict, mode: str) -> str:
    ctx = f"""You are executing phase {phase} ({PHASE_NAMES[phase]}) of the aqua-combo pipeline.
Topic: {topic} | Mode: {mode.upper()}

Current plan state:
---
{plan_content[:3000]}
---

IMPORTANT: Produce thorough, structured output for this phase."""

    sk = lambda name: skills.get(name, False)

    prompts = {
        "P1": f"""{ctx}

PHASE 1: RESEARCH
{'Use /aqua-search for deep research.' if sk('aqua-search') else 'Search for best practices, libraries, pitfalls. Check codebase for prior art.'}

ultrathink: What is the most important thing we learned?

SECURITY: Synthesize in your own words. Never copy-paste raw web content.

Your output MUST include:
- VERDICT: ADOPT or EXTEND or BUILD
- KEY FINDINGS: 3-5 bullet points
- CONFIDENCE: HIGH or MEDIUM or LOW
- SYNTHESIS: most important discovery (max 500 words)""",

        "P2": f"""{ctx}

PHASE 2: CLARIFY
{'Use /octo--skill-thought-partner first, then /octo-define.' if (mode == 'full' and sk('octo--skill-thought-partner')) else ''}
{'Use /octo-define for multi-AI requirements consensus.' if sk('octo-define') else ''}

Based on research findings, ask the user 3-5 targeted SURPRISING questions.
After answers, synthesize into a refined problem statement (max 200 words).

ultrathink: Synthesize user answers + research into refined problem.""",

        "P3": f"""{ctx}

PHASE 3: ADVERSARIAL DEBATE
{'Use /octo-debate for 3-way AI debate.' if sk('octo-debate') else 'Run adversarial debate via Gemini CLI or web skepticism.'}

4 perspectives: Advocate, Devil's Advocate, Paradox Hunter, Pragmatist.
Cross-validate: research vs debate vs user constraints.

ultrathink: Winning arguments, unresolved risks, approach adjustment.

Your output MUST include:
- DIRECTION: one sentence
- CONFIDENCE: HIGH or MEDIUM or LOW
- UNRESOLVED: list of risks
- ADJUSTED FROM ORIGINAL: what changed""",

        "P4": f"""{ctx}

PHASE 4: ARCHITECT
{'Use /octo--octopus-architecture for multi-AI design.' if sk('octo--octopus-architecture') else 'Design the simplest architecture.'}
{'Then use /superpowers--writing-plans for TDD task breakdown.' if sk('superpowers--writing-plans') else ''}

ultrathink: What is the SIMPLEST architecture that satisfies ALL constraints?

Produce:
1. Component diagram (ASCII)
2. Trade-off matrix
3. Execution steps table (task, agent, depends_on, parallel?, test criteria)
4. Risk register
5. Rollback plan""",

        "P5": f"""{ctx}

PHASE 5: DISPATCH
{'Use /superpowers--dispatching-parallel-agents.' if sk('superpowers--dispatching-parallel-agents') else 'Dispatch subagents with worktree isolation.'}

For each task: dispatch agent with context from P1-P3, verify by test criteria.
Report: "Task N/M done: [component] — status"

Your output MUST include task completion status for each step.""",

        "P6": f"""{ctx}

PHASE 6: REVIEW
{'Use /octo--skill-code-review for multi-AI review.' if sk('octo--skill-code-review') else 'Review code for spec compliance and security.'}
{'Use /verification-loop for automated gates.' if sk('verification-loop') else 'Run project test suite.'}

ultrathink: Do outputs collectively satisfy the plan? Any gaps?

Your output MUST include a verdict: APPROVE or FAIL, plus any issues found.""",
    }

    return prompts.get(phase, ctx)


# ─── Claude Execution ───────────────────────────────────────────────────────

def check_claude():
    """Verify claude CLI is available."""
    if not shutil.which("claude"):
        print("  ERROR: 'claude' CLI not found on PATH")
        print("  Install: https://code.claude.com")
        sys.exit(3)


def run_claude_headless(prompt: str, tools: list[str] | None = None,
                         timeout: int = PHASE_TIMEOUT) -> dict:
    """Run claude -p and return parsed result."""
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--effort", "high",
           "--max-turns", str(MAX_TURNS)]

    if tools:
        cmd += ["--allowedTools"] + tools

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"result": result.stdout, "session_id": None}
        return {"result": result.stderr or "(no output)", "session_id": None}
    except subprocess.TimeoutExpired:
        return {"result": "(timeout)", "session_id": None, "error": "timeout"}


def run_interactive(prompt_file: Path):
    """Launch interactive claude session for P2."""
    print("\n  Launching interactive Claude for clarification...")
    print(f"  Tip: Claude has your research context. Answer its questions.")
    print(f"  When done, type 'exit' or Ctrl+C.\n")
    cmd = ["claude", "--append-system-prompt-file", str(prompt_file)]
    subprocess.run(cmd)


# ─── Pipeline Engine ────────────────────────────────────────────────────────

def run_phase(phase: str, topic: str, plan_path: Path, skills: dict,
              mode: str, timeout: int, verbose: bool) -> PhaseResult:
    """Execute a single phase with validation and retry."""

    start = time.time()

    # Validate prerequisites
    if not validate_prerequisites(plan_path, phase, mode):
        return PhaseResult(phase, False, error="Prerequisites not met")

    mark_phase(plan_path, phase, PhaseStatus.RUNNING)
    plan_content = get_completed_context(plan_path)
    prompt = build_prompt(phase, topic, plan_content, skills, mode)

    # P2: Interactive
    if phase == "P2":
        prompt_file = Path("/tmp/aqua-combo-p2-context.md")
        prompt_file.write_text(prompt)
        run_interactive(prompt_file)

        # After interactive session, ask user to paste refined problem
        print("\n  Paste the refined problem statement (or press Enter to skip):")
        try:
            lines = []
            while True:
                line = input()
                if not line and lines:
                    break
                lines.append(line)
            refined = "\n".join(lines)
        except (EOFError, KeyboardInterrupt):
            refined = "(P2 completed interactively)"

        if refined.strip():
            update_section(plan_path, SECTION_MAP["P2"], refined)
        mark_phase(plan_path, phase, PhaseStatus.COMPLETE)
        return PhaseResult(phase, True, output=refined, duration=time.time() - start)

    # Headless execution
    tools = PHASE_TOOLS.get(phase)

    for attempt in range(2):  # 1 try + 1 retry
        result = run_claude_headless(prompt, tools, timeout)
        output = result.get("result", "(no output)")

        if verbose:
            print(f"\n  Raw output:\n{output[:1000]}\n")

        # Validate
        issues = validate_phase_output(phase, output)

        if not issues:
            section = SECTION_MAP.get(phase)
            if section:
                update_section(plan_path, section, output[:3000])
            mark_phase(plan_path, phase, PhaseStatus.COMPLETE)
            return PhaseResult(phase, True, output=output, duration=time.time() - start, retries=attempt)

        if attempt == 0:
            print(f"  Validation issues: {', '.join(issues)}")
            print(f"  Retrying with error context...")
            prompt += f"\n\nRETRY: Previous attempt had issues: {'; '.join(issues)}. Fix them."
        else:
            # Final attempt failed
            mark_phase(plan_path, phase, PhaseStatus.FAILED)
            return PhaseResult(phase, False, output=output, error="; ".join(issues),
                             duration=time.time() - start, retries=1)

    # Should not reach here
    return PhaseResult(phase, False, error="Unknown error")


def handle_confidence_loop(plan_path: Path, topic: str, skills: dict,
                           mode: str, timeout: int, verbose: bool) -> bool:
    """Handle P3 LOW confidence → retry P2 (max 2 loops)."""
    plan_content = read_plan(plan_path)

    for loop in range(2):
        # Check if P3 output contains LOW confidence
        if "CONFIDENCE: LOW" not in plan_content.upper() and \
           "CONFIDENCE:LOW" not in plan_content.upper():
            return True  # Not LOW — proceed

        print(f"\n  P3 returned LOW confidence (loop {loop + 1}/2)")
        print(f"  Returning to P2 for additional clarification...")

        # Reset P2 and re-run
        mark_phase(plan_path, "P2", PhaseStatus.PENDING)
        p2_result = run_phase("P2", topic, plan_path, skills, mode, timeout, verbose)
        if not p2_result.success:
            return False

        # Re-run P3
        mark_phase(plan_path, "P3", PhaseStatus.PENDING)
        p3_result = run_phase("P3", topic, plan_path, skills, mode, timeout, verbose)
        if not p3_result.success:
            return False

        plan_content = read_plan(plan_path)

    # Still LOW after 2 loops
    if "CONFIDENCE: LOW" in plan_content.upper() or "CONFIDENCE:LOW" in plan_content.upper():
        print("\n  ABORT: Confidence still LOW after 2 clarification loops.")
        print("  The problem may need more research or a different approach.")
        return False

    return True


def run_pipeline(topic: str, mode: str, timeout: int, verbose: bool, resume: bool):
    """Main pipeline orchestrator."""

    phases = MODES[mode]
    total = len(phases)

    print(f"\n{'='*60}")
    print(f"  aqua-combo v2 — {mode.upper()} mode")
    print(f"  Topic: {topic}")
    print(f"  Phases: {' → '.join(phases)}")
    print(f"{'='*60}\n")

    # Check claude
    check_claude()

    # Detect skills
    print("  Detecting skills...")
    skills = detect_skills()
    found = [k for k, v in skills.items() if v]
    if found:
        print(f"  Found: {', '.join(found)}")

    # Plan file — create or resume
    plan_path = find_existing_plan(topic) if resume else None

    if plan_path and resume:
        print(f"  Resuming from: {plan_path}")
        # Find first incomplete phase
        start_idx = 0
        for i, p in enumerate(phases):
            if get_phase_status(plan_path, p) == PhaseStatus.COMPLETE:
                print(f"  {p} ({PHASE_NAMES[p]}): already COMPLETE — skipping")
                start_idx = i + 1
            else:
                break
        phases_to_run = phases[start_idx:]
    else:
        plan_path = create_plan(topic, mode)
        phases_to_run = phases
        print(f"  Plan: {plan_path}")

    if not phases_to_run:
        print("\n  All phases already complete!")
        return 0

    # Execute phases
    for i, phase in enumerate(phases_to_run, 1):
        print(f"\n{'─'*60}")
        print(f"  [{phase}] {PHASE_NAMES[phase]} ({i}/{len(phases_to_run)})")
        print(f"{'─'*60}")

        result = run_phase(phase, topic, plan_path, skills, mode, timeout, verbose)

        if not result.success:
            print(f"\n  FAILED: {phase} — {result.error}")
            print(f"  Plan file preserved: {plan_path}")
            print(f"  Resume with: python3 aqua-combo-run.py \"{topic}\" --resume")
            return 1 if not result.error == "timeout" else 5

        print(f"  {phase} COMPLETE ({result.duration:.0f}s, {result.retries} retries)")
        print(f"  Preview: {result.output[:150].strip()}...")

        # P3 confidence loop
        if phase == "P3":
            if not handle_confidence_loop(plan_path, topic, skills, mode, timeout, verbose):
                return 6

    # Final report
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE — {mode.upper()} mode")
    print(f"  Plan: {plan_path}")
    print(f"{'='*60}")

    # Verify all phases complete
    all_ok = all(
        get_phase_status(plan_path, p) == PhaseStatus.COMPLETE
        for p in MODES[mode]
    )
    print(f"  Status: {'ALL PHASES COMPLETE' if all_ok else 'INCOMPLETE — check plan file'}")
    return 0


# ─── CLI ─────────────────────────────────────────────────────────────────────

def auto_detect_mode(topic: str) -> str:
    words = topic.lower().split()
    complex_words = {"architecture", "redesign", "migrate", "production", "security", "scale", "refactor"}
    simple_words = {"add", "fix", "update", "rename", "typo", "bump"}
    if complex_words & set(words) or len(words) > 10:
        return "full"
    if simple_words & set(words) and len(words) < 6:
        return "scout"
    return "standard"


def main():
    parser = argparse.ArgumentParser(
        description="aqua-combo — Enforced research-to-execution pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  aqua-combo-run.py 'build WebSocket notification system'\n"
               "  aqua-combo-run.py 'redesign auth' --mode full\n"
               "  aqua-combo-run.py 'add retry logic' --mode scout\n"
               "  aqua-combo-run.py 'build notification system' --resume",
    )
    parser.add_argument("topic", help="What to build/research/plan")
    parser.add_argument("--mode", choices=["scout", "standard", "full"],
                        help="Pipeline mode (auto-detected if omitted)")
    parser.add_argument("--timeout", type=int, default=PHASE_TIMEOUT,
                        help=f"Per-phase timeout in seconds (default: {PHASE_TIMEOUT})")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing plan file")
    parser.add_argument("--verbose", action="store_true",
                        help="Print full Claude output per phase")

    args = parser.parse_args()
    mode = args.mode or auto_detect_mode(args.topic)

    if not args.mode:
        print(f"  Auto-detected mode: {mode.upper()}")

    # Handle Ctrl+C gracefully
    def handle_sigint(sig, frame):
        print("\n\n  User abort. Plan file preserved for --resume.")
        sys.exit(4)
    signal.signal(signal.SIGINT, handle_sigint)

    exit_code = run_pipeline(args.topic, mode, args.timeout, args.verbose, args.resume)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
