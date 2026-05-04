import json
import os
import subprocess

files = [
    '/home/tetsuya/Development/openjlpt/data/n1/vocab_context.json',
    '/home/tetsuya/Development/openjlpt/data/n3/vocab_context.json',
    '/home/tetsuya/Development/openjlpt/data/n4/vocab_context.json',
    '/home/tetsuya/Development/openjlpt/data/n5/vocab_context.json'
]

prefixes = [
    "文脈に最も合うものを選びなさい。",
    "文脈に最も合うものを選びなさい",
    "（　）に入れるのに最もよいものを選びなさい。"
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
            
    fixes = 0
    for q in data.get('questions', []):
        sentence = q.get('sentence', '')
        original_sentence = sentence
        
        for prefix in prefixes:
            if sentence.startswith(prefix):
                sentence = sentence[len(prefix):].strip()
        
        # sometimes it might have spaces before the prefix
        sentence = sentence.strip()
        for prefix in prefixes:
            if sentence.startswith(prefix):
                sentence = sentence[len(prefix):].strip()
                
        if sentence != original_sentence:
            q['sentence'] = sentence
            fixes += 1
            
    if fixes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Fixed {fixes} items in {file_path}")
        level = file_path.split('/')[-2]
        cmd = f'git add {file_path} && git commit -m "fix({level}/vocab_context): remove instruction prefix from sentences"'
        subprocess.run(cmd, shell=True, cwd='/home/tetsuya/Development/openjlpt')
    else:
        print(f"No fixes needed in {file_path}")
