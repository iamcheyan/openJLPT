#!/usr/bin/env python3
"""
JLPT 题库进度报告生成器。

用法:
    python3 tools/count_questions.py N2
    python3 tools/count_questions.py N2 --report   # 同时生成 Markdown 报告

功能:
    1. 统计 data/<level>/ 下各题型的当前题数
    2. 读取 resources/ 下的资源文件，获取目标数量
    3. 计算每种题型的覆盖率和缺口
    4. 在终端打印表格，并可选生成 Markdown 报告
"""

import csv
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent

# 题型分类
CATEGORIES = {
    "文字・語彙": [
        "vocab_reading",   # 漢字の読み方
        "vocab_kanji",     # 漢字の表記
        "vocab_context",   # 文脈規定
        "vocab_synonym",   # 言い換え・類義
        "vocab_usage",     # 用法
    ],
    "文法": [
        "grammar_fill",    # 文の文法
        "grammar_order",   # 文の組み立て
        "grammar_passage", # 文章の文法
    ],
    "読解": [
        "reading_short",   # 短文読解
        "reading_medium",  # 中文読解
        "reading_long",    # 長文読解
        "reading_search",  # 情報検索
    ],
}

# 题型中文名
TYPE_NAMES = {
    "vocab_reading":   "漢字の読み方",
    "vocab_kanji":     "漢字の表記",
    "vocab_context":   "文脈規定",
    "vocab_synonym":   "言い換え・類義",
    "vocab_usage":     "用法",
    "grammar_fill":    "文の文法",
    "grammar_order":   "文の組み立て",
    "grammar_passage": "文章の文法",
    "reading_short":   "短文読解",
    "reading_medium":  "中文読解",
    "reading_long":    "長文読解",
    "reading_search":  "情報検索",
}

# 资源映射：题型 -> (资源路径, 说明)
# 词汇题型共享同一个词表，每个词在每种题型下都应出一道题
VOCAB_RESOURCE = ("resources/vocabulary/{level}.csv", "词汇总量")
GRAMMAR_RESOURCE = ("resources/grammar/{level}.json", "语法点数量")
KANJI_RESOURCE = ("resources/kanji/{level}.json", "汉字数量")

RESOURCE_MAP = {
    "vocab_reading":   VOCAB_RESOURCE,
    "vocab_kanji":     VOCAB_RESOURCE,
    "vocab_context":   VOCAB_RESOURCE,
    "vocab_synonym":   VOCAB_RESOURCE,
    "vocab_usage":     VOCAB_RESOURCE,
    "grammar_fill":    GRAMMAR_RESOURCE,
    "grammar_order":   GRAMMAR_RESOURCE,
    "grammar_passage": GRAMMAR_RESOURCE,
    # 阅读题型无对应资源文件
}


def count_questions(data_dir: Path) -> dict[str, int]:
    """读取目录下所有 JSON 文件，返回 {题型: 题数}。"""
    counts = {}
    for f in sorted(data_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        counts[f.stem] = len(data.get("questions", []))
    return counts


def load_resource_count(level: str, resource_tpl: str) -> int:
    """加载资源文件，返回条目数。"""
    path = ROOT / resource_tpl.format(level=level.lower())
    if not path.exists():
        return 0
    if path.suffix == ".csv":
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            return sum(1 for _ in reader)
    elif path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return len(data) if isinstance(data, list) else 0
    return 0


def build_report(level: str) -> dict:
    """构建完整报告数据。"""
    data_dir = ROOT / "data" / level.lower()
    if not data_dir.is_dir():
        print(f"エラー: {data_dir} が見つかりません", file=sys.stderr)
        sys.exit(1)

    counts = count_questions(data_dir)

    # 加载资源
    vocab_total = load_resource_count(level, VOCAB_RESOURCE[0])
    grammar_total = load_resource_count(level, GRAMMAR_RESOURCE[0])
    kanji_total = load_resource_count(level, KANJI_RESOURCE[0])

    sections = []
    grand_current = 0
    grand_target = 0

    for cat_name, types in CATEGORIES.items():
        rows = []
        cat_current = 0
        for t in types:
            current = counts.get(t, 0)
            cat_current += current

            res_info = RESOURCE_MAP.get(t)
            if res_info:
                target = load_resource_count(level, res_info[0])
                gap = max(0, target - current)
                coverage = f"{current / target * 100:.1f}%" if target > 0 else "-"
            else:
                target = None
                gap = None
                coverage = "-"

            rows.append({
                "type": t,
                "name": TYPE_NAMES[t],
                "current": current,
                "target": target,
                "gap": gap,
                "coverage": coverage,
            })

        sections.append({
            "name": cat_name,
            "rows": rows,
            "cat_current": cat_current,
        })

    return {
        "level": level,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resources": {
            "vocabulary": vocab_total,
            "grammar": grammar_total,
            "kanji": kanji_total,
        },
        "sections": sections,
        "total": sum(s["cat_current"] for s in sections),
    }


