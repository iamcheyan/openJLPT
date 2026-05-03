#!/usr/bin/env python3
"""
JLPT N2 题库生成器（配置驱动版）
- 从 config.json 读取模型配置
- 从 .env 读取密钥
- 支持多供应商生成 + 独立审核模型
- 结果写入 data/n2/*.json
"""

import json
import random
import urllib.request
import urllib.error
import os
import sys
import time
from datetime import datetime

# ============================================================
# Config loading
# ============================================================

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_vocab_index(vocab_dir):
    """加载所有级别词汇 CSV，构建 kanji->kana 和 kana->kanji 索引。
    同时写入 kanji_reading.json 供前端使用。"""
    kanji_to_kana = {}
    kana_to_kanji = {}

    for level in ["n5", "n4", "n3", "n2", "n1"]:
        path = os.path.join(vocab_dir, f"{level}.csv")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 3:
                    continue
                kana = parts[1]
                kanji = parts[2]
                if not kana or not kanji:
                    continue
                if kanji not in kanji_to_kana:
                    kanji_to_kana[kanji] = []
                if kana not in kanji_to_kana[kanji]:
                    kanji_to_kana[kanji].append(kana)
                if kana not in kana_to_kanji:
                    kana_to_kanji[kana] = []
                if kanji not in kana_to_kanji[kana]:
                    kana_to_kanji[kana].append(kanji)

    # 写入前端可用的 JSON
    index_path = os.path.join(vocab_dir, "kanji_reading.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(kanji_to_kana, f, ensure_ascii=False, indent=2)

    return {"kanji_to_kana": kanji_to_kana, "kana_to_kanji": kana_to_kanji}


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


# ============================================================
# Vocabulary state management (for vocab_reading / vocab_kanji)
# ============================================================

VOCAB_SECTIONS = ("vocab_reading", "vocab_kanji")


def load_n2_vocab_records(vocab_dir):
    """读取 n2.csv，返回所有 kanji 非空的记录列表。"""
    records = []
    path = os.path.join(vocab_dir, "n2.csv")
    if not os.path.exists(path):
        return records
    with open(path, "r", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            kana = parts[1]
            kanji = parts[2]
            if not kana or not kanji:
                continue
            records.append({
                "jmdict_seq": parts[0],
                "kana": kana,
                "kanji": kanji,
            })
    return records


def init_vocab_state(records, state_path):
    """从 n2.csv 初始化状态文件。"""
    state = {}
    for r in records:
        state[r["jmdict_seq"]] = {
            "kana": r["kana"],
            "kanji": r["kanji"],
            "vocab_reading": "pending",
            "vocab_reading_attempts": 0,
            "vocab_reading_issue": "",
            "vocab_kanji": "pending",
            "vocab_kanji_attempts": 0,
            "vocab_kanji_issue": "",
        }
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state


def load_vocab_state(state_path):
    """加载词汇生成状态。"""
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_vocab_state(state_path, state):
    """保存词汇生成状态。"""
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def pick_pending_words(state, section_id, count=3):
    """从状态中随机选取指定题型的 pending 词汇。"""
    pending = [
        {"jmdict_seq": k, **v}
        for k, v in state.items()
        if v.get(section_id) == "pending"
    ]
    if len(pending) <= count:
        return pending
    return random.sample(pending, count)


def count_pending(state, section_id):
    """统计指定题型的 pending 数量。"""
    return sum(1 for v in state.values() if v.get(section_id) == "pending")


def load_existing_vocab_targets(data_dir, section_id):
    """读取已入库词汇题的 target，用于去重和修复状态。"""
    path = os.path.join(data_dir, f"{section_id}.json")
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        q.get("target")
        for q in data.get("questions", [])
        if isinstance(q, dict) and q.get("target")
    }


def repair_vocab_state(vocab_state, state_path, data_dir):
    """把状态中 generated 但题库 JSON 缺失的词重置为 pending。

    旧版本会先把词标记为 generated，等整个题型完成后才统一写 JSON。
    如果进程中断，会留下 generated 状态但没有实际题目。启动时修复这类不一致。
    """
    repaired = 0
    for section_id in VOCAB_SECTIONS:
        existing_targets = load_existing_vocab_targets(data_dir, section_id)
        for record in vocab_state.values():
            if record.get(section_id) != "generated":
                continue
            target = record.get("kanji") if section_id == "vocab_reading" else record.get("kana")
            if target in existing_targets:
                continue
            record[section_id] = "pending"
            record[f"{section_id}_issue"] = "state_repaired_missing_json"
            repaired += 1

    if repaired:
        save_vocab_state(state_path, vocab_state)
        print(f"词汇状态修复完成: {repaired} 个 generated 但未入库的词已重置为 pending")


def mark_vocab_failure(vocab_state, vocab_state_path, word, section_id, issue, max_attempts=2):
    """记录一次生成/审核失败，并立即保存状态。"""
    attempts_key = f"{section_id}_attempts"
    issue_key = f"{section_id}_issue"
    record = vocab_state[word["jmdict_seq"]]
    current = record.get(attempts_key, 0)
    record[attempts_key] = current + 1
    record[issue_key] = issue
    if current + 1 >= max_attempts:
        record[section_id] = "failed"
    if vocab_state_path:
        save_vocab_state(vocab_state_path, vocab_state)


def mark_vocab_generated(vocab_state, vocab_state_path, word, section_id):
    """标记词汇题已入库，并立即保存状态。"""
    record = vocab_state[word["jmdict_seq"]]
    record[section_id] = "generated"
    record[f"{section_id}_issue"] = ""
    if vocab_state_path:
        save_vocab_state(vocab_state_path, vocab_state)


# ============================================================
# Provider resolution
# ============================================================

def resolve_provider(provider_id, provider_cfg, env):
    """Resolve provider config + env vars into a usable dict.
    Returns None if required env vars are missing."""
    api_key = env.get(provider_cfg["api_key_env"])
    base_url = env.get(provider_cfg["base_url_env"], "")

    if not api_key:
        print(f"    [WARN] {provider_id}: API key missing ({provider_cfg['api_key_env']})")
        return None
    if not base_url:
        print(f"    [WARN] {provider_id}: Base URL missing ({provider_cfg['base_url_env']})")
        return None

    # URL suffix handling (skip for Gemini native API)
    suffix = provider_cfg.get("url_suffix", "")
    fmt = provider_cfg.get("format", "openai")
    if fmt != "gemini" and suffix and not base_url.endswith(suffix):
        base_url = base_url.rstrip("/") + suffix

    # Model name: fixed or from env
    model = provider_cfg.get("model", "")
    if "model_env" in provider_cfg:
        model = env.get(provider_cfg["model_env"], model)

    return {
        "id": provider_id,
        "label": provider_cfg.get("label", provider_id),
        "url": base_url,
        "api_key": api_key,
        "model": model,
        "format": provider_cfg.get("format", "openai"),
        "headers": provider_cfg.get("headers", {}),
    }


# ============================================================
# API calling (OpenAI-compatible)
# ============================================================

def call_gemini_api(provider, prompt, timeout=120):
    """Call Google Gemini native REST API."""
    url = f"{provider['url'].rstrip('/')}/models/{provider['model']}:generateContent?key={provider['api_key']}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return f"ERROR: No candidates in response: {json.dumps(result, ensure_ascii=False)[:200]}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return f"ERROR: HTTP {e.code} - {body}"
    except Exception as e:
        return f"ERROR: {e}"


def call_openai_api(provider, prompt, timeout=120):
    """Call an OpenAI-compatible API. Returns response text or 'ERROR: ...'."""
    url = provider["url"]
    api_key = provider["api_key"]
    model = provider["model"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    headers.update(provider.get("headers", {}))

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return f"ERROR: HTTP {e.code} - {body}"
    except Exception as e:
        return f"ERROR: {e}"


def call_api(provider, prompt, timeout=120):
    """Dispatch to the correct API caller based on provider format."""
    fmt = provider.get("format", "openai")
    if fmt == "gemini":
        return call_gemini_api(provider, prompt, timeout)
    return call_openai_api(provider, prompt, timeout)


def check_provider(provider, timeout=15):
    """快速检测模型是否可用。返回 (ok, error_msg)。"""
    result = call_api(provider, "hi", timeout=timeout)
    if result.startswith("ERROR"):
        return False, result
    return True, ""


# ============================================================
# JSON extraction helpers
# ============================================================

def extract_json(text):
    """Extract JSON array from API response."""
    if not text or text.startswith("ERROR"):
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_json_object(text):
    """Extract JSON object from API response."""
    if not text or text.startswith("ERROR"):
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ============================================================
# Vocab question builders (vocab_reading / vocab_kanji)
# ============================================================

def build_reading_prompt(words):
    """为读音题构建 prompt。words: [{kanji, kana}, ...]"""
    lines = []
    for i, w in enumerate(words, 1):
        lines.append(f"{i}. 目标词：《{w['kanji']}》（正确读音：{w['kana']}）")
    word_list = "\n".join(lines)
    return f"""你是一位JLPT N2出题专家。请为以下{len(words)}个目标词各出一道「漢字の読み方」题目。

{word_list}

【你的任务】
1. 为每个目标词写一句自然、N2难度的日语例句，目标词用《》标注。
2. 提供3个错误读音作为干扰项（distractors）。
3. 干扰项设计要求：针对长短音、清浊音、促音或常见误读进行设计。
4. 绝对禁止：干扰项等于正确读音、干扰项之间重复、干扰项与正确读音完全相同。
5. 每个干扰项必须是看起来像正确读音的"常见误读"，不能是明显错误的随机假名。

【反例——这些是错误的，会导致题目作废】
目标词：《掲載》（正确读音：けいさい）
- 错误干扰项1：けいさい（等于正确答案，绝对禁止）
- 错误干扰项2：けいさい（与另一个干扰项重复，绝对禁止）
- 错误干扰项3：あ（太短，明显不是候选，禁止）

【正确示例】
目标词：《掲載》（正确读音：けいさい）
干扰项：けさい（清浊混淆）、けっさい（促音误读）、けいざい（长音误读）

【输出格式】严格输出JSON数组，不要输出其他内容：
[
  {{
    "sentence": "包含《目标词》的完整日语例句",
    "distractors": ["错误读音1", "错误读音2", "错误读音3"],
    "explanation": "中文解析，说明为什么正确读音是对的，干扰项错在哪"
  }},
  ...
]"""


def build_kanji_prompt(words):
    """为汉字表记题构建 prompt。words: [{kana, kanji}, ...]"""
    lines = []
    for i, w in enumerate(words, 1):
        lines.append(f"{i}. 目标读音：{w['kana']}（正确汉字：{w['kanji']}）")
    word_list = "\n".join(lines)
    return f"""你是一位JLPT N2出题专家。请为以下{len(words)}个目标读音各出一道「漢字の表記」题目。

{word_list}

【你的任务】
1. 为每个目标读音写一句自然、N2难度的日语例句，目标读音用《》标注（如《けいさい》）。
2. 提供3个错误汉字写法作为干扰项（distractors）。
3. 干扰项设计要求：同音异义字、形似字、相同部首混淆。
4. 绝对禁止：干扰项等于正确汉字、干扰项之间重复、干扰项与正确汉字完全相同。
5. 每个干扰项必须是看起来像正确汉字的"常见误写"，不能是明显错误的随机汉字。

【反例——这些是错误的，会导致题目作废】
目标读音：けいさい（正确汉字：掲載）
- 错误干扰项1：掲載（等于正确答案，绝对禁止）
- 错误干扰项2：掲載（与另一个干扰项重复，绝对禁止）
- 错误干扰项3：一（明显不是候选，禁止）

【正确示例】
目标读音：けいさい（正确汉字：掲載）
干扰项：掲栽（形似字）、計裁（同音异义）、啓載（部首混淆）

【输出格式】严格输出JSON数组，不要输出其他内容：
[
  {{
    "sentence": "包含《目标读音》的完整日语例句",
    "distractors": ["错误汉字1", "错误汉字2", "错误汉字3"],
    "explanation": "中文解析，说明为什么正确汉字是对的，干扰项错在哪"
  }},
  ...
]"""


def generate_vocab_questions(provider, section_id, words, timeout):
    """专门为读音/汉字题生成。返回 (items, 实际使用的words)。"""
    if section_id == "vocab_reading":
        prompt = build_reading_prompt(words)
    elif section_id == "vocab_kanji":
        prompt = build_kanji_prompt(words)
    else:
        return None, []

    print(f"    [{provider['id']}] 生成 {len(words)} 道 {section_id} ...", end="", flush=True)
    raw = call_api(provider, prompt, timeout=timeout)
    if not raw or raw.startswith("ERROR"):
        print(f" 失败: {raw}")
        return None, []

    parsed = extract_json(raw)
    if parsed is None:
        print(f" JSON解析失败")
        return None, []

    # 实际返回数量可能和请求数量不一致，按实际返回处理
    actual_count = min(len(parsed), len(words))
    print(f" 返回 {actual_count}/{len(words)} 道")
    return parsed[:actual_count], words[:actual_count]


def assemble_vocab_item(raw_item, word, section_id):
    """将 LLM 返回的 raw_item 与词库数据组合成完整题目。
    返回 (item, errors)。"""
    errors = []

    if section_id == "vocab_reading":
        target = word["kanji"]
        correct = word["kana"]
    elif section_id == "vocab_kanji":
        target = word["kana"]
        correct = word["kanji"]
    else:
        return None, ["未知题型"]

    distractors = raw_item.get("distractors", [])
    if len(distractors) < 3:
        errors.append(f"干扰项不足: {len(distractors)}")
        return None, errors

    # 去重并过滤掉正确答案
    seen = {correct}
    unique_distractors = []
    for d in distractors:
        if d not in seen:
            unique_distractors.append(d)
            seen.add(d)

    # 兜底：从词库补充干扰项
    if len(unique_distractors) < 3 and VOCAB_INDEX:
        if section_id == "vocab_reading":
            pool = list(VOCAB_INDEX.get("kana_to_kanji", {}).keys())
        else:
            pool = list(VOCAB_INDEX.get("kanji_to_kana", {}).keys())
        target_len = len(correct)
        # 优先选长度相近的真实词
        candidates = [k for k in pool if k != correct and k not in seen and abs(len(k) - target_len) <= 2]
        random.shuffle(candidates)
        for cand in candidates:
            if len(unique_distractors) >= 3:
                break
            unique_distractors.append(cand)
            seen.add(cand)

    if len(unique_distractors) < 3:
        errors.append(f"有效干扰项不足: {len(unique_distractors)}")
        return None, errors

    options = [correct] + unique_distractors[:3]
    random.shuffle(options)
    answer = options.index(correct)

    item = {
        "sentence": raw_item.get("sentence", ""),
        "target": target,
        "options": options,
        "answer": answer,
        "explanation": raw_item.get("explanation", ""),
    }

    # 本地硬校验
    if not item["sentence"]:
        errors.append("缺少sentence")
    if f"《{target}》" not in item["sentence"] and target not in item["sentence"]:
        errors.append(f"例句中未包含目标词: {target}")
    if len(set(options)) < 4:
        errors.append("存在重复选项")

    # 词库校验
    if VOCAB_INDEX and section_id == "vocab_reading":
        correct_readings = VOCAB_INDEX.get("kanji_to_kana", {}).get(target, [])
        if correct_readings and correct not in correct_readings:
            errors.append(f"词库不匹配: {target} 的读音应为 {correct_readings}，但程序设定为 {correct}")
        chosen = options[answer]
        if correct_readings and chosen not in correct_readings:
            errors.append(f"答案读音错误: {chosen} 不在 {correct_readings}")

    if VOCAB_INDEX and section_id == "vocab_kanji":
        correct_kanjis = VOCAB_INDEX.get("kana_to_kanji", {}).get(target, [])
        if correct_kanjis and correct not in correct_kanjis:
            errors.append(f"词库不匹配: {target} 的汉字应为 {correct_kanjis}，但程序设定为 {correct}")
        chosen = options[answer]
        if correct_kanjis and chosen not in correct_kanjis:
            errors.append(f"答案汉字错误: {chosen} 不在 {correct_kanjis}")

    return item, errors


# ============================================================
# Question type definitions (prompts)
# ============================================================

SECTION_DEFS = [
    {
        "id": "vocab_reading",
        "name": "① 漢字の読み方",
        "prompt": """你是一位JLPT N2出题专家。请出2道「漢字の読み方」题目。

【出题准则】
1. 难度级别：严格N2。禁止使用N5/N4基础词汇。
2. 目标词汇参考：謙虚、納得、把握、冷静、豊富、衝突、深刻、恩恵、妥協、慎重、巧妙、克服、愉快、貴重、怪しい、慌てる、隔てる、企てる。
3. 干扰项设计：针对长短音、清浊音、促音或常见误读进行设计。

【输出格式】严格输出JSON数组，不要输出其他内容：
[
  {
    "sentence": "完整的日语句子，目标汉字词用《》标注",
    "target": "目标汉字词",
    "options": ["假名1", "假名2", "假名3", "假名4"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "vocab_kanji",
        "name": "② 漢字の表記",
        "prompt": """你是一位JLPT N2出题专家。请出2道「漢字の表記」题目。

【出题准则】
1. 难度：N2级别，禁止使用简单汉字。
2. 目标词汇参考：招く、保証、援助、拡張、継続、貢献、衝突、維持、派遣、省略、履歴、冷静、募集、掲載。
3. 干扰项：同音异义字、形似字、相同部首混淆。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "完整的日语句子，目标假名词用《》标注",
    "target": "目标假名词",
    "options": ["汉字1", "汉字2", "汉字3", "汉字4"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "vocab_context",
        "name": "③ 文脈規定",
        "prompt": """你是一位JLPT N2出题专家。请出2道「文脈規定」题目。

【出题准则】
1. 考点：N2级别的固定搭配、复合词、副词辨析。
2. 关键词参考：～観、高～、社会貢献、経済成長率、情報漏洩、異文化理解、相変わらず、せめて、わざと。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含（　）的完整日语句子",
    "options": ["词1", "词2", "词3", "词4"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "vocab_synonym",
        "name": "④ 言い換え・類義",
        "prompt": """你是一位JLPT N2出题专家。请出2道「言い換え・類義」题目。

【出题准则】
1. 考点：N2级别近义词辨析。
2. 关键词参考：愉快（面白い）、やむをえない（しかたない）、張り切る、冷静だ、深刻だ、質素だ、妥当だ。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含目标词的日语句子，目标词用《》标注",
    "target": "目标词",
    "options": ["选项1", "选项2", "选项3", "选项4"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "vocab_usage",
        "name": "⑤ 用法",
        "prompt": """你是一位JLPT N2出题专家。请出2道「用法」题目。

【出题准则】
1. 难度：严格N2级别。
2. 关键词参考：延長、さびる、謙虚、納得、把握、冷静、豊富、衝突、深刻、恩恵、妥協、慎重。
3. 干扰项：考查词汇的特定搭配或语用限制。

【输出格式】严格输出JSON数组：
[
  {
    "target": "目标词",
    "options": ["句子1", "句子2", "句子3", "句子4"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "grammar_fill",
        "name": "⑥ 文の文法",
        "prompt": """你是一位JLPT N2出题专家。请出2道「文の文法」语法填空题目。

【出题准则】
1. 考查N2核心语法点，如：～を通じて、～にかけて、～たびに、～わけがない、～にすぎない、～上で、～かわりに。
2. 每题4个选项，只有1个语法正确且语义通顺。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含（　）的完整日语句子",
    "options": ["语法A", "语法B", "语法C", "语法D"],
    "answer": 0,
    "explanation": "中文解析，说明语法用法和接续"
  }
]"""
    },
    {
        "id": "grammar_order",
        "name": "⑦ 文の組み立て",
        "prompt": """你是一位JLPT N2出题专家。请出2道「文の組み立て」句子排序题目。

【题型说明】
给出一个句子，其中有★标记的位置需要填入一个词。从4个选项中选出★处应填的词。

【示例】
题目：結婚生活を送る★、相手への思いやりの気持ちを持つことだと思う。
选项：1 うえで  2 といえば  3 大切か  4 何が
答案：4（何が）
完整句：結婚生活を送る上で、何が大切かといえば、相手への思いやりの気持ちを持つことだと思う。

【重要】
- 题目中必须有★标记
- 答案是★处应填入的词的序号
- 必须能组成一个语法正确的完整句子

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含★的句子",
    "fragments": ["片段1", "片段2", "片段3", "片段4"],
    "answer": 0,
    "complete_sentence": "完整的正确句子",
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "grammar_passage",
        "name": "⑧ 文章の文法",
        "prompt": """你是一位JLPT N2出题专家。请出1道「文章の文法」题目，包含3个空格。

【题型说明】
给出一篇短文（3-5句），其中3个空格，每个空格从4个选项中选出最合适的语法表达。

【输出格式】严格输出JSON数组（只有1个元素）：
[
  {
    "passage": "短文内容，空格用（　1　）（　2　）（　3　）标注",
    "blanks": [
      {"num": 1, "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "中文解析"},
      {"num": 2, "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "中文解析"},
      {"num": 3, "options": ["A", "B", "C", "D"], "answer": 2, "explanation": "中文解析"}
    ]
  }
]"""
    },
    {
        "id": "reading_short",
        "name": "⑨ 短文読解",
        "prompt": """你是一位JLPT N2出题专家。请出2道「短文読解」题目。

【题型说明】
每篇短文（100-200字）配1个问题，考查对作者观点的理解。

【干扰项设计】
- 部分正确但不完整
- 与原文意思相反
- 文中未提及的内容

【输出格式】严格输出JSON数组：
[
  {
    "passage": "100-200字的日语文章（注明出处）",
    "question": "问题",
    "options": ["A", "B", "C", "D"],
    "answer": 0,
    "explanation": "中文解析"
  }
]"""
    },
    {
        "id": "reading_medium",
        "name": "⑩ 中文読解",
        "prompt": """你是一位JLPT N2出题专家。请出1篇「中文読解」，配2个问题。

【题型说明】
一篇中等长度文章（300-400字）配2个问题，考查对作者论点的理解。

【输出格式】严格输出JSON数组：
[
  {
    "passage": "300-400字的日语文章",
    "questions": [
      {"question": "问题1", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "解析"},
      {"question": "问题2", "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "解析"}
    ]
  }
]"""
    },
    {
        "id": "reading_long",
        "name": "⑪ 長文読解",
        "prompt": """你是一位JLPT N2出题专家。请出1篇「長文読解」，配3个问题。

【题型说明】
一篇长文（500-700字）配3个问题，考查深层理解和推理。

【输出格式】严格输出JSON数组：
[
  {
    "passage": "500-700字的日语文章",
    "questions": [
      {"question": "Q1", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "解析"},
      {"question": "Q2", "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "解析"},
      {"question": "Q3", "options": ["A", "B", "C", "D"], "answer": 2, "explanation": "解析"}
    ]
  }
]"""
    },
    {
        "id": "reading_search",
        "name": "⑫ 情報検索",
        "prompt": """你是一位JLPT N2出题专家。请出1篇「情報検索」，配2个问题。

【题型说明】
给出一个实用信息文档（酒店指南、时刻表、公告等），从中检索信息。

【输出格式】严格输出JSON数组：
[
  {
    "passage": "实用信息文档（模拟真实场景，含具体时间/价格/条件）",
    "questions": [
      {"question": "带具体人物和条件的问题", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "解析"},
      {"question": "问题2", "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "解析"}
    ]
  }
]"""
    },
]

# 审核 prompt
REVIEW_PROMPT_TEMPLATE = """你是一位JLPT N2审题专家。请审核以下题目是否合格。

【审核标准】
1. 答案是否正确
2. 干扰项是否合理（不能有两个选项意思相同）
3. 难度是否符合N2级别
4. 句子是否自然、语法是否正确

【题目】
{question_json}

请严格输出以下JSON格式：
{{
  "approved": true或false,
  "review_explanation": "详细的中文解析（如果approved=true，必须包含：答案解释、干扰项分析、语法/词汇重点、学习建议）",
  "issues": ["如果不通过，列出问题列表"]
}}"""


# 全局词汇索引，由 main() 注入
VOCAB_INDEX = None


# ============================================================
# Validation
# ============================================================

def validate_question(section_id, q):
    """校验单道题（展平后的单题）。返回 (valid, errors)。"""
    errors = []
    options = q.get("options", [])
    if not options or len(options) < 4:
        errors.append(f"选项不足: {len(options) if options else 0}")
        return False, errors

    answer = q.get("answer")
    if answer is None or not isinstance(answer, int) or answer < 0 or answer >= len(options):
        errors.append(f"answer无效: {answer}")
    if not q.get("explanation"):
        errors.append("缺少explanation")

    # 检查选项是否重复
    if len(set(str(o) for o in options)) < len(options):
        errors.append("存在重复选项")

    # 题型特定校验
    if section_id == "vocab_reading":
        target = q.get("target", "")
        if not any('一' <= c <= '鿿' for c in target):
            errors.append(f"目标词不含汉字: {target}")
        # 本地词库校验读音
        if VOCAB_INDEX and target:
            correct_readings = VOCAB_INDEX.get("kanji_to_kana", {}).get(target, [])
            chosen = options[answer] if answer is not None and 0 <= answer < len(options) else ""
            if correct_readings and chosen not in correct_readings:
                errors.append(f"读音错误: target={target} 正确={correct_readings} 选中={chosen}")

    if section_id == "vocab_kanji":
        target = q.get("target", "")
        if not target:
            errors.append("缺少target假名")
        # 本地词库校验汉字
        if VOCAB_INDEX and target:
            correct_kanjis = VOCAB_INDEX.get("kana_to_kanji", {}).get(target, [])
            chosen = options[answer] if answer is not None and 0 <= answer < len(options) else ""
            if correct_kanjis and chosen not in correct_kanjis:
                errors.append(f"汉字错误: target={target} 正确={correct_kanjis} 选中={chosen}")

    return len(errors) == 0, errors


def validate_item(section_id, item):
    """校验一个顶层item（可能是嵌套结构）。返回 (valid_count, total_count, errors)。"""
    errors = []

    if section_id == "grammar_order":
        if "★" not in item.get("sentence", ""):
            errors.append("缺少★标记")
            return 0, 1, errors
        frags = item.get("fragments", [])
        if len(frags) != 4:
            errors.append(f"fragments数量错误: {len(frags)}")
            return 0, 1, errors
        if not item.get("complete_sentence"):
            errors.append("缺少complete_sentence")
            return 0, 1, errors
        return 1, 1, []

    if section_id == "grammar_passage":
        blanks = item.get("blanks", [])
        if not blanks:
            errors.append("缺少blanks")
            return 0, 0, errors
        valid = 0
        for b in blanks:
            opts = b.get("options", [])
            if len(opts) >= 4 and b.get("answer") is not None and b.get("explanation"):
                valid += 1
            else:
                errors.append(f"blank#{b.get('num','?')} 校验失败")
        return valid, len(blanks), errors

    if "questions" in item:
        questions = item["questions"]
        valid = 0
        for q in questions:
            ok, errs = validate_question(section_id, q)
            if ok:
                valid += 1
            else:
                errors.extend(errs)
        return valid, len(questions), errors

    ok, errs = validate_question(section_id, item)
    return (1, 1, []) if ok else (0, 1, errs)


def flatten_for_count(section_id, items):
    """展平并计数实际题目数。"""
    count = 0
    for item in items:
        if "questions" in item:
            count += len(item["questions"])
        elif "blanks" in item:
            count += len(item["blanks"])
        else:
            count += 1
    return count


# ============================================================
# Main pipeline
# ============================================================

def generate_questions(provider, section_def, timeout):
    """调用模型生成题目。返回解析后的JSON数组或None。"""
    print(f"    [{provider['id']}] 生成 {section_def['name']} ...", end="", flush=True)
    raw = call_api(provider, section_def["prompt"], timeout=timeout)
    if not raw or raw.startswith("ERROR"):
        print(f" 失败: {raw}")
        return None
    parsed = extract_json(raw)
    if parsed is None:
        print(f" JSON解析失败")
        return None
    total_valid = 0
    total_questions = 0
    for item in parsed:
        v, t, _ = validate_item(section_def["id"], item)
        total_valid += v
        total_questions += t
    print(f" {total_valid}/{total_questions} 通过校验")
    return parsed


def review_question(provider, question, section_id):
    """调用审核模型审核一道题。返回 (approved, review_explanation) 或 (False, None)。"""
    q_str = json.dumps(question, ensure_ascii=False, indent=2)
    prompt = REVIEW_PROMPT_TEMPLATE.format(question_json=q_str)
    raw = call_api(provider, prompt, timeout=120)
    if not raw or raw.startswith("ERROR"):
        return False, None
    result = extract_json_object(raw)
    if result is None:
        return False, None
    approved = result.get("approved", False)
    explanation = result.get("review_explanation", "")
    return approved, explanation


def _process_vocab_section(section_id, section_name, available, timeout, vocab_state, vocab_state_path, data_dir):
    """专门处理读音/汉字题：循环抽词→生成→审核→更新状态，直到跑完所有 pending 词。"""
    if vocab_state is None:
        print(f"  [WARN] 未加载词汇状态，跳过")
        return []

    provider_ids = list(available.keys())
    all_approved = []

    while True:
        words = pick_pending_words(vocab_state, section_id, count=3)
        if not words:
            print(f"  无更多 pending 词汇，{section_name} 完成")
            break

        print(f"  本轮选中 {len(words)} 个 pending 词")

        # 1. 生成：逐个模型尝试
        assembled = None
        used_generator = None
        random.shuffle(provider_ids)
        for pid in provider_ids:
            provider = available[pid]
            raw_items, used_words = generate_vocab_questions(provider, section_id, words, timeout)
            if raw_items:
                assembled = []
                for raw, word in zip(raw_items, used_words):
                    item, errs = assemble_vocab_item(raw, word, section_id)
                    if item and not errs:
                        assembled.append((item, word))
                    else:
                        print(f"      组装失败: {'; '.join(errs)}")
                        mark_vocab_failure(vocab_state, vocab_state_path, word, section_id, "; ".join(errs))
                if assembled:
                    used_generator = provider
                    break

        if not assembled:
            print(f"  本轮全部组装失败，继续下一轮")
            continue

        # 2. 审核：从剩余模型中随机选一个
        remaining_ids = [p for p in provider_ids if p != used_generator["id"]]
        if remaining_ids:
            random.shuffle(remaining_ids)
            reviewer_id = remaining_ids[0]
            reviewer = available[reviewer_id]
            print(f"    [{reviewer_id}] 审核中 ...")

            for item, word in assembled:
                approved, review_exp = review_question(reviewer, item, section_id)
                if approved:
                    item["generated_by"] = f"{used_generator['id']}:{used_generator['label']}"
                    item["reviewed_by"] = reviewer_id
                    item["review_explanation"] = review_exp
                    item["verified"] = True
                    item["created_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    item["level"] = "N2"
                    item["question_type"] = section_id
                    # 先落盘，再更新状态。save_to_json 对词汇题按 target 去重。
                    added = save_to_json(section_id, [item], data_dir)
                    mark_vocab_generated(vocab_state, vocab_state_path, word, section_id)
                    if added:
                        all_approved.append(item)
                    else:
                        print(f"      已存在，跳过重复入库: {item.get('target')}")
                else:
                    print(f"      未通过审核")
                    mark_vocab_failure(vocab_state, vocab_state_path, word, section_id, "审核未通过")
                time.sleep(1)
        else:
            print(f"    [WARN] 无其他模型可用做审核，跳过审核直接入库")
            for item, word in assembled:
                item["generated_by"] = f"{used_generator['id']}:{used_generator['label']}"
                item["reviewed_by"] = "none"
                item["review_explanation"] = ""
                item["verified"] = False
                item["created_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                item["level"] = "N2"
                item["question_type"] = section_id
                added = save_to_json(section_id, [item], data_dir)
                mark_vocab_generated(vocab_state, vocab_state_path, word, section_id)
                if added:
                    all_approved.append(item)
                else:
                    print(f"      已存在，跳过重复入库: {item.get('target')}")

        pending_count = count_pending(vocab_state, section_id)
        print(f"  {section_name} 进度: 累计入库 {len(all_approved)} 题，剩余 pending {pending_count}")

    print(f"  {section_name} 总计入库: {len(all_approved)} 题")
    return all_approved


def process_section(section_def, available, timeout, data_dir, vocab_state=None, vocab_state_path=None):
    """处理一个题型：随机选模型生成→失败换模型重试→成功后换另一模型审核。"""
    section_id = section_def["id"]
    print(f"\n  === {section_def['name']} ===")

    # 特殊处理 vocab_reading / vocab_kanji
    if section_id in ("vocab_reading", "vocab_kanji"):
        return _process_vocab_section(section_id, section_def["name"], available, timeout, vocab_state, vocab_state_path, data_dir)

    # 通用流程（其他题型）
    provider_ids = list(available.keys())
    random.shuffle(provider_ids)

    # 1. 生成：逐个模型尝试，直到成功
    items = None
    used_generator = None
    for pid in provider_ids:
        provider = available[pid]
        print(f"    [{pid}] 尝试生成 ...", end="", flush=True)
        items = generate_questions(provider, section_def, timeout)
        if not items:
            print(f" 生成/解析失败，换模型")
            continue
        valid_items = []
        for item in items:
            valid, total, errs = validate_item(section_id, item)
            if valid > 0:
                valid_items.append(item)
            else:
                print(f"\n      跳过（校验失败: {'; '.join(errs)}）")
        if valid_items:
            used_generator = provider
            items = valid_items
            print(f" 生成成功，{len(items)} 题通过校验")
            break
        else:
            print(f" 全部校验失败，换模型重试")

    if not items:
        print(f"  {section_def['name']} 所有模型均生成失败")
        return []

    # 2. 审核：从剩余模型中随机选一个
    remaining_ids = [p for p in provider_ids if p != used_generator["id"]]
    if not remaining_ids:
        print(f"    [WARN] 无其他模型可用做审核，跳过审核直接入库")
        for item in items:
            item["generated_by"] = f"{used_generator['id']}:{used_generator['label']}"
            item["reviewed_by"] = "none"
            item["review_explanation"] = ""
            item["verified"] = False
            item["created_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(f"  {section_def['name']} 总计: {len(items)} 题入库（未审核）")
        return items

    random.shuffle(remaining_ids)
    reviewer_id = remaining_ids[0]
    reviewer = available[reviewer_id]
    print(f"    [{reviewer_id}] 审核中 ...")

    approved_items = []
    approved_count = 0
    for item in items:
        approved, review_exp = review_question(reviewer, item, section_id)
        if approved:
            item["generated_by"] = f"{used_generator['id']}:{used_generator['label']}"
            item["reviewed_by"] = reviewer_id
            item["review_explanation"] = review_exp
            item["verified"] = True
            item["created_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            approved_items.append(item)
            approved_count += 1
        else:
            print(f"      未通过审核")
        time.sleep(1)

    print(f"    [{reviewer_id}] 审核通过: {approved_count}/{len(items)}")
    print(f"  {section_def['name']} 总计: {approved_count} 题入库")
    return approved_items


def save_to_json(section_id, questions, data_dir):
    """将题目追加到对应的JSON文件。"""
    path = os.path.join(data_dir, f"{section_id}.json")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing = data.get("questions", [])
    if section_id in VOCAB_SECTIONS:
        existing_targets = {
            q.get("target")
            for q in existing
            if isinstance(q, dict) and q.get("target")
        }
        questions = [
            q for q in questions
            if not q.get("target") or q.get("target") not in existing_targets
        ]
        if not questions:
            return 0

    start_idx = len(existing)

    for i, q in enumerate(questions):
        q["id"] = f"n2-{section_id}-{start_idx + i + 1:03d}"
        q["level"] = "N2"
        q["question_type"] = section_id

    data["questions"].extend(questions)
    data["meta"]["count"] = len(data["questions"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return len(questions)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JLPT N2 题库生成器（配置驱动版）")
    parser.add_argument("--only", nargs="*", help="只生成指定题型ID")
    parser.add_argument("--config", default="config.json", help="配置文件路径 (默认: config.json)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    config_path = os.path.join(base_dir, args.config)
    data_dir = os.path.join(base_dir, "data", "n2")

    env = load_env(env_path)
    cfg = load_config(config_path)

    # 加载词汇索引（供本地读音/汉字校验 + 前端显示假名）
    vocab_dir = os.path.join(base_dir, "resources", "vocabulary")
    global VOCAB_INDEX
    VOCAB_INDEX = load_vocab_index(vocab_dir)
    print(f"词汇索引加载完成: {len(VOCAB_INDEX['kanji_to_kana'])} 个汉字词, {len(VOCAB_INDEX['kana_to_kanji'])} 个读音")

    # 加载或初始化词汇生成状态
    state_dir = os.path.join(base_dir, "data", "generation-state")
    vocab_state_path = os.path.join(state_dir, "n2-vocabulary.json")
    vocab_state = load_vocab_state(vocab_state_path)
    if not vocab_state:
        print("初始化词汇生成状态...")
        records = load_n2_vocab_records(vocab_dir)
        vocab_state = init_vocab_state(records, vocab_state_path)
        print(f"状态初始化完成: {len(vocab_state)} 个词汇")
    else:
        print(f"词汇状态加载完成: {len(vocab_state)} 个词汇")

    repair_vocab_state(vocab_state, vocab_state_path, data_dir)

    # 解析可用提供商
    candidates = {}
    for pid, pc in cfg["providers"].items():
        resolved = resolve_provider(pid, pc, env)
        if resolved:
            candidates[pid] = resolved

    # 健康检查：筛选掉当前不可用的模型
    print("检测模型可用性...")
    available = {}
    for pid, provider in candidates.items():
        ok, err = check_provider(provider, timeout=15)
        if ok:
            available[pid] = provider
            print(f"  ✓ {pid}")
        else:
            print(f"  ✗ {pid} — {err[:120]}")

    if len(available) < 2:
        print(f"[FATAL] 至少需要 2 个可用模型（1 生成 + 1 审核），当前只有 {len(available)} 个")
        print(f"通过检测: {', '.join(available.keys())}")
        sys.exit(1)

    timeout = cfg.get("pipeline", {}).get("timeout", 180)

    sections = SECTION_DEFS
    if args.only:
        sections = [s for s in SECTION_DEFS if s["id"] in args.only]
        if not sections:
            print(f"未找到指定题型: {args.only}")
            print(f"可用: {', '.join(s['id'] for s in SECTION_DEFS)}")
            return

    print("=" * 60)
    print("JLPT N2 题库生成器（随机模型 + 串行 fallback）")
    print("=" * 60)
    print(f"配置文件: {args.config}")
    print(f"可用模型: {', '.join(available.keys())}")
    print(f"题型: {len(sections)} 个")
    print(f"输出: data/n2/*.json")
    print()

    total_added = 0
    results = {}

    for section_def in sections:
        questions = process_section(section_def, available, timeout, data_dir, vocab_state, vocab_state_path)
        if questions:
            if section_def["id"] in VOCAB_SECTIONS:
                # 词汇题在审核通过时已经逐题落盘，这里只汇总数量，避免重复追加。
                added = len(questions)
            else:
                added = save_to_json(section_def["id"], questions, data_dir)
            total_added += added
            results[section_def["name"]] = added
        else:
            results[section_def["name"]] = 0

    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    for name, count in results.items():
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {name}: +{count} 题")
    print(f"\n  总计新增: {total_added} 题")

    print("\n  各题库当前总量:")
    for section_def in SECTION_DEFS:
        path = os.path.join(data_dir, f"{section_def['id']}.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"    {section_def['name']}: {data['meta']['count']} 题")

    print("\n完成！")


if __name__ == "__main__":
    main()
