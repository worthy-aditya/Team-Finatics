"""Day 20 direct single-run helper.

Usage:
    py -u day20_direct.py <label> <input_json> <output_md> <provider> <mode> <title>
provider: gemini | ollama
mode:     standard | remediation
"""
import sys, time
from sentinelai.prompt_engine import (
    LLMProvider, PromptMode, analyze_event_log_file,
)

def main():
    label, input_file, output_file, prov, mode_s, title = sys.argv[1:7]
    provider = LLMProvider(prov)
    mode = PromptMode(mode_s)
    print(f"[{label}] START provider={prov} mode={mode_s} -> {output_file}", flush=True)
    t0 = time.time()
    model, _ = analyze_event_log_file(
        input_file=input_file,
        output_file=output_file,
        title=title,
        provider=provider,
        mode=mode,
    )
    print(f"[{label}] DONE {model} {time.time()-t0:.1f}s -> {output_file}", flush=True)

if __name__ == "__main__":
    main()