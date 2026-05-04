import json, glob, re, os

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_FILE = os.path.join(DATA_DIR, "data", "n2", "vocab_reading.json")
SENTENCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sentences_*.json")

# Load main data
with open(MAIN_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

questions = data["questions"]
q_by_id = {q["id"]: q for q in questions}

# Load all sentence files
sentence_files = sorted(glob.glob(SENTENCES_DIR))
total_sentences = 0
updated = 0

for sf in sentence_files:
    with open(sf, "r", encoding="utf-8") as f:
        sentences = json.load(f)
    for qid, sentence in sentences.items():
        if qid in q_by_id:
            q_by_id[qid]["sentence"] = sentence
            updated += 1
        else:
            print(f"WARNING: {qid} not found in main data")
    total_sentences += len(sentences)

print(f"Read {total_sentences} sentences from {len(sentence_files)} files")
print(f"Updated {updated} questions in main data")

# Verify: check for any remaining template-format sentences
remaining_templates = 0
for q in questions:
    s = q.get("sentence", "")
    if "の読み方として" in s or "の読み方" in s:
        remaining_templates += 1
        print(f"  Remaining template: {q['id']} - {q['target']}")

print(f"\nTemplate sentences remaining: {remaining_templates}")
print(f"Total questions: {len(questions)}")

# Write back
with open(MAIN_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done! Wrote back to", MAIN_FILE)
