import json

file_path = "/home/tetsuya/Development/openjlpt/data/n2/vocab_kanji.json"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

ids = set()
duplicates = []

max_id = 0
for q in data['questions']:
    id_str = q.get('id', '')
    if id_str.startswith('n2-vocab_kanji-'):
        try:
            num = int(id_str.split('-')[-1])
            if num > max_id:
                max_id = num
        except:
            pass

next_id = max_id + 1

for q in data['questions']:
    q_id = q.get('id')
    if q_id in ids:
        new_id = f"n2-vocab_kanji-{next_id:04d}"
        q['id'] = new_id
        next_id += 1
        ids.add(new_id)
    else:
        ids.add(q_id)

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed duplicate IDs.")
