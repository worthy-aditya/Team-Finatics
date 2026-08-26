"""Aditya Day 9 test wrapper for the reusable prompt engine."""

from sentinelai.prompt_engine import analyze_scan_file


def main() -> None:
    print("[*] Aditya Day 9: sending sample Nmap JSON to Gemini...")
    model, analysis = analyze_scan_file(title="Day 9 Nmap LLM Analysis")

    print(f"[+] LLM analysis generated with {model}")
    print("[+] Saved output to day9_nmap_llm_analysis.md")
    print()
    print(analysis)


if __name__ == "__main__":
    main()
