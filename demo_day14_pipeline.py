"""Day 14: One-command end-to-end pipeline demo (scan -> LLM -> report).

Team-sync demo for Week 2. Runs the FULL SentinelAI pipeline:

    Nmap scan (localhost, ~10s) -> structured JSON -> refined 5-section prompt
    -> LLM (ollama local OR gemini cloud) -> Markdown analysis

Usage:
    python demo_day14_pipeline.py                      # ollama (local, no wifi needed)
    python demo_day14_pipeline.py --provider gemini    # cloud free tier
    python demo_day14_pipeline.py --skip-scan          # reuse existing JSON (fastest)

Resume-safe: reuses day14_scan_demo.json when present unless --rescan.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinelai.prompt_engine import (
    PromptMode,
    analyze_scan_data,
    load_scan_data,
    resolve_provider,
)
from sentinelai.scanner import NmapScanner

SCAN_JSON = Path("day14_scan_demo.json")
ANALYSIS_MD = Path("day14_analysis_demo.md")
SCAN_ARGS = "-sV -p 135,137,139,445,3389,80,443"
REQUIRED_SECTIONS = [
    "## 1. Plain-English Summary",
    "## 2. Risk Findings",
    "## 3. Attacker Perspective",
    "## 4. Recommended Next Steps",
    "## 5. Confidence & Limitations",
]


def banner(text: str) -> None:
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def do_scan(rescan: bool) -> dict:
    """Step 1: Nmap scan -> structured JSON (skipped if already present)."""
    if SCAN_JSON.exists() and not rescan:
        print(f"[skip] Scan JSON exists: {SCAN_JSON}")
        return load_scan_data(SCAN_JSON)

    print(f"[*] Scanning 127.0.0.1 {SCAN_ARGS} ...")
    t0 = time.time()
    scanner = NmapScanner("127.0.0.1")
    if not scanner.scan(arguments=SCAN_ARGS):
        raise SystemExit(
            "[!] Scan failed: "
            + ("; ".join(scanner.scan_errors) or "no hosts responded")
        )
    scanner.export_json(str(SCAN_JSON))
    print(f"[+] Scan done in {time.time() - t0:.1f}s -> {SCAN_JSON}")
    return scanner.get_json_dict()


def do_analyze(scan_data: dict, provider_name: str):
    """Step 2+3: prompt -> LLM -> validated 5-section analysis."""
    provider = resolve_provider(provider_name)
    print(f"[*] Analyzing with provider={provider.value} "
          f"(mode={PromptMode.STANDARD.value}) ...")
    t0 = time.time()
    result = analyze_scan_data(scan_data, provider=provider)
    dt = time.time() - t0

    missing = [s for s in REQUIRED_SECTIONS if s not in result.analysis]
    if missing:
        raise SystemExit(f"[!] Analysis missing required sections: {missing}")

    usage = result.usage or {}
    print(
        f"[+] Analysis OK in {dt:.1f}s via {result.model} "
        f"(prompt={usage.get('prompt_tokens', '?')} tok, "
        f"response={usage.get('response_tokens', '?')} tok)"
    )
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="SentinelAI Day 14 pipeline demo")
    ap.add_argument("--provider", default="ollama",
                    help="gemini | ollama (free providers; default: ollama)")
    ap.add_argument("--skip-scan", action="store_true",
                    help="reuse existing scan JSON if present")
    ap.add_argument("--rescan", action="store_true",
                    help="force a fresh Nmap scan even if JSON exists")
    args = ap.parse_args()

    banner("SentinelAI Day 14 Demo: scan -> LLM -> security analysis")

    t_start = time.time()
    scan_data = do_scan(rescan=args.rescan)

    hosts = scan_data.get("hosts") or []
    open_ports = [
        f"{p.get('port')}/{p.get('service', {}).get('name', '?')}"
        for h in hosts
        for p in (h.get("ports") or [])
        if p.get("state") == "open"
    ]
    print(f"[+] Parsed {len(hosts)} host(s), open TCP ports: {open_ports}")

    result = do_analyze(scan_data, args.provider)

    ANALYSIS_MD.write_text(
        f"# Day 14 Pipeline Demo Analysis\n\n"
        f"Provider: {result.provider.value} | Model: `{result.model}`\n\n"
        f"{result.analysis}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved {ANALYSIS_MD}")

    banner("PIPELINE COMPLETE")
    print(f"Total wall time : {time.time() - t_start:.1f}s")
    print(f"Scan JSON       : {SCAN_JSON}")
    print(f"Analysis (5/5 sections verified): {ANALYSIS_MD}")
    print(f"Provider/Model  : {result.provider.value} / {result.model}")


if __name__ == "__main__":
    main()