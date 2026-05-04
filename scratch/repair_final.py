import json
from datetime import datetime

FILE_PATH = '/home/tetsuya/Development/openjlpt/data/n2/vocab_synonym.json'

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

qs = data['questions']
fixes = 0

for i, q in enumerate(qs):
    qid = q.get('id', '')

    # Fix 1: Empty explanations on IDs 007-011 (early entries, manually added)
    if qid in ['n2-vocab_synonym-007', 'n2-vocab_synonym-008',
               'n2-vocab_synonym-009', 'n2-vocab_synonym-010', 'n2-vocab_synonym-011']:
        if not q.get('explanation', '').strip():
            target = q.get('target', '')
            opts = q.get('options', [])
            ans_idx = q.get('answer', 0)
            ans_val = opts[ans_idx] if 0 <= ans_idx < len(opts) else target
            q['explanation'] = f"1. 正确项分析：「{target}」的同义词（类义词）为「{ans_val}」。"
            fixes += 1
            print(f"Fixed explanation: {qid}")

    # Fix 2: Duplicate ID 021 — the SECOND occurrence (工芸) should be renumbered
    # We'll change its ID to 021b to avoid collision; we identify it by target=工芸
    if qid == 'n2-vocab_synonym-021' and q.get('target') == '工芸':
        q['id'] = 'n2-vocab_synonym-021b'
        fixes += 1
        print(f"Fixed duplicate ID 021 (工芸) -> 021b")

    # Fix 3: ID 061 — self-answer (磁石 option at idx 1 == target 磁石)
    # Change to a proper synonym question: 磁石 → じしゃく
    if qid == 'n2-vocab_synonym-061':
        q['sentence'] = '《磁石》で方位を確認する。'
        q['target'] = '磁石'
        q['options'] = ['じしゃく', 'コンパス', '方位計', '羅針盤']
        q['answer'] = 0
        q['explanation'] = '1. 正确项分析：「磁石（じしゃく）」即磁铁、磁石。'
        fixes += 1
        print(f"Fixed self-answer: {qid}")

    # Fix 4: ID 0704 — garbage template sentence + self-answer (冷ます)
    if qid == 'n2-vocab_synonym-0704':
        q['sentence'] = 'スープを少し《冷まして》から飲む。'
        q['target'] = '冷ます'
        q['options'] = ['さます', '温める', '捨てる', '沸かす']
        q['answer'] = 0
        q['explanation'] = '1. 正确项分析：「冷ます（さます）」意为使冷却、冷却（他动词）。'
        fixes += 1
        print(f"Fixed garbage+self-answer: {qid}")

    # Fix 5: ID 0990 — garbage template sentence + self-answer (茶色い)
    if qid == 'n2-vocab_synonym-0990':
        q['sentence'] = '《茶色い》熊が森にいる。'
        q['target'] = '茶色い'
        q['options'] = ['ちゃいろい', '黒い', '白い', '赤い']
        q['answer'] = 0
        q['explanation'] = '1. 正确项分析：「茶色い（ちゃいろい）」意为茶色、棕色。'
        fixes += 1
        print(f"Fixed garbage+self-answer: {qid}")

    # Fix 6: ID 1292 — self-answer (物騒 option at idx 0 == target 物騒)
    if qid == 'n2-vocab_synonym-1292':
        q['options'] = ['物騒', '危険', '不安', '騒然']
        q['answer'] = 0  # 物騒 is still correct but now we distinguish with synonyms
        # Actually the issue was options[0] == target which IS the self-answer pattern
        # We should have the answer be a synonym WORD, not the word itself
        q['options'] = ['危険な', '安全な', '平和な', '静かな']
        q['answer'] = 0
        q['explanation'] = '1. 正确项分析：「物騒（ぶっそう）」意为骚然、不安定、危险，与「危険な」意思最接近。'
        fixes += 1
        print(f"Fixed self-answer: {qid}")

with open(FILE_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nTotal fixes applied: {fixes}")
