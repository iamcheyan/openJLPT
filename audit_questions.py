#!/usr/bin/env python3
"""
题目审核工具 — 多模型投票验证 + 自动修复
- 多个 AI 模型独立审核每道题
- 多数通过 → 标记 verified_by_audit: true
- 多数不通过 → 多模型协商修复 → 再审核
- 每道题处理完立即写盘
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
# API 基础设施
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

def extract_json_object(text):
    if not text or text.startswith("ERROR"):
        return None
    text = text.strip()
    if "```" in text:
        import re
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if m:
            text = m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end+1])
    except json.JSONDecodeError:
        pass
    return None

def extract_json_array(text):
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

def get_question_text(q, section_id):
    """获取题目的完整文本（用于审核上下文）。"""
    parts = []
    if q.get("passage"):
        parts.append(f"【文章】\n{q['passage']}")
    if q.get("sentence"):
        parts.append(f"【句子】{q['sentence']}")
    if q.get("target"):
        parts.append(f"【目标词】{q['target']}")
    if q.get("question"):
        parts.append(f"【问题】{q['question']}")
    if q.get("options"):
        for i, opt in enumerate(q["options"]):
            parts.append(f"  选项{i+1}：{opt}")
    ans = q.get("answer", 0)
    if q.get("options") and ans < len(q["options"]):
        parts.append(f"【标记的答案】选项{ans+1}（{q['options'][ans]}）")
    if q.get("explanation"):
        parts.append(f"【解析】{q['explanation'][:200]}")
    return "\n".join(parts)

def build_audit_prompt(q, section_id):
    """构建审核 prompt — 让模型判断答案是否正确。"""
    q_text = get_question_text(q, section_id)

    return f"""你是一位JLPT N2审题专家。请仔细审核以下题目的**答案是否正确**。

{q_text}

【审核任务】
1. 仔细阅读题目和所有选项
2. 判断标记的答案是否真的是正确答案
3. 如果你认为正确答案不是标记的那个，请指出你认为正确的选项

请严格输出以下JSON格式：
{{
  "correct": true或false,
  "my_answer": 你认为正确的选项编号(0-3),
  "reason": "简要中文说明为什么这个答案是对的/错的"
}}

只输出JSON，不要其他内容。"""

def build_fix_prompt(q, section_id, audit_results):
    """构建修复 prompt — 根据审核结果修复题目。"""
    q_text = get_question_text(q, section_id)

    votes = []
    for r in audit_results:
        votes.append(f"- {r['provider']}: 答案{'正确' if r['correct'] else '错误'}，认为正确答案是选项{r['my_answer']+1}，理由：{r['reason']}")
    votes_text = "\n".join(votes)

    return f"""你是一位JLPT N2出题专家。以下题目被多位审核专家判定为答案有误，请修复。

【原题】
{q_text}

【审核专家意见】
{votes_text}

【修复要求】
1. 根据专家意见，修正 answer 字段为正确的选项编号(0-3)
2. 修正 explanation 使其准确解释为什么该选项正确
3. 如果题目本身有问题（如选项不合理），可以微调选项，但尽量保持原题意
4. 如果题目完全没有问题（专家意见分歧），保持原样

请严格输出修复后的完整题目JSON：
{{
  "answer": 修正后的答案编号(0-3),
  "explanation": "修正后的中文解析",
  "options": ["选项1", "选项2", "选项3", "选项4"],
  "fixed": true或false
}}

