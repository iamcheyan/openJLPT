import json
from pathlib import Path

FILE_PATH = '/home/tetsuya/Development/openjlpt/data/n2/vocab_kanji.json'
data = json.loads(Path(FILE_PATH).read_text('utf-8'))
qs = data['questions']

# ── Step 1: Fix duplicate IDs 413-449 ──────────────────────────────────────
# The first occurrence of each ID is the original.
# The second occurrence has DIFFERENT content and needs a new sequential ID.
# We'll renumber the second occurrences starting from the next available ID after max.

# Find the max numeric ID currently in use
max_id = max(
    int(q['id'].rsplit('-', 1)[-1])
    for q in qs
    if q.get('id', '').startswith('n2-vocab_kanji-')
)
print(f'Current max numeric ID: {max_id}')

seen_ids = set()
next_id = max_id + 1
fixes_dup = 0

for q in qs:
    qid = q.get('id', '')
    if qid in seen_ids:
        new_id = f'n2-vocab_kanji-{next_id}'
        print(f'  Renumber: {qid} → {new_id}  (target={q.get("target")})')
        q['id'] = new_id
        next_id += 1
        fixes_dup += 1
    else:
        seen_ids.add(qid)

# ── Step 2: Fix 4 empty explanations ───────────────────────────────────────
EXPL_MAP = {
    'n2-vocab_kanji-006': {
        'target': 'みとめた',
        'correct_kanji': '認めた',
        'explanation': '「みとめた」の正しい漢字は「認めた」です。（中文：承认、认可）「承めた」「証めた」「確めた」はいずれも誤字です。'
    },
    'n2-vocab_kanji-007': {
        'target': 'いんさつ',
        'correct_kanji': '印刷',
        'explanation': '「いんさつ」の正しい漢字は「印刷」です。（中文：印刷）「刷」の字に注意。'
    },
    'n2-vocab_kanji-008': {
        'target': 'ゆたかな',
        'correct_kanji': '豊かな',
        'explanation': '「ゆたかな」の正しい漢字は「豊かな」です。（中文：丰富的、富饶的）「豊」の字形に注意。'
    },
    'n2-vocab_kanji-249': {
        'target': 'らん',
        'correct_kanji': '欄',
        'explanation': '「らん」の正しい漢字は「欄」です。（中文：栏、栏目）書類や表のマス目・区切りを指します。'
    },
}

fixes_expl = 0
for q in qs:
    qid = q.get('id', '')
    if qid in EXPL_MAP and len(q.get('explanation', '').strip()) < 5:
        q['explanation'] = EXPL_MAP[qid]['explanation']
        fixes_expl += 1
        print(f'  Fixed explanation: {qid}')

# ── Save ────────────────────────────────────────────────────────────────────
Path(FILE_PATH).write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding='utf-8'
)

print(f'\nDone: {fixes_dup} IDs renumbered, {fixes_expl} explanations filled.')
print(f'Total questions after fix: {len(qs)}')
