#!/usr/bin/env python3
"""
为阅读题补充题目 — 每篇文章至少5道题
- 读取现有阅读数据，找出不足5题的文章
- 调用 AI 为每篇文章补充题目
- 逐篇生成、审核、写盘
- 只处理 N2
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
# API 基础设施（复用 generate_bank.py 的逻辑）
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

def extract_json(text):
    if not text or text.startswith("ERROR"):
        return None
    text = text.strip()
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
        return json.loads(text[start:end+1])
    except json.JSONDecodeError:
        pass
    return None

# ============================================================
# Prompt 构建
# ============================================================

def build_generate_prompt(passage, existing_questions, need_count, section_id):
    """为一篇阅读文章生成新题目。"""
    existing_qs = []
    for entry in existing_questions:
        # 每个 entry 可能有嵌套的 questions 数组
        sub_qs = entry.get("questions", [])
        if sub_qs:
            for sq in sub_qs:
                q_text = sq.get("question", "")
                if q_text:
                    existing_qs.append(f"- {q_text}")
        else:
            # 兼容扁平结构
            q_text = entry.get("question", "")
            if q_text:
                existing_qs.append(f"- {q_text}")
    existing_list = "\n".join(existing_qs) if existing_qs else "（无）"

    if section_id == "reading_short":
        desc = "短文読解（100-200字の短文、作者の意見や主張を問う）"
    elif section_id == "reading_medium":
        desc = "中文読解（300-400字の文章、筆者の論点を問う）"
    elif section_id == "reading_long":
        desc = "長文読解（500-700字の長文、深い理解と推理を問う）"
    elif section_id == "reading_search":
        desc = "情報検索（案内・時刻表・公告など実用文から情報を検索する）"
    else:
        desc = "読解"

    return f"""你是一位JLPT N2出题专家。请为以下日语阅读文章补充{need_count}道新题目。

【题型说明】{desc}

【文章】
{passage}

【已有题目（不能重复）】
{existing_list}

【出题要求】
1. 每道题必须基于文章内容，考查不同的信息点或理解角度
2. 4个选项中只有1个正确
3. 干扰项设计：部分正确但不完整、与原文意思相反、文中未提及
4. 难度：严格N2级别
5. 禁止与已有题目重复

【输出格式】严格输出JSON数组：
[
  {{
    "question": "问题",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": 0,
    "explanation": "中文详细解析。要求包含：1)正确答案在原文中的具体依据 2)每个干扰项为什么错 3)解题思路"
  }}
]

只输出JSON数组，不要其他内容。"""

def build_review_prompt(question_json):
    """审核一道阅读题。"""
    return f"""你是一位JLPT N2审题专家。请审核以下阅读题目是否合格。

【审核标准——只审核致命问题】
致命问题（任一则 rejected）：
1. answer 索引与正确答案不匹配
2. 四个选项中有两个完全相同
3. 题目或选项有语法错误
4. 正确答案不在选项中
5. 题目与文章内容无关

非致命问题（不影响 approved）：
- 解释不够详细
- 干扰项不够巧妙
- 题目表述略有不自然

请宽松审核，优先通过。

【题目】
{question_json}

