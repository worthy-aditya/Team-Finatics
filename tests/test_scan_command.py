from click.testing import CliRunner

from commands.scan import scan


def test_scan_command_reads_scan_file_and_generates_report(tmp_path):
    scan_file = tmp_path / "sample_scan.txt"
    scan_file.write_text(
        """
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu
5985/tcp open  http    Microsoft HTTPAPI httpd 2.0
""".strip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(scan, [str(scan_file), "--format", "markdown", "--no-llm"])

    assert result.exit_code == 0
    assert "SentinelAI Security Findings Report" in result.output
    assert "ssh" in result.output.lower()
