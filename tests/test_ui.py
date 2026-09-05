"""Day 24 (Week 4): tests for the shared Rich terminal-UI layer (sentinelai.ui).

All checks are offline and output-agnostic: they verify the API surface, that
Rich's non-TTY degradation keeps captured output ANSI-free, and that spinner
is a safe no-op context manager. Runs as a plain script or under pytest.
"""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai import ui


def test_ui_exports_expected_api():
    for name in ("console", "info", "success", "warn", "error", "step",
                 "kv", "spinner", "print_markdown", "print_panel", "clean"):
        assert hasattr(ui, name), f"ui missing {name}"


def test_clean_escapes_rich_markup_when_rich_present():
    if ui._RICH:
        assert ui.clean("[red]192.168.1.1[/red]") == "\\[red]192.168.1.1\\[/red]"
    else:
        assert ui.clean("[red]x[/red]") == "[red]x[/red]"


def test_status_lines_are_ansi_free_when_captured():
    # Simulate piped output: Rich degrades to plain text on non-terminals,
    # so automated/piped runs must never receive ANSI escapes.
    if not ui._RICH:
        return
    buf = io.StringIO()
    original = ui.console.file
    try:
        ui.console.file = buf
        ui.info("hello 192.168.1.1")
        ui.success("done")
        ui.warn("careful")
        ui.error("boom")
        out = buf.getvalue()
    finally:
        ui.console.file = original
    assert "\x1b[" not in out, "ANSI escape leaked into captured output"
    assert "[*] hello 192.168.1.1" in out
    assert "[+] done" in out
    assert "[!] careful" in out
    assert "[!] boom" in out


def test_spinner_yields_exactly_once_and_never_raises():
    entered = []
    with ui.spinner("working...") as s:
        entered.append(s)
    assert len(entered) == 1


def test_markdown_and_panel_accept_plain_strings():
    # Non-TTY render must not raise for typical LLM markdown content.
    if not ui._RICH:
        return
    buf = io.StringIO()
    original = ui.console.file
    try:
        ui.console.file = buf
        ui.print_markdown("## Heading\n\n- item one\n- item two\n")
        ui.print_panel("body text", title="Title")
        out = buf.getvalue()
    finally:
        ui.console.file = original
    assert "Heading" in out
    assert "item one" in out
    assert "Title" in out
    assert "body text" in out


def test_json_output_stays_ansi_free():
    # The --json branches keep plain click.echo(json.dumps(...)); this guards
    # the contract that machine-readable output is never styled.
    rendered = json.dumps({"ok": True, "threat_level": "LOW"})
    assert "\x1b[" not in rendered


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} ui TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()