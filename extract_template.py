#!/usr/bin/env python3
"""
Extract questions from output/template.html and append to data/n2/*.json
Model: Google Gemini (both generator and reviewer)
"""

import json
import re
from datetime import datetime
from html.parser import HTMLParser

HTML_PATH = "output/template.html"
DATA_DIR = "data/n2"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self._skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip -= 1
    def handle_data(self, data):
        if self._skip == 0:
            self.texts.append(data)
    def get_text(self):
        return ''.join(self.texts)


def strip_html_tags(html):
    extractor = TextExtractor()
    extractor.feed(html)
    return extractor.get_text().strip()


def extract_answer_from_explanation(exp_html):
    """Extract answer index (0-based) from explanation HTML."""
    text = strip_html_tags(exp_html)
    # Match 正解：２「...」 or 正解：２ or 正解：２.
    m = re.search(r'正解[：:]\s*[１２３４](\.|\s|「|$)', text)
    if m:
        answer_char = m.group(0).replace('正解', '').replace('：', '').replace(':', '').replace('.', '').replace('「', '').strip()
        answer_map = {'１': 0, '２': 1, '３': 2, '４': 3, '1': 0, '2': 1, '3': 2, '4': 3}
        return answer_map.get(answer_char, 0)
    return 0


def clean_option(text):
    """Remove １. prefix from option text."""
    text = text.strip()
    m = re.match(r'^[１２３４]\.\s*', text)
    if m:
        text = text[m.end():]
    return text.strip()


def parse_html():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # Split by question blocks
    question_blocks = re.findall(r'<div class="question-block" id="q(\d+)">(.*?)</div>\s*</div>', html, re.DOTALL)

    questions = {}
    for qnum_str, block in question_blocks:
        qnum = int(qnum_str)
        # Extract question text
        qtext_match = re.search(r'<div class="question-text">(.*?)</div>', block, re.DOTALL)
        qtext_html = qtext_match.group(1) if qtext_match else ""
        qtext = strip_html_tags(qtext_html)

        # Extract options
        options = []
        option_matches = re.findall(r'<li[^>]*>(.*?)</li>', block, re.DOTALL)
        for opt_html in option_matches:
            opt_text = strip_html_tags(opt_html)
            options.append(clean_option(opt_text))

        # Extract explanation
        exp_match = re.search(r'<div class="explanation"[^>]*>(.*?)</div>', block, re.DOTALL)
        exp_html = exp_match.group(1) if exp_match else ""
        exp_text = strip_html_tags(exp_html)

        # Extract answer from explanation
        answer = extract_answer_from_explanation(exp_html)

        # Extract target word for vocab types
        target_match = re.search(r'<span class="target-word">(.*?)</span>', qtext_html)
        target = target_match.group(1) if target_match else ""

        questions[qnum] = {
            'qtext': qtext,
            'options': options,
            'answer': answer,
            'explanation': exp_text,
            'target': target,
        }

    return html, questions


def extract_passage(html, section_title):
    """Extract passage text for a given section."""
    # Find the section by looking for the h3 tag, then find the next passage div
    pattern = re.compile(
        r'<h3>\s*' + re.escape(section_title) + r'\s*</h3>\s*'
        r'<div class="instruction">.*?</div>\s*'
        r'(<div class="passage">(.*?)</div>)?',
        re.DOTALL
    )
    m = pattern.search(html)
    if m and m.group(2):
        return strip_html_tags(m.group(2)).strip()
    return ""


def extract_grammar_passage(html):
    """Extract grammar passage with blanks."""
    m = re.search(r'<h3>⑧ 文章の文法</h3>\s*<div class="passage">(.*?)</div>', html, re.DOTALL)
    if m:
        return strip_html_tags(m.group(1)).strip()
    return ""


