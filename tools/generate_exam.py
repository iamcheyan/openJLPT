#!/usr/bin/env python3
"""
工具：LLM 试卷生成器（旧版）
作用：调用 LLM API 一次性生成完整 N2 模拟试卷的 HTML 文件。
      早期版本，现在主要用 generate_bank.py 按题型分别生成题库。
用法：python3 tools/generate_exam.py
"""

import json
import urllib.request
import urllib.error
import os
import sys

# ============================================================
# 试卷结构定义（基于JLPT N2官方真题格式）
# ============================================================
EXAM_SECTIONS = [
    # ---- 一、文字・語彙 ----
    {
        "id": "vocab_reading",
        "part": "一、文字・語彙",
        "name": "① 漢字の読み方",
        "count": 5,
        "instruction": "＿＿の言葉の読み方として最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「漢字の読み方」题目。

【出题准则】
1. **难度级别**：严格遵守N2级别。禁止使用N5/N4基础词汇（如：方法、文化、料理、勉強、行く、食べる）。
2. **目标词汇参考**：謙虚、納得、把握、冷静、豊富、衝突、深刻、恩恵、妥協、慎重、巧妙、克服、愉快、貴重、怪しい、慌てる、隔てる、企てる。
3. **干扰项设计**：针对长短音、清浊音、促音或常见误读进行设计。
4. **语境**：句子应具有N2级别的正式感或社会性。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "完整的日语句子，目标汉字词用《》标注",
    "target": "目标汉字词",
    "options": ["假名1", "假名2", "假名3", "假名4"],
    "answer": 0,
    "explanation": "中文解析：说明正确读音及干扰项解析。"
  }
]"""
    },
    {
        "id": "vocab_kanji",
        "part": "一、文字・語彙",
        "name": "② 漢字の表記",
        "count": 5,
        "instruction": "＿＿の言葉を漢字で書くとき、最もよいものを１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「漢字の表記」题目。

【出题准则】
1. **难度级别**：N2级别，禁止使用简单汉字。
2. **目标词汇参考**：招く、保証、援助、拡張、継続、貢献、衝突、維持、派遣、省略、履歴、冷静、募集、掲載。
3. **干扰项设计**：同音异义字、形似字、相同部首混淆。

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
        "part": "一、文字・語彙",
        "name": "③ 文脈規定",
        "count": 7,
        "instruction": "（　）に入れるのに最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出7道「文脈規定」题目。

【出题准则】
1. **考点**：N2级别的固定搭配、复合词、副词辨析。
2. **关键词参考**：～観、高～、～摩擦、社会貢献、経済成長率、情報漏洩、異文化理解、相変わらず、せめて、わざと。

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
        "part": "一、文字・語彙",
        "name": "④ 言い換え・類義",
        "count": 5,
        "instruction": "＿＿の言葉に意味が最も近いものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「言い換え・類義」题目。

【出题准则】
1. **考点**：N2级别近义词辨析。
2. **关键词参考**：愉快（面白い）、やむをえない（しかたない）、張り切る、冷静だ、深刻だ、質素だ、妥当だ。

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
        "part": "一、文字・語彙",
        "name": "⑤ 用法",
        "count": 5,
        "instruction": "次の言葉の使い方として最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「用法」题目。

【出题准则】
1. **难度**：严格N2级别。
2. **关键词参考**：延長、さびる、謙虚、納得、把握、冷静、豊富、衝突、深刻、恩恵、妥協、慎重。
3. **干扰项设计**：考查词汇的特定搭配（コロケーション）或语用限制（如“さびる”只能用于金属）。

【输出格式】严格输出JSON数组：
[
  {
    "target": "目标词",
    "options": ["句子1", "句子2", "句子3", "句子4"],
    "answer": 0,
    "explanation": "中文解析：说明为何此用法正确，并指出其他句子的搭配错误。"
  }
]"""
    },

    # ---- 二、文法 ----
    {
        "id": "grammar_fill",
        "part": "二、文法",
        "name": "⑥ 文の文法",
        "count": 12,
        "instruction": "次の文の（　）に入れるのに最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出12道「文の文法」题目。

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含（　）的完整日语句子",
    "options": ["语法A", "语法B", "语法C", "语法D"],
    "answer": 0,
    "explanation": "中文解析，说明这个语法的用法和接续方式"
  }
]"""
    },
    {
        "id": "grammar_order",
        "part": "二、文法",
        "name": "⑦ 文の組み立て",
        "count": 5,
        "instruction": "次の文の ★ に入る最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「文の組み立て」题目。

【题型说明】
给出一个句子，其中有★标记的位置需要填入一个词。从4个选项中选出★处应填的词。

【官方真题示例】
题目：結婚生活を送る ★ 、相手への思いやりの気持ちを持つことだと思う。
选项：1 うえで  2 といえば  3 大切か  4 何が
答案：4
解析：完整句子是「結婚生活を送る上で、何が大切かといえば、相手への思いやりの気持ちを持つことだと思う。」

题目：就職したときに ★ 、とうとう壊れたので、買い換えることにした。
选项：1 ずっと  2 買って以来  3 かばんが  4 使っていた
答案：3
解析：完整句子は「就職したときに買って以来、ずっと使っていたかばんがとうとう壊れたので、買い換えることにした。」

【重要】
- 题目中必须有★标记
- 给出的是打乱的4个片段
- 答案是★处应填入的词
- 必须能组成一个语法正确的完整句子

【输出格式】严格输出JSON数组：
[
  {
    "sentence": "含★的句子（★处需要填词）",
    "fragments": ["片段1", "片段2", "片段3", "片段4"],
    "complete_sentence": "完整的正确句子",
    "answer": 0,
    "explanation": "中文解析，说明完整语序"
  }
]"""
    },
    {
        "id": "grammar_passage",
        "part": "二、文法",
        "name": "⑧ 文章の文法",
        "count": 5,
        "instruction": "次の文章を読んで、文章全体の内容を考えて、＿＿から＿＿の中に入る最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出1道「文章の文法」题目，包含5个空格。

【题型说明】
给出一篇短文（4-6句），其中有5个空格，每个空格从4个选项中选出最合适的语法表达。

【官方真题示例】
（一篇关于厕所标志起源的短文，5个空格分别考查：）
- 空格1：疑问句形式（ご存じだろうか vs ご存じのようだ）
- 空格2：转折连接词（しかし vs それに vs または）
- 空格3：句子开头（こうして生まれたのが vs ここに生み出したのは）
- 空格4：被动/主动（使用されている vs 使用した点だ）
- 空格5：结尾表达（結果に違いない vs 結果のはずだった）

【干扰项设计要求】
- 话语连接词混淆（それに vs しかし vs または vs それどころか）
- 句尾形式（わけだ vs だろうか vs のようだ vs だからだろう）
- 被动vs主动（使用されている vs 使用した点だ）

【输出格式】严格输出JSON数组：
[
  {
    "passage": "短文内容，空格用（　）标注，并编号（　1　）（　2　）等",
    "blanks": [
      {
        "num": 1,
        "options": ["选项A", "选项B", "选项C", "选项D"],
        "answer": 0,
        "explanation": "中文解析"
      },
      {
        "num": 2,
        "options": ["选项A", "选项B", "选项C", "选项D"],
        "answer": 1,
        "explanation": "中文解析"
      }
    ]
  }
]"""
    },

    # ---- 三、読解 ----
    {
        "id": "reading_short",
        "part": "三、読解",
        "name": "⑨ 短文読解",
        "count": 5,
        "instruction": "次の＿＿から＿＿の文章を読んで、後の問いに対する答えとして最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出5道「短文読解」题目。

【题型说明】
每篇短文（100-200字）配1个问题，考查对作者观点或文章主旨的理解。

【官方真题示例】
文章：
「ルール」はなぜあるのでしょうか？スポーツを理解するために最初に確認しておきますが、スポーツは人間が楽しむためのものです。これが出発点です。決して「世の中に無ければならないモノ」でもなければ、生きるためにどうしても「必要なモノ」でもありませんが、楽しむためのモノであり、そのスポーツで楽しむために「ルール」があるのです。そして、ルールのもとで勝敗を競いますが、このことが楽しくないのであれば、スポーツをする価値はありません。
（高峰修『スポーツ教養入門』岩波書店による）

问题：筆者の考えに合うのはどれか。
选项：
1 ルールのないスポーツにも価値がある。
2 ルールはスポーツで楽しむためのものだ。
3 スポーツはルールを理解してから始めるべきだ。
4 スポーツを通して、ルールの重要さが理解できる。
答案：2

【文章类型】
- 议论文（作者观点）
- 通知/社内文书（目的）
- 随笔/评论（主旨）

【干扰项设计要求】
- 部分正确但不完整
- 与原文意思相反
- 过于极端的表述
- 文中未提及的内容

【输出格式】严格输出JSON数组：
[
  {
    "passage": "100-200字的日语文章",
    "question": "问题（如：筆者の考えに合うのはどれか。）",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": 0,
    "explanation": "中文解析，说明答案在文章中的依据"
  }
]"""
    },
    {
        "id": "reading_medium",
        "part": "三、読解",
        "name": "⑩ 中文読解",
        "count": 4,
        "instruction": "次の文章を読んで、後の問いに対する答えとして最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出2篇「中文読解」，每篇2个问题（共4题）。

【题型说明】
每篇中等长度文章（300-500字）配2个问题，考查对作者论点的理解。

【官方真题示例主题】
- 个性论（日本人对个性的误解）
- 教育观（学习方法的思考）
- 社会现象分析

【问题类型】
- 作者对XX的看法是什么？（～について、筆者はどのように述べているか。）
- 与作者观点一致的是？（筆者の考えに合うものはどれか。）

【干扰项设计要求】
- 文中提到但不是答案的内容
- 与作者观点相反的理解
- 过度推断

【输出格式】严格输出JSON数组：
[
  {
    "passage": "300-500字的日语文章",
    "questions": [
      {
        "question": "问题1",
        "options": ["A", "B", "C", "D"],
        "answer": 0,
        "explanation": "解析"
      },
      {
        "question": "问题2",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "explanation": "解析"
      }
    ]
  }
]"""
    },
    {
        "id": "reading_long",
        "part": "三、読解",
        "name": "⑪ 長文読解",
        "count": 1,
        "instruction": "次の文章を読んで、後の問いに対する答えとして最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出1篇「長文読解」，配4个问题。

【题型说明】
一篇长文（600-800字）配4个问题，考查深层理解和推理能力。

【官方真题示例主题】
- 设计灵感（感動の森）
- 人生哲学
- 社会观察

【问题类型】
- 细节理解（～とはどのようなことか。）
- 作者观点（筆者の考えに合うのはどれか。）
- 推理判断（～について、筆者はどのように考えているか。）

【输出格式】严格输出JSON数组：
[
  {
    "passage": "600-800字的日语文章",
    "questions": [
      {
        "question": "Q1",
        "options": ["A", "B", "C", "D"],
        "answer": 0,
        "explanation": "解析"
      },
      {
        "question": "Q2",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "explanation": "解析"
      },
      {
        "question": "Q3",
        "options": ["A", "B", "C", "D"],
        "answer": 2,
        "explanation": "解析"
      },
      {
        "question": "Q4",
        "options": ["A", "B", "C", "D"],
        "answer": 3,
        "explanation": "解析"
      }
    ]
  }
]"""
    },
    {
        "id": "reading_search",
        "part": "三、読解",
        "name": "⑫ 情報検索",
        "count": 2,
        "instruction": "右のページは、あるホテルのホームページに載っている案内である。下の問いに対する答えとして最もよいものを、１・２・３・４から一つ選びなさい。",
        "prompt": """你是一位JLPT N2出题专家。请出1篇「情報検索」，配2个问题。

【题型说明】
给出一个实用信息文档（酒店指南、时刻表、公告等），从中检索特定信息。

【官方真题示例】
文档：酒店自助餐指南（包含餐厅名、时段、价格、年龄段分类、特别席位附加费等）
问题1：某人想在特定条件下用餐，选哪个最合适？
问题2：某人要计算特定条件下的费用，是多少？

【文档类型】
- 酒店/餐厅指南
- 时刻表/日程表
- 公告/通知
- 网页信息

【干扰项设计要求】
- 读错条件（日期、时间、年龄段）
- 漏算附加费用
- 搞混不同选项的条件

【输出格式】严格输出JSON数组：
[
  {
    "passage": "实用信息文档内容（模拟真实场景）",
    "questions": [
      {
        "question": "问题1（带具体人物和条件）",
        "options": ["A", "B", "C", "D"],
        "answer": 0,
        "explanation": "解析，说明从哪里找到信息"
      },
      {
        "question": "问题2",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "explanation": "解析"
      }
    ]
  }
]"""
    },
]


