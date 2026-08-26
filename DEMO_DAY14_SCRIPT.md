# 🎤 Day 14 Team-Sync Demo Script — Full Pipeline (Scan → LLM → Analysis)

**Week 2 Capstone | Presenter:** Aditya Gupta | **Target runtime:** 3–5 min
**Providers:** `ollama` (local, offline-proof) and `gemini` (cloud free tier)

---

## ✅ Pre-Demo Checklist (run 10 min before presenting)

| # | Check | Command | Expect |
|---|-------|---------|--------|
| 1 | venv active | `(venv)` in prompt / `.\venv\Scripts\Activate.ps1` | prompt shows `(venv)` |
| 2 | Nmap installed | `nmap --version` | 7.9x |
| 3 | Ollama up + model warm | `ollama ps` (empty OK) then `ollama run gemma4 "Say ready"` | replies "ready" |
| 4 | Gemini key set (only if demoing cloud) | `Get-Content .env | Select-String GEMINI` | key line exists |
| 5 | Old artifacts cleaned | `Remove-Item day14_scan_demo.json, day14_analysis_demo.md -EA SilentlyContinue` | clean start |

> 💡 **Warm the model before going live:** the first Ollama call after boot can
> take minutes to load weights. One throwaway `ollama run gemma4 "hi"` makes
> the real demo fast.

---

## 🚀 Option A — One-Command Demo (recommended, safest)

```powershell
python demo_day14_pipeline.py
```

What the audience sees, in order:
1. Banner: *SentinelAI Day 14 Demo: scan -> LLM -> security analysis*
2. Live Nmap scan of `127.0.0.1` (~10 s) → `day14_scan_demo.json`
3. Parsed ports summary (e.g. `[135, 445]`)
4. Local LLM analysis via gemma4 — **works with wifi off**
5. Programmatic verification: **all 5 sections present**
6. Final summary box: total wall time + artifact paths

Variants:
```powershell
python demo_day14_pipeline.py --provider gemini   # show the cloud path too
python demo_day14_pipeline.py --skip-scan         # instant rerun using saved JSON
```

---

## 🖥️ Option B — Manual Stage-by-Stage (shows the CLI surface)

```powershell
# Stage 1: scan (save JSON when prompted: y)
python sentinelai.py scan --target 127.0.0.1

# Stage 2: analyze locally (free, private)
python sentinelai.py analyze -i scan_127_0_0_1.json --llm ollama -o day14_manual_ollama.md

# Stage 3: same file through the cloud provider
python sentinelai.py analyze -i scan_127_0_0_1.json --llm gemini -o day14_manual_gemini.md

# Bonus: show the switcher guardrails live
python sentinelai.py analyze --llm openai    # friendly paid-API refusal
```

Talking point while it runs: *"Same scan file, one flag, two brains — a local
model for privacy and Gemini for cloud quality."*

---

## 🗣️ 30-Second Pitch (between stages)

> SentinelAI is a defensive cybersecurity CLI agent. We scan with Nmap, then an
> LLM turns raw port data into a plain-English security report — ranked risks,
> attacker view, and concrete next steps. Unlike offensive pentest tools, we're
> defender-first, work on Windows and Linux, and — unique among competitors —
> run fully LOCAL via Ollama, so nothing leaves your machine.

## ⏱️ Expected Timings (after warm-up)

| Stage | Typical |
|-------|---------|
| Nmap localhost scan | ~10–15 s |
| Ollama gemma4 analysis (warm) | ~45–120 s |
| Gemini analysis | ~30–90 s |
| Section validation + save | <1 s |

---

## 🛟 Fallback Plans

| Problem | Fallback |
|---------|----------|
| Wifi dies mid-demo | Use ollama path — fully local |
| Gemini quota/timeout | Switch flag to `--llm ollama` |
| Model cold/slow first call | Pre-warm in checklist step 3; or `--skip-scan` to cut stage 1 |
| Nmap missing on demo PC | `--skip-scan` with committed `day14_scan_demo.json` |
| Anything crashes | Open `day10_analysis_gateway.md` / `day12_analysis_localhost.md` as pre-baked results |

---

## ❓ Anticipated Q&A

- **Why not ChatGPT/Claude?** — Paid APIs; switcher already accepts them (`--llm openai`) and refuses gracefully until wired.
- **Is scanning legal?** — Demo scans localhost or scanme.nmap.org (Nmap's public practice host); gateway scans are our own router.
- **Where do reports go?** — Markdown today; DOCX/PDF land in Week 3 (Suraj).
- **What's next?** — Week 3: Windows Event Logs → LLM, OWASP/MITRE mapping, beginner mode.

---

## ✔️ Sign-off checklist for the sync

- [ ] Pipeline demo ran end-to-end (`demo_day14_pipeline.py`)
- [ ] Both providers shown (or fallback documented if one unavailable)
- [ ] Week 2 milestone declared: *Nmap scans + AI plain-English analysis* ✅