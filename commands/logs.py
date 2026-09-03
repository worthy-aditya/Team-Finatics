"""commands/logs.py - thin re-export of the shared `logs` command.

The actual implementation lives in sentinelai/logs_command.py (Day 22), shared
by both CLI entry points (sentinelai/cli.py and this root-command CLI) so the
real/sample event-log read + analysis behavior is identical everywhere.
"""
from sentinelai.logs_command import build_logs_command

logs = build_logs_command()