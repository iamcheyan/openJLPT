#!/usr/bin/env python3
"""Generate natural Japanese N2-level sentences for batches 22-24.

Matches sentences to questions by position (index in each batch array),
since the question IDs have gaps in numbering.
"""
import json

# Sentences for batch_22 items, in the same order as the batch array
sentences_22_list = [
    # idx 988: 突っ込む
    "プールに飛び《突っ込む》と、冷たい水が気持ちよかった。",
    # idx 989: 務める
    "彼女は卒業後、地元の銀行に《務める》ことになった。",
    # idx 990: 努める
    "毎日少しずつ練習を《努める》ことが上達の秘訣だ。",
    # idx 991: 綱
    "荷物を運ぶために太い《綱》を準備した。",
    # idx 992: 繋がる
    "この二つの事件は深く《繋がる》ているらしい。",
    # idx 993: 粒
    "一粒一粒の《粒》がしっかりとした食感で美味しい。",
    # idx 994: 潰す
    "時間を《潰す》ために駅前の本屋で立ち読みした。",
    # idx 995: 潰れる
    "台風で停電すると冷蔵庫の食材が《潰れる》恐れがある。",
    # idx 996: 詰まる
    "道路工事のせいでこの道はいつも車が《詰まる》ている。",
    # idx 997: 爪
    "猫が《爪》を出してカーペットを引っかいてしまった。",
    # idx 998: 艶
    "このテーブルは表面の《艶》が美しく、高級感がある。",
    # idx 999: 強気
    "彼は株に対する《強気》の姿勢を崩さない。",
    # idx 1000: 釣り合う
    "収入と支出のバランスが《釣り合う》ように家計を管理している。",
    # idx 1001: 吊る
    "天井からランプを《吊る》ために、専用のフックを取り付けた。",
    # idx 1002: 定員
    "この劇場の《定員》は五百人だ。",
    # idx 1003: 定価
    "この商品は《定価》の三割引で販売されている。",
    # idx 1004: 定期券
    "《定期券》の期限が切れる前に更新しなければならない。",
    # idx 1005: 定休日
    "あのレストランは毎週水曜日が《定休日》だ。",
    # idx 1006: 停電
    "昨夜の台風で一時間ほど《停電》した。",
    # idx 1007: 出入口
    "駅の《出入口》で友達と待ち合わせをした。",
    # idx 1008: 出来上がり
    "ケーキの《出来上がり》を見て、思わず歓声を上げた。",
    # idx 1009: 出来上がる
    "注文した家具がやっと《出来上がる》まであと三日だ。",
    # idx 1010: 適確
    "彼の分析はいつも《適確》で、誰もが信頼している。",
    # idx 1011: 手首
    "転んだ時に《手首》を捻ってしまったらしい。",
    # idx 1012: 凸凹
    "古い道は《凸凹》が多くて自転車の運転が大変だ。",
    # idx 1013: 手頃
    "この値段なら《手頃》なので、迷わず購入した。",
    # idx 1014: 鉄橋
    "川に架かる《鉄橋》は百年前に建設されたものだ。",
    # idx 1015: 手続き
    "入園の《手続き》は窓口で行ってください。",
    # idx 1016: 鉄砲
    "子供の頃、竹で《鉄砲》を作って遊んだ記憶がある。",
    # idx 1017: 手拭い
    "旅先で買った《手拭い》を毎日使っている。",
]

# Sentences for batch_23 items, in order
sentences_23_list = [
    # idx 1018: 手前
    "駅の《手前》の交差点を左に曲がると郵便局がある。",
    # idx 1019: 出迎え
    "空港での《出迎え》は家族全員で行くことにした。",
    # idx 1020: 出迎える
    "毎日駅まで子供を《出迎える》のが日課だ。",
    # idx 1021: 照らす
    "懐中電灯で足元を《照らす》と、道がよく見えた。",
    # idx 1022: 展開
    "事件の新たな《展開》に警察は注目している。",
    # idx 1023: 伝記
    "図書館で偉人の《伝記》を借りて読んでいる。",
    # idx 1025: 伝染
    "手洗いを徹底することで《伝染》を防ぐことができる。",
    # idx 1026: 電池
    "リモコンの《電池》が切れたので新しいものに替えた。",
    # idx 1027: 転々
    "彼は仕事を《転々》と変えて、なかなか落ち着かない。",
    # idx 1028: 天皇
    "《天皇》陛下のご在位を祝う行事が各地で行われた。",
    # idx 1030: 問い合わせ
    "製品についての《問い合わせ》が多くのお客様から寄せられている。",
    # idx 1031: 銅
    "この置物は《銅》でできている。",
    # idx 1032: 統一
    "異なる意見を《統一》するのは会議の重要な役割だ。",
    # idx 1033: 同格
    "両者は経験年数が同じなので《同格》とみなされる。",
    # idx 1034: 峠
    "《峠》の頂上まで登ると、一面の雲海が広がっていた。",
    # idx 1035: 統計
    "最新の《統計》によると、高齢化がさらに進んでいる。",
    # idx 1037: 東西
    "この通りは《東西》にまっすぐ伸びている。",
    # idx 1038: 当日
    "《当日》は混雑が予想されるので、早めに会場へお越しください。",
    # idx 1039: 投書
    "新聞の《投書》欄に意見を送ってみた。",
    # idx 1040: 登場
    "新しいキャラクターがこのドラマに《登場》するのは来週からだ。",
    # idx 1041: 灯台
    "岬の先端に立つ白い《灯台》が美しい。",
    # idx 1042: 当番
    "今日の《当番》は私なので、教室の掃除をしなければならない。",
    # idx 1043: 等分
    "賞金は四人で《等分》することにした。",
    # idx 1044: 透明
    "ガラスが《透明》なので中の様子がよく見える。",
    # idx 1045: 灯油
    "寒い冬には《灯油》ストーブが欠かせない。",
    # idx 1046: 東洋
    "《東洋》の文化に興味がある留学生が増えている。",
    # idx 1047: 童話
    "子供のころよく読んだ《童話》を、今でも覚えている。",
    # idx 1048: 通り掛かる
    "事故現場に《通り掛かる》と、既に救急車が到着していた。",
    # idx 1050: 尖る
    "鉛筆の先が《尖る》ので、手を切らないように注意しよう。",
    # idx 1051: 溶く
    "卵を《溶く》ときは、白身と黄身がよく混ざるまでかき混ぜる。",
]

