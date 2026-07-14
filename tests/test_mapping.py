import sys
from pathlib import Path

# Make sure src/ is importable when running pytest from project root
sys.path.append(str(Path(__file__).parent.parent))

from src.mapping import map_keyword_to_owasp, load_owasp_data


# Load real OWASP data once and reuse across all tests
owasp_data = load_owasp_data()


def test_access_control_keyword():
    result = map_keyword_to_owasp("access control", owasp_data)
    assert result == "Broken Access Control"


def test_sql_injection_keyword():
    result = map_keyword_to_owasp("sql injection", owasp_data)
    assert result == "Injection"


def test_encryption_keyword():
    result = map_keyword_to_owasp("encryption", owasp_data)
    assert result == "Cryptographic Failures"


def test_logging_keyword():
    result = map_keyword_to_owasp("logging", owasp_data)
    assert result == "Security Logging & Alerting Failures"


def test_supply_chain_keyword():
    result = map_keyword_to_owasp("supply chain", owasp_data)
    assert result == "Software Supply Chain Failures"


def test_ssrf_consolidation():
    # SSRF was consolidated into Broken Access Control in the 2025 update
    result = map_keyword_to_owasp("ssrf", owasp_data)
    assert result == "Broken Access Control"


def test_unmatched_keyword_returns_none():
    result = map_keyword_to_owasp("banana smoothie recipe", owasp_data)
    assert result is None


def test_case_insensitivity():
    result = map_keyword_to_owasp("SQL INJECTION", owasp_data)
    assert result == "Injection"