# ============================================================
# 题目校验模块
# ============================================================

def validate_question(section_id, q_data):
    """校验单道题目的质量。返回 (is_valid, errors)。"""
    errors = []

    # 1. 基础结构检查
    options = q_data.get("options", [])
    if not options or len(options) < 4:
        errors.append(f"选项数量不足: {len(options) if options else 0}")
        return False, errors

    # 2. 检查是否有answer和explanation
    answer = q_data.get("answer")
    if answer is None or not isinstance(answer, int) or answer < 0 or answer >= len(options):
        errors.append(f"answer值无效: {answer}")
    if not q_data.get("explanation"):
        errors.append("缺少explanation")

    # 3. 语言质量检查 (Level Heuristics)
    # N5/N4基础词汇黑名单
    BASICS_BLACKLIST = ["方法", "文化", "料理", "勉強", "行く", "食べる", "美味しい", "簡単", "親切", "元気"]

    sentence = q_data.get("sentence", q_data.get("question", ""))
    target = q_data.get("target", "")

    # 检查目标词是否太简单
    for word in BASICS_BLACKLIST:
        if word in target:
            errors.append(f"目标词包含低级词汇: {word}")

    # 4. 针对不同题型的特殊校验
    if section_id == "vocab_reading":
        # 汉字读音题：target必须包含汉字，options必须是纯假名
        if not any('\u4e00' <= char <= '\u9fff' for char in target):
            errors.append(f"汉字读音题目标词不含汉字: {target}")
        for opt in options:
            if any('\u4e00' <= char <= '\u9fff' for char in str(opt)):
                 errors.append(f"读音选项包含汉字: {opt}")

    if section_id == "vocab_kanji":
        # 汉字书写题：target必须是假名，options必须包含汉字
        if any('\u4e00' <= char <= '\u9fff' for char in target):
            errors.append(f"汉字书写题目标词含有汉字: {target}")

    if section_id == "grammar_order":
        if not q_data.get("fragments") or len(q_data.get("fragments", [])) != 4:
            errors.append("排序题片段数量错误")
        if "★" not in q_data.get("sentence", ""):
            errors.append("排序题句子缺少★")

    return len(errors) == 0, errors


