#!/usr/bin/env python3
"""Test all configured LLM providers from config.json."""

import json
import urllib.request
import urllib.error
import os
import sys


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_provider(pid, pc, env):
    """从 config + env 解析出 provider 配置，缺失则返回 None。"""
    api_key = env.get(pc.get("api_key_env", ""), "")
    base_url = env.get(pc.get("base_url_env", ""), "")
    if not api_key or not base_url:
        return None

    # 支持多 key
    api_keys_env = pc.get("api_key_envs", [])
    api_keys = [env[k] for k in api_keys_env if env.get(k)]
    if not api_keys:
        api_keys = [api_key]

    model = env.get(pc.get("model_env", ""), pc.get("model", ""))
    fmt = pc.get("format", "openai")

    return {
        "id": pid,
        "label": pc.get("label", pid),
        "api_key": api_keys[0],
        "api_keys": api_keys,
        "base_url": base_url,
        "model": model,
        "format": fmt,
        "enabled": pc.get("enabled", True),
    }


def test_openai_compatible(label, api_key, base_url, model):
    """Test OpenAI-compatible API."""
    actual_url = base_url.rstrip("/")
    if not actual_url.endswith("/chat/completions"):
        actual_url += "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Hi, reply with one sentence."}],
        "max_tokens": 50,
    }).encode("utf-8")

    req = urllib.request.Request(actual_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            print(f"  Model: {result.get('model', model)}")
            print(f"  Reply: {content.strip()[:100]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:300]}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_gemini(label, api_key, base_url, model):
    """Test Gemini REST API."""
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "contents": [{"parts": [{"text": "Hi, reply with one sentence."}]}]
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"  Model: {model}")
            print(f"  Reply: {content.strip()[:100]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:300]}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(base_dir, ".env"))
    cfg = load_config(os.path.join(base_dir, "config.json"))

    providers = cfg.get("providers", {})
    results = {}

    for pid, pc in providers.items():
        if pc.get("enabled") is False:
            print(f"\n[{pc.get('label', pid)}] SKIPPED (disabled)")
            continue

        provider = resolve_provider(pid, pc, env)
        if not provider:
            missing = []
            if not env.get(pc.get("api_key_env", "")):
                missing.append(pc["api_key_env"])
            if not env.get(pc.get("base_url_env", "")):
                missing.append(pc["base_url_env"])
            print(f"\n[{pc.get('label', pid)}] SKIPPED (missing: {', '.join(missing)})")
            continue

        label = provider["label"]
        print(f"\n{'=' * 50}")
        print(f"[{label}]")
        print(f"{'=' * 50}")

        if provider["format"] == "gemini":
            ok = test_gemini(label, provider["api_key"], provider["base_url"], provider["model"])
        else:
            ok = test_openai_compatible(label, provider["api_key"], provider["base_url"], provider["model"])

        results[label] = ok

    print(f"\n{'=' * 50}")
    print("Summary")
    print(f"{'=' * 50}")
    for name, ok in results.items():
        print(f"  {name:<20}: {'PASS' if ok else 'FAIL'}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {passed}/{total} passed")
    sys.exit(0 if passed > 0 else 1)
