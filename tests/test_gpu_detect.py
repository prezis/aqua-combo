"""Tests for GPU detection and model recommendation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from gpu_detect import GPUInfo, recommend_config, detect_apis


def test_power_tier():
    gpu = GPUInfo("nvidia", "RTX 5090", 32000, 30000, False)
    tier, models, settings, notes = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "power"
    assert len(models) == 4
    roles = [m.role for m in models]
    assert "reasoning" in roles
    assert "embedding" in roles


def test_enthusiast_tier():
    gpu = GPUInfo("nvidia", "RTX 4070", 16000, 14000, False)
    tier, models, _, _ = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "enthusiast"
    assert len(models) == 3


def test_mainstream_tier():
    gpu = GPUInfo("nvidia", "RTX 3060", 8000, 7000, False)
    tier, models, _, _ = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "mainstream"
    assert len(models) == 2


def test_budget_tier():
    gpu = GPUInfo("nvidia", "GTX 1650", 4500, 4000, False)
    tier, models, _, _ = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "budget"


def test_minimal_tier():
    gpu = GPUInfo("amd", "AMD APU", 2500, 2000, True)
    tier, models, _, _ = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "minimal"


def test_cpu_only():
    gpu = GPUInfo("none", "No GPU", 0, 0, False)
    tier, models, _, notes = recommend_config(gpu, True, {})
    assert tier == "cpu_only"
    assert any("CPU" in n for n in notes)


def test_api_only():
    gpu = GPUInfo("none", "No GPU", 0, 0, False)
    tier, models, _, notes = recommend_config(gpu, False, {})
    assert tier == "api_only"
    assert len(models) == 0


def test_apple_silicon():
    gpu = GPUInfo("apple", "Apple Silicon", 10700, 10700, True)
    tier, _, _, _ = recommend_config(gpu, True, {"anthropic": True})
    assert tier == "mainstream"


def test_api_detection_with_claude_dir(tmp_path, monkeypatch):
    # Simulate ~/.claude/ existing
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    apis = detect_apis()
    assert apis["anthropic"] is True


def test_all_tiers_have_notes():
    """Every tier should return at least one note."""
    configs = [
        (GPUInfo("nvidia", "X", 32000, 30000, False), True),
        (GPUInfo("nvidia", "X", 16000, 14000, False), True),
        (GPUInfo("nvidia", "X", 8000, 7000, False), True),
        (GPUInfo("nvidia", "X", 4500, 4000, False), True),
        (GPUInfo("amd", "X", 2500, 2000, True), True),
        (GPUInfo("none", "X", 0, 0, False), True),
        (GPUInfo("none", "X", 0, 0, False), False),
    ]
    for gpu, has_ollama in configs:
        tier, _, _, notes = recommend_config(gpu, has_ollama, {})
        assert len(notes) > 0, f"Tier {tier} has no notes"
