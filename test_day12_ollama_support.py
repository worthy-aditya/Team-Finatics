"""Day 12 test wrapper: validate Ollama support (local LLM analysis).

Pipeline:
    scan JSON -> build_prompt(mode) -> analyze_scan_data(provider=OLLAMA)
              -> local Ollama server -> save Markdown

Checks performed (in order):
    1. Ollama server reachable + list installed models (no API key needed!)
    2. Tiny live smoke prompt through the unified analyze_scan_data() entry
    3. Full STANDARD-mode analysis of the localhost scan saved to Markdown

Run:  python test_day12_ollama_support.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinelai.prompt_engine import (
    LLMProvider,
    PromptMode,
    analyze_scan_data,
    check_ollama_server,
    list_ollama_models,
)


def main() -> None:
    print("=" * 60)
    print("SentinelAI Day 12 - Ollama support validation")
    print("=" * 60)

    # 1. Server reachable + models installed
    tags = check_ollama_server()
    models = list_ollama_models()
    print(f"[+] Ollama server reachable at {tags.get('host', 'localhost')}")
    print(f"[+] Installed models: {models}")
    if not models:
        raise SystemExit(
            "No Ollama models installed. Pull one first, e.g. 'ollama pull llama3'."
        )

    # 2. Tiny smoke prompt through the unified entry point
    t0 = time.time()
    result = analyze_scan_data(
        {
            "smoke_test": True,
            "note": "Reply with exactly: SMOKE-OK",
        },
        provider=LLMProvider.OLLAMA,
        mode=PromptMode.STANDARD,
    )
    dt = time.time() - t0
    print(f"[+] Smoke OK via {result.model} in {dt:.1f}s "
          f"(tokens in={result.usage['prompt_tokens']}, out={result.usage['response_tokens']})")
    assert result.analysis.strip(), "Ollama returned an empty response"

    # 3. Full localhost-scan analysis through Ollama (resume-safe skip)
    out_file = Path("day12_analysis_localhost.md")
    if out_file.exists():
        print(f"[*] {out_file} already exists - skipping full analysis")
        return

    scan_data = json.loads(Path("scan_results.json").read_text(encoding="utf-8"))
    print("[*] Running FULL localhost analysis through Ollama (may take minutes)...")
    t0 = time.time()
    result = analyze_scan_data(scan_data, provider=LLMProvider.OLLAMA)
    dt = time.time() - t0
    out_file.write_text(
        f"# Day 12 Ollama Nmap Analysis\n\n"
        f"Provider: ollama | Model: `{result.model}`\n\n{result.analysis}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved {out_file} via {result.model} in {dt:.1f}s "
          f"(prompt={result.usage['prompt_tokens']} tok, "
          f"response={result.usage['response_tokens']} tok)")
    print("Day 12 validation complete.")


if __name__ == "__main__":
    main()