def print_terminal(report: dict):
    """在终端打印报告。"""
    level = report["level"]
    res = report["resources"]

    print(f"\n  JLPT {level} 題庫進捗レポート")
    print(f"  {report['timestamp']}")
    print(f"  {'═' * 60}")

    print(f"\n  リソース:")
    print(f"    語彙: {res['vocabulary']} 語")
    print(f"    文法: {res['grammar']} ポイント")
    print(f"    漢字: {res['kanji']} 字")

    for section in report["sections"]:
        print(f"\n  {section['name']}")
        print(f"  {'─' * 60}")
        print(f"  {'題型':<20} {'現在':>6} {'目標':>6} {'不足':>6} {'進捗':>8}")
        print(f"  {'─' * 60}")
        for row in section["rows"]:
            target_str = str(row["target"]) if row["target"] is not None else "-"
            gap_str = str(row["gap"]) if row["gap"] is not None else "-"
            print(f"  {row['name']:<20} {row['current']:>6} {target_str:>6} {gap_str:>6} {row['coverage']:>8}")

    print(f"\n  {'═' * 60}")
    print(f"  {'合計':<20} {report['total']:>6}")
    print()


def write_markdown(report: dict):
    """生成 Markdown 报告文件。"""
    level = report["level"]
    data_dir = ROOT / "data" / level.lower()
    report_path = data_dir / "progress_report.md"

    res = report["resources"]
    lines = [
        f"# JLPT {level} 題庫進捗報告",
        f"",
        f"生成日時: {report['timestamp']}",
        f"",
        f"## リソース",
        f"",
        f"| 種類 | 数量 |",
        f"|------|------|",
        f"| 語彙 | {res['vocabulary']} 語 |",
        f"| 文法 | {res['grammar']} ポイント |",
        f"| 漢字 | {res['kanji']} 字 |",
        f"",
    ]

    for section in report["sections"]:
        lines.append(f"## {section['name']}")
        lines.append(f"")
        lines.append(f"| 題型 | 現在 | 目標 | 不足 | 進捗 |")
        lines.append(f"|------|------|------|------|------|")
        for row in section["rows"]:
            target_str = str(row["target"]) if row["target"] is not None else "-"
            gap_str = str(row["gap"]) if row["gap"] is not None else "-"
            lines.append(f"| {row['name']} | {row['current']} | {target_str} | {gap_str} | {row['coverage']} |")
        lines.append(f"")

    lines.append(f"## 合計")
    lines.append(f"")
    lines.append(f"全題型合計: **{report['total']}** 題")
    lines.append(f"")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  レポート保存先: {report_path}")


def main():
    if len(sys.argv) < 2:
        print(f"用法: python3 {sys.argv[0]} <LEVEL> [--report]")
        print(f"例:   python3 {sys.argv[0]} N2")
        print(f"      python3 {sys.argv[0]} N2 --report")
        sys.exit(1)

    level = sys.argv[1].upper()
    gen_report = "--report" in sys.argv

    report = build_report(level)
    print_terminal(report)

    if gen_report:
        write_markdown(report)


if __name__ == "__main__":
    main()
