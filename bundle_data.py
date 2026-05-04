import os
import json

DATA_DIR = 'data/n2'
OUTPUT_FILE = 'data_n2.js'

def bundle():
    all_questions = []
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    
    for filename in files:
        path = os.path.join(DATA_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_questions.extend(data)
            else:
                print(f"Skipping {filename}: not a list")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("window.OFFLINE_DATA = ")
        json.dump(all_questions, f, ensure_ascii=False)
        f.write(";")
    
    print(f"Bundled {len(all_questions)} questions into {OUTPUT_FILE}")

if __name__ == '__main__':
    bundle()
