#!/usr/bin/env python3
"""Generate natural Japanese sentences for n3_batch_12.json reading questions."""

import json

# map of question id -> natural JLPT N3-level sentence with target in 《》
sentences = {
    "n3-vocab_reading-1111": "新しいルールをこのプロジェクトに《適用》することにした。",
    "n3-vocab_reading-1112": "《出来るだけ》早くレポートを提出してください。",
    "n3-vocab_reading-1113": "パーティーで《手品》を披露したらみんな驚いていた。",
    "n3-vocab_reading-1114": "この橋は《鉄》でできているのでとても丈夫だ。",
    "n3-vocab_reading-1115": "引っ越しのとき、友達に《手伝い》を頼んだ。",
    "n3-vocab_reading-1116": "《鉄道》は日本の主要な交通手段の一つです。",
    "n3-vocab_reading-1117": "試験前の《徹夜》は体に良くないと知っている。",
    "n3-vocab_reading-1118": "この料理は作るのに《手間》がかかるが、とても美味しい。",
    "n3-vocab_reading-1119": "彼の意見は《典型》的な日本人の考え方だと言える。",
    "n3-vocab_reading-1120": "今日は《天候》が不安定なので、傘を持って出かけた方がいい。",
    "n3-vocab_reading-1121": "日本には昔からの《伝統》を大切にする習慣がある。",
    "n3-vocab_reading-1122": "この湖は《天然》のものなので、水がとてもきれいだ。",
    "n3-vocab_reading-1123": "先生に《問い》を出すときは、言葉遣いに気をつけましょう。",
    "n3-vocab_reading-1124": "彼は新しい《党》を作って選挙に出ることにした。",
    "n3-vocab_reading-1125": "東京タワーは有名な《塔》の一つです。",
    "n3-vocab_reading-1126": "試験の《答案》を提出する前に、もう一度確認しましょう。",
    "n3-vocab_reading-1127": "この二つの製品は《同一》のものではなく、少し違います。",
    "n3-vocab_reading-1128": "《当時》のことを思い出すと、懐かしい気持ちになる。",
    "n3-vocab_reading-1129": "「走る」という《動詞》は活用の種類が多い。",
    "n3-vocab_reading-1130": "食事をしながら《同時》にテレビを見る人が増えている。",
    "n3-vocab_reading-1131": "学校で《道徳》の授業が行われることがある。",
    "n3-vocab_reading-1132": "会長を決める《投票》が明日行われる予定だ。",
    "n3-vocab_reading-1133": "兄は父と《同様》に医者を目指している。",
    "n3-vocab_reading-1134": "会社の《同僚》と昼食を食べに行くことが多い。",
    "n3-vocab_reading-1135": "この《道路》は工事中なので、迂回してください。",
    "n3-vocab_reading-1136": "窓から新鮮な空気を《通す》ために、少し開けておいた。",
    "n3-vocab_reading-1137": "この《通り》をまっすぐ行くと駅に着く。",
    "n3-vocab_reading-1138": "あのバスは停留所を《通り過ぎる》ところだった。",
    "n3-vocab_reading-1139": "《都会》の生活に慣れるのに時間がかかった。",
    "n3-vocab_reading-1140": "帰る《時》になったら、私に知らせてください。",
    "n3-vocab_reading-1141": "この数学の問題を《解く》のに一時間かかった。",
    "n3-vocab_reading-1142": "キノコの中には《毒》があるものもあるので注意が必要だ。",
    "n3-vocab_reading-1143": "彼女は料理が《得意》で、よく友達を家に招いている。",
    "n3-vocab_reading-1144": "彼はまだ《独身》で、一人暮らしをしている。",
    "n3-vocab_reading-1145": "このレストランは《独特》な雰囲気があって人気だ。",
    "n3-vocab_reading-1146": "十八歳で親元を離れ、《独立》して生活し始めた。",
    "n3-vocab_reading-1147": "日曜日に友達と《登山》に行く約束をした。",
    "n3-vocab_reading-1148": "東京のような大《都市》には多くの人が集まる。",
    "n3-vocab_reading-1149": "本を読んだらちゃんと《閉じる》ようにしてください。",
    "n3-vocab_reading-1150": "《突然》の知らせに彼は驚いて言葉を失った。",
    "n3-vocab_reading-1151": "凧を高く《飛ばす》ために、もっと強い風が必要だ。",
    "n3-vocab_reading-1152": "猫が急に道に《飛び出す》ことがあるので気をつけて運転しよう。",
    "n3-vocab_reading-1153": "壁にカレンダーを《留める》ために画鋲を使った。",
    "n3-vocab_reading-1154": "彼は十年以上の《友》であり、大切な存在だ。",
    "n3-vocab_reading-1155": "来週の《土曜》日にコンサートに行く予定だ。",
    "n3-vocab_reading-1156": "動物園で《虎》の赤ちゃんが生まれたというニュースを見た。",
    "n3-vocab_reading-1157": "会議で新しい企画を《取り上げる》予定だ。",
    "n3-vocab_reading-1158": "このボタンは簡単に《取れる》ので、子供の服には付けない方がいい。",
    "n3-vocab_reading-1159": "雨の後、道が《泥》だらけになって歩きにくかった。",
    "n3-vocab_reading-1160": "この本の《内容》はとても面白くて、最後まで飽きなかった。",
    "n3-vocab_reading-1161": "涙を《流す》と気持ちがすっきりすることがある。",
    "n3-vocab_reading-1162": "会議の《半ば》で彼は突然意見を変えた。",
    "n3-vocab_reading-1163": "仕事を辞めた後も、前の職場の《仲間》とは連絡を取り合っている。",
    "n3-vocab_reading-1164": "山頂からの《眺め》はとても素晴らしかった。",
    "n3-vocab_reading-1165": "彼女は窓の外の景色を静かに《眺める》のが好きだ。",
    "n3-vocab_reading-1166": "川の《流れ》が速いので、泳ぐのは危険だ。",
    "n3-vocab_reading-1167": "事件の《謎》がようやく解けた。",
    "n3-vocab_reading-1168": "彼の説明を聞いて、ようやく《納得》した。",
    "n3-vocab_reading-1169": "図書館では、話すことや食べること《など》は禁止されている。",
    "n3-vocab_reading-1170": "彼は《何か》言いたそうだったが、結局何も言わなかった。",
    "n3-vocab_reading-1171": "新しい《鍋》を買ったので、週末に鍋料理を作ろうと思う。",
    "n3-vocab_reading-1172": "試験前に《怠ける》と後で後悔することになる。",
    "n3-vocab_reading-1173": "進路のことで《悩む》時期があった。",
    "n3-vocab_reading-1174": "彼女は立派な医者に《為る》ために毎日勉強している。",
    "n3-vocab_reading-1175": "長年の努力が実って、夢が《成る》のが楽しみだ。",
    "n3-vocab_reading-1176": "《縄》を使って荷物をしっかり縛った。",
    "n3-vocab_reading-1177": "《何で》今日の授業を休んだのか、理由を聞かせてください。",
    "n3-vocab_reading-1178": "彼は《何でも》一人でやろうとして、いつも忙しそうだ。",
    "n3-vocab_reading-1179": "お金が足りなかったが、《何とか》旅行に行くことができた。",
    "n3-vocab_reading-1180": "その赤いスカートはあなたによく《似合う》。",
    "n3-vocab_reading-1181": "台所からカレーの《匂い》がしてきた。",
    "n3-vocab_reading-1182": "私は人前で話すのが《苦手》なので、発表のときはいつも緊張する。",
    "n3-vocab_reading-1183": "手をしっかり《握る》と、相手の気持ちが伝わる気がする。",
    "n3-vocab_reading-1184": "このイベントは毎年同じ《日》に行われている。",
    "n3-vocab_reading-1185": "《日常》の小さな出来事に感謝することが大切だ。",
    "n3-vocab_reading-1186": "《日曜》日はいつもより遅く起きることが多い。",
    "n3-vocab_reading-1187": "《日光》に長時間当たると肌が焼けてしまう。",
    "n3-vocab_reading-1188": "《日中》は暖かいが、夜は冷え込むので注意が必要だ。",
    "n3-vocab_reading-1189": "来年、家族で《日本》の各地を旅行する予定だ。",
    "n3-vocab_reading-1190": "この映画は十八歳未満の《入場》が禁止されている。",
    "n3-vocab_reading-1191": "あの新しいカフェは若い人の間で《人気》がある。",
    "n3-vocab_reading-1192": "《人間》は他の動物と違って言葉を使ってコミュニケーションができる。",
    "n3-vocab_reading-1193": "この歯は痛いので、早く《抜く》ことにした。",
    "n3-vocab_reading-1194": "電車の中で眠ってしまい、降りる駅を《抜ける》ことができなかった。",
    "n3-vocab_reading-1195": "この《布》は柔らかくて肌触りがいい。",
    "n3-vocab_reading-1196": "急に雨が降り出したので、急いで帰らないと《濡れる》。",
    "n3-vocab_reading-1197": "この骨董品の《値》はいくらぐらいですか。",
    "n3-vocab_reading-1198": "その問題の《根》はもっと深いところにあると思う。",
    "n3-vocab_reading-1199": "彼は誕生日に《願い》を込めてろうそくを消した。",
    "n3-vocab_reading-1200": "台所に《鼠》が出たので、大家さんに連絡した。",
    "n3-vocab_reading-1201": "この商品は《値段》の割に品質が良い。",
    "n3-vocab_reading-1202": "彼は《熱心》にボランティア活動に取り組んでいる。",
    "n3-vocab_reading-1203": "沖縄は《熱帯》の気候で、冬でも暖かい。",
    "n3-vocab_reading-1204": "彼女は読書に《熱中》して、周りの音が聞こえなくなっていた。",
    "n3-vocab_reading-1205": "あの店は《年中》無休で営業している。",
    "n3-vocab_reading-1206": "この地域の建物は《年代》を感じさせるデザインが多い。",
    "n3-vocab_reading-1207": "日本では二十歳になると、《年齢》的にお酒が飲めるようになる。",
    "n3-vocab_reading-1208": "この辺りは昔、広い《野》原だったそうだ。",
    "n3-vocab_reading-1209": "彼はリーダーとしての《能》力を高めるために研修に参加した。",
    "n3-vocab_reading-1210": "祖父は《農家》として四十年前から米を作っている。",
}


def main():
    batch_path = "/home/tetsuya/Development/openjlpt/repair_workdir/n3_batch_12.json"
    output_path = "/home/tetsuya/Development/openjlpt/repair_workdir/sentences_n3_12.json"

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
