#!/usr/bin/env python3
"""Generate natural Japanese sentences for batch_04.json reading questions."""

import json

# map of question id -> sentence
sentences = {
    "n2-vocab_reading-0402": "となりの《小父さん》が庭の花に水をあげている。",
    "n2-vocab_reading-0403": "《叔父さん》は毎年お正月に私にお年玉をくれる。",
    "n2-vocab_reading-0404": "私は子供の頃、先生にピアノを《教わる》ことになった。",
    "n2-vocab_reading-0405": "《御手洗》はこの廊下をまっすぐ行ったところにあります。",
    "n2-vocab_reading-0406": "母は帽子をかぶって《お出掛け》の準備をしている。",
    "n2-vocab_reading-0407": "子供の頃、家に《お手伝いさん》がいた。",
    "n2-vocab_reading-0408": "駅で《落し物》をしたので、交番に届けた。",
    "n2-vocab_reading-0409": "彼は後ろから急に声をかけて友達を《驚かす》。",
    "n2-vocab_reading-0410": "《各々》が自分の意見を述べた。",
    "n2-vocab_reading-0411": "《叔母さん》は料理がとても上手だ。",
    "n2-vocab_reading-0412": "お正月には神社に《お参り》する習慣がある。",
    "n2-vocab_reading-0413": "旅行先で《思い掛けない》出来事に遭った。",
    "n2-vocab_reading-0414": "彼は自分だけが正しいと《思い込む》傾向がある。",
    "n2-vocab_reading-0415": "《思いっ切り》遊んでストレスを発散した。",
    "n2-vocab_reading-0416": "いいアイデアが《思い付く》とすぐにメモするようにしている。",
    "n2-vocab_reading-0417": "この荷物は《重たい》ので、二人で運びましょう。",
    "n2-vocab_reading-0418": "料理をしているときに《親指》を切ってしまった。",
    "n2-vocab_reading-0419": "この地域は川の《恩恵》を受けて発展した。",
    "n2-vocab_reading-0420": "《温室》でたくさんの花を育てている。",
    "n2-vocab_reading-0421": "週末に家族で《温泉》に行く予定だ。",
    "n2-vocab_reading-0422": "日本は《温帯》に属している。",
    "n2-vocab_reading-0423": "会社に手紙を送るときは、宛名に《御中》と書く。",
    "n2-vocab_reading-0424": "あの《女の人》は私の母です。",
    "n2-vocab_reading-0425": "夏の夜は《蚊》に刺されないように気をつけている。",
    "n2-vocab_reading-0426": "ただいまから会議の《開会》を宣言します。",
    "n2-vocab_reading-0427": "市民《会館》でコンサートが開かれる。",
    "n2-vocab_reading-0428": "クラス会は十時に《解散》した。",
    "n2-vocab_reading-0429": "子供の頃、毎年夏に《海水浴》に行くのが楽しみだった。",
    "n2-vocab_reading-0430": "図書館に行く《回数》が増えた。",
    "n2-vocab_reading-0431": "《回数券》を買うと定期より安い。",
}


def main():
    batch_path = "/home/tetsuya/Development/openjlpt/repair_workdir/batch_04.json"
    output_path = "/home/tetsuya/Development/openjlpt/repair_workdir/sentences_04.json"

    with open(batch_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Total questions in batch: {len(questions)}")

    result = {}
    missing = []

    for q in questions:
        qid = q["id"]
        target = q["target"]
        if qid in sentences:
            result[qid] = sentences[qid]
        else:
            missing.append((qid, target))

    if missing:
        print(f"WARNING: {len(missing)} questions have no sentence:")
        for qid, target in missing:
            print(f"  {qid} ({target})")

    # Verify all present
    print(f"Sentences generated: {len(result)}")

    # Sort by id for clean output
    sorted_result = dict(sorted(result.items()))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_result, f, ensure_ascii=False, indent=2)

    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()
