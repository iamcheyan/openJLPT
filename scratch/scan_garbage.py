import json
import os
import re

DATA_DIR = "/home/tetsuya/Development/openjlpt/data/n2"
FILES = [
    "vocab_reading.json",
    "vocab_kanji.json",
    "vocab_context.json",
    "vocab_synonym.json",
    "vocab_usage.json"
]

def scan_file(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    section_id = filename.replace(".json", "")
    
    stats = {
        "total": len(questions),
        "garbage_template": 0,
        "garbage_placeholder": 0,
        "garbage_usage_missing_target": 0,
        "garbage_truncated": 0,
        "garbage_short_explanation": 0,
        "garbage_synonym_self": 0,
        "total_garbage": 0
    }
    
    garbage_ids = []

    for q in questions:
        is_garbage = False
        reasons = []
        
        sentence = q.get("sentence", "")
        options = q.get("options", [])
        options_str = str(options)
        target = q.get("target", "")
        explanation = q.get("explanation", "")
        
        # 1. 模板特征
        if any(p in sentence for p in ["として最もよいものを一つ選びなさい", "の類義語を選びなさい", "の言い換えを選びなさい", "意味が最も近いもの"]):
            stats["garbage_template"] += 1
            is_garbage = True
            reasons.append("template")
            
        # 2. 占位符特征
        if any(p in options_str for p in ["かな2", "かな1", "かな3"]):
            stats["garbage_placeholder"] += 1
            is_garbage = True
            reasons.append("placeholder")

        # 3. 用法题异常
        if section_id == "vocab_usage":
            if not all(target[:2] in opt for opt in options):
                stats["garbage_usage_missing_target"] += 1
                is_garbage = True
                reasons.append("usage_missing_target")
        
        # 4. 截断特征
        if any(not opt.strip().endswith(("。", "！", "？", "」", "．")) for opt in options if len(opt) > 10):
            stats["garbage_truncated"] += 1
            is_garbage = True
            reasons.append("truncated")
            
        # 5. 解析过短
        if len(explanation) < 25:
            stats["garbage_short_explanation"] += 1
            is_garbage = True
            reasons.append("short_explanation")
            
        # 6. 类义语自指
        if section_id == "vocab_synonym" and target in options_str:
            stats["garbage_synonym_self"] += 1
            is_garbage = True
            reasons.append("synonym_self")
            
        if is_garbage:
            stats["total_garbage"] += 1
            garbage_ids.append(f"{q.get('id')} ({', '.join(reasons)})")

    return stats

def main():
    print("=== JLPT N2 词库质量扫描报告 ===\n")
    for f in FILES:
        stats = scan_file(f)
        if not stats: continue
        
        print(f"文件: {f}")
        print(f"  总题数: {stats['total']}")
        print(f"  识别到的垃圾总数: {stats['total_garbage']} ({stats['total_garbage']/stats['total']*100:.1f}%)")
        print(f"  细节分类:")
        if stats["garbage_template"]: print(f"    - 模板化例句: {stats['garbage_template']}")
        if stats["garbage_placeholder"]: print(f"    - 包含占位符(かな2等): {stats['garbage_placeholder']}")
        if stats["garbage_usage_missing_target"]: print(f"    - 用法题缺失目标词: {stats['garbage_usage_missing_target']}")
        if stats["garbage_truncated"]: print(f"    - 句子截断/无标点: {stats['garbage_truncated']}")
        if stats["garbage_short_explanation"]: print(f"    - 解析过于简略: {stats['garbage_short_explanation']}")
        if stats["garbage_synonym_self"]: print(f"    - 类义语包含原词: {stats['garbage_synonym_self']}")
        print("-" * 30)

if __name__ == "__main__":
    main()
