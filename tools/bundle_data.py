#!/usr/bin/env python3
"""
工具：离线数据打包
作用：将 data/n2/ 下所有 JSON 题库合并为一个 data_n2.js 文件，供离线试卷使用。
用法：python3 tools/bundle_data.py
"""
import os
import json

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, 'data', 'n2')
OUTPUT_FILE = os.path.join(_PROJECT_ROOT, 'data_n2.js')

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
