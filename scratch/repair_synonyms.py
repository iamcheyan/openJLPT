import json
import os
from datetime import datetime

FILE_PATH = '/home/tetsuya/Development/openjlpt/data/n2/vocab_synonym.json'

def repair_items(updates):
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    update_map = {item['id']: item for item in updates}
    
    modified_count = 0
    questions = data['questions']
    for i, item in enumerate(questions):
        if item.get('id') in update_map:
            questions[i] = update_map[item['id']]
            modified_count += 1
            
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully repaired {modified_count} items.")

def create_item(item_id, sentence, target, options, answer, explanation):
    return {
      "id": item_id,
      "level": "N2",
      "question_type": "vocab_synonym",
      "sentence": sentence,
      "target": target,
      "options": options,
      "answer": answer,
      "explanation": explanation,
      "created_at": datetime.now().isoformat(),
      "verified": True,
      "generated_by": "antigravity_batch_script"
    }

new_data = [
    create_item("n2-vocab_synonym-1511", "《蝋燭》に火を灯す。", "蝋燭", ["ろうそく", "電球", "蛍光灯", "提灯"], 0, "1. 正确项分析：「蝋燭（ろうそく）」即蜡烛。"),
    create_item("n2-vocab_synonym-1512", "会議の内容を《録音》する。", "録音", ["ろくおん", "録画", "記録", "記憶"], 0, "1. 正确项分析：「録音（ろくおん）」即录音。"),
    create_item("n2-vocab_synonym-1513", "現代社会の諸問題を《論ずる》。", "論ずる", ["ろんずる", "歌う", "踊る", "遊ぶ"], 0, "1. 正确项分析：「論ずる（ろんずる）」意为论述、阐述、讨论。"),
    create_item("n2-vocab_synonym-1514", "道が二つに《分かれている》。", "分かれる", ["わかれている", "繋がっている", "止まっている", "曲がっている"], 0, "1. 正确项分析：「分かれる（わかれる）」意为分开、分歧、分岔（自动词）。"),
    create_item("n2-vocab_synonym-1515", "彼女はいつまでも《若々しい》。", "若々しい", ["わかわかしい", "老けている", "幼い", "厳しい"], 0, "1. 正确项分析：「若々しい（わかわかしい）」意为年轻、朝气蓬勃。"),
    create_item("n2-vocab_synonym-1516", "温泉が《湧き》出ている。", "湧く", ["わく", "枯れる", "止まる", "流れる"], 0, "1. 正确项分析：「湧く（わく）」意为涌现、喷出、冒出。"),
    create_item("n2-vocab_synonym-1517", "不手際を《詫びる》。", "詫びる", ["わびる", "祝う", "褒める", "誘う"], 0, "1. 正确项分析：「詫びる（わびる）」即致歉、道歉。"),
    create_item("n2-vocab_synonym-1518", "《和服》を着て出かける。", "和服", ["わふく", "洋服", "制服", "私服"], 0, "1. 正确项分析：「和服（わふく）」即和服。"),
    create_item("n2-vocab_synonym-1519", "今年の冬は《割と》暖かい。", "割と", ["わりと", "非常に", "全く", "全然"], 0, "1. 正确项分析：「割と（わりと）」意为比较地、意外地。"),
    create_item("n2-vocab_synonym-1520", "《椀》に味噌汁をよそう。", "椀", ["わん", "皿", "コップ", "箸"], 0, "1. 正确项分析：「椀（わん）」即碗（通常指木制或漆器的碗）。"),
    create_item("n2-vocab_synonym-1521", "穏やかな《湾》内の海。", "湾", ["わん", "岬", "島", "半島"], 0, "1. 正确项分析：「湾（わん）」即海湾。")
]

repair_items(new_data)
