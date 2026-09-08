# Week 5 — Day 31: Consent-Gate Attestation Flow — Design (Active Testing & Authorization Sprint)

**Date:** 2026-09-07
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 114-Day Plan | Feature Sprint (Days 31–44) — Active Testing & Authorization | Week 5, Day 31
**Day 31 task:** *"Design the consent-gate attestation flow — exact wording, CLI prompt structure."*
**Deliverable:** ✅ Attestation text finalized · UX flow sketched (this document, for team review before Day 32 implementation)

---

## 1. Context — Why This Gate Exists

Days 31–44 add **active security testing** (`sentinelai scan --target <site> --active`)
powered by OWASP ZAP. Active scans send real attack traffic, so before any of it can
run the plan mandates a genuine **two-layer authorization system**:

1. **Consent gate** (Aditya, Days 31–34) — a typed attestation + audit trail (accountability).
2. **Domain verification** (Aditya, Day 33) — a `.well-known` token file the target's
   real administrator must place (proof of control).

**Design decisions already locked in (from the Feature-Sprint design notes, carried forward):**
- ✅ No custom exploit code — all active testing is delegated to ZAP's own engine.
- ✅ The gate verifies **domain control + creates an audit trail**, NOT legal authorization — this distinction is stated plainly in the UX and in `SECURITY.md` (Day 38).
- ✅ Government ID collection (Aadhaar/PAN) rejected — doesn't prove ownership and imposes DPDP Act risk.
- ✅ Dev-time testing only against OWASP Juice Shop locally — no real third-party targets.

---

## 2. Consent-Gate UX Flow (sketch)

```
sentinelai scan --target https://juice-shop.local --active
  │
  ├─[1] CONSENT GATE   request_consent(target, ...)          (Days 32 + 34)
  │      ├─ render ATTESTATION PANEL (ui.print_panel, red "ACTIVE TESTING" banner)
  │      ├─ prompt  : type the exact attestation sentence (quotes included)
  │      ├─ match?  : ✗ mismatch / "quit" / Ctrl+C  → DENIED → audit → ABORT (no scan)
  │      └─ match?  : ✓ verbatim (case/whitespace-normalized) → GRANTED → audit
  │
  ├─[2] DOMAIN VERIFICATION  verify_domain_ownership(target)  (Day 33, wired Day 34)
  │      ├─ expect https://<host>/.well-known/sentinelai-verify.txt
  │      ├─ unreachable / token mismatch → DENIED → audit → ABORT
  │      └─ token match → VERIFIED → audit → proceed
  │
  ├─[3] ZAP ACTIVE SCAN    (Affan's "active" box, Days 36/38–40 — gated by
  │      active_authorized=True; runs only because BOTH checks passed above)
  │
  ├─[4] LLM EXPLANATION    zap_analysis prompt (Day 35–36, refined Days 38–41)
  │
  └─[5] REPORT             Authorization Record appendix (Suraj, Day 38)
```

**Design principle:** no step may execute before the two-layer gate passes. The
`--active` flag is the *only* entry point into step [3]; there is no side door.

---

## 3. Finalized Attestation Text (exact wording)

### 3a. Attestation panel (shown before the prompt)

