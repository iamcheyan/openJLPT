#!/usr/bin/env python3
"""Test script for ZhipuAI, Volcengine ARK, and Xiaomi MiMo API keys."""

import json
import urllib.request
import urllib.error
import os


def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env


def test_zhipu(api_key, base_url):
    """Test ZhipuAI GLM API."""
    print("=" * 50)
    print("[1] ZhipuAI (GLM)")
    print("=" * 50)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "model": "glm-4-flash",
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍自己。"}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            print(f"  API Key: ...{api_key[-8:]}")
            print(f"  Status:  OK")
            print(f"  Model:   {result.get('model', 'unknown')}")
            print(f"  Reply:   {content[:100]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  API Key: ...{api_key[-8:]}")
        print(f"  Status:  FAIL (HTTP {e.code})")
        print(f"  Error:   {body[:200]}")
        return False
    except Exception as e:
        print(f"  Status:  FAIL")
        print(f"  Error:   {e}")
        return False


def test_ark(api_key, base_url):
    """Test Volcengine ARK Coding Plan API."""
    print()
    print("=" * 50)
    print("[2] Volcengine ARK (Coding Plan)")
    print("=" * 50)

    print(f"  API Key: ...{api_key[-8:]}")
    print(f"  Endpoint: {base_url}")
    print()

    # Coding Plan supported models
    models = [
        "doubao-seed-2-0-pro-260215",
        "doubao-seed-2-0-lite-260215",
        "doubao-seed-2-0-mini-260215",
        "deepseek-v3-2-251201",
        "glm-4-7-251222",
    ]

    for model in models:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "你好"}]
        }).encode("utf-8")
        req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                print(f"  [OK]   {model}")
                print(f"         Reply: {content[:80]}")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                err = json.loads(body)
                code = err.get("error", {}).get("code", "")
            except:
                code = str(e.code)
            print(f"  [FAIL] {model} ({code})")
        except Exception as e:
            print(f"  [FAIL] {model} ({e})")

    return False


def test_mimo(api_key, base_url, model):
    """Test Xiaomi MiMo API (OpenAI-compatible)."""
    print()
    print("=" * 50)
    print("[3] Xiaomi MiMo")
    print("=" * 50)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "model": model,
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍自己。"}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            print(f"  API Key: ...{api_key[-8:]}")
            print(f"  Status:  OK")
            print(f"  Model:   {result.get('model', model)}")
            print(f"  Reply:   {content[:100]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  API Key: ...{api_key[-8:]}")
        print(f"  Status:  FAIL (HTTP {e.code})")
        print(f"  Error:   {body[:200]}")
        return False
    except Exception as e:
        print(f"  Status:  FAIL")
        print(f"  Error:   {e}")
        return False


if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)

    r1 = test_zhipu(env["ZHIPU_API_KEY"], env["ZHIPU_BASE_URL"])
    r2 = test_ark(env["ARK_API_KEY"], env["ARK_BASE_URL"])
    r3 = test_mimo(env["MIMO_API_KEY"], env["MIMO_BASE_URL"], env["MIMO_MODEL"])

    print()
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"  [1] ZhipuAI (GLM):        {'PASS' if r1 else 'FAIL'}")
    print(f"  [2] ARK (Coding Plan):    {'PASS' if r2 else 'FAIL'}")
    print(f"  [3] MiMo (Xiaomi):        {'PASS' if r3 else 'FAIL'}")
