from pathlib import Path

from setup_wizard import detect_environment, run_setup_wizard


def test_detect_environment_reports_clean_install_defaults(tmp_path):
    result = detect_environment(project_root=tmp_path)
    assert "python_version" in result
    assert "install_ready" in result
    assert isinstance(result["install_ready"], bool)


def test_run_setup_wizard_creates_env_for_fresh_machine(tmp_path):
    env_path = tmp_path / ".env"

    config = run_setup_wizard(
        project_root=tmp_path,
        env_path=env_path,
        interactive=False,
        provider="ollama",
        model="mistral",
        privacy_mode=True,
    )

    assert env_path.exists()
    assert "LLM_PROVIDER=ollama" in env_path.read_text(encoding="utf-8")
    assert "OLLAMA_MODEL=mistral" in env_path.read_text(encoding="utf-8")
    assert "PRIVACY_MODE=true" in env_path.read_text(encoding="utf-8")
    assert config["LLM_PROVIDER"] == "ollama"
    assert config["PRIVACY_MODE"] == "true"


def test_run_setup_wizard_includes_provider_key_placeholders_and_normalizes_provider(tmp_path):
    env_path = tmp_path / ".env"

    config = run_setup_wizard(
        project_root=tmp_path,
        env_path=env_path,
        provider="OLLAMA",
        model="llama3.2",
        privacy_mode=False,
    )

    env_text = env_path.read_text(encoding="utf-8")
    assert "LLM_PROVIDER=ollama" in env_text
    assert "OLLAMA_MODEL=llama3.2" in env_text
    assert "GEMINI_API_KEY=" in env_text
    assert "MISTRAL_API_KEY=" in env_text
    assert config["LLM_PROVIDER"] == "ollama"
