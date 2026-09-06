"""
Aditya Day 10 test wrapper: validate the REFINED LLM prompt
(risk identification + actionable next steps) across 3 real Nmap test scans.

Pipeline per target:
    NmapScanner.scan() -> export JSON -> build refined prompt -> Gemini -> save Markdown

Targets (safe, legal test hosts):
    1. 127.0.0.1       - localhost baseline (Windows RPC/SMB services)
    2. scanme.nmap.org - Nmap's official public scan target (safe to probe)
    3. 172.16.2.1      - local gateway/router on the user's own network
"""

import json
from pathlib import Path

from sentinelai.prompt_engine import analyze_scan_file
from sentinelai.scanner import NmapScanner

# (target, nmap arguments, json_out, md_out)
SCANS = [
    (
        "127.0.0.1",
        "-sV -p 135,137,139,445,3389,80,443",
        "scan_results_day10_localhost.json",
        "day10_analysis_localhost.md",
    ),
    (
        "scanme.nmap.org",
        "-sV -p 1-1000",
        "scan_results_day10_scanme.json",
        "day10_analysis_scanme.md",
    ),
    (
        "172.16.2.1",
        "-sV -p 22,23,53,80,443,445,8080,8443,3389",
        "scan_results_day10_gateway.json",
        "day10_analysis_gateway.md",
    ),
]


def run_scan(target: str, arguments: str, json_out: str) -> dict:
    """Run one Nmap scan through NmapScanner and export structured JSON."""
    if Path(json_out).exists():
        print(f"[*] Scan JSON already present, skipping scan: {json_out}")
        return json.loads(Path(json_out).read_text(encoding="utf-8"))

    scanner = NmapScanner(target)
    ok = scanner.scan(arguments=arguments)
    if not ok:
        raise RuntimeError(
            f"Scan failed for {target}: {'; '.join(scanner.scan_errors) or 'no hosts found'}"
        )
    if scanner.export_json(json_out):
        print(f"[+] Exported scan JSON -> {json_out}")
    return scanner.get_json_dict()


def main(limit: int = None) -> None:
    print("=" * 60)
    print("SentinelAI Day 10 - Refined prompt validation (3 test scans)")
    print("=" * 60)

    results = []
    for i, (target, args, json_out, md_out) in enumerate(SCANS, start=1):
        if limit is not None and i > limit:
            break
        print(f"\n[{i}/3] Scanning {target} ...")
        scan_json = run_scan(target, args, json_out)

        print(f"[*] Analyzing {target} with refined prompt ...")
        used_model, analysis = analyze_scan_file(
            input_file=json_out,
            output_file=md_out,
            title="Day 10 Nmap LLM Analysis",
        )
        print(f"[+] LLM analysis generated with {used_model} -> {md_out}")
        results.append({"target": target, "model": used_model, "output": md_out})

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  {r['target']:<18} model={r['model']:<24} -> {r['output']}")
    print("Day 10 validation complete.")


if __name__ == "__main__":
    main()