#!/usr/bin/env python3
"""Diagnose Volcengine Ark endpoint/model/API-key failures.

The script tests the current .env URL plus common Ark chat-completions URLs
against one or more model IDs, and prints HTTP status, parsed error bodies,
latency, and a short reply preview.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_URLS = [
    "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
    "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "https://ark.cn-beijing.volces.com/api/coding/chat/completions",
]

DEFAULT_MODELS = [
    "auto",
    "doubao-seed-2-0-code",
    "Doubao-Seed-2.0-Code",
    "doubao-seed-2-0-pro-260215",
    "doubao-seed-1-6-250615",
    "doubao-pro-32k",
]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def mask_secret(value: str) -> str:
    if len(value) <= 10:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def unique(items: list[str]) -> list[str]:
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def request_chat(url: str, api_key: str, model: str, timeout: float) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "temperature": 0,
        "max_tokens": 16,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - started
            body = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(body)
            text = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "ok": bool(text),
                "http_status": resp.status,
                "elapsed_sec": round(elapsed, 3),
                "model_returned": parsed.get("model"),
                "preview": text.replace("\n", " ")[:120],
                "error": None if text else "HTTP 200 but no assistant text",
            }
    except urllib.error.HTTPError as exc:
        elapsed = time.monotonic() - started
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        return {
            "ok": False,
            "http_status": exc.code,
            "elapsed_sec": round(elapsed, 3),
            "model_returned": None,
            "preview": "",
            "error": parsed if parsed is not None else body[:1000],
        }
    except Exception as exc:
        elapsed = time.monotonic() - started
        return {
            "ok": False,
            "http_status": None,
            "elapsed_sec": round(elapsed, 3),
            "model_returned": None,
            "preview": "",
            "error": str(exc),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Volcengine Ark API endpoint and model IDs.")
    parser.add_argument("--env", default=".env", help="Path to env file. Default: .env")
    parser.add_argument("--api-key", default=None, help="Override ARK_API_KEY.")
    parser.add_argument("--url", action="append", help="URL to test. Can be passed multiple times.")
    parser.add_argument("--model", action="append", help="Model or endpoint ID to test. Can be passed multiple times.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout seconds. Default: 30")
    parser.add_argument("--json", action="store_true", help="Print full JSON diagnostics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = {**load_env(Path(args.env)), **os.environ}
    api_key = args.api_key or env.get("ARK_API_KEY", "")
    env_url = env.get("ARK_BASE_URL", "")
    env_model = env.get("ARK_MODEL", "")

    if not api_key:
        print("ARK_API_KEY is missing. Put it in .env or pass --api-key.", file=sys.stderr)
        return 2

    urls = unique((args.url or []) + [env_url] + DEFAULT_URLS)
    models = unique((args.model or []) + [env_model] + DEFAULT_MODELS)

    diagnostics = {
        "api_key": mask_secret(api_key),
        "urls": urls,
        "models": models,
        "tests": [],
    }

    for url in urls:
        for model in models:
            result = request_chat(url, api_key, model, args.timeout)
            diagnostics["tests"].append({"url": url, "model": model, **result})

    if args.json:
        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(f"ARK API key: {mask_secret(api_key)}")
        for test in diagnostics["tests"]:
            status = "OK" if test["ok"] else "FAIL"
            print()
            print(f"[{status}] {test['http_status']} {test['elapsed_sec']}s")
            print(f"  URL:   {test['url']}")
            print(f"  Model: {test['model']}")
            if test["model_returned"]:
                print(f"  Returned model: {test['model_returned']}")
            if test["preview"]:
                print(f"  Reply: {test['preview']}")
            if test["error"]:
                error = test["error"]
                if isinstance(error, dict):
                    error = json.dumps(error, ensure_ascii=False)
                print(f"  Error: {error}")

    return 0 if any(test["ok"] for test in diagnostics["tests"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
