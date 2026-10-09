"""Run the Day 47 four-provider comparison on synthetic inputs only.

Each provider receives the exact same prompt text for each case. The script
makes one HTTP request per provider/case (no application retries) and records
responses, model IDs, timing, usage metadata, and prompt hashes.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from sentinelai.prompt_engine import build_event_log_prompt, build_nmap_analysis_prompt

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "day47_provider_comparison.md"
MAX_OUTPUT_TOKENS = 1000
TIMEOUT_SECONDS = 180

PROVIDERS = [
    {"id": "openai", "label": "GPT-4o", "model": "gpt-4o", "key_env": "OPENAI_API_KEY"},
    {"id": "anthropic", "label": "Claude Sonnet 5.5", "model": "claude-sonnet-5-5", "key_env": "CLAUDE_API_KEY"},
    {"id": "gemini", "label": "Gemini Flash", "model": "gemini-flash-latest", "key_env": "GEMINI_API_KEY"},
    {"id": "ollama", "label": "Ollama Gemma 4", "model": "gemma4:latest", "key_env": None},
]


def build_cases() -> list[dict[str, str]]:
    """Build two small prompts from synthetic, documentation-range data."""
    scan_data = {
        "scan_metadata": {
            "target": "192.0.2.10",
            "scan_type": "synthetic Day 47 comparison fixture",
            "duration_seconds": 1,
        },
        "summary": {"hosts_up": 1, "open_ports": 1},
        "hosts": [
            {
                "ip": "192.0.2.10",
                "hostname": "sample-lab",
                "status": "up",
                "ports": [
                    {
                        "port": 22,
                        "protocol": "tcp",
                        "state": "open",
                        "service": "ssh",
                        "version": "OpenSSH 9.6",
                    }
                ],
            }
        ],
    }
    events = [
        {
            "event_id": 4625,
            "timestamp": "2026-10-07T09:00:00Z",
            "level": "warning",
            "channel": "Security",
            "account": "sample-user",
            "domain": "SAMPLE-LAB",
            "logon_type": 3,
            "logon_type_name": "Network",
            "source_ip": "203.0.113.42",
            "source_host": "sample-client",
            "message": "Synthetic failed logon event.",
            "count": 3,
        },
        {
            "event_id": 4624,
            "timestamp": "2026-10-07T09:02:00Z",
            "level": "information",
            "channel": "Security",
            "account": "sample-user",
            "domain": "SAMPLE-LAB",
            "logon_type": 3,
            "logon_type_name": "Network",
            "source_ip": "203.0.113.42",
            "source_host": "sample-client",
            "message": "Synthetic successful logon event.",
            "count": 1,
        },
    ]
    event_data = {
        "source": "Synthetic Windows Security Event Log",
        "host": "sample-workstation",
        "collected_at": "2026-10-07T09:05:00Z",
        "window_start": "2026-10-07T09:00:00Z",
        "window_end": "2026-10-07T09:05:00Z",
        "count": len(events),
        "events": events,
    }
    return [
        {"case": "Synthetic Nmap scan", "prompt": build_nmap_analysis_prompt(scan_data)},
        {"case": "Synthetic Windows event log", "prompt": build_event_log_prompt(event_data)},
    ]


def extract_text(provider_id: str, payload: dict[str, Any]) -> str:
    """Extract generated text from each provider's native REST response."""
    if provider_id == "openai":
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, str):
            text = content
        else:
            text = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    elif provider_id == "anthropic":
        text = "\n".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if block.get("type") == "text"
        )
    elif provider_id == "gemini":
        text = "\n".join(
            part.get("text", "")
            for candidate in payload.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
            if isinstance(part, dict)
        )
    elif provider_id == "ollama":
        text = str(payload.get("response", ""))
    else:
        raise ValueError(f"Unknown provider: {provider_id}")
    if not text.strip():
        raise ValueError("Provider returned no text content")
    return text.strip()


