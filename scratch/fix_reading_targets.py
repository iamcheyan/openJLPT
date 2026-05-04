import json

file_path = '/home/tetsuya/Development/openjlpt/data/n2/vocab_kanji.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

fixes = 0
for q in data['questions']:
    sentence = q.get('sentence', '')
    target = q.get('target', '')
    if '《' in sentence and '》' in sentence:
        parts = sentence.split('《')
        before = parts[0]
        rest = parts[1].split('》')
        in_brackets = rest[0]
        after = rest[1]
        
        if in_brackets != target:
            # Replace the conjugated form with the dictionary form (target)
            q['sentence'] = f"{before}《{target}》{after}"
            fixes += 1

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed {fixes} items in {file_path}")
