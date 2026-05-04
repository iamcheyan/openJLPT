import json
import requests
import time
import os

FILE_PATH = '/home/tetsuya/Development/openjlpt/data/n2/vocab_reading.json'
API_URL = 'http://localhost:8000/v1/chat/completions' # Update this if using a different port or service
API_KEY = os.environ.get('API_KEY', 'your_api_key_here') # Use proper API key if needed

def enrich_explanation(sentence, target, options, answer_idx, old_explanation):
    prompt = f"""
请你作为一名JLPT N2级别的日语教师，为以下日语单词读音题编写详细的中文解析。
题目类型：选择画线单词的正确读音。
句子：{sentence}
考查单词：{target}
选项：
0. {options[0]}
1. {options[1]}
2. {options[2]}
3. {options[3]}
正确答案索引：{answer_idx}
原有的简单解释：{old_explanation}

要求：
1. 请提供中文的题目句子翻译。
2. 解释正确答案为什么正确（读音、词义）。
3. 简要分析一下其他三个干扰项（如：发音错误、清浊音混淆等）。
4. 输出格式请严格遵守以下纯文本结构（不需要Markdown标记代码块，直接返回文本即可）：

1. 正确项分析：句意为“（句子翻译）”。「{target}」的读音为「（正确读音）」，意为“（词义）”。正确答案为（正确索引）。
2. 干扰项分析：选项X、Y、Z均为错误读音，（简要说明错误原因）。
"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    payload = {
        'model': 'gpt-3.5-turbo', # or whatever model you are using
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def main():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qs = data.get('questions', [])
    processed = 0

    for i, q in enumerate(qs):
        old_exp = q.get('explanation', '')
        
        # Skip already enriched ones
        if '1. 正确项分析' in old_exp:
            continue
            
        # Target the ones with '意味：'
        if '意味：' in old_exp:
            print(f"Processing question {i+1}/{len(qs)} (ID: {q.get('id')})...")
            
            new_exp = enrich_explanation(
                q.get('sentence', ''),
                q.get('target', ''),
                q.get('options', []),
                q.get('answer', 0),
                old_exp
            )
            
            if new_exp:
                q['explanation'] = new_exp
                processed += 1
                
                # Save every 10 items to avoid losing progress
                if processed % 10 == 0:
                    with open(FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print("Progress saved.")
            
            # Rate limiting sleep
            time.sleep(1)

    # Final save
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Completed! Enriched {processed} explanations.")

if __name__ == '__main__':
    main()