def validate_section(section_id, questions):
    """校验一个section的所有题目。返回 (valid_count, total_count, all_errors)。"""
    all_errors = []
    valid_count = 0

    for i, q in enumerate(questions):
        is_valid, errors = validate_question(section_id, q)
        if is_valid:
            valid_count += 1
        else:
            all_errors.append(f"  第{i+1}题: {'; '.join(errors)}")

    return valid_count, len(questions), all_errors


def flatten_questions(section_def, section_data):
    """展平section数据为题目列表（处理阅读题的嵌套结构）。"""
    if section_data is None:
        return []

    questions = []
    for item in section_data:
        if "questions" in item and isinstance(item["questions"], list):
            # 阅读题：passage + 多个子问题
            for sub_q in item["questions"]:
                q = dict(sub_q)
                q["passage"] = item.get("passage", "")
                questions.append(q)
        elif "blanks" in item and isinstance(item["blanks"], list):
            # 文章语法：passage + 多个空格
            for blank in item["blanks"]:
                q = dict(blank)
                q["passage"] = item.get("passage", "")
                questions.append(q)
        else:
            questions.append(item)
    return questions


# ============================================================
# API 调用
# ============================================================

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


def call_api(provider, prompt, env):
    if provider == "zhipu":
        url = env["ZHIPU_BASE_URL"]
        headers = {"Authorization": f"Bearer {env['ZHIPU_API_KEY']}", "Content-Type": "application/json"}
        data = json.dumps({"model": "glm-4-flash", "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    elif provider == "ark":
        url = env["ARK_BASE_URL"]
        headers = {"Authorization": f"Bearer {env['ARK_API_KEY']}", "Content-Type": "application/json"}
        data = json.dumps({"model": "doubao-seed-2-0-pro-260215", "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    elif provider == "mimo":
        url = env["MIMO_BASE_URL"]
        headers = {"Authorization": f"Bearer {env['MIMO_API_KEY']}", "Content-Type": "application/json"}
        data = json.dumps({"model": env["MIMO_MODEL"], "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    else:
        return None

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def extract_json(text):
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


def call_section_with_retry(provider, section, env, max_retries=2):
    """调用API出题，带重试和校验。"""
    for attempt in range(max_retries + 1):
        print(f"  [{provider}] {section['name']} ({section['count']}题) " + (f"(重试{attempt})" if attempt > 0 else "") + " ...", flush=True)

        full_prompt = section['prompt']
        raw = call_api(provider, full_prompt, env)

        if not raw or raw.startswith("ERROR"):
            print(f"  [{provider}] {section['name']} -> API错误: {raw}")
            continue

        parsed = extract_json(raw)
        if parsed is None:
            print(f"  [{provider}] {section['name']} -> JSON解析失败")
            continue

        # 校验
        flat = flatten_questions(section, parsed)
        valid_count, total_count, errors = validate_section(section["id"], flat)

        if valid_count == total_count:
            print(f"  [{provider}] {section['name']} -> OK ({total_count}题全部通过校验)")
            return parsed
        else:
            print(f"  [{provider}] {section['name']} -> 校验: {valid_count}/{total_count} 通过")
            for err in errors[:3]:
                print(f"    {err}")
            if attempt < max_retries:
                print(f"    -> 重试...")
            else:
                print(f"    -> 已达最大重试次数，使用当前结果")
                return parsed

    return None


# ============================================================
# HTML 生成
# ============================================================

def build_q_html(num, key, q_data):
    """Build HTML for one question."""
    html = f'<div class="question-block" id="block_{key}">'
    html += f'<div class="question-text">{num}. '

    target = q_data.get("target", "")
    sentence = q_data.get("sentence", q_data.get("question", ""))

    if target and target in sentence:
        html += sentence.replace(target, f'<span class="target-word">{target}</span>')
    else:
        html += sentence

    html += '</div>'

    # Passage (for reading questions)
    if q_data.get("passage"):
        html += f'<div class="passage">{q_data["passage"]}</div>'

    # Fragments (for sentence ordering)
    if q_data.get("fragments"):
        html += f'<div class="fragments">{"　".join(q_data["fragments"])}</div>'

    # Options
    if q_data.get("options"):
        html += f'<ul class="options" data-key="{key}">'
        for i, opt in enumerate(q_data["options"]):
            label = "１２３４"[i] if i < 4 else str(i+1)
            html += f'<li><label><input type="radio" name="{key}" value="{i}" onclick="selectAnswerByKey(\'{key}\',{i})"> {label}. {opt}</label></li>'
        html += '</ul>'

    # Explanation
    explanation = q_data.get("explanation", "")
    if explanation:
        html += f'<div class="explanation" id="exp_{key}">💡 {explanation}</div>'

    html += '</div>'
    return html


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JLPT N2 模拟试卷 — __PROVIDER__</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Hiragino Sans", "Yu Gothic", "Noto Sans JP", sans-serif; background: #fff; color: #111; line-height: 1.9; max-width: 800px; margin: 0 auto; padding: 20px 20px 80px; }
h1 { font-size: 24px; margin-bottom: 4px; }
h2 { font-size: 20px; margin: 30px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #111; }
.subtitle { color: #666; font-size: 14px; margin-bottom: 20px; }
.instruction { color: #555; font-size: 14px; margin-bottom: 12px; font-style: italic; }
.passage { background: #f9f9f9; border-left: 3px solid #333; padding: 14px 18px; margin: 12px 0; font-size: 15px; white-space: pre-wrap; line-height: 2; }
.question-block { margin: 18px 0; padding: 14px; border: 1px solid #ddd; border-radius: 6px; }
.question-block.answered-correct { border-color: #2e7d32; background: #f1f8e9; }
.question-block.answered-wrong { border-color: #c62828; background: #ffebee; }
.question-text { font-size: 16px; font-weight: bold; margin-bottom: 10px; line-height: 1.8; }
.target-word { background: #fff9c4; padding: 1px 4px; border-bottom: 2px solid #f9a825; }
.fragments { background: #e3f2fd; padding: 10px 14px; margin: 10px 0; border-radius: 4px; font-size: 15px; }
.options { list-style: none; }
.options li { margin: 5px 0; }
.options label { display: block; padding: 10px 14px; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 15px; line-height: 1.6; }
.options label:hover { background: #f5f5f5; }
.options input[type="radio"] { margin-right: 10px; }
.options label.selected-correct { background: #e8f5e9; border-color: #2e7d32; }
.options label.selected-wrong { background: #ffebee; border-color: #c62828; }
.options label.show-correct { background: #e8f5e9; border-color: #2e7d32; font-weight: bold; }
.explanation { display: none; margin-top: 10px; padding: 10px 14px; background: #fff8e1; border-radius: 4px; font-size: 14px; color: #333; border-left: 3px solid #ffa000; }
.explanation.show { display: block; }
.nav { position: sticky; top: 0; background: #fff; padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 20px; z-index: 10; }
.nav a { display: inline-block; width: 30px; height: 30px; line-height: 30px; text-align: center; border: 1px solid #ccc; border-radius: 4px; margin: 2px; font-size: 12px; text-decoration: none; color: #333; }
.nav a.done-correct { background: #e8f5e9; border-color: #2e7d32; }
.nav a.done-wrong { background: #ffebee; border-color: #c62828; }
.score-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #111; color: #fff; padding: 12px 20px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
.score-bar .score { font-size: 20px; font-weight: bold; }
.btn { padding: 8px 18px; background: #fff; color: #111; border: 1px solid #111; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn:hover { background: #f5f5f5; }
</style>
</head>
<body>
<h1>JLPT N2 模拟试卷</h1>
<div class="subtitle">Provider: __PROVIDER__ | 共 __TOTAL__ 题</div>
<div class="nav" id="nav"></div>
__CONTENT__
<div style="height:60px"></div>
<div class="score-bar">
  <div>进度: <span id="progress">0</span> / __TOTAL__</div>
  <div>得分: <span class="score" id="score">0</span> / <span id="answered">0</span></div>
  <button class="btn" onclick="resetAll()">重置</button>
</div>
<script>
const DATA = __DATA_JSON__;
let answered = 0, correct = 0;
const questionMap = [];
DATA.forEach((sec, si) => {
  sec.questions.forEach((q, qi) => {
    questionMap.push({si, qi, key: q._key || ''});
  });
});
function init() {
  let nav = '';
  questionMap.forEach((q, i) => {
    nav += `<a href="#block_${q.key}" id="nav_${q.key}">${i+1}</a>`;
  });
  document.getElementById('nav').innerHTML = nav;
}
function selectAnswerByKey(key, optIdx) {
  const entry = questionMap.find(q => q.key === key);
  if (!entry) return;
  const q = DATA[entry.si].questions[entry.qi];
  if (q._answered) return;
  q._answered = true;
  const isCorrect = (optIdx === q.answer);
  const labels = document.querySelectorAll(`[data-key="${key}"] label`);
  labels.forEach((label, i) => {
    label.querySelector('input').disabled = true;
    if (i === optIdx && !isCorrect) label.classList.add('selected-wrong');
    if (i === q.answer) label.classList.add('show-correct');
    if (i === optIdx && isCorrect) label.classList.add('selected-correct');
  });
  const expEl = document.getElementById(`exp_${key}`);
  if (expEl) expEl.classList.add('show');
  const block = document.getElementById(`block_${key}`);
  if (block) block.classList.add(isCorrect ? 'answered-correct' : 'answered-wrong');
  const navEl = document.getElementById(`nav_${key}`);
  if (navEl) navEl.classList.add(isCorrect ? 'done-correct' : 'done-wrong');
  answered++;
  if (isCorrect) correct++;
  document.getElementById('progress').textContent = answered;
  document.getElementById('score').textContent = correct;
  document.getElementById('answered').textContent = answered;
}
function resetAll() {
  if (!confirm('确定重置所有答案？')) return;
  DATA.forEach(sec => sec.questions.forEach(q => q._answered = false));
  document.querySelectorAll('.question-block').forEach(b => b.classList.remove('answered-correct','answered-wrong'));
  document.querySelectorAll('label').forEach(l => l.classList.remove('selected-correct','selected-wrong','show-correct'));
  document.querySelectorAll('input[type="radio"]').forEach(r => r.disabled = false);
  document.querySelectorAll('.explanation').forEach(e => e.classList.remove('show'));
  document.querySelectorAll('.nav a').forEach(a => a.classList.remove('done-correct','done-wrong'));
  answered = 0; correct = 0;
  document.getElementById('progress').textContent = 0;
  document.getElementById('score').textContent = 0;
  document.getElementById('answered').textContent = 0;
}
init();
</script>
</body>
</html>"""


def build_final_html(provider_name, sections_data):
    """Build complete interactive HTML exam."""
    content_parts = []
    data_js = []
    total = 0

    for sec_idx, section_def in enumerate(EXAM_SECTIONS):
        section_data = sections_data.get(section_def["id"])
        sec_html = f'<h2>{section_def["name"]}</h2>'
        sec_html += f'<div class="instruction">{section_def["instruction"]}</div>'

        if section_data is None:
            sec_html += '<p style="color:red;">出题失败</p>'
            data_js.append({"name": section_def["name"], "questions": []})
            content_parts.append(sec_html)
            continue

        questions_js = []
        q_html_parts = []

        # Flatten questions
        flat = []
        for item in section_data:
            if "questions" in item and isinstance(item["questions"], list):
                passage = item.get("passage", "")
                for sub_q in item["questions"]:
                    q = dict(sub_q)
                    q["_passage"] = passage
                    flat.append(q)
            elif "blanks" in item and isinstance(item["blanks"], list):
                passage = item.get("passage", "")
                for blank in item["blanks"]:
                    q = dict(blank)
                    q["_passage"] = passage
                    flat.append(q)
            else:
                flat.append(item)

        for q_idx, q_data in enumerate(flat):
            total += 1
            key = f"s{sec_idx}_{q_idx}_{total}"

            # Add passage if exists
            if q_data.get("_passage") and q_idx == 0:
                q_html_parts.append(f'<div class="passage">{q_data["_passage"]}</div>')
            elif q_data.get("passage") and q_idx == 0:
                q_html_parts.append(f'<div class="passage">{q_data["passage"]}</div>')

            q_html_parts.append(build_q_html(total, key, q_data))

            # Build JS data
            js_q = {
                "_key": key,
                "answer": q_data.get("answer", 0),
                "explanation": q_data.get("explanation", ""),
                "_answered": False,
            }
            questions_js.append(js_q)

        data_js.append({"name": section_def["name"], "questions": questions_js})
        content_parts.append(sec_html + "".join(q_html_parts))

    html = HTML_TEMPLATE
    html = html.replace("__PROVIDER__", provider_name)
    html = html.replace("__TOTAL__", str(total))
    html = html.replace("__CONTENT__", "\n".join(content_parts))
    html = html.replace("__DATA_JSON__", json.dumps(data_js, ensure_ascii=False))
    return html


# ============================================================
# Main
# ============================================================

def main():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    env = load_env(env_path)

    providers = ["zhipu", "ark", "mimo"]
    names = {
        "zhipu": "智谱AI (GLM-4-Flash)",
        "ark": "火山ARK (Doubao-Seed-2.0-Pro)",
        "mimo": "小米MiMo (mimo-v2.5-pro)",
    }

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("JLPT N2 模拟试卷生成器 v2")
    print("=" * 60)
    print(f"题型: {len(EXAM_SECTIONS)} 种 | Provider: {len(providers)} 个")
    print(f"特性: 基于官方真题格式 + 自动校验 + 失败重试")
    print(f"输出: {output_dir}/")
    print()

    for provider in providers:
        print(f"\n{'=' * 60}")
        print(f"生成: {names[provider]}")
        print(f"{'=' * 60}")

        sections_data = {}
        for section in EXAM_SECTIONS:
            result = call_section_with_retry(provider, section, env, max_retries=2)
            sections_data[section["id"]] = result

        # Generate HTML
        html = build_final_html(names[provider], sections_data)
        path = os.path.join(output_dir, f"exam_{provider}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n  已保存: {path}")

        # Generate validation report
        print(f"\n  --- {provider} 校验报告 ---")
        total_valid = 0
        total_questions = 0
        for section in EXAM_SECTIONS:
            data = sections_data.get(section["id"])
            flat = flatten_questions(section, data)
            valid, total, errors = validate_section(section["id"], flat)
            total_valid += valid
            total_questions += total
            status = "✓" if valid == total else "✗"
            print(f"  {status} {section['name']}: {valid}/{total}")
            for err in errors[:2]:
                print(f"    {err}")
        print(f"  总计: {total_valid}/{total_questions} 通过校验")

    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"请用浏览器打开 output/ 下的HTML文件做题对比。")


if __name__ == "__main__":
    main()
