import os
import sys
from pathlib import Path


DEFAULT_CONFIG = {
    "LLM_PROVIDER": "gemini",
    "GEMINI_API_KEY": "",
    "GEMINI_MODEL": "gemini-3.6-flash",
    "OLLAMA_MODEL": "llama3.1",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "MISTRAL_API_KEY": "",
    "MISTRAL_MODEL": "mistral-small",
    "MISTRAL_BASE_URL": "http://localhost:11434/v1",
    "PRIVACY_MODE": "false",
}


def detect_environment(project_root=None):
    """Return a simple environment snapshot for a fresh or existing machine."""
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parent
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    requirements_path = root / "requirements.txt"
    install_ready = requirements_path.exists()

    return {
        "python_version": python_version,
        "project_root": str(root),
        "requirements_present": install_ready,
        "install_ready": install_ready,
        "default_provider": "gemini",
    }


def build_default_config(provider="gemini", model=None, privacy_mode=False):
    """Create an environment config dictionary for a clean install."""
    selected_provider = (provider or "gemini").lower()
    config = dict(DEFAULT_CONFIG)
    config["LLM_PROVIDER"] = selected_provider
    config["PRIVACY_MODE"] = "true" if privacy_mode else "false"

    # Keep placeholder API keys in the generated env file so a fresh machine
    # can be configured without needing a second setup step.
    config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", config["GEMINI_API_KEY"])
    config["MISTRAL_API_KEY"] = os.environ.get("MISTRAL_API_KEY", config["MISTRAL_API_KEY"])

    if selected_provider == "gemini":
        config["GEMINI_MODEL"] = model or config["GEMINI_MODEL"]
    elif selected_provider == "ollama":
        config["OLLAMA_MODEL"] = model or config["OLLAMA_MODEL"]
    elif selected_provider == "mistral":
        config["MISTRAL_MODEL"] = model or config["MISTRAL_MODEL"]

    return config


def run_setup_wizard(project_root=None, env_path=None, interactive=False, provider=None, model=None, privacy_mode=False):
    """Write a .env file suitable for a fresh machine with no prior configuration."""
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parent
    env_file = Path(env_path) if env_path is not None else root / ".env"

    selected_provider = (provider or "gemini").lower()
    selected_model = model or DEFAULT_CONFIG.get(f"{selected_provider.upper()}_MODEL", "") or DEFAULT_CONFIG["GEMINI_MODEL"]
    config = build_default_config(
        provider=selected_provider,
        model=selected_model,
        privacy_mode=privacy_mode,
    )

    lines = [f"{key}={value}" for key, value in config.items()]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config


if __name__ == "__main__":
    print("SentinelAI setup wizard")
    config = run_setup_wizard(interactive=True)
    print("Setup complete. Created .env with defaults:")
    for key, value in config.items():
        print(f"{key}={value}")