严格输出JSON格式：
{{
  "approved": true或false,
  "issues": ["问题列表（如通过则为空数组）"]
}}"""

# ============================================================
# 数据处理
# ============================================================

def group_by_passage(questions):
    """按文章分组，返回 [(passage, [questions])] 列表。"""
    groups = []
    passage_map = {}
    for q in questions:
        p = q.get("passage", "")
        if p not in passage_map:
            passage_map[p] = len(groups)
            groups.append((p, []))
        groups[passage_map[p]][1].append(q)
    return groups

def save_reading_data(filepath, questions):
    """保存阅读数据到文件。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["questions"] = questions
    # 计算实际题目数（嵌套的 questions 数组）
    total = 0
    for entry in questions:
        sub = entry.get("questions", [])
        total += len(sub) if sub else 1
    data["meta"]["count"] = total
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 主逻辑
# ============================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(base_dir, ".env"))
    cfg = load_config(os.path.join(base_dir, "config.json"))
    data_dir = os.path.join(base_dir, "data", "n2")
    timeout = cfg.get("pipeline", {}).get("timeout", 120)
    min_questions = 5  # 每篇文章至少5道题

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

    if len(available) < 2:
        print(f"[FATAL] 至少需要 2 个可用模型（1 生成 + 1 审核），当前只有 {len(available)} 个")
        sys.exit(1)

    provider_ids = list(available.keys())
    print(f"\n可用模型: {', '.join(provider_ids)}")
    print(f"目标: 每篇文章至少 {min_questions} 道题\n")

    reading_files = ['reading_short', 'reading_medium', 'reading_long', 'reading_search']
    provider_idx = 0
    total_generated = 0
    total_failed = 0

    for fname in reading_files:
        filepath = os.path.join(data_dir, f"{fname}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = data["questions"]
        groups = group_by_passage(questions)

        print(f"\n{'='*50}")
        print(f"[{fname}] {len(groups)} 篇文章, {len(questions)} 道题")

        # 找出需要补充的文章
        need_work = []
        for passage, qs in groups:
            # 计算实际题目数（嵌套的 questions 数组）
            actual_count = 0
            for entry in qs:
                sub = entry.get("questions", [])
                if sub:
                    actual_count += len(sub)
                else:
                    actual_count += 1
            if actual_count < min_questions:
                need_work.append((passage, qs, min_questions - actual_count))

        if not need_work:
            print(f"  全部已满 {min_questions} 题，跳过")
            continue

        print(f"  需要补充: {len(need_work)} 篇文章, 共 {sum(n for _, _, n in need_work)} 道新题\n")

        for passage, existing_qs, need_count in need_work:
            short_passage = passage[:40].replace('\n', ' ')
            actual = sum(len(e.get("questions", [])) or 1 for e in existing_qs)
            print(f"  [{short_passage}...] 已有{actual}题, 需补{need_count}题")

            # 1. 生成新题
            gen_provider = available[provider_ids[provider_idx % len(provider_ids)]]
            provider_idx += 1

            prompt = build_generate_prompt(passage, existing_qs, need_count, fname)
            print(f"    [{gen_provider['id']}] 生成中...", end="", flush=True)
            raw = call_api(gen_provider, prompt, timeout=timeout)

            if not raw or raw.startswith("ERROR"):
                print(f" ✗ ({raw[:50] if raw else 'empty'})")
                total_failed += need_count
                continue

            new_items = extract_json(raw)
            if not new_items or len(new_items) < 1:
                print(f" ✗ (JSON解析失败)")
                total_failed += need_count
                continue

            # 只取需要的数量
            new_items = new_items[:need_count]
            print(f" ✓ 生成{len(new_items)}题")

            # 2. 审核
            rev_provider = available[provider_ids[provider_idx % len(provider_ids)]]
            provider_idx += 1

            approved_items = []
            for item in new_items:
                q_str = json.dumps(item, ensure_ascii=False, indent=2)
                review_prompt = build_review_prompt(q_str)

                print(f"    [{rev_provider['id']}] 审核...", end="", flush=True)
                review_raw = call_api(rev_provider, review_prompt, timeout=60)

                if review_raw and not review_raw.startswith("ERROR"):
                    # 提取JSON
                    text = review_raw.strip()
                    if "```" in text:
                        import re
                        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                        if m:
                            text = m.group(1).strip()
                    start = text.find("{")
                    end = text.rfind("}")
                    if start != -1 and end != -1:
                        try:
                            result = json.loads(text[start:end+1])
                            if result.get("approved", False):
                                approved_items.append(item)
                                print(f" ✓")
                            else:
                                print(f" ✗ (未通过: {result.get('issues', ['unknown'])})")
                        except json.JSONDecodeError:
                            print(f" ✗ (JSON解析失败)")
                    else:
                        print(f" ✗ (无JSON)")
                else:
                    print(f" ✗ (API失败)")

                time.sleep(0.5)

            # 3. 追加到数据
            if approved_items:
                # 找到对应 passage 的条目，把新题追加到它的 questions 数组
                target_entry = None
                for entry in questions:
                    if entry.get("passage", "") == passage:
                        target_entry = entry
                        break

                if target_entry:
                    # 追加到已有条目的 questions 数组
                    if "questions" not in target_entry:
                        target_entry["questions"] = []
                    for item in approved_items:
                        target_entry["questions"].append({
                            "question": item.get("question", ""),
                            "options": item.get("options", []),
                            "answer": item.get("answer", 0),
                            "explanation": item.get("explanation", ""),
                        })
                        total_generated += 1
                else:
                    # 创建新条目
                    new_entry = {
                        "id": f"n2-{fname}-{len(questions)+1:03d}",
                        "level": "N2",
                        "question_type": fname,
                        "source": "ai",
                        "passage": passage,
                        "questions": [],
                        "generated_by": "ai",
                        "verified": True,
                    }
                    for item in approved_items:
                        new_entry["questions"].append({
                            "question": item.get("question", ""),
                            "options": item.get("options", []),
                            "answer": item.get("answer", 0),
                            "explanation": item.get("explanation", ""),
                        })
                        total_generated += 1
                    questions.append(new_entry)

                # 每篇处理完立即写盘
                save_reading_data(filepath, questions)
                print(f"    入库: {len(approved_items)} 题 (已写盘)")
            else:
                print(f"    无题目通过审核")
                total_failed += need_count

            time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"生成完成!")
    print(f"  成功: {total_generated} 道新题")
    print(f"  失败: {total_failed} 道")
    print(f"\n各文件最终题目数:")
    for fname in reading_files:
        filepath = os.path.join(data_dir, f"{fname}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data["questions"]
        total_q = 0
        for entry in entries:
            sub = entry.get("questions", [])
            total_q += len(sub) if sub else 1
        print(f"  {fname}: {total_q} 题, {len(entries)} 篇文章")


if __name__ == "__main__":
    main()
