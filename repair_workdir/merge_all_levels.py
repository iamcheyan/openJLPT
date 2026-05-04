import json, glob, os

DATA_DIR = '/home/tetsuya/Development/openjlpt/data'
WORKDIR = '/home/tetsuya/Development/openjlpt/repair_workdir'

levels = ['n1', 'n3', 'n4', 'n5']

for level in levels:
    fpath = os.path.join(DATA_DIR, level, 'vocab_reading.json')
    data = json.load(open(fpath))
    questions = data['questions']
    q_by_id = {q['id']: q for q in questions}

    # Find all sentence files for this level
    pattern = os.path.join(WORKDIR, f'sentences_{level}_*.json')
    sentence_files = sorted(glob.glob(pattern))

    total_read = 0
    updated = 0

    for sf in sentence_files:
        with open(sf, 'r', encoding='utf-8') as f:
            sentences = json.load(f)
        for qid, sentence in sentences.items():
            if qid in q_by_id:
                old_s = q_by_id[qid].get('sentence', '')
                # Only update if it's a template/lazy format
                if 'の読み方として最もよいもの' in old_s or 'の読み方を選んでください' in old_s:
                    q_by_id[qid]['sentence'] = sentence
                    updated += 1
                elif '《' not in old_s and '》' not in old_s:
                    q_by_id[qid]['sentence'] = sentence
                    updated += 1
            else:
                print(f'WARNING: {qid} not found in {level} data')
        total_read += len(sentences)

    # Write back
    json.dump(data, open(fpath, 'w'), ensure_ascii=False, indent=2)

    # Count remaining templates
    remaining = sum(1 for q in questions if 'の読み方として最もよいもの' in q.get('sentence', '') or 'の読み方を選んでください' in q.get('sentence', ''))
    print(f'{level}: read {total_read} sentences from {len(sentence_files)} files, updated {updated} questions, {remaining} templates remaining, total {len(questions)}')

print('\nDone!')
