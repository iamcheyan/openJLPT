#!/usr/bin/env python3
"""
修复阅读题翻译 — 逐条翻译（不批量），确保顺序正确
"""

import json
import os
import sys
import time
import random
import urllib.request
import urllib.error

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

def resolve_provider(provider_id, provider_cfg, env):
    if provider_cfg.get("enabled") is False:
        return None
    api_key_envs = provider_cfg.get("api_key_envs") or [provider_cfg.get("api_key_env", "")]
    api_key_envs = [e for e in api_key_envs if e]
    api_keys = []
    for env_name in api_key_envs:
        api_key = env.get(env_name, "")
        if api_key:
            api_keys.append({"env": env_name, "key": api_key})
    base_url = env.get(provider_cfg["base_url_env"], "")
    if not api_keys or not base_url:
        return None
    model = provider_cfg.get("model", "")
    if "model_env" in provider_cfg:
        model = env.get(provider_cfg["model_env"], model)
    return {
        "id": provider_id,
        "url": base_url,
        "api_key": api_keys[0]["key"],
        "api_keys": api_keys,
        "api_key_index": 0,
        "model": model,
        "format": provider_cfg.get("format", "openai"),
    }

def call_gemini_api(provider, prompt, api_key, timeout=120):
    url = f"{provider['url'].rstrip('/')}/models/{provider['model']}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return f"ERROR: No candidates"
    except urllib.error.HTTPError as e:
        return f"ERROR: HTTP {e.code}"
    except Exception as e:
        return f"ERROR: {e}"

def call_openai_api(provider, prompt, api_key, timeout=120):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": provider["model"],
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(provider["url"], data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        return f"ERROR: HTTP {e.code} - {body}"
    except Exception as e:
        return f"ERROR: {e}"

def call_api(provider, prompt, timeout=60):
    fmt = provider.get("format", "openai")
    api_keys = provider.get("api_keys") or [{"key": provider["api_key"]}]
    start = provider.get("api_key_index", 0) % len(api_keys)
    provider["api_key_index"] = (start + 1) % len(api_keys)
    key_entry = api_keys[start]
    if fmt == "gemini":
        return call_gemini_api(provider, prompt, key_entry["key"], timeout)
    else:
        return call_openai_api(provider, prompt, key_entry["key"], timeout)

def check_provider(provider, timeout=15):
    result = call_api(provider, "hi", timeout=timeout)
    if result.startswith("ERROR"):
        return False, result
    return True, ""

def translate_one(provider, passage, timeout=60):
    """逐条翻译一篇阅读文章。"""
    prompt = f"""这是一份JLPT日语考试的阅读材料。请按以下要求翻译：

【翻译要求】
1. 逐句完整翻译全文，一字一词都不要省略
2. 忠实原文语义，不要改写、概括或添加任何原文没有的内容
3. 保持原文的段落结构和格式（如■、・等符号保留）

【附加解析】
翻译完成后，请在末尾附上以下内容（用"---"分隔）：

【重点语法】
列出文中出现的N2级别语法点，简要说明接续和含义（2-4个即可）

【重点词汇】
列出文中值得记忆的词汇，标注读音和词义（3-5个即可）

以下是原文：
{passage}

请直接输出翻译和解析，不要加其他前缀。"""
    return call_api(provider, prompt, timeout=timeout)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(base_dir, ".env"))
    cfg = load_config(os.path.join(base_dir, "config.json"))
    data_dir = os.path.join(base_dir, "data", "n2")
    timeout = cfg.get("pipeline", {}).get("timeout", 60)

    # 解析可用提供商
    candidates = {}
    for pid, pc in cfg["providers"].items():
        resolved = resolve_provider(pid, pc, env)
        if resolved:
            candidates[pid] = resolved

    print("检测模型可用性...")
    available = {}
    for pid, provider in candidates.items():
        ok, err = check_provider(provider, timeout=15)
        if ok:
            available[pid] = provider
            print(f"  ✓ {pid}")
        else:
            print(f"  ✗ {pid} — {err[:80]}")

    if not available:
        print("[FATAL] 没有可用的 API 模型")
        sys.exit(1)

    provider_ids = list(available.keys())
    print(f"\n可用模型: {', '.join(provider_ids)}")

    reading_files = ['reading_search', 'reading_short', 'reading_medium', 'reading_long']
    provider_idx = 0
    total_fixed = 0
    total_failed = 0

    for fname in reading_files:
        filepath = os.path.join(data_dir, f"{fname}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = data["questions"]
        need_fix = []

        for i, q in enumerate(questions):
            passage = q.get("passage", "")
            trans = q.get("translation", "")
            if not passage:
                continue
            # 翻译为空或错位都需要修复
            if not trans:
                need_fix.append(i)
            else:
                p_start = passage[:20]
                if p_start[:5] not in trans and passage.split('\n')[0][:10] not in trans:
                    need_fix.append(i)

        if not need_fix:
            print(f"\n[{fname}] 全部正确，跳过")
            continue

        print(f"\n[{fname}] {len(need_fix)}/{len(questions)} 条翻译错位，逐条修复")

        for idx in need_fix:
            q = questions[idx]
            passage = q.get("passage", "")

            provider = available[provider_ids[provider_idx % len(provider_ids)]]
            provider_idx += 1

            print(f"  [{provider['id']}] 翻译 #{idx}...", end="", flush=True)
            result = translate_one(provider, passage, timeout=timeout)

            if result and not result.startswith("ERROR"):
                # 清理 markdown 代码块
                result = result.strip()
                if result.startswith("```"):
                    lines = result.split('\n')
                    result = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                questions[idx]["translation"] = result.strip()
                total_fixed += 1
                print(f" ✓")
            else:
                total_failed += 1
                print(f" ✗ ({result[:50] if result else 'empty'})")

            time.sleep(0.5)

        # 每个文件修完立即写盘
        data["questions"] = questions
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [{fname}] 已保存")

    print(f"\n{'='*50}")
    print(f"修复完成!")
    print(f"  成功: {total_fixed} 条")
    print(f"  失败: {total_failed} 条")

if __name__ == "__main__":
    main()