只输出JSON，不要其他内容。"""

# ============================================================
# 主逻辑
# ============================================================

def audit_question(q, section_id, available, provider_ids, provider_idx):
    """审核一道题。返回 (passed, fixed_q, provider_idx)。"""
    # 收集所有模型的审核意见
    audit_results = []
    voter_count = min(3, len(available))  # 最多3个模型投票

    voters = []
    for i in range(voter_count):
        pid = provider_ids[(provider_idx + i) % len(provider_ids)]
        voters.append(available[pid])
    provider_idx += voter_count

    for voter in voters:
        prompt = build_audit_prompt(q, section_id)
        raw = call_api(voter, prompt, timeout=60)
        result = extract_json_object(raw)
        if result and "correct" in result:
            audit_results.append({
                "provider": voter["id"],
                "correct": result["correct"],
                "my_answer": result.get("my_answer", q.get("answer", 0)),
                "reason": result.get("reason", ""),
            })
        time.sleep(0.3)

    if not audit_results:
        return None, q, provider_idx  # 审核失败

    # 投票
    correct_votes = sum(1 for r in audit_results if r["correct"])
    total_votes = len(audit_results)
    majority = total_votes // 2 + 1

    if correct_votes >= majority:
        # 多数认为正确
        return True, q, provider_idx
    else:
        # 多数认为错误，尝试修复
        return False, q, provider_idx, audit_results

def fix_question(q, section_id, audit_results, available, provider_ids, provider_idx):
    """修复一道题。返回 (fixed_q, success, provider_idx)。"""
    # 用一个模型来修复
    fixer_id = provider_ids[provider_idx % len(provider_ids)]
    fixer = available[fixer_id]
    provider_idx += 1

    prompt = build_fix_prompt(q, section_id, audit_results)
    raw = call_api(fixer, prompt, timeout=60)
    result = extract_json_object(raw)

    if not result:
        return q, False, provider_idx

    # 应用修复
    fixed_q = dict(q)
    if "answer" in result and isinstance(result["answer"], int):
        fixed_q["answer"] = result["answer"]
    if "explanation" in result:
        fixed_q["explanation"] = result["explanation"]
    if "options" in result and isinstance(result["options"], list) and len(result["options"]) == 4:
        fixed_q["options"] = result["options"]

    return fixed_q, True, provider_idx

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(base_dir, ".env"))
    cfg = load_config(os.path.join(base_dir, "config.json"))
    data_dir = os.path.join(base_dir, "data", "n2")
    timeout = cfg.get("pipeline", {}).get("timeout", 120)

    # 解析参数
    import argparse
    parser = argparse.ArgumentParser(description="题目审核工具 — 多模型投票验证+修复")
    parser.add_argument("--files", nargs="*", help="指定要审核的文件（不含.json后缀）")
    parser.add_argument("--only-wrong", action="store_true", help="只审核标记为错误的题目")
    parser.add_argument("--sample", type=int, default=0, help="只随机抽样N道题审核（0=全部）")
    args = parser.parse_args()

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
        print(f"[FATAL] 至少需要 2 个可用模型，当前只有 {len(available)} 个")
        sys.exit(1)

    provider_ids = list(available.keys())
    print(f"\n可用模型: {', '.join(provider_ids)}")

    # 确定要审核的文件
    if args.files:
        file_list = [f if f.endswith('.json') else f"{f}.json" for f in args.files]
    else:
        file_list = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])

    print(f"审核文件: {', '.join(f.replace('.json','') for f in file_list)}")

    provider_idx = 0
    total_checked = 0
    total_passed = 0
    total_fixed = 0
    total_failed = 0

    for fname in file_list:
        filepath = os.path.join(data_dir, fname)
        if not os.path.exists(filepath):
            print(f"\n[SKIP] {fname}: 文件不存在")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = data.get("questions", [])
        section_id = fname.replace(".json", "")

        # 筛选要审核的题目
        if args.only_wrong:
            targets = [(i, q) for i, q in enumerate(questions) if not q.get("verified", True)]
        elif args.sample > 0:
            indices = random.sample(range(len(questions)), min(args.sample, len(questions)))
            targets = [(i, questions[i]) for i in sorted(indices)]
        else:
            targets = list(enumerate(questions))

        if not targets:
            print(f"\n[{section_id}] 无需审核的题目")
            continue

        print(f"\n{'='*50}")
        print(f"[{section_id}] {len(targets)}/{len(questions)} 道题待审核")

        section_passed = 0
        section_fixed = 0
        section_failed = 0

        for q_idx, q in targets:
            q_preview = (q.get("question") or q.get("sentence") or q.get("target") or "")[:30]
            print(f"\n  #{q_idx+1} [{q_preview}...]")

            # 第一轮：多模型投票
            audit_result = audit_question(q, section_id, available, provider_ids, provider_idx)
            passed = audit_result[0]
            provider_idx = audit_result[2]

            if passed is None:
                print(f"    审核失败（无响应）")
                section_failed += 1
                total_failed += 1
                total_checked += 1
                continue

            if passed:
                print(f"    ✓ 通过（{audit_result[0]}）")
                questions[q_idx]["verified_by_audit"] = True
                questions[q_idx]["audit_date"] = datetime.now().strftime("%Y-%m-%d")
                section_passed += 1
                total_passed += 1
            else:
                audit_results = audit_result[3]
                votes_summary = ", ".join(f"{r['provider']}:{'✓' if r['correct'] else '✗'}" for r in audit_results)
                print(f"    ✗ 未通过 [{votes_summary}]")

                # 第二轮：修复
                print(f"    修复中...", end="", flush=True)
                fixed_q, success, provider_idx = fix_question(
                    q, section_id, audit_results, available, provider_ids, provider_idx
                )

                if success:
                    questions[q_idx] = fixed_q
                    questions[q_idx]["verified_by_audit"] = True
                    questions[q_idx]["audit_fixed"] = True
                    questions[q_idx]["audit_date"] = datetime.now().strftime("%Y-%m-%d")
                    print(f" ✓ 已修复")
                    section_fixed += 1
                    total_fixed += 1
                else:
                    questions[q_idx]["verified_by_audit"] = False
                    questions[q_idx]["audit_date"] = datetime.now().strftime("%Y-%m-%d")
                    print(f" ✗ 修复失败")
                    section_failed += 1
                    total_failed += 1

            total_checked += 1

            # 每道题处理完立即写盘
            data["questions"] = questions
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            time.sleep(0.5)

        print(f"\n  [{section_id}] 通过:{section_passed} 修复:{section_fixed} 失败:{section_failed}")

    print(f"\n{'='*50}")
    print(f"审核完成!")
    print(f"  总计审核: {total_checked} 道")
    print(f"  直接通过: {total_passed} 道")
    print(f"  修复通过: {total_fixed} 道")
    print(f"  审核失败: {total_failed} 道")


if __name__ == "__main__":
    main()
