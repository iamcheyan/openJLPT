import json
import glob
import os

def check_files():
    files = glob.glob("/home/tetsuya/Development/openjlpt/data/**/*.json", recursive=True)
    report = []
    
    for f in files:
        if "generation-state" in f: continue # skip generation state
        if not ("vocab" in f or "grammar" in f or "reading" in f or "listening" in f): continue
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            issues = []
            
            if isinstance(data, dict) and 'questions' in data:
                questions = data['questions']
            elif isinstance(data, list):
                questions = data
            else:
                issues.append("Root is neither a list nor a valid object with 'questions'")
                report.append((f, issues))
                continue
            
            ids = set()
            for i, item in enumerate(questions):
                if 'id' not in item:
                    issues.append(f"Missing id at index {i}")
                else:
                    if item['id'] in ids:
                        issues.append(f"Duplicate id: {item['id']}")
                    ids.add(item['id'])
                
                # Depending on type, it might not have 'question' (it might have 'sentence')
                if 'question' not in item and 'sentence' not in item and 'passage' not in item:
                    issues.append(f"Missing question/sentence/passage at index {i} (id: {item.get('id', 'unknown')})")
                
                # if 'options' not in item or not isinstance(item['options'], list) or len(item['options']) != 4:
                #     issues.append(f"Invalid options at index {i} (id: {item.get('id', 'unknown')})")
                
                if 'answer' not in item or str(item['answer']) not in ['1', '2', '3', '4', '0', 0, 1, 2, 3]:
                    issues.append(f"Invalid or missing answer at index {i} (id: {item.get('id', 'unknown')})")
            
            if issues:
                report.append((f, issues))
                
        except json.JSONDecodeError as e:
            report.append((f, [f"JSON decode error: {str(e)}"]))
        except Exception as e:
            report.append((f, [f"Error reading file: {str(e)}"]))
            
    for f, issues in report:
        print(f"File: {f}")
        for issue in issues[:10]: # Print up to 10 issues per file
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  - ... and {len(issues)-10} more issues")
    if not report:
        print("All checks passed.")

if __name__ == "__main__":
    check_files()
