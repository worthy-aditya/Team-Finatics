"""Day 53 unit tests for provider registry and health dashboard (offline, pure functions).

Covers the new registry helpers in sentinelai.routing and dashboard module.
No LLM or network is required.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.routing import (
    get_all_providers,
    get_provider_registry,
    provider_is_healthy,
)
from sentinelai.dashboard import build_dashboard


def test_provider_registry_has_three_providers():
    providers = get_all_providers()
    assert len(providers) == 3
    assert "gemini" in providers
    assert "ollama" in providers
    assert "deepseek" in providers


def test_provider_registry_metadata():
    registry = get_provider_registry()
    gemini = registry["gemini"]
    assert gemini["name"] == "Gemini"
    assert gemini["type"] == "cloud"
    assert gemini["api_key_required"] == True
    assert gemini["default_model"] == "gemini-3.6-flash"
    assert "note" in gemini


def test_provider_is_healthy_true():
    assert provider_is_healthy("gemini", {"gemini": 80.0}) is True
    assert provider_is_healthy("gemini", {"gemini": 70.0}) is True


def test_provider_is_healthy_false():
    assert provider_is_healthy("gemini", {"gemini": 69.9}) is False
    assert provider_is_healthy("gemini", {"gemini": 0.0}) is False
    assert provider_is_healthy("unknown", {"gemini": 80.0}) is False


def test_get_all_providers():
    providers = get_all_providers()
    assert isinstance(providers, list)
    assert len(providers) == 3


def test_get_provider_registry():
    registry = get_provider_registry()
    assert isinstance(registry, dict)
    assert len(registry) == 3
    assert "gemini" in registry
    assert "ollama" in registry
    assert "deepseek" in registry


def test_dashboard_formats_correctly():
    output = build_dashboard()
    assert "gemini" in output.lower()
    assert "ollama" in output.lower()
    assert "deepseek" in output.lower()
    assert "Score" in output
    assert "Healthy" in output


def test_dashboard_uses_supplied_scores():
    output = build_dashboard({"gemini": 10.0, "ollama": 95.0, "deepseek": 50.0})
    # A score below the healthy threshold renders as LOW, above as OK.
    assert "LOW" in output  # gemini 10.0 is unhealthy
    assert "OK" in output  # ollama 95.0 is healthy


def test_dashboard_flag_on_both_analyze_entry_points():
    # Day 4/53 sync: --dashboard must exist on both analyze entry points.
    import click

    from commands.analyze import analyze as analyze_root
    from sentinelai.cli import analyze as analyze_pkg

    root_opts = {o for p in analyze_root.params for o in p.opts}
    pkg_opts = {o for p in analyze_pkg.params for o in p.opts}
    assert "--dashboard" in root_opts, "root analyze missing --dashboard"
    assert "--dashboard" in pkg_opts, "sentinelai/cli.py analyze missing --dashboard"


def _main() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day53 registry DASHBOARD TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()
