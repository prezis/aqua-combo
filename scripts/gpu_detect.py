#!/usr/bin/env python3
"""Cross-platform GPU detection for aqua-combo.

Detects: NVIDIA (nvidia-smi), AMD (sysfs), Apple Silicon (sysctl), Intel, None.
Returns JSON with GPU info + recommended model config.
"""

import subprocess
import platform
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class GPUInfo:
    vendor: str       # "nvidia", "amd", "apple", "intel", "none"
    name: str
    vram_total_mb: int
    vram_free_mb: int
    is_integrated: bool


@dataclass
class ModelConfig:
    name: str
    role: str         # "reasoning", "fast", "structured", "embedding", "vision"
    vram_mb: int
    keep_alive: str
    good_for: list


@dataclass
class Capabilities:
    gpu: GPUInfo
    tier: str         # "power", "enthusiast", "mainstream", "budget", "minimal", "cpu_only", "api_only"
    ollama_available: bool
    ollama_models: list
    models_recommended: list
    ollama_settings: dict
    apis: dict
    notes: list


def detect_gpu() -> GPUInfo:
    """Detect GPU vendor and VRAM. Cross-platform."""
    # NVIDIA
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().split(",")]
            return GPUInfo("nvidia", parts[0], int(parts[1]), int(parts[2]), False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # AMD (sysfs — works without rocm-smi)
    if platform.system() == "Linux":
        for vendor_file in Path("/sys/class/drm").glob("card*/device/vendor"):
            try:
                if vendor_file.read_text().strip() == "0x1002":
                    dev_dir = vendor_file.parent
                    total_path = dev_dir / "mem_info_vram_total"
                    used_path = dev_dir / "mem_info_vram_used"
                    if total_path.exists():
                        total = int(total_path.read_text().strip())
                        used = int(used_path.read_text().strip()) if used_path.exists() else 0
                        total_mb = total // (1024 * 1024)
                        free_mb = (total - used) // (1024 * 1024)
                        if total_mb >= 1024:  # Only count >= 1GB dedicated VRAM
                            return GPUInfo("amd", "AMD GPU", total_mb, free_mb, False)
                        else:
                            return GPUInfo("amd", "AMD APU (integrated)", total_mb, free_mb, True)
            except (OSError, ValueError):
                continue

    # macOS / Apple Silicon
    if platform.system() == "Darwin":
        try:
            r = subprocess.run(["sysctl", "-n", "hw.memsize"],
                             capture_output=True, text=True, timeout=5)
            total_ram_mb = int(r.stdout.strip()) // (1024 * 1024)
            # Apple Silicon: GPU uses ~67% of unified memory
            usable_vram = int(total_ram_mb * 0.67)
            return GPUInfo("apple", "Apple Silicon", usable_vram, usable_vram, True)
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

    return GPUInfo("none", "No GPU detected", 0, 0, False)


def detect_ollama() -> tuple[bool, list]:
    """Check if Ollama is running and list installed models."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return True, models
    except Exception:
        pass
    # Check if installed but not running
    try:
        subprocess.run(["which", "ollama"], capture_output=True, timeout=3)
        return False, []  # Installed but not running
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, []


def detect_apis() -> dict:
    """Detect available API keys from environment."""
    checks = {
        "anthropic": ["ANTHROPIC_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"],
        "perplexity": ["PERPLEXITY_API_KEY", "PPLX_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "deepseek": ["DEEPSEEK_API_KEY"],
    }
    result = {}
    for provider, env_vars in checks.items():
        result[provider] = any(os.environ.get(v) for v in env_vars)
    # Claude Code users always have Anthropic access
    if Path.home().joinpath(".claude").exists():
        result["anthropic"] = True
    return result


def recommend_config(gpu: GPUInfo, ollama_available: bool, apis: dict) -> tuple[str, list, dict, list]:
    """Given hardware, return tier + recommended models + settings + notes.
    Uses TOTAL VRAM for recommendations (models can be swapped), not free."""
    vram = gpu.vram_total_mb  # Total, not free — Ollama swaps models as needed

    if vram >= 24000:
        return "power", [
            ModelConfig("qwen3.5:27b", "reasoning", 17000, "5m", ["code_review", "analysis", "architecture"]),
            ModelConfig("hermes3:8b", "structured", 5000, "5m", ["json", "function_calling"]),
            ModelConfig("qwen3:4b", "fast", 2500, "24h", ["classification", "routing", "simple_qa"]),
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search", "similarity"]),
        ], {
            "OLLAMA_KV_CACHE_TYPE": "q8_0",
            "OLLAMA_FLASH_ATTENTION": "1",
            "OLLAMA_NUM_PARALLEL": "4",
        }, ["Full local stack. All phases can use local GPU.", "External APIs optional."]

    elif vram >= 12000:
        return "enthusiast", [
            ModelConfig("qwen2.5:14b", "reasoning", 9500, "5m", ["code_review", "analysis"]),
            ModelConfig("qwen3:4b", "fast", 2500, "24h", ["classification", "routing"]),
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search"]),
        ], {
            "OLLAMA_KV_CACHE_TYPE": "q8_0",
            "OLLAMA_FLASH_ATTENTION": "1",
            "OLLAMA_KEEP_ALIVE": "2m",
        }, ["Good local capability.", "API recommended for complex architecture tasks."]

    elif vram >= 6000:
        return "mainstream", [
            ModelConfig("qwen3:8b", "reasoning", 5500, "5m", ["code_review", "analysis"]),
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search"]),
        ], {
            "OLLAMA_KV_CACHE_TYPE": "q8_0",
            "OLLAMA_FLASH_ATTENTION": "1",
            "OLLAMA_KEEP_ALIVE": "1m",
        }, ["Solid 8B model covers most tasks.", "API needed for hard reasoning."]

    elif vram >= 4000:
        return "budget", [
            ModelConfig("qwen3:4b", "fast", 2500, "30s", ["classification", "extraction", "simple_review"]),
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search"]),
        ], {
            "OLLAMA_KV_CACHE_TYPE": "q4_0",
            "OLLAMA_FLASH_ATTENTION": "1",
            "OLLAMA_KEEP_ALIVE": "30s",
        }, ["4B model handles classification and extraction.", "API essential for reasoning."]

    elif vram >= 2000:
        return "minimal", [
            ModelConfig("qwen3:0.6b", "fast", 800, "30s", ["classification", "routing"]),
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search"]),
        ], {
            "OLLAMA_KEEP_ALIVE": "30s",
        }, ["Embeddings + tiny classifier only.", "All generation needs external API."]

    elif ollama_available:
        return "cpu_only", [
            ModelConfig("nomic-embed-text", "embedding", 300, "24h", ["semantic_search"]),
        ], {}, ["CPU embeddings are fast and useful for RAG.", "LLM on CPU: ~5 tok/s, batch only."]

    else:
        return "api_only", [], {}, [
            "No local GPU or Ollama detected.",
            "All tasks route to Claude/OpenAI/Gemini API.",
            "Install Ollama (ollama.com) for local embeddings even on CPU."
        ]


def run_detection() -> Capabilities:
    """Run full hardware detection and return capabilities."""
    gpu = detect_gpu()
    ollama_available, ollama_models = detect_ollama()
    apis = detect_apis()
    tier, models, settings, notes = recommend_config(gpu, ollama_available, apis)

    return Capabilities(
        gpu=gpu,
        tier=tier,
        ollama_available=ollama_available,
        ollama_models=ollama_models,
        models_recommended=models,
        ollama_settings=settings,
        apis=apis,
        notes=notes,
    )


def save_capabilities(caps: Capabilities, path: Optional[str] = None):
    """Save capabilities to YAML-like config."""
    if path is None:
        path = str(Path.home() / ".aqua-combo" / "capabilities.json")
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "gpu": asdict(caps.gpu),
        "tier": caps.tier,
        "ollama": {
            "available": caps.ollama_available,
            "models_installed": caps.ollama_models,
        },
        "recommended_models": [asdict(m) for m in caps.models_recommended],
        "ollama_settings": caps.ollama_settings,
        "apis": caps.apis,
        "notes": caps.notes,
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


if __name__ == "__main__":
    caps = run_detection()

    if "--save" in sys.argv:
        path = save_capabilities(caps)
        print(f"Saved to {path}")
    elif "--json" in sys.argv:
        print(json.dumps({
            "gpu": asdict(caps.gpu),
            "tier": caps.tier,
            "ollama_available": caps.ollama_available,
            "models": [asdict(m) for m in caps.models_recommended],
            "apis": caps.apis,
            "notes": caps.notes,
        }, indent=2))
    else:
        print(f"GPU: {caps.gpu.vendor} — {caps.gpu.name}")
        print(f"VRAM: {caps.gpu.vram_total_mb}MB total, {caps.gpu.vram_free_mb}MB free")
        print(f"Tier: {caps.tier}")
        print(f"Ollama: {'running' if caps.ollama_available else 'not detected'}")
        if caps.ollama_models:
            print(f"Models installed: {', '.join(caps.ollama_models)}")
        print(f"APIs: {', '.join(k for k,v in caps.apis.items() if v) or 'none detected'}")
        print(f"Recommended models: {len(caps.models_recommended)}")
        for m in caps.models_recommended:
            print(f"  {m.role}: {m.name} ({m.vram_mb}MB)")
        for note in caps.notes:
            print(f"  → {note}")
