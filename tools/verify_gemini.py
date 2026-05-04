#!/usr/bin/env python3
"""
工具：Google Gemini 诊断
作用：测试 Gemini API 的连通性、延迟和稳定性，支持多 Key 轮换测试。
用法：python3 tools/verify_gemini.py
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
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


def build_url(base_url: str, path: str, api_key: str) -> str:
    base = base_url.rstrip("/")
    separator = "&" if "?" in path else "?"
    return f"{base}{path}{separator}{urllib.parse.urlencode({'key': api_key})}"


def request_json(url: str, payload: dict | None, timeout: float) -> tuple[int | None, dict | None, str | None, float]:
    headers = {"Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if payload is None else "POST")

    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - started
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body), None, elapsed
    except urllib.error.HTTPError as exc:
        elapsed = time.monotonic() - started
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        return exc.code, parsed, body[:1000], elapsed
    except Exception as exc:
        elapsed = time.monotonic() - started
        return None, None, str(exc), elapsed


def list_models(base_url: str, api_key: str, timeout: float) -> tuple[set[str], dict]:
    status, parsed, raw_error, elapsed = request_json(build_url(base_url, "/models", api_key), None, timeout)
    names: set[str] = set()
    if parsed and isinstance(parsed.get("models"), list):
        for item in parsed["models"]:
            name = str(item.get("name", ""))
            if name.startswith("models/"):
                names.add(name.split("/", 1)[1])

    return names, {
        "status": status,
        "elapsed_sec": round(elapsed, 3),
        "model_count": len(names),
        "error": extract_error(parsed, raw_error),
    }


def extract_error(parsed: dict | None, raw_error: str | None) -> dict | str | None:
    if parsed and isinstance(parsed.get("error"), dict):
        error = parsed["error"]
        return {
            "code": error.get("code"),
            "status": error.get("status"),
            "message": error.get("message"),
        }
    return raw_error


def generate_once(base_url: str, api_key: str, model: str, prompt: str, timeout: float) -> dict:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 64,
        },
    }
    url = build_url(base_url, f"/models/{model}:generateContent", api_key)
    status, parsed, raw_error, elapsed = request_json(url, payload, timeout)

    result = {
        "http_status": status,
        "elapsed_sec": round(elapsed, 3),
        "ok": False,
        "error": extract_error(parsed, raw_error),
        "finish_reason": None,
        "text_len": 0,
        "preview": "",
    }

    candidates = parsed.get("candidates") if parsed else None
    if status == 200 and isinstance(candidates, list) and candidates:
        candidate = candidates[0]
        result["finish_reason"] = candidate.get("finishReason")
        parts = candidate.get("content", {}).get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
        result["text_len"] = len(text)
        result["preview"] = text.replace("\n", " ")[:120]
        result["ok"] = bool(text)
        result["error"] = None if text else "empty text in first candidate"
    elif status == 200:
        result["error"] = "HTTP 200 but no candidates"

    return result


def summarize(results: list[dict]) -> dict:
    latencies = [item["elapsed_sec"] for item in results if item["ok"]]
    errors: dict[str, int] = {}
    for item in results:
        if item["ok"]:
            continue
        key = json.dumps(item["error"], ensure_ascii=False, sort_keys=True)
        errors[key] = errors.get(key, 0) + 1

    summary = {
        "runs": len(results),
        "ok": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "errors": errors,
    }
    if latencies:
        summary.update(
            {
                "latency_min_sec": round(min(latencies), 3),
                "latency_median_sec": round(statistics.median(latencies), 3),
                "latency_max_sec": round(max(latencies), 3),
            }
        )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Gemini API model stability.")
    parser.add_argument("--env", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), help="Path to env file.")
    parser.add_argument("--base-url", default=None, help="Override GEMINI_BASE_URL.")
    parser.add_argument("--api-key", action="append", help="Override Gemini API key. Can be passed multiple times.")
    parser.add_argument("--model", action="append", help="Model to test. Can be passed multiple times.")
    parser.add_argument("--runs", type=int, default=10, help="Requests per model. Default: 10")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests. Default: 1")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout seconds. Default: 30")
    parser.add_argument("--prompt", default="Reply with exactly: OK", help="Prompt used for generateContent.")
    parser.add_argument("--json", action="store_true", help="Print full JSON diagnostics.")
    return parser.parse_args()


def collect_api_keys(args: argparse.Namespace, env: dict[str, str]) -> list[str]:
    if args.api_key:
        return args.api_key

    keys: list[str] = []
    for name in ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 11)]:
        value = env.get(name, "")
        if value and value not in keys:
            keys.append(value)

    for value in env.get("GEMINI_API_KEYS", "").split(","):
        value = value.strip()
        if value and value not in keys:
            keys.append(value)

    return keys


def main() -> int:
    args = parse_args()
    env = {**load_env(Path(args.env)), **os.environ}
    api_keys = collect_api_keys(args, env)
    base_url = args.base_url or env.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    models = args.model or DEFAULT_MODELS

    if not api_keys:
        print("Gemini API key is missing. Put GEMINI_API_KEY in .env or pass --api-key.", file=sys.stderr)
        return 2

    diagnostics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "api_keys": [mask_secret(api_key) for api_key in api_keys],
        "models_requested": models,
        "keys": [],
    }

    for key_index, api_key in enumerate(api_keys, 1):
        visible_models, list_info = list_models(base_url, api_key, args.timeout)
        key_report = {
            "key_index": key_index,
            "api_key": mask_secret(api_key),
            "list_models": list_info,
            "models_visible": sorted(visible_models),
            "tests": {},
        }

        for model in models:
            results = []
            for run_index in range(args.runs):
                result = generate_once(base_url, api_key, model, args.prompt, args.timeout)
                result["run"] = run_index + 1
                results.append(result)
                if run_index + 1 < args.runs:
                    time.sleep(args.delay)
            key_report["tests"][model] = {
                "visible_in_list_models": model in visible_models,
                "summary": summarize(results),
                "runs": results,
            }
        diagnostics["keys"].append(key_report)

    if args.json:
        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(f"Gemini base URL: {base_url}")
        for key_report in diagnostics["keys"]:
            print()
            print(f"API key #{key_report['key_index']}: {key_report['api_key']}")
            list_info = key_report["list_models"]
            print(
                "list_models: "
                f"HTTP {list_info['status']}, {list_info['model_count']} models, {list_info['elapsed_sec']}s"
            )
            if list_info["error"]:
                print(f"list_models error: {list_info['error']}")

            for model, report in key_report["tests"].items():
                summary = report["summary"]
                visible = "yes" if report["visible_in_list_models"] else "no"
                print()
                print(f"[{model}] visible={visible}")
                print(f"  ok={summary['ok']}/{summary['runs']} failed={summary['failed']}")
                if "latency_median_sec" in summary:
                    print(
                        "  latency: "
                        f"min={summary['latency_min_sec']}s "
                        f"median={summary['latency_median_sec']}s "
                        f"max={summary['latency_max_sec']}s"
                    )
                if summary["errors"]:
                    print("  errors:")
                    for error, count in summary["errors"].items():
                        print(f"    x{count} {error}")

    failed = any(
        report["summary"]["failed"]
        for key_report in diagnostics["keys"]
        for report in key_report["tests"].values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