```
╔══════════════════════════════════════════════════════════════════════╗
║  ⚠️  ACTIVE TESTING — AUTHORIZATION REQUIRED                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  You are about to run ACTIVE security testing against:                ║
║                                                                       ║
║      Target : <target>                                                ║
║      Engine : OWASP ZAP active scan (sends real attack traffic)       ║
║                                                                       ║
║  Active scans can:                                                     ║
║    • alter, damage, or crash the target application                    ║
║    • trigger WAF / IDS alerts on the hosting network                   ║
║    • carry legal consequences if you do not own the target             ║
║                                                                       ║
║  SentinelAI requires TWO confirmations before any active request:      ║
║    1. ATTESTATION — you confirm you own the target or have written     ║
║       authorization to test it.                                        ║
║    2. DOMAIN VERIFICATION — SentinelAI checks the token file the        ║
║       target's administrator publishes at                              ║
║       https://<host>/.well-known/sentinelai-verify.txt                 ║
║                                                                       ║
║  Typing the attestation below is a binding statement of intent. Your   ║
║  exact response and decision will be recorded in the local audit log   ║
║  (consent_audit_log.jsonl).                                            ║
║                                                                       ║
║  SentinelAI verifies domain control only; it does not and cannot       ║
║  verify legal authorization. You remain responsible.                   ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 3b. The typed-phrase prompt (must be typed verbatim)

> Type this EXACT sentence to confirm — quotes included — or type `quit` / press Ctrl+C to cancel:
>
> ```
> "I authorize active security testing of <target> and confirm that I own
> this system or have written authorization to test it."
> ```
>
> *(`<target>` is replaced by the exact target string shown in the panel above.)*

**Exact match semantics (for Day 32 implementation):**
- The expected string is `request_consent()`'s `expected_phrase`, built from the
  literal template + the validated target.
- Matching normalizes **case → lowercase**, **whitespace → single spaces**, and strips the
  outer quotes before comparison — so typos in spacing/caps don't pass, `quit` always cancels.
- **No `--yes` / auto-approve path exists for active testing.** Unlike the passive
  Day 20 `request_approval()` flow, a typed response cannot be pre-signed. `--active --yes`
  is explicitly unsupported and rejected with guidance.

### 3c. Audit record schema (every attempt, granted or denied)

Appended (one JSON object per line) to `consent_audit_log.jsonl`:
```json
{
  "timestamp": "2026-09-07T14:22:10.123456",
  "event": "consent_attempt",
  "target": "https://juice-shop.local",
  "decision": "granted" | "denied",
  "reason": "attestation_match" | "attestation_mismatch" | "user_quit" | "aborted",
  "typed_length": 102,
  "user": "ADITYA-GUPTA",
  "host": "DESKTOP-XXXX",
  "version": "1.0.0"
}
```
- Append-only, local-only, never uploaded (privacy-first: same spirit as Ollama mode).
- Written **before** proceeding on grant (crash-safe: a granted-but-unlogged run is impossible).
---

## 4. CLI Prompt Structure (where the code will live)

| Aspect | Design | Reuses |
|---|---|---|
| Module | `sentinelai/consent.py` — `request_consent(target, *, audit_path=...) -> ConsentResult` | new (Day 32) |
| Audit writer | JSONL append with `utf-8` | pattern from `sentinelai/approval.py` audit block |
| Rendering | `ui.warn(...)`/`ui.print_panel(...)`, plain-text shim for non-TTY | `sentinelai/ui.py` |
| Prompt input | `click.prompt` with `hide_input=False`, `Ctrl+C` handled via `KeyboardInterrupt` → denied | click + approval.py pattern |
| Error surface | `ConsentError(ValueError)` mirroring `ApprovalError` | `sentinelai/approval.py` |
| CLI wiring | New `--active` flag on `scan` (both entry points, already parity-locked) | Days 34, `test_cli_sync.py` |

**Scope guard (team boundary):**
- Aditya: attestation wording + `request_consent()` + domain verification + `--active` wiring.
- Affan: `VulnerabilityCheck`/`CheckType` base (`checks/base.py`), orchestrator, ZAP wrapper.
- Suraj: active-findings report section + Authorization Record appendix.
- Sneha: pytest for consent/domain/plugins, ZAP→OWASP/MITRE mapping extensions.
- Day-31 deliverable is **this design only**; `request_consent()` implementation is Day 32.

---

## 5. Open Questions for Team Review

1. Should the audit log rotate (size cap) for long-use sessions? — default: no for sprint; note in SECURITY.md.
2. Confirm the exact phrase reads naturally for the demo narrative (Juice Shop target).
3. Should the panel warn when a scan target contains a protocol (https://) vs bare host, to keep the `.well-known` URL unambiguous? — proposed: yes, normalize to host for verification.

---

## Sign-Off

**Day 31 Status:** ✅ **COMPLETE (design)** — attestation wording finalized, UX flow sketched,
aligned with existing `approval.py`/`ui.py` patterns and the Feature-Sprint design constraints.
Ready for Day 32 implementation (`request_consent()` + typed-phrase matching + audit logging).

**Developer:** Aditya Gupta | **Team:** Team Finatics | **CodeQuest 4.0**
