from pathlib import Path

from click.testing import CliRunner

from commands.report import report


def test_report_command_generates_report_from_nmap_file(tmp_path):
    nmap_file = tmp_path / "scan.txt"
    nmap_file.write_text(
        """
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu
5985/tcp open  http    Microsoft HTTPAPI httpd 2.0
""".strip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(report, [str(nmap_file), "--format", "markdown", "--no-llm"])

    assert result.exit_code == 0
    assert "SentinelAI Security Findings Report" in result.output
    assert "ssh" in result.output.lower()
