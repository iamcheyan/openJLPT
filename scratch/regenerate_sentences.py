import json
import os
import requests
import time

FILES = [
    '/home/tetsuya/Development/openjlpt/data/n2/vocab_reading.json',
    '/home/tetsuya/Development/openjlpt/data/n2/vocab_kanji.json'
]

# 请确保这里的地址和 Key 与您的本地模型网关（如 opencode2api 或 Kimi）匹配
API_URL = os.environ.get('API_URL', 'http://localhost:8000/v1/chat/completions')
API_KEY = os.environ.get('API_KEY', 'your_api_key_here')

def rewrite_sentence(sentence, in_brackets, target):
    prompt = f"""你是一个专业的日语教师。
原句是：{sentence}
这道题目前的正确答案（考查单词的词典原形）是：{target}
但是句子中实际使用的是它的变形：{in_brackets}

请你重新写一个符合N2级别难度的日文句子，要求：
1. 必须自然地使用该词的词典原形“{target}”。
2. 句意尽量与原句保持一致，如果原句的语法（如过去时态）不支持直接填入原形，请适当修改句子结构或时态，使其符合日语语法。
3. 请在句子中用《》将该词的原形括起来（例如：お客様からのご要望を確かに《承る》つもりだ。 等）
4. 只输出改写后的这一个日文句子，绝对不要输出任何多余的解释、引号、翻译、拼音。"""

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    payload = {
        'model': 'gpt-3.5-turbo', # 请根据您的网关修改模型名称
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.2
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def process_file(file_path):
    print(f"\nProcessing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qs = data.get('questions', [])
    processed = 0

    for i, q in enumerate(qs):
        sentence = q.get('sentence', '')
        target = q.get('target', '')
        
        if '《' in sentence and '》' in sentence:
            parts = sentence.split('《')
            rest = parts[1].split('》')
            in_brackets = rest[0]
            
            if in_brackets != target and in_brackets != "":
                print(f"[{i+1}/{len(qs)}] Target: {target} | Current: {in_brackets}")
                new_sentence = rewrite_sentence(sentence, in_brackets, target)
                
                if new_sentence and '《' in new_sentence and '》' in new_sentence:
                    print(f"  -> Regenerated: {new_sentence}")
                    q['sentence'] = new_sentence
                    processed += 1
                    
                    # 每 10 条保存一次
                    if processed % 10 == 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    print(f"  -> Failed to regenerate or format incorrect.")
                
                time.sleep(0.5)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Completed! Regenerated {processed} sentences in {file_path}.")

if __name__ == '__main__':
    for f in FILES:
        if os.path.exists(f):
            process_file(f)
