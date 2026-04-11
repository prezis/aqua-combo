# Changelog

## [4.0.0] - 2026-04-11

### Added
- 6-phase pipeline: Research → Clarify → Debate → Architect → Dispatch → Review
- Cross-platform GPU detection (NVIDIA/AMD/Apple Silicon/none)
- 7-tier auto-config: power, enthusiast, mainstream, budget, minimal, cpu_only, api_only
- DiffServ routing: BE (local) → AF (cascade) → EF (API)
- Lusser's Law mitigation: deterministic wrapper + retry + checkpoint + verification
- Multi-session GPU contention handling via /api/ps check
- Plugin format with marketplace.json
- 17 tests (GPU tiers, skill validation, secret scanning)
- Multi-platform support (Claude Code, Cursor, Codex, Gemini CLI, Windsurf)
- Researcher and reviewer agent personas

### Architecture
- Based on research: 20+ agents dispatched, 8 papers, 12 repos, production data from 1837 teams
- Praetorian "Thin Agent / Fat Platform" pattern
- Anthropic "Harness Design" pattern
- n8n node-level retry + fallback model pattern
