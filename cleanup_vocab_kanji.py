#!/usr/bin/env python3
"""Remove template-format vocab_kanji questions that lack real context sentences."""
import json

PATH = "data/n2/vocab_kanji.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

before = len(data["questions"])
data["questions"] = [
    q for q in data["questions"]
    if "適当な漢字" not in q.get("sentence", "")
]
after = len(data["questions"])
data["meta"]["count"] = after

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Removed {before - after} template questions, {after} remaining.")
