#!/usr/bin/env python3
"""Enhanced test script for multiple LLM providers."""

import json
import urllib.request
import urllib.error
import os


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


def test_openai_compatible(name, api_key, base_url, model):
    """Generic test for OpenAI-compatible APIs."""
    print()
    print("=" * 50)
    print(f"[{name}]")
    print("=" * 50)

    # Simple path handling: ensure /chat/completions is there if not provided
    actual_url = base_url
    if not actual_url.endswith("/chat/completions") and "generativelanguage" not in actual_url:
        actual_url = actual_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Hi, 1 sentence intro."}]
    }).encode("utf-8")

    req = urllib.request.Request(actual_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            print(f"  URL:     {actual_url}")
            print(f"  Model:   {result.get('model', model)}")
            print(f"  Reply:   {content[:100]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  URL:     {actual_url}")
        print(f"  Status:  FAIL (HTTP {e.code})")
        print(f"  Error:   {body[:500]}")
        return False
    except Exception as e:
        print(f"  Status:  FAIL")
        print(f"  Error:   {e}")
        return False


def test_gemini(api_key, base_url):
    """Test Google Gemini API (REST v1beta)."""
    print()
    print("=" * 50)
    print("[Google Gemini]")
    print("=" * 50)

    model = "gemini-2.0-flash"
    # Ensure v1beta or similar is in URL
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "contents": [{"parts": [{"text": "Hi, 1 sentence intro."}]}]
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "candidates" in result:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  Model:   {model}")
                print(f"  Reply:   {content.strip()[:100]}")
                return True
            else:
                print(f"  Status:  FAIL")
                print(f"  Response: {result}")
                return False
    except Exception as e:
        print(f"  Status:  FAIL")
        print(f"  Error:   {e}")
        return False


def test_ark(api_key, base_url):
    """Test Volcengine ARK."""
    print()
    print("=" * 50)
    print("[Volcengine ARK]")
    print("=" * 50)

    # Try standard model names
    models = ["doubao-seed-2-0-pro-260215", "doubao-pro-32k"]

    for model in models:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}]
        }).encode("utf-8")
        req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                print(f"  [OK]   {model} -> {content[:50]}")
                return True
        except Exception:
            continue
    print("  Status: FAIL (All models failed)")
    return False


if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)

    results = {}

    # Providers
    configs = [
        ("ZhipuAI", "ZHIPU_API_KEY", "ZHIPU_BASE_URL", "glm-4-flash"),
        ("ARK", "ARK_API_KEY", "ARK_BASE_URL", "doubao-seed-2-0-pro-260215"),
        ("MiMo", "MIMO_API_KEY", "MIMO_BASE_URL", env.get("MIMO_MODEL", "mimo-v2.5-pro")),
        ("Kimi 1", "KIMI_API_KEY", "KIMI_BASE_URL", "kimi-for-coding"),
        ("Kimi 2 (C2K)", "KIMI_API_KEY_2", "KIMI_BASE_URL_2", "kimi-for-coding"),
        ("NVIDIA", "NVIDIA_API_KEY", "NVIDIA_BASE_URL", "qwen/qwen2.5-coder-32b-instruct"),
        ("OpenRouter", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "moonshotai/kimi-k2.5")
    ]

    for name, key_name, url_name, model in configs:
        if key_name in env and url_name in env:
            if name == "ARK":
                results[name] = test_ark(env[key_name], env[url_name])
            else:
                results[name] = test_openai_compatible(name, env[key_name], env[url_name], model)

    if "GEMINI_API_KEY" in env:
        results["Gemini"] = test_gemini(env["GEMINI_API_KEY"], env["GEMINI_BASE_URL"])

    print()
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    for name, ok in results.items():
        print(f"  {name:<20}: {'PASS' if ok else 'FAIL'}")
