import json

# 修复所有 257 个错位和变形问题
# 其中包含 144-299 和 0790-0793 的严重错位问题
# 以及其他几十个动词变形的问题

reading_file = 'data/n2/vocab_reading.json'
kanji_file = 'data/n2/vocab_kanji.json'

corrections = {
    "n2-vocab_reading-0302": "彼は子供の頃よく災難に《遭う》ことがあった。",
    "n2-vocab_reading-0307": "彼は具体例を《挙げる》ことで、わかりやすく説明した。",
    "n2-vocab_reading-0308": "彼女は子供の頃から芸術家に《憧れる》傾向があった。",
    "n2-vocab_reading-0315": "酔っ払った男が駅前で《暴れる》ので、警察が駆けつけた。",
    "n2-vocab_reading-0325": "彼は若い頃に多くの小説を《著す》などの功績を残した。",
    "n2-vocab_reading-0329": "彼が突然その話を《言い出す》とは、誰も思わなかった。",
    "n2-vocab_reading-0351": "彼は後輩の前でいつも《威張る》から嫌われる。",
    "n2-vocab_reading-0358": "長い冬の間、人々は食べ物に《飢える》状況だった。",
    "n2-vocab_reading-0360": "彼女は満足そうな笑みを口元に《浮かべる》。",
    "n2-vocab_reading-0362": "お客様からのご要望を確かに《承る》。",
    "n2-vocab_reading-0366": "この洗剤は水で《薄める》のが正しい使い方です。",
    "n2-vocab_reading-0371": "この写真には遠くの山がきれいに《写る》。",
    "n2-vocab_reading-0372": "彼女の姿が窓ガラスに《映る》。",
    "n2-vocab_reading-0376": "布団を乾かすために、《裏返す》のがよい。",
    "n2-vocab_reading-0385": "新発売のゲームソフトはすぐに《売り切れる》だろう。",
    "n2-vocab_reading-0398": "安全確認を《怠る》と、大事故につながる恐れがある。",
    "n2-vocab_reading-0404": "私は彼から多くのことを《教わる》。",
    "n2-vocab_reading-0409": "後ろから大声を出して彼を《驚かす》。",
    "n2-vocab_reading-0414": "彼は自分が正しいと《思い込む》傾向がある。",
    "n2-vocab_reading-0416": "解決策をすぐに《思い付く》のは素晴らしい。",
    "n2-vocab_reading-0473": "掃除をしたので、机の上がやっと《片付く》。",
    "n2-vocab_reading-0476": "栄養が《片寄る》ことがないようにバランスよく食べよう。",
    "n2-vocab_reading-0488": "このカフェは喫茶店と本屋を《兼ねる》店舗だ。",
    "n2-vocab_reading-0490": "料理に蓋を《被せる》としばらく蒸らすことができる。",
    "n2-vocab_reading-0557": "地震の揺れで棚の上の本が《崩れる》危険がある。",
    "n2-vocab_reading-0558": "氷を《砕く》と、すぐに冷えて美味しい。",
    "n2-vocab_reading-0559": "窓ガラスに石が当たって、粉々に《砕ける》。",
    "n2-vocab_reading-0560": "船で川を《下る》と、三日目に目的地に着く。",
    "n2-vocab_reading-0562": "先生が教室でテスト用紙を一人ずつ《配る》。",
    "n2-vocab_reading-0566": "日曜日に子供と一緒に本棚を《組み立てる》。",
    "n2-vocab_reading-0567": "相手の事情も《酌む》ことが大切だ。",
    "n2-vocab_reading-0569": "彼はあの時もっと早く決断しなかったことを《悔やむ》。",
    "n2-vocab_reading-0570": "彼はタバコを《咥える》のが癖だ。",
    "n2-vocab_reading-0587": "彼はナイフで鉛筆を丁寧に《削る》。",
    "n2-vocab_reading-0636": "トーストを《焦がす》と、台所中に煙が充満する。",
    "n2-vocab_reading-0639": "ケーキが《焦げる》ことがないように温度に注意した。",
    "n2-vocab_reading-0648": "彼に「また後で連絡する」と《言付ける》ようにお願いします。",
    "n2-vocab_reading-0651": "涙が彼女の頬を伝って静かに《零れる》。",
    "n2-vocab_reading-0656": "子供がボールを楽しそうに《転がす》。",
    "n2-vocab_reading-0657": "ボールが坂道を勢いよく《転がる》。",
    "n2-vocab_reading-0667": "財布を落としたので、あちこち《捜す》。",
    "n2-vocab_reading-0677": "彼女は彼の耳元で何かを《囁く》。",
    "n2-vocab_reading-0678": "指にとげが《刺さる》と痛い。",
    "n2-vocab_reading-0681": "収入から支出を《差し引き》すると残りが今月の貯金だ。",
    "n2-vocab_reading-0683": "蜂に《刺す》危険があるので注意してください。",
    "n2-vocab_reading-0684": "彼女は花瓶に水を《注す》ことで生花を生けた。",
    "n2-vocab_reading-0685": "朝日が窓から部屋に優しく《射す》。",
    "n2-vocab_reading-0693": "スープが《冷める》前に早く食べてください。",
    "n2-vocab_reading-0697": "工事現場の近くは一日中《騒がしい》。",
    "n2-vocab_reading-0711": "庭の木々が《茂る》と、日当たりが悪くなる。",
    "n2-vocab_reading-0717": "夜が更けるにつれて、街の騒音も次第に《静まる》。",
    "n2-vocab_reading-0737": "スポンジをしっかり《絞る》のがポイントです。",
    "n2-vocab_reading-0741": "雨の日は洗濯物が《湿る》ため、乾きにくい。",
    "n2-vocab_reading-0895": "この新しい体育館は最新の空調設備を《具える》。",
    "n2-vocab_reading-0899": "子どもたちは新しいノートを机の上にきちんと《揃える》。",
    "n2-vocab_reading-0900": "その点につきましては、私もそう《存ずる》。",
    "n2-vocab_reading-0922": "使い終わったら折りたたみ傘をきちんと《畳む》こと。",
    "n2-vocab_reading-0943": "彼は手紙を読んだ後、怒ってびりびりに《千切る》。",
    "n2-vocab_reading-0948": "秋が深まると公園の葉っぱが《茶色い》色に変わっていく。",
    "n2-vocab_reading-0951": "この画家の作品は非常に《抽象》的だ。",
    "n2-vocab_reading-0970": "机の上に書類が《散らかる》と、必要な書類がすぐに見つからない。",
    "n2-vocab_reading-0971": "強い風が雲を《散らす》と、青空が広がってくる。",
    "n2-vocab_reading-0973": "桜の花びらが風に舞いながら、美しく《散る》。",
    "n2-vocab_reading-0978": "この抜け道は大通りに《通ずる》。",
    "n2-vocab_reading-0986": "この酒蔵では昔ながらの伝統的な方法で日本酒を《造る》。",
    "n2-vocab_reading-0987": "梅酒を作るには、梅をホワイトリカーに《浸ける》必要がある。",
    "n2-vocab_reading-1184": "航空券のキャンセルをしたら、手数料を引いた金額を《払い戻す》。",
    "n2-vocab_reading-1186": "試験に向けて《張り切る》のは良いことだ。",
    "n2-vocab_reading-1199": "彼は難しいプロジェクトを《引受る》ことに躊躇しなかった。",
    "n2-vocab_reading-1200": "途中で道を間違えたので、来た道を《引返す》。",
    "n2-vocab_reading-1202": "銀行でお金を《引出す》には、身分証明書が必要だ。",
    "n2-vocab_reading-1203": "友人が早く帰ろうとしたので、もう少しいてほしいと《引き止める》。",
    "n2-vocab_reading-1208": "セーターの袖がドアの取っ手に《引っ掛かる》。",
    "n2-vocab_reading-1210": "子どもが走り回って、テーブルの上のコップを《引っ繰り返す》。",
    "n2-vocab_reading-1223": "この薬は《日日》の時間を決めて、決められた量を飲んでください。",
    "n2-vocab_reading-1224": "瓶の蓋が固くて、力を込めて《捻る》。",
    "n2-vocab_reading-1228": "隣の部屋のテレビの音が《響く》ので、集中できない。",
    "n2-vocab_reading-1239": "テーブルの上に地図を《広げる》と見やすい。",
    "n2-vocab_reading-1243": "彼はボランティア活動を通して、地域交流の大切さを《広める》。",
    "n2-vocab_reading-1247": "貯金をしても利息がほとんどつかないので、なかなかお金が《殖える》ことはない。",
    "n2-vocab_reading-1252": "テーブルを濡れた布で《拭く》。",
    "n2-vocab_reading-1255": "参加費には昼食代も《含める》ことができる。",
    "n2-vocab_reading-1256": "子供たちが風船を《膨らます》。",
    "n2-vocab_reading-1261": "事故の影響で道路が《塞がる》。",
    "n2-vocab_reading-1278": "投資を始めて、少しずつ資産を《殖やす》。",
    "n2-vocab_reading-1384": "昨夜は《蒸し暑い》天候だった。",
    "n2-vocab_reading-1399": "彼女は才能に《恵まれる》人だ。",
    "n2-vocab_reading-1401": "彼は一流の料理人を《目指す》。",
    "n2-vocab_reading-1404": "彼女は派手な服装でいつも《目立つ》。",
    "n2-vocab_reading-1409": "書類の整理が《面倒臭い》。",
    "n2-vocab_reading-1411": "彼は株の取引で大金を《儲ける》。",
    "n2-vocab_reading-1415": "海に《潜る》と美しい珊瑚礁が見える。",
    "n2-vocab_reading-1419": "この古い写真は、家族の長い歴史を《物語る》。",
    "n2-vocab_reading-1422": "肩が凝ったので、母に《揉む》よう頼んだ。",
    "n2-vocab_reading-1441": "古くなったズボンの膝部分が《破れる》。",
    "n2-vocab_reading-1442": "このパンはとても《軟らかい》。",
    "n2-vocab_reading-1473": "白いシャツにコーヒーをこぼして《汚す》。",
    "n2-vocab_reading-1474": "机を壁に《寄せる》と部屋を広く使える。",
    "n2-vocab_kanji-919": "細い金属の棒を無理に《まげる》と、折れてしまう可能性がある。"
}

with open(reading_file, 'r', encoding='utf-8') as f:
    reading_data = json.load(f)

qs = reading_data['questions']

# 1. 修复偏移 144 到 300
for i in range(len(qs)):
    qid = qs[i]['id']
    if qid.startswith('n2-vocab_reading-'):
        num = int(qid.split('-')[-1])
        if 145 <= num <= 300:
            # qs[i] 的正确句子在 qs[i-1] 中
            qs[i]['sentence'] = qs[i-1]['sentence']

# 为 144 单独手写一个补充
for q in qs:
    if q['id'] == 'n2-vocab_reading-144':
        q['sentence'] = "彼はスポーツの世界で大いに《活躍》している。"

# 2. 修复偏移 0790 到 0793
# n2-vocab_reading-0790 (証明), n2-vocab_reading-0791 (小便), n2-vocab_reading-0792 (消防署), 0793(省略)
for i in range(len(qs)):
    qid = qs[i]['id']
    if qid.startswith('n2-vocab_reading-'):
        num = int(qid.split('-')[-1])
        if 791 <= num <= 793:
            qs[i]['sentence'] = qs[i-1]['sentence']
for q in qs:
    if q['id'] == 'n2-vocab_reading-0790':
        q['sentence'] = "自分の実力を《証明》するために試験を受ける。"

# 3. 修复字典 corrections
for q in qs:
    if q['id'] in corrections:
        q['sentence'] = corrections[q['id']]

with open(reading_file, 'w', encoding='utf-8') as f:
    json.dump(reading_data, f, ensure_ascii=False, indent=2)

print("Fixed vocab_reading.json")

with open(kanji_file, 'r', encoding='utf-8') as f:
    kanji_data = json.load(f)
    
for q in kanji_data['questions']:
    if q['id'] in corrections:
        q['sentence'] = corrections[q['id']]

with open(kanji_file, 'w', encoding='utf-8') as f:
    json.dump(kanji_data, f, ensure_ascii=False, indent=2)

print("Fixed vocab_kanji.json")
