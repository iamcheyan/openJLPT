#!/usr/bin/env python3
"""
JLPT 模拟考试服务器
- 支持 N1-N5，通过 URL 参数 ?level=n1~n5 切换
- 加载题库，首次访问随机抽题，客户端 localStorage 保持
- 基于 template/exam_base.html 渲染静态 HTML
- 支持 --export 导出静态文件
"""

import json
import random
import os
import sys
import argparse
import errno
import signal
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# 题型配置：section_id -> { section_num, 抽题数量 }
# count 为 None 表示全部
# ============================================================
SECTION_CONFIG = {
    "vocab_reading":    {"s": 1, "count": 5},
    "vocab_kanji":      {"s": 2, "count": 5},
    "vocab_context":    {"s": 3, "count": 5},
    "vocab_synonym":    {"s": 4, "count": 5},
    "vocab_usage":      {"s": 5, "count": 5},
    "grammar_fill":     {"s": 6, "count": 12},
    "grammar_order":    {"s": 7, "count": 5},
    "grammar_passage":  {"s": 8, "count": None},
    "reading_short":    {"s": 9, "count": None},
    "reading_medium":   {"s": 10, "count": None},
    "reading_long":     {"s": 11, "count": None},
    "reading_search":   {"s": 12, "count": None},
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template", "exam_base.html")

VALID_LEVELS = ("n1", "n2", "n3", "n4", "n5")
DEFAULT_LEVEL = "n2"
LEVEL_NAMES = {"n1": "N1", "n2": "N2", "n3": "N3", "n4": "N4", "n5": "N5"}

# 缓存各等级的题库，按需加载
_banks_cache = {}


def load_banks(level=DEFAULT_LEVEL):
    """加载指定等级的题库文件。"""
    if level in _banks_cache:
        return _banks_cache[level]
    data_dir = os.path.join(BASE_DATA_DIR, level)
    banks = {}
    for section_id in SECTION_CONFIG:
        path = os.path.join(data_dir, f"{section_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    banks[section_id] = json.load(f)
            except json.JSONDecodeError:
                pass
    _banks_cache[level] = banks
    return banks


import re

_BLANK_RE = re.compile(r'（[ 　\d]*）')
_STAR_RE = re.compile(r'★')


def wrap_target_word(sentence, target):
    """把句子中的 《target》 替换为 target-word span。
    如果没有 《》 标记，但 target 在 sentence 中，直接高亮 target。
    """
    if not target or not sentence:
        return sentence
    if f"《{target}》" in sentence:
        return sentence.replace(f"《{target}》", f'<span class="target-word">{target}</span>')
    if target in sentence:
        return sentence.replace(target, f'<span class="target-word">{target}</span>', 1)
    return sentence


def highlight_blanks(text):
    """高亮文本中的填空括号（　）和排序标记 ★。"""
    if not text:
        return text
    # 高亮 ★
    text = _STAR_RE.sub('<span class="target-word">★</span>', text)
    # 高亮（　）、（　1　）、（ 45 ）等
    text = _BLANK_RE.sub(lambda m: f'<span class="target-word">{m.group(0)}</span>', text)
    return text


def has_target_word(text):
    """检查文本中是否已包含 target-word 高亮。"""
    return text and 'target-word' in text


def try_extract_target(sentence, options, answer_idx):
    """尝试从 sentence 中提取正确答案词并替换为带高亮的空白。
    用于处理那些 sentence 是完整句子、没有括号的题目。"""
    if not sentence or not options or answer_idx is None:
        return sentence
    ans_word = options[answer_idx]
    # 优先匹配不含助词的裸词（去掉 trailing だ/です/する等）
    stripped = ans_word.rstrip('する').rstrip('だ').rstrip('です')
    candidates = [ans_word]
    if stripped and stripped != ans_word:
        candidates.insert(0, stripped)
    for cand in candidates:
        if cand in sentence:
            return sentence.replace(cand, '<span class="target-word">（　）</span>', 1)
    return sentence


def build_questions(banks, include_all=False):
    """从题库抽题并转换为模板 JS 格式，返回 QUESTIONS 列表。
    include_all=True 时返回全部题（客户端抽题），否则服务端随机抽题。"""
    questions = []

    for section_id, config in SECTION_CONFIG.items():
        if section_id not in banks:
            continue

        bank = banks[section_id]
        raw_list = bank.get("questions", [])
        if not raw_list:
            continue

        count = config["count"]
        s = config["s"]

        # ---------- 文章语法（passage + blanks）----------
        if section_id == "grammar_passage":
            selected = raw_list if (include_all or count is None or count >= len(raw_list)) else random.sample(raw_list, count)
            for item in selected:
                passage = highlight_blanks(item.get("passage", ""))
                for blank in item.get("blanks", []):
                    questions.append({
                        "s": s,
                        "pas": passage,
                        "txt": f"（　{blank['num']}　）",
                        "opts": blank.get("options", []),
                        "ans": blank.get("answer", 0),
                        "exp": blank.get("explanation", ""),
                    })

        # ---------- 阅读（passage + sub-questions）----------
        elif section_id.startswith("reading_"):
            if section_id == "reading_short":
                # 单题结构，每题自带 passage
                selected = raw_list if (include_all or count is None or count >= len(raw_list)) else random.sample(raw_list, count)
                for q in selected:
                    questions.append({
                        "s": s,
                        "pas": q.get("passage", ""),
                        "txt": q.get("question", ""),
                        "opts": q.get("options", []),
                        "ans": q.get("answer", 0),
                        "exp": q.get("explanation", ""),
                    })
            else:
                # passage 嵌套结构
                selected = raw_list if (include_all or count is None or count >= len(raw_list)) else random.sample(raw_list, count)
                for item in selected:
                    passage = item.get("passage", "")
                    for sub in item.get("questions", []):
                        questions.append({
                            "s": s,
                            "pas": passage,
                            "txt": sub.get("question", ""),
                            "opts": sub.get("options", []),
                            "ans": sub.get("answer", 0),
                            "exp": sub.get("explanation", ""),
                        })

        # ---------- 排序题 ----------
        elif section_id == "grammar_order":
            selected = raw_list if (include_all or count is None or count >= len(raw_list)) else random.sample(raw_list, count)
            for q in selected:
                frags = q.get("fragments") or q.get("options", [])
                star_parts = []
                markers = ["１", "２", "３", "４"]
                for i, frag in enumerate(frags):
                    star_parts.append(f"{markers[i]}. {frag}")
                questions.append({
                    "s": s,
                    "txt": highlight_blanks(q.get("sentence", "")),
                    "star": "　".join(star_parts),
                    "opts": frags,
                    "ans": q.get("answer", 0),
                    "exp": q.get("explanation", ""),
                })

        # ---------- 普通单题 ----------
        else:
            selected = raw_list if (include_all or count is None or count >= len(raw_list)) else random.sample(raw_list, count)
            for q in selected:
                sentence = q.get("sentence", "")
                target = q.get("target", "")
                options = q.get("options", [])
                answer = q.get("answer", 0)

                if section_id == "vocab_usage":
                    # 没有 sentence，直接用 target 作为考点提示
                    sentence = f'<span class="target-word">{target}</span>'

                elif section_id in ("vocab_reading", "vocab_kanji", "vocab_synonym"):
                    sentence = wrap_target_word(sentence, target)

                elif section_id == "vocab_context":
                    sentence = highlight_blanks(sentence)
                    if not has_target_word(sentence):
                        sentence = try_extract_target(sentence, options, answer)

                elif section_id == "grammar_fill":
                    sentence = highlight_blanks(sentence)

                questions.append({
                    "s": s,
                    "txt": sentence,
                    "opts": options,
                    "ans": answer,
                    "exp": q.get("explanation", ""),
                })

    return questions


def build_bank_stats(banks):
    """统计每个题型的可用题目数量，返回 {section_id: count}。"""
    stats = {}
    for section_id in SECTION_CONFIG:
        if section_id not in banks:
            stats[section_id] = 0
            continue
        raw = banks[section_id].get("questions", [])
        if section_id == "grammar_passage":
            stats[section_id] = sum(len(item.get("blanks", [])) for item in raw)
        elif section_id.startswith("reading_") and section_id != "reading_short":
            stats[section_id] = sum(len(item.get("questions", [])) for item in raw)
        else:
            stats[section_id] = len(raw)
    return stats


def bank_stats_to_js(banks):
    """生成 BANK_STATS JS 对象字符串，包含每个 JSON 文件的题目数和文件名。"""
    stats = build_bank_stats(banks)
    lines = ["const BANK_STATS = {"]
    for section_id, config in SECTION_CONFIG.items():
        count = stats.get(section_id, 0)
        filename = f"{section_id}.json"
        bank = banks.get(section_id, {})
        meta = bank.get("meta", {})
        display_name = meta.get("name", section_id)
        lines.append(f'    "{section_id}": {{ s:{config["s"]}, total:{count}, file:"{filename}", name:"{display_name}" }},')
    lines.append("};")
    return "\n".join(lines)


def questions_to_js(questions, include_all=False):
    """把 Python 问题列表转成 JS 数组字符串（保持字段顺序，无引号 key）。"""
    lines = []
    if include_all:
        lines.append("const SELECT_ALL = true;")
        lines.append("const SECTION_COUNTS = {")
        for section_id, config in SECTION_CONFIG.items():
            count = config["count"]
            lines.append(f"    {config['s']}: {count if count is not None else 'null'},")
        lines.append("};")
    lines.append("")
    lines.append("const QUESTIONS = [")
    for q in questions:
        parts = [f"s:{q['s']}"]
        if q.get("pas"):
            parts.append(f'pas:{json.dumps(q["pas"], ensure_ascii=False)}')
        parts.append(f'txt:{json.dumps(q["txt"], ensure_ascii=False)}')
        if q.get("star"):
            parts.append(f'star:{json.dumps(q["star"], ensure_ascii=False)}')
        parts.append(f'opts:{json.dumps(q["opts"], ensure_ascii=False)}')
        parts.append(f"ans:{q['ans']}")
        if q.get("exp"):
            parts.append(f'exp:{json.dumps(q["exp"], ensure_ascii=False)}')
        lines.append("    {" + ", ".join(parts) + "},")
    lines.append("];")
    return "\n".join(lines)


def build_html(banks, level=DEFAULT_LEVEL):
    """读取模板，替换 QUESTIONS 占位符，返回完整 HTML。"""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    questions = build_questions(banks, include_all=True)
    level_js = f'const CURRENT_LEVEL = "{level}";'
    questions_js = level_js + "\n\n" + bank_stats_to_js(banks) + "\n\n" + questions_to_js(questions, include_all=True)

    if "/*QUESTIONS_DATA*/" not in template:
        raise RuntimeError("模板中未找到 /*QUESTIONS_DATA*/ 占位符")

    html = template.replace("/*QUESTIONS_DATA*/", questions_js)
    # 替换标题中的等级
    html = html.replace("N2 模擬試験", f"{LEVEL_NAMES.get(level, level.upper())} 模擬試験")
    html = html.replace("JLPT N2", f"JLPT {LEVEL_NAMES.get(level, level.upper())}")
    return html


def export_html(output_path, level=None):
    """导出静态 HTML 文件。level=None 时导出所有等级。"""
    levels = [level] if level else list(VALID_LEVELS)
    for lv in levels:
        banks = load_banks(lv)
        html = build_html(banks, lv)
        if level:
            out = output_path
        else:
            base, ext = os.path.splitext(output_path)
            out = f"{base}_{lv}{ext}"
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"已导出: {out}")


# ============================================================
# HTTP Server
# ============================================================

class ExamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        level = params.get("level", [DEFAULT_LEVEL])[0].lower()
        if level not in VALID_LEVELS:
            level = DEFAULT_LEVEL

        if parsed.path == "/" or parsed.path == "":
            banks = load_banks(level)
            html = build_html(banks, level)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def _listening_socket_inodes(port):
    """Return socket inodes listening on the given TCP port."""
    inodes = set()
    port_hex = f"{port:04X}"
    for proc_path in ("/proc/net/tcp", "/proc/net/tcp6"):
        if not os.path.exists(proc_path):
            continue
        with open(proc_path, "r", encoding="utf-8") as f:
            next(f, None)
            for line in f:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local_address = parts[1]
                state = parts[3]
                inode = parts[9]
                if state == "0A" and local_address.rsplit(":", 1)[-1] == port_hex:
                    inodes.add(inode)
    return inodes


def _pids_for_socket_inodes(inodes):
    """Return PIDs that own any socket inode in inodes."""
    if not inodes:
        return set()
    pids = set()
    self_pid = os.getpid()
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == self_pid:
            continue
        fd_dir = os.path.join("/proc", name, "fd")
        if not os.path.isdir(fd_dir):
            continue
        try:
            for fd in os.listdir(fd_dir):
                try:
                    target = os.readlink(os.path.join(fd_dir, fd))
                except OSError:
                    continue
                if target.startswith("socket:[") and target[8:-1] in inodes:
                    pids.add(pid)
                    break
        except PermissionError:
            continue
    return pids


def _cmdline_for_pid(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read().replace(b"\x00", b" ").strip()
        return raw.decode("utf-8", errors="replace") or f"pid {pid}"
    except OSError:
        return f"pid {pid}"


def kill_processes_on_port(port):
    """Terminate processes listening on port. Returns killed PID count."""
    if not os.path.exists("/proc/net/tcp"):
        print(f"[WARN] 无法检查端口 {port}: 当前系统没有 /proc/net/tcp")
        return 0

    pids = _pids_for_socket_inodes(_listening_socket_inodes(port))
    if not pids:
        return 0

    print(f"端口 {port} 已被占用，准备终止占用进程:")
    for pid in sorted(pids):
        print(f"  PID {pid}: {_cmdline_for_pid(pid)}")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.time() + 2
    remaining = set(pids)
    while remaining and time.time() < deadline:
        remaining = {pid for pid in remaining if os.path.exists(f"/proc/{pid}")}
        if remaining:
            time.sleep(0.1)

    for pid in sorted(remaining):
        print(f"  PID {pid}: SIGTERM 后仍在运行，发送 SIGKILL")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return len(pids)


def create_server_or_reclaim_port(port):
    try:
        return HTTPServer(("0.0.0.0", port), ExamHandler)
    except OSError as e:
        if e.errno != errno.EADDRINUSE:
            raise

    killed = kill_processes_on_port(port)
    if not killed:
        raise OSError(errno.EADDRINUSE, f"端口 {port} 被占用，但没有找到可终止的监听进程")

    time.sleep(0.2)
    return HTTPServer(("0.0.0.0", port), ExamHandler)


def run_server(port=8080):
    server = create_server_or_reclaim_port(port)
    print(f"Server running at http://0.0.0.0:{port}")
    print(f"支持等级: {', '.join(VALID_LEVELS)}  (默认: {DEFAULT_LEVEL})")
    print(f"访问方式: http://localhost:{port}/?level=n1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(description="JLPT 模拟考试服务器")
    parser.add_argument("--export", metavar="PATH", help="导出静态 HTML 文件并退出")
    parser.add_argument("--level", choices=VALID_LEVELS, help="导出指定等级 (默认: 全部)")
    parser.add_argument("--port", type=int, default=8080, help="HTTP 端口 (默认: 8080)")
    args = parser.parse_args()

    if args.export:
        export_html(args.export, level=args.level)
    else:
        run_server(args.port)


if __name__ == "__main__":
    main()
