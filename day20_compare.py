"""Day 20: formal cross-provider (ollama vs gemini) quality comparison.

Runs the Day 16/17 harness checks (sections, no-fabrication, risk posture,
findings) over every saved analysis/remediation markdown for BOTH providers and
emits:
  * a console summary matrix
  * day20_provider_comparison.md (the report-ready markdown table)

Offline - no LLM calls. Missing files are reported as PENDING so the same
script serves as baseline now and final matrix after the runs land.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_day16_event_log_llm as H

ROOT = Path(__file__).resolve().parent

# (label, mode, input_json, md_file, expected_max or None for remediation)
PAIRS = [
    # ---- standard (5-section) ----
    ("benign",    "standard", "day16_scenario_benign.json",      "day16_analysis_benign.md",            "low"),
    ("benign",    "standard", "day16_scenario_benign.json",      "day16_analysis_benign.gemini.md",     "low"),
    ("bruteforce","standard", "day16_scenario_bruteforce.json",  "day16_analysis_bruteforce.md",        "high"),
    ("bruteforce","standard", "day16_scenario_bruteforce.json",  "day16_analysis_bruteforce.gemini.md", "high"),
    ("incident",  "standard", "day15_sample_events.json",        "day16_analysis_incident.md",          "critical"),
    ("incident",  "standard", "day15_sample_events.json",        "day16_analysis_incident.gemini.md",   "critical"),
    ("real",      "standard", "day19_parsed_events.json",        "day19_analysis_real.md",              "critical"),
    ("real",      "standard", "day19_parsed_events.json",        "day19_analysis_real.gemini.md",       "critical"),
    # ---- remediation (4-section) ----
    ("benign",    "remediation", "day16_scenario_benign.json",     "day17_analysis_benign_remediation.md",            None),
    ("benign",    "remediation", "day16_scenario_benign.json",     "day17_analysis_benign_remediation.gemini.md",     None),
    ("bruteforce","remediation", "day16_scenario_bruteforce.json", "day17_analysis_bruteforce_remediation.md",        None),
    ("bruteforce","remediation", "day16_scenario_bruteforce.json", "day17_analysis_bruteforce_remediation.gemini.md", None),
    ("incident",  "remediation", "day15_sample_events.json",       "day17_analysis_incident_remediation.md",          None),
    ("incident",  "remediation", "day15_sample_events.json",       "day17_analysis_incident_remediation.gemini.md",   None),
    ("real",      "remediation", "day19_parsed_events.json",       "day19_remediation_real.md",                       None),
    ("real",      "remediation", "day19_parsed_events.json",       "day19_remediation_real.gemini.md",                None),
]

def model_of(text: str) -> str:
    m = re.search(r"Model:\s*`([^`]+)`", text)
    return m.group(1) if m else "?"

def analyze_row(label, mode, jsonf, mdf, expected_max):
    md = ROOT / mdf
    if not md.exists():
        return {"label": label, "mode": mode, "md": mdf, "model": "-",
                "status": "PENDING", "size": 0, "sec": "-", "inv": "-",
                "posture": "-", "findings": 0, "note": "file not generated yet"}
    text = md.read_text(encoding="utf-8")
    js = ROOT / jsonf
    known = {int(e["event_id"]) for e in json.loads(js.read_text(encoding="utf-8"))["events"]}
    if mode == "remediation":
        verdict, rows = H.check_analysis(text, known, expected_max=None,
                                         required_sections=H.REMEDIATION_REQUIRED_SECTIONS)
    else:
        verdict, rows = H.check_analysis(text, known, expected_max=expected_max)
    sec = rows[0]; inv = rows[1]; post = rows[2]; find = rows[3]
    return {"label": label, "mode": mode, "md": mdf, "model": model_of(text),
            "status": verdict, "size": len(text),
            "sec": sec[1], "inv": inv[1], "posture": post[1], "findings": int(find[2] or 0),
            "note": ("invented=" + ",".join(map(str, H.hallucinated_event_ids(
                text.split("## 4. Recommended Next Steps")[0], known)))) if inv[1] == "WARN" else ""}

def main():
    rows = [analyze_row(*p) for p in PAIRS]
    # console
    print("=== Day 20 cross-provider quality matrix (baseline/final) ===")
    hdr = f"{'mode':<11}{'scenario':<11}{'provider':<8}{'status':<8}{'sec':<4}{'inv':<5}{'posture':<10}{'findings':<9}{'bytes':<7}model"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        prov = "gemini" if ".gemini." in r["md"] else ("ollama" if r["status"] != "PENDING" else "?")
        print(f"{r['mode']:<11}{r['label']:<11}{prov:<8}{r['status']:<8}{r['sec']:<4}{r['inv']:<5}{r['posture']:<10}{r['findings']:<9}{r['size']:<7}{r['model']}")
    # aggregates per provider
    for prov in ("ollama", "gemini"):
        pr = [r for r in rows if ("gemini" in r["md"]) == (prov == "gemini") and r["status"] != "PENDING"]
        if pr:
            v = [r["status"] for r in pr]
            print(f"[{prov}] {len(v)} files: PASS={v.count('PASS')} WARN={v.count('WARN')} FAIL={v.count('FAIL')} | avg bytes={sum(r['size'] for r in pr)//len(pr)} | avg findings={sum(r['findings'] for r in pr)/len(pr):.1f}")
    # markdown report
    lines = [
        "# Day 20 — Cross-Provider Quality Matrix (ollama `gemma4:latest` vs gemini `gemini-3.6-flash`)",
        "",
        "| # | Mode | Scenario | Provider | Status | Sections | Invented IDs | Risk posture | Findings | Bytes | Model |",
        "|---|------|----------|----------|--------|----------|--------------|--------------|----------|-------|-------|",
    ]
    for i, r in enumerate(rows, 1):
        prov = "gemini" if ".gemini." in r["md"] else ("ollama" if r["status"] != "PENDING" else "?")
        ic = "✅ none" if r["inv"] == "PASS" else (f"⚠ {r['note']}" if r["inv"] == "WARN" else "—")
        pc = {"PASS": "✅", "WARN": "⚠", "INFO": "INFO", "FAIL": "❌", "-": "—"}.get(r["posture"], r["posture"])
        sc = "✅" if r["sec"] == "PASS" else "❌"
        st = {"PASS": "✅ PASS", "WARN": "⚠ WARN", "FAIL": "❌ FAIL", "PENDING": "⏳ PENDING"}[r["status"]]
        lines.append(f"| {i} | {r['mode']} | {r['label']} | {prov} | {st} | {sc} | {ic} | {pc} | {r['findings']} | {r['size']} | {r['model']} |")
        lines.append("")
    (ROOT / "day20_provider_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote day20_provider_comparison.md")

if __name__ == "__main__":
    main()