# Sentences for batch_24 items, in order
sentences_24_list = [
    # idx 1052: 退く
    "車が来たので道の端に《退く》ことにした。",
    # idx 1053: 特殊
    "この機械は《特殊》な部品を使っているため修理に時間がかかる。",
    # idx 1054: 特色
    "この地域の《特色》は何と言っても新鮮な海産物だ。",
    # idx 1055: 特長
    "彼の《特長》はどんな状況でも冷静さを失わないことだ。",
    # idx 1056: 特定
    "《特定》の人物だけを対象にしたアンケートを実施した。",
    # idx 1057: 特売
    "このスーパーは毎週水曜日に《特売》を開催している。",
    # idx 1058: 溶け込む
    "転校して間もないが、新しいクラスにすぐに《溶け込む》ことができた。",
    # idx 1059: 溶ける
    "バターは熱するとすぐに《溶ける》ので、料理に使いやすい。",
    # idx 1060: 退ける
    "歩行者の邪魔になる自転車を《退ける》ことにした。",
    # idx 1061: 床の間
    "和室には《床の間》が設けられていて、掛け軸が飾ってあった。",
    # idx 1062: 床屋
    "《床屋》で髪を切ってもらってさっぱりした。",
    # idx 1063: 所々
    "地震の影響で《所々》の道路が陥没している。",
    # idx 1064: 戸棚
    "キッチンの《戸棚》を整理して使いやすくした。",
    # idx 1065: 整う
    "結婚式の準備がようやく全て《整う》まで、あと一週間だ。",
    # idx 1068: 跳ぶ
    "子供たちはトランポリンの上で《跳ぶ》のを楽しんでいる。",
    # idx 1069: 泊める
    "友達を一晩《泊める》ために客間を片付けた。",
    # idx 1070: 捕える
    "猫が玄関先で雀を《捕える》ところだった。",
    # idx 1071: 取り入れる
    "新しいシステムを会社の業務に《取り入れる》ことにした。",
    # idx 1072: 取り消す
    "予約を《取り消す》場合は、前日までに連絡してください。",
    # idx 1073: 取り出す
    "財布から千円札を《取り出す》と、一緒にレシートも出てきた。",
    # idx 1074: 採る
    "会議で出た良い意見は積極的に《採る》べきだ。",
    # idx 1075: 捕る
    "川で魚を《捕る》ために網を用意した。",
    # idx 1076: 丼
    "昼食に《丼》ものを食べようと食堂に入った。",
    # idx 1077: 内科
    "《内科》で診察を受けたら、特に異常はないと言われた。",
    # idx 1078: 内線
    "会社に電話したら、《内線》で担当者につないでくれた。",
    # idx 1080: 永い
    "《永い》年月をかけて完成させた研究論文がついに発表された。",
    # idx 1081: 長引く
    "風邪が《長引く》と、仕事にも影響が出てしまう。",
    # idx 1082: 中身
    "箱の《中身》を確認してから送り状にサインした。",
    # idx 1083: 中味
    "プレゼントの《中味》は開けてからのお楽しみだ。",
    # idx 1084: 中指
    "ギターを弾くときに《中指》を弦に引っかけてしまった。",
]


def main():
    base = "/home/tetsuya/Development/openjlpt/repair_workdir"
    batches = [
        ("batch_22.json", sentences_22_list, "sentences_22.json"),
        ("batch_23.json", sentences_23_list, "sentences_23.json"),
        ("batch_24.json", sentences_24_list, "sentences_24.json"),
    ]

    all_ok = True
    for batch_file, sentence_list, output_file in batches:
        batch_path = f"{base}/{batch_file}"
        output_path = f"{base}/{output_file}"

        with open(batch_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        if len(questions) != len(sentence_list):
            print(
                f"ERROR: {batch_file} has {len(questions)} items but "
                f"sentence list has {len(sentence_list)} sentences."
            )
            all_ok = False
            continue

        result = {}
        for i, (q, sentence) in enumerate(zip(questions, sentence_list)):
            qid = q["id"]
            target = q["target"]
            # Verify the target appears inside 《》 in the sentence
            if f"《{target}》" not in sentence:
                print(f"WARNING: Item {i} ({qid}) target '{target}' not found in sentence: {sentence}")
                all_ok = False
            result[qid] = sentence

        sorted_result = dict(sorted(result.items()))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_result, f, ensure_ascii=False, indent=2)

        print(f"{batch_file}: {len(result)} sentences written to {output_file}.")

    if all_ok:
        print("\nAll checks passed!")
    else:
        print("\nWarnings found above.")

    # Verify by reading back
    print("\nVerification:")
    for output_file in ["sentences_22.json", "sentences_23.json", "sentences_24.json"]:
        with open(f"{base}/{output_file}", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  {output_file}: {len(data)} sentences.")


if __name__ == "__main__":
    main()
