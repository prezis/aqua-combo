"""Verify SKILL.md files have valid frontmatter and required sections."""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_skill_files_exist():
    skill_dir = REPO_ROOT / "skills" / "aqua-combo"
    assert (skill_dir / "SKILL.md").exists(), "Main SKILL.md missing"


def test_skill_has_frontmatter():
    skill = (REPO_ROOT / "skills" / "aqua-combo" / "SKILL.md").read_text()
    assert skill.startswith("---"), "SKILL.md must start with YAML frontmatter"
    parts = skill.split("---", 2)
    assert len(parts) >= 3, "SKILL.md must have opening and closing --- for frontmatter"
    frontmatter = parts[1]
    assert "name:" in frontmatter
    assert "description:" in frontmatter
    assert "version:" in frontmatter


def test_skill_has_required_sections():
    skill = (REPO_ROOT / "skills" / "aqua-combo" / "SKILL.md").read_text()
    required = ["Phase 1", "Phase 2", "Phase 4", "Phase 5", "Phase 6",
                "Iron Laws", "Mode Selection", "SCOUT"]
    for section in required:
        assert section in skill, f"Missing section: {section}"


def test_no_hardcoded_paths():
    """Ensure no user-specific paths leaked into public skill."""
    skill = (REPO_ROOT / "skills" / "aqua-combo" / "SKILL.md").read_text()
    forbidden = ["palyslaf0s", "/home/", "RTX 5090", "qwen3.5:27b",
                 "bielik", "~/ai/global-graph"]
    for term in forbidden:
        assert term not in skill, f"Hardcoded user-specific term found: {term}"


def test_no_secrets_in_repo():
    """Scan all files for potential secrets."""
    secret_patterns = [
        r"sk-[a-zA-Z0-9]{20,}",
        r"AKIA[A-Z0-9]{16}",
        r"ghp_[a-zA-Z0-9]{36}",
        r"-----BEGIN.*PRIVATE KEY-----",
        r"AIza[a-zA-Z0-9_-]{35}",
    ]
    for path in REPO_ROOT.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".py", ".sh", ".json", ".yaml") \
                and "tests/" not in str(path):  # Skip test files (contain patterns as strings)
            content = path.read_text(errors="ignore")
            for pattern in secret_patterns:
                assert not re.search(pattern, content), \
                    f"Potential secret found in {path}: pattern {pattern}"


def test_plugin_json_valid():
    import json
    plugin = REPO_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin.exists()
    data = json.loads(plugin.read_text())
    assert "name" in data
    assert "version" in data
    assert "license" in data


def test_marketplace_json_valid():
    import json
    mp = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    assert mp.exists()
    data = json.loads(mp.read_text())
    assert "plugins" in data
    assert len(data["plugins"]) > 0