def _post_json(url: str, *, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(url, headers=headers, json=body, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Provider returned a non-object JSON response")
    return payload


def request_provider(provider: dict[str, Any], prompt: str, api_key: str | None) -> tuple[str, dict[str, Any], str]:
    """Perform one provider request with no harness retry or model fallback."""
    provider_id = provider["id"]
    model = provider["model"]
    if provider_id == "openai":
        payload = _post_json(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            body={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": MAX_OUTPUT_TOKENS,
            },
        )
        return extract_text(provider_id, payload), payload.get("usage", {}), payload.get("model", model)
    if provider_id == "anthropic":
        payload = _post_json(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": str(api_key), "anthropic-version": "2023-06-01"},
            body={
                "model": model,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return extract_text(provider_id, payload), payload.get("usage", {}), payload.get("model", model)
    if provider_id == "gemini":
        payload = _post_json(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent",
            headers={"x-goog-api-key": str(api_key)},
            body={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": MAX_OUTPUT_TOKENS},
            },
        )
        usage = payload.get("usageMetadata", {})
        return extract_text(provider_id, payload), usage, payload.get("modelVersion", model)
    if provider_id == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        payload = _post_json(
            f"{host}/api/generate",
            headers={},
            body={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": MAX_OUTPUT_TOKENS, "num_ctx": 6144},
            },
        )
        usage = {
            "prompt_eval_count": payload.get("prompt_eval_count"),
            "eval_count": payload.get("eval_count"),
            "total_duration": payload.get("total_duration"),
        }
        return extract_text(provider_id, payload), usage, payload.get("model", model)
    raise ValueError(f"Unknown provider: {provider_id}")


def _safe_error(exc: Exception, api_keys: dict[str, str]) -> str:
    message = str(exc)
    for value in api_keys.values():
        if value:
            message = message.replace(value, "[REDACTED]")
    return message[:1200]


def run_comparison() -> list[dict[str, Any]]:
    load_dotenv(dotenv_path=".env")
    api_keys = {
        provider["key_env"]: os.getenv(provider["key_env"], "")
        for provider in PROVIDERS
        if provider["key_env"]
    }
    cases = build_cases()
    rows = []
    for case in cases:
        prompt_hash = hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest()
        for provider in PROVIDERS:
            started = time.perf_counter()
            key_env = provider["key_env"]
            api_key = api_keys.get(key_env, "") if key_env else None
            label = provider["label"]
            print(f"START {case['case']} | {label} | model={provider['model']}", flush=True)
            row = {
                "case": case["case"],
                "provider": label,
                "provider_id": provider["id"],
                "requested_model": provider["model"],
                "prompt_sha256": prompt_hash,
                "status": "ERROR",
                "elapsed_seconds": None,
                "usage": {},
                "output": "",
            }
            if key_env and not api_key:
                row["status"] = "SKIPPED"
                row["output"] = f"Missing {key_env}; no request was sent."
            else:
                try:
                    text, usage, reported_model = request_provider(provider, case["prompt"], api_key)
                    row.update(
                        status="OK",
                        reported_model=reported_model,
                        usage=usage,
                        output=text,
                    )
                except Exception as exc:
                    row["output"] = _safe_error(exc, api_keys)
            row["elapsed_seconds"] = round(time.perf_counter() - started, 2)
            rows.append(row)
            print(f"DONE {case['case']} | {label} | {row['status']} | {row['elapsed_seconds']}s", flush=True)
    return rows


def render_report(rows: list[dict[str, Any]], generated_at: str | None = None) -> str:
    cases = build_cases()
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    lines = [
        "# Day 47 - Four-Provider Prompt Comparison",
        "",
        f"**Generated:** {generated_at}",
        "**Models:** GPT-4o (`gpt-4o`), Claude Sonnet 5.5 (`claude-sonnet-5-5`), Gemini Flash (`gemini-flash-latest`), Ollama Gemma 4 (`gemma4:latest`).",
        "**Data:** synthetic only; reserved documentation IP ranges; no real scan or personal event-log data.",
        "**Method:** Each provider received the exact same prompt for a given case; temperature was set to 0 and output was capped at 1,000 tokens. No harness retries or model fallback were used. HTTP/client SDKs may still implement their own retry policies.",
        "**Interpretation:** This is a descriptive comparison, not an accuracy ranking. Day 48 will score MITRE mapping against a ground-truth dataset.",
        "",
        "## Results",
        "",
        "| Case | Provider | Status | Requested model | Reported model | Seconds | Usage metadata | Prompt SHA-256 |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        usage = json.dumps(row.get("usage", {}), sort_keys=True, separators=(",", ":"))
        lines.append(
            f"| {row['case']} | {row['provider']} | {row['status']} | `{row['requested_model']}` | "
            f"`{row.get('reported_model', '-')}` | {row['elapsed_seconds']} | `{usage}` | `{row['prompt_sha256']}` |"
        )
    for case in cases:
        lines.extend(["", f"## Exact prompt - {case['case']}", "", "````text", case["prompt"], "````"])
        for row in rows:
            if row["case"] != case["case"]:
                continue
            lines.extend(
                [
                    "",
                    f"### {row['provider']} ({row['status']})",
                    "",
                    f"Elapsed: {row['elapsed_seconds']} seconds",
                    "",
                    "````markdown",
                    row["output"],
                    "````",
                ]
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    rows = run_comparison()
    OUTPUT.write_text(render_report(rows), encoding="utf-8")
    print(f"Wrote {OUTPUT.name}", flush=True)
    failures = [row for row in rows if row["status"] != "OK"]
    print(f"Results: {len(rows) - len(failures)}/{len(rows)} succeeded", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
