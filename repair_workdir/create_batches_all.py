import json, os, math

DATA_DIR = '/home/tetsuya/Development/openjlpt/data'
WORKDIR = '/home/tetsuya/Development/openjlpt/repair_workdir'
BATCH_SIZE = 100

levels = {
    'n1': 10,
    'n3': 10,
    'n4': 10,
    'n5': 10,
}

all_batches = {}
total_need = 0

for level, natural_count in levels.items():
    fpath = os.path.join(DATA_DIR, level, 'vocab_reading.json')
    data = json.load(open(fpath))
    qs = data['questions']

    # Find questions needing new sentences (template or lazy format)
    need_new = []
    for q in qs:
        s = q.get('sentence', '')
        if 'の読み方として最もよいもの' in s or 'の読み方を選んでください' in s:
            need_new.append(q)

    # Split into batches
    n = len(need_new)
    num_batches = math.ceil(n / BATCH_SIZE)

    print(f'{level}: {n} questions need sentences, splitting into {num_batches} batches')

    for i in range(num_batches):
        start = i * BATCH_SIZE
        end = min(start + BATCH_SIZE, n)
        batch = need_new[start:end]

        # Build minimal batch data
        batch_data = []
        for q in batch:
            batch_data.append({
                'idx': int(q['id'].split('-')[-1]),
                'id': q['id'],
                'target': q['target'],
                'sentence': q.get('sentence', ''),
                'options': q.get('options', []),
                'answer': q.get('answer', 0),
                'correct': q.get('correct', ''),
            })

        batch_name = f'{level}_batch_{i+1:02d}'
        batch_file = os.path.join(WORKDIR, f'{batch_name}.json')
        json.dump(batch_data, open(batch_file, 'w'), ensure_ascii=False, indent=2)
        all_batches[batch_name] = len(batch_data)
        total_need += len(batch_data)

print(f'\nTotal batches: {len(all_batches)}')
print(f'Total questions needing sentences: {total_need}')
for name, count in sorted(all_batches.items()):
    print(f'  {name}.json: {count} questions')
