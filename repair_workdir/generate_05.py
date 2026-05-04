#!/usr/bin/env python3
"""Generate natural Japanese N2-level sentences for batch_05.json."""
import json

with open('/home/tetsuya/Development/openjlpt/repair_workdir/batch_05.json') as f:
    questions = json.load(f)

# Build id -> sentence map
sentences = {}

for q in questions:
    qid = q['id']
    target = q['target']
    marked = f"《{target}》"

    if target == '改正':
        s = f"法律の{marked}案が国会で承認された。"
    elif target == '快晴':
        s = f"昨日までの雨が上がり、今日は{marked}となった。"
    elif target == '解説':
        s = f"先生がこの問題を詳しく{marked}してくれた。"
    elif target == '改造':
        s = f"古い車を{marked}して新しく生まれ変わらせた。"
    elif target == '開通':
        s = f"新しいトンネルが来月{marked}する予定だ。"
    elif target == '回転':
        s = f"このレストランは二十四時間{marked}している。"
    elif target == '解答':
        s = f"試験の{marked}を来週配ります。"
    elif target == '外部':
        s = f"{marked}から新しい社長が来た。"
    elif target == '解放':
        s = f"長かった仕事から{marked}されてほっとした。"
    elif target == '開放':
        s = f"学校の体育館を地域に{marked}することになった。"
    elif target == '海洋':
        s = f"{marked}汚染の問題について調べている。"
    elif target == '概論':
        s = f"この授業では日本文学の{marked}を学ぶ。"
    elif target == '帰す':
        s = f"子供たちを早く家に{marked}ましょう。"
    elif target == '却って':
        s = f"余計なことを言って、{marked}問題を複雑にしてしまった。"
    elif target == '家屋':
        s = f"古い{marked}を取り壊して新しい建物を建てる。"
    elif target == '係わる':
        s = f"この問題に{marked}人は全員集まってください。"
    elif target == '書留':
        s = f"大切な書類は{marked}で送ったほうが安心だ。"
    elif target == '書取':
        s = f"日本語の授業で{marked}の練習をした。"
    elif target == '垣根':
        s = f"隣の家との{marked}に花を植えた。"
    elif target == '掻く':
        s = f"暑くて汗を{marked}いる。"
    elif target == '嗅ぐ':
        s = f"花の香りを{marked}でみた。"
    elif target == '各地':
        s = f"{marked}から観光客が集まっている。"
    elif target == '拡張':
        s = f"駐車場を{marked}する工事が始まった。"
    elif target == '学年':
        s = f"この{marked}になると、新しい科目が増える。"
    elif target == '格別':
        s = f"母の手料理の味は{marked}だ。"
    elif target == '確率':
        s = f"宝くじが当たる{marked}は非常に低い。"
    elif target == '掛け算':
        s = f"小学校で{marked}の九九を覚えた。"
    elif target == '可決':
        s = f"新しい法案が国会で{marked}された。"
    elif target == '下降':
        s = f"気温が急に{marked}して、雪が降り出した。"
    elif target == '重なる':
        s = f"予定が{marked}で、どちらに行くか迷っている。"
    else:
        s = f"「{marked}」の意味を調べてください。"
        print(f"WARNING: unhandled target: {target} ({qid})")

    sentences[qid] = s

# Write output
output_path = '/home/tetsuya/Development/openjlpt/repair_workdir/sentences_05.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(sentences, f, ensure_ascii=False, indent=2, sort_keys=True)

print(f"Written {len(sentences)} sentences to {output_path}")

# Verify no missing
expected_count = len(questions)
actual_count = len(sentences)
if expected_count == actual_count:
    print(f"All {expected_count} sentences generated successfully.")
else:
    print(f"MISMATCH: expected {expected_count}, got {actual_count}")