def extract_star_line(html, qnum):
    """Extract fragments from star-line for grammar_order."""
    block_match = re.search(rf'<div class="question-block" id="q{qnum}">(.*?)</div>\s*</div>', html, re.DOTALL)
    if not block_match:
        return []
    block = block_match.group(1)
    star_match = re.search(r'<div class="star-line">(.*?)</div>', block, re.DOTALL)
    if not star_match:
        return []
    text = strip_html_tags(star_match.group(1))
    # Parse: １. と思えば　２. 誰にでも　３. 努力次第で　４. できる
    fragments = []
    for i in range(1, 5):
        pattern = rf'[１２３４]\.\s*(.*?)(?=\s*[１２３４]\.\s*|$)'
        matches = re.findall(pattern, text)
        if matches:
            return [m.strip() for m in matches if m.strip()]
    # Fallback: split by spaces and extract 4 items
    parts = re.split(r'\s*[１２３４]\.\s*', text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts[:4]


def build_items(html, questions):
    """Build JSON items grouped by type."""
    items = {
        'vocab_reading': [],
        'vocab_kanji': [],
        'vocab_context': [],
        'vocab_synonym': [],
        'vocab_usage': [],
        'grammar_fill': [],
        'grammar_order': [],
        'grammar_passage': [],
        'reading_short': [],
        'reading_medium': [],
        'reading_long': [],
        'reading_search': [],
    }

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    meta = {
        'generated_by': 'gemini:Google Gemini',
        'reviewed_by': 'gemini',
        'verified': True,
        'created_at': now,
        'level': 'N2',
        'source': 'ai',
    }

    def make_base(q):
        return {
            'sentence': q['qtext'],
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
            **meta,
        }

    # ① 漢字の読み方 (q1-q5)
    for i in range(1, 6):
        q = questions.get(i)
        if not q:
            continue
        item = make_base(q)
        item['target'] = q['target']
        item['question_type'] = 'vocab_reading'
        items['vocab_reading'].append(item)

    # ② 漢字の表記 (q6-q10)
    for i in range(6, 11):
        q = questions.get(i)
        if not q:
            continue
        item = make_base(q)
        item['target'] = q['target']
        item['question_type'] = 'vocab_kanji'
        items['vocab_kanji'].append(item)

    # ③ 文脈規定 (q11-q17)
    for i in range(11, 18):
        q = questions.get(i)
        if not q:
            continue
        item = make_base(q)
        item['question_type'] = 'vocab_context'
        items['vocab_context'].append(item)

    # ④ 言い換え・類義 (q18-q22)
    for i in range(18, 23):
        q = questions.get(i)
        if not q:
            continue
        item = make_base(q)
        item['target'] = q['target']
        item['question_type'] = 'vocab_synonym'
        items['vocab_synonym'].append(item)

    # ⑤ 用法 (q23-q27)
    for i in range(23, 28):
        q = questions.get(i)
        if not q:
            continue
        # Extract target from bold text
        target = q['target']
        if not target and q['qtext'].startswith('**'):
            target = q['qtext'].strip('*').strip()
        item = make_base(q)
        item['target'] = target
        item['question_type'] = 'vocab_usage'
        items['vocab_usage'].append(item)

    # ⑥ 文の文法 (q28-q39)
    for i in range(28, 40):
        q = questions.get(i)
        if not q:
            continue
        item = make_base(q)
        item['question_type'] = 'grammar_fill'
        items['grammar_fill'].append(item)

    # ⑦ 文の組み立て (q40-q44)
    for i in range(40, 45):
        q = questions.get(i)
        if not q:
            continue
        fragments = extract_star_line(html, i)
        if len(fragments) != 4:
            print(f"  WARN: q{i} has {len(fragments)} fragments, expected 4")
            continue
        # Reconstruct complete sentence from explanation
        complete = reconstruct_complete_sentence(q['qtext'], fragments, q['answer'], q['explanation'])
        item = {
            'sentence': q['qtext'],
            'fragments': fragments,
            'options': fragments[:],
            'answer': q['answer'],
            'complete_sentence': complete,
            'explanation': q['explanation'],
            **meta,
            'question_type': 'grammar_order',
        }
        items['grammar_order'].append(item)

    # ⑧ 文章の文法 (q45-q49) - single passage with 5 blanks
    passage = extract_grammar_passage(html)
    blanks = []
    for i in range(45, 50):
        q = questions.get(i)
        if not q:
            continue
        blanks.append({
            'num': i - 44,
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
        })
    if blanks:
        items['grammar_passage'].append({
            'passage': passage,
            'blanks': blanks,
            **meta,
            'question_type': 'grammar_passage',
        })

    # ⑨ 短文読解 (q50-q52) - each is separate item with passage
    passage_short = extract_passage(html, '⑨ 短文読解')
    for i in range(50, 53):
        q = questions.get(i)
        if not q:
            continue
        items['reading_short'].append({
            'passage': passage_short,
            'question': q['qtext'],
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
            **meta,
            'question_type': 'reading_short',
        })

    # ⑩ 中文読解 (q53-q56) - single passage with 4 questions
    passage_medium = extract_passage(html, '⑩ 中文読解')
    medium_questions = []
    for i in range(53, 57):
        q = questions.get(i)
        if not q:
            continue
        medium_questions.append({
            'question': q['qtext'],
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
        })
    if medium_questions:
        items['reading_medium'].append({
            'passage': passage_medium,
            'questions': medium_questions,
            **meta,
            'question_type': 'reading_medium',
        })

    # ⑪ 長文読解 (q57-q58) - single passage with 2 questions
    passage_long = extract_passage(html, '⑪ 長文読解')
    long_questions = []
    for i in range(57, 59):
        q = questions.get(i)
        if not q:
            continue
        long_questions.append({
            'question': q['qtext'],
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
        })
    if long_questions:
        items['reading_long'].append({
            'passage': passage_long,
            'questions': long_questions,
            **meta,
            'question_type': 'reading_long',
        })

    # ⑫ 情報検索 (q59-q60) - single passage with 2 questions
    passage_search = extract_passage(html, '⑫ 情報検索')
    search_questions = []
    for i in range(59, 61):
        q = questions.get(i)
        if not q:
            continue
        search_questions.append({
            'question': q['qtext'],
            'options': q['options'][:4],
            'answer': q['answer'],
            'explanation': q['explanation'],
        })
    if search_questions:
        items['reading_search'].append({
            'passage': passage_search,
            'questions': search_questions,
            **meta,
            'question_type': 'reading_search',
        })

    return items


def reconstruct_complete_sentence(sentence, fragments, answer, explanation):
    """Try to reconstruct complete sentence from explanation text."""
    # Parse explanation like: 努力次第で(3) 誰にでも(2) できる(4) と思えば(1)
    text = strip_html_tags(explanation)
    # Extract order mapping from explanation
    order = {}
    # Pattern: word(数字) or word（数字）
    matches = re.findall(r'(\S+?)[(（]([１２３４1234])[)）]', text)
    for word, num in matches:
        idx = int(num.replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4')) - 1
        if 0 <= idx < 4:
            order[idx] = word

    if len(order) == 4:
        # All fragments mapped
        parts = re.split(r'＿＿|＿★＿', sentence)
        if len(parts) == 5:
            # 4 blanks
            result = parts[0]
            for i in range(4):
                result += order.get(i, fragments[i] if i < len(fragments) else '') + parts[i + 1]
            return result
        elif len(parts) == 4:
            # 3 blanks + 1 something else
            result = parts[0]
            for i in range(4):
                result += order.get(i, fragments[i] if i < len(fragments) else '') + parts[i + 1]
            return result

    # Fallback: just join all fragments in order
    # Find the sentence template without blanks
    clean_sentence = sentence.replace('＿＿', '{}').replace('＿★＿', '{}')
    try:
        return clean_sentence.format(*[order.get(i, fragments[i]) for i in range(4)])
    except:
        pass

    # Last resort: just append all fragments
    base = sentence.split('＿')[0].strip()
    ending = sentence.split('＿')[-1].strip()
    return base + ''.join(fragments) + ending


def fix_duplicate_options(items):
    """Fix questions with duplicate options."""
    fixes = {
        10: {3: '望める'},  # vocab_kanji q10: duplicate 眺める
    }
    for item_list in items.values():
        for item in item_list:
            opts = item.get('options', item.get('blanks', [{}])[0].get('options', []))
            # Check for duplicates in flat items
            if 'options' in item:
                seen = set()
                for i, opt in enumerate(item['options']):
                    if opt in seen:
                        # Find a replacement
                        if opt == '眺める' and i == 3:
                            item['options'][i] = '望める'
                        else:
                            item['options'][i] = opt + '（異なる用法）'
                    seen.add(opt)


def append_to_json(items):
    """Append items to corresponding JSON files."""
    for type_id, item_list in items.items():
        if not item_list:
            continue
        path = f"{DATA_DIR}/{type_id}.json"
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing = data.get('questions', [])
        start_idx = len(existing)

        for i, item in enumerate(item_list):
            item['id'] = f"n2-{type_id}-{start_idx + i + 1:03d}"
            data['questions'].append(item)

        data['meta']['count'] = len(data['questions'])

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  {type_id}: +{len(item_list)} 题 (总计 {data['meta']['count']})")


def main():
    print("Parsing template.html...")
    html, questions = parse_html()
    print(f"Found {len(questions)} questions")

    print("Building JSON items...")
    items = build_items(html, questions)

    print("Fixing duplicate options...")
    fix_duplicate_options(items)

    print("Appending to data files...")
    total = 0
    for type_id, item_list in items.items():
        if item_list:
            total += len(item_list)
    print(f"Total items to append: {total}")

    append_to_json(items)
    print("Done!")


if __name__ == "__main__":
    main()
