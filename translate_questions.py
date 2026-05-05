#!/usr/bin/env python3
"""
批量翻译脚本 — 为所有缺少 translation 字段的题目补充中文翻译
- 从 config.json / .env 读取 API 配置
- 自动检测可用模型，轮循使用
- 每处理一条立即写盘（防中断丢失）
- 支持断点续翻（跳过已有 translation 的条目）
"""

import json
import os
import sys
import time
import random
import urllib.request
import urllib.error
from datetime import datetime

# ============================================================
# 复用 generate_bank.py 的基础设施
# ============================================================

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
        "label": provider_cfg.get("label", provider_id),
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


# ============================================================
# 翻译 prompt 构建
# ============================================================

def build_translate_prompt(questions, section_id):
    """根据题型构建批量翻译 prompt。"""
    lines = []
    for i, q in enumerate(questions):
        if section_id in ("reading_short", "reading_medium", "reading_long", "reading_search"):
            # 阅读题：翻译文章段落
            passage = q.get("passage", q.get("sentence", ""))
            lines.append(f"{i+1}. {passage}")
        elif section_id == "grammar_passage":
            passage = q.get("passage", "")
            lines.append(f"{i+1}. {passage}")
        elif section_id in ("vocab_context", "vocab_compound", "grammar_fill", "grammar_order"):
            # 填空/排序题：翻译句子
            sentence = q.get("sentence", "")
            lines.append(f"{i+1}. {sentence}")
        elif section_id == "vocab_usage":
            # 用法题：翻译目标词和选项句子
            target = q.get("target", "")
            opts = q.get("options", [])
            lines.append(f"{i+1}. 目标词：{target}")
            for j, opt in enumerate(opts):
                lines.append(f"   选项{j+1}：{opt}")
        elif section_id in ("vocab_reading", "vocab_kanji", "vocab_synonym"):
            # 读音/汉字/类义题：翻译例句
            sentence = q.get("sentence", "")
            target = q.get("target", "")
            lines.append(f"{i+1}. 目标词：{target}，例句：{sentence}")
        else:
            sentence = q.get("sentence", q.get("passage", ""))
            lines.append(f"{i+1}. {sentence}")

    item_list = "\n".join(lines)

    is_reading = section_id.startswith("reading_") or section_id == "grammar_passage"

    if is_reading:
        return f"""这是一份JLPT日语考试的阅读材料。请按以下要求翻译：

【翻译要求】
1. 逐句完整翻译全文，一字一词都不要省略
2. 忠实原文语义，不要改写、概括或添加任何原文没有的内容
3. 保持原文的段落结构和格式（如■、・等符号保留）

【附加解析】
翻译完成后，在末尾附上以下内容（用"---"分隔）：
- 【重点语法】：列出文中N2语法点，简要说明接续和含义（2-4个）
- 【重点词汇】：列出值得记忆的词汇，标注读音和词义（3-5个）

{item_list}

严格按JSON数组格式输出，每个元素是一篇文章的完整翻译+解析，顺序与上面一致：
["翻译+解析1", "翻译+解析2", ...]

只输出JSON数组，不要其他内容。"""
    else:
        return f"""请将以下日语内容翻译成中文。要求完整翻译，不要省略。

{item_list}

严格按JSON数组格式输出，每个元素是一个翻译字符串，顺序与上面一致：
["翻译1", "翻译2", ...]

只输出JSON数组，不要其他内容。"""


# ============================================================
# 主逻辑
# ============================================================

def translate_batch(provider, questions, section_id, timeout=60):
    """翻译一批题目，返回翻译列表或 None。"""
    prompt = build_translate_prompt(questions, section_id)
    raw = call_api(provider, prompt, timeout=timeout)
    if not raw or raw.startswith("ERROR"):
        return None
    # 提取 JSON 数组
    text = raw.strip()
    if "```" in text:
        import re
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if m:
            text = m.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return None
    try:
        result = json.loads(text[start:end+1])
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    return None


def save_question_translation(filepath, q_index, translation):
    """给指定文件的指定题目写入 translation 字段（立即落盘）。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    if q_index >= len(questions):
        return
    questions[q_index]["translation"] = translation
    data["questions"] = questions
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def count_missing(filepath):
    """统计文件中缺少 translation 的题目数。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    missing = []
    for i, q in enumerate(questions):
        if not q.get("translation"):
            missing.append(i)
    return missing, len(questions)


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

    # 健康检查
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

    # 扫描所有文件的缺失情况
    files_to_translate = []
    total_missing = 0
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith(".json"):
            continue
        filepath = os.path.join(data_dir, fname)
        section_id = fname.replace(".json", "")
        try:
            missing, total = count_missing(filepath)
        except Exception:
            continue
        if missing:
            files_to_translate.append((section_id, filepath, missing, total))
            total_missing += len(missing)
            print(f"  {section_id}: {len(missing)}/{total} 缺翻译")

    if not files_to_translate:
        print("\n所有题目都已有翻译，无需处理。")
        return

    print(f"\n共 {total_missing} 条需要翻译")
    print("=" * 50)

    # 轮循翻译
    provider_idx = 0
    translated_total = 0
    failed_total = 0
    start_time = time.time()

    for section_id, filepath, missing_indices, total in files_to_translate:
        print(f"\n[{section_id}] {len(missing_indices)}/{total} 缺翻译")

        # 读取题目
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        questions = data["questions"]

        batch_size = 5  # 每批翻译 5 条
        i = 0
        while i < len(missing_indices):
            batch_indices = missing_indices[i:i+batch_size]
            batch_questions = [questions[idx] for idx in batch_indices]

            # 轮循选模型
            provider = available[provider_ids[provider_idx % len(provider_ids)]]
            provider_idx += 1

            print(f"  [{provider['id']}] 翻译 {i+1}-{min(i+batch_size, len(missing_indices))}/{len(missing_indices)}...", end="", flush=True)
            translations = translate_batch(provider, batch_questions, section_id, timeout=timeout)

            if translations and len(translations) >= len(batch_indices):
                # 逐条写盘
                for j, idx in enumerate(batch_indices):
                    trans = translations[j].strip() if j < len(translations) else ""
                    if trans:
                        save_question_translation(filepath, idx, trans)
                        translated_total += 1
                    else:
                        failed_total += 1
                print(f" ✓")
            else:
                failed_total += len(batch_indices)
                print(f" ✗ (模型返回异常)")

            i += batch_size
            time.sleep(0.5)  # 避免触发限流

    elapsed = time.time() - start_time
    print(f"\n{'=' * 50}")
    print(f"翻译完成!")
    print(f"  成功: {translated_total} 条")
    print(f"  失败: {failed_total} 条")
    print(f"  耗时: {elapsed:.0f} 秒")


if __name__ == "__main__":
    main()
