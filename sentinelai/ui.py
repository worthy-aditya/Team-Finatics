"""
sentinelai/ui.py
Day 24 (Week 4): ONE shared Rich terminal-UI layer used by BOTH CLI entry
points (sentinelai.py -> commands/ and sentinelai/cli.py) so every command
renders identical, professional output: colors, spinner progress indicators,
clean status messages, and Markdown rendering for LLM analyses.

Non-negotiables (carried over from Weeks 1-3):
- Machine-readable paths (`--json`) NEVER go through this module; they keep
  plain ``click.echo(json.dumps(...))`` so piping/parsing stays clean.
- Rich auto-degrades to plain text on non-TTY (tests, pipes, CI) and honors
  NO_COLOR / TERM=dumb, so automated output never gains ANSI escapes.
- If ``rich`` is not importable, a minimal plain-text shim keeps every
  command working with the same message text (no hard crash on machines
  that skip the venv).
"""

from __future__ import annotations

from contextlib import contextmanager, nullcontext

try:  # rich is pinned in requirements.txt; the shim below is just insurance.
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.markup import escape as _escape
    from rich.panel import Panel

    _RICH = True
except ImportError:  # pragma: no cover - teammate machines without rich
    _RICH = False

def _clean(text: str) -> str:
    """Escape Rich markup characters in dynamic text (targets, paths, errors)."""
    return _escape(str(text)) if _RICH else str(text)


def clean(text: str) -> str:
    """Public alias of :func:`_clean` for modules composing their own lines."""
    return _clean(text)


if _RICH:
    # highlight=False keeps Rich from auto-styling numbers/IPs inside our
    # status lines (e.g. turning parts of "4625" or "192.168.x.x" purple).
    console = Console(highlight=False)
else:  # pragma: no cover
    console = None


if _RICH:

    def info(msg: str) -> None:
        """Progress/status line: cyan ``[*]``."""
        console.print(f"[bold cyan]\\[*][/] {_clean(msg)}", soft_wrap=True)

    def success(msg: str) -> None:
        """Completion line: green bold ``[+]``."""
        console.print(f"[bold green]\\[+][/] {_clean(msg)}", soft_wrap=True)

    def warn(msg: str) -> None:
        """Warning line: yellow bold ``[!]``."""
        console.print(f"[bold yellow]\\[!][/] {_clean(msg)}", soft_wrap=True)

    def error(msg: str) -> None:
        """Failure line: red bold ``[!]``."""
        console.print(f"[bold red]\\[!][/] {_clean(msg)}", soft_wrap=True)

    def step(title: str) -> None:
        """Section header rendered as a full-width horizontal rule."""
        console.rule(f"[bold cyan]{_clean(title)}")

    def kv(key: str, value: str) -> None:
        """Indented ``Key: value`` line for network/report-style listings."""
        console.print(
            f"  [bold green]{_clean(key)}:[/] {_clean(value)}", soft_wrap=True
        )

    @contextmanager
    def spinner(text: str):
        """Progress indicator for long operations (scans, LLM calls).

        Yields the Rich Live status object; when stdout is not a terminal
        (tests, pipes) this is a no-op so captured output stays clean.
        """
        if console.is_terminal:
            with console.status(f"[bold cyan]{_clean(text)}", spinner="dots"):
                yield None
        else:
            yield None

    def print_markdown(text: str) -> None:
        """Render LLM analysis (Markdown) with headings/tables/bullets."""
        console.print(Markdown(str(text)))

    def print_panel(text: str, title: str = "", border_style: str = "cyan") -> None:
        """Render a bordered panel (scan summaries, multi-line results)."""
        console.print(
            Panel(str(text), title=title or None, border_style=border_style)
        )

else:  # pragma: no cover - plain-text fallback, same message text

    def _colorize(text: str, color: str) -> str:
        try:
            from colorama import Fore, Style

            return f"{color}{text}{Style.RESET_ALL}"
        except ImportError:
            return text

    def info(msg: str) -> None:
        print(_colorize(f"[*] {msg}", "\x1b[36m"))

    def success(msg: str) -> None:
        print(_colorize(f"[+] {msg}", "\x1b[32m"))

    def warn(msg: str) -> None:
        print(_colorize(f"[!] {msg}", "\x1b[33m"))

    def error(msg: str) -> None:
        print(_colorize(f"[!] {msg}", "\x1b[31m"))

    def step(title: str) -> None:
        print(f"\n{title}\n{'-' * len(str(title))}")

    def kv(key: str, value: str) -> None:
        print(f"  {key}: {value}")

    @contextmanager
    def spinner(text: str):
        print(f"[*] {text}")
        yield None

    def print_markdown(text: str) -> None:
        print(text)

    def print_panel(text: str, title: str = "", border_style: str = "") -> None:
        line = "=" * 60
        print(line)
        if title:
            print(title)
            print(line)
        print(text)
        print(line)


__all__ = [
    "console",
    "info",
    "success",
    "warn",
    "error",
    "step",
    "kv",
    "spinner",
    "print_markdown",
    "print_panel",
    "nullcontext",
]
