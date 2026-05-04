import json

# Batch 13 sentences
sentences_13 = {
    "n2-vocab_reading-0696": "再来年には、この地域に新しい図書館が建設される予定だ。",
    "n2-vocab_reading-0697": "工事現場の近くは一日中《騒がしく》て、勉強に集中できない。",
    "n2-vocab_reading-0698": "子供たちは折り紙で《三角》の形を作る練習をしている。",
    "n2-vocab_reading-0699": "彼は《算数》の問題を解くのがとても速くて、クラスで一番だった。",
    "n2-vocab_reading-0700": "この野菜は《産地》直送なので、新鮮で味が違う。",
    "n2-vocab_reading-0701": "新しいスーツが来週の火曜日までに《仕上がる》と言われた。",
    "n2-vocab_reading-0702": "この《寺院》は数百年の歴史があり、国の重要文化財に指定されている。",
    "n2-vocab_reading-0703": "災害に備えて、《自衛》のための備蓄品を用意しておくべきだ。",
    "n2-vocab_reading-0704": "彼女は結婚式の《司会》を頼まれて、緊張しながらも立派に務めた。",
    "n2-vocab_reading-0705": "テーブルの上に《四角》い箱が置いてあり、中には何が入っているのだろう。",
    "n2-vocab_reading-0706": "その《四角い》窓からは、美しい庭園の景色が見えた。",
    "n2-vocab_reading-0707": "日本は《四季》の変化が豊かで、それぞれの季節を楽しむことができる。",
    "n2-vocab_reading-0708": "この学校の《敷地》内には、体育館とプールが二つある。",
    "n2-vocab_reading-0709": "《至急》、田中さんに連絡を取ってくれませんか。",
    "n2-vocab_reading-0710": "畳の部屋にはそのまま布団を《敷く》だけで寝ることができる。",
    "n2-vocab_reading-0711": "庭の木々が《茂り》すぎて、日当たりが悪くなってしまった。",
    "n2-vocab_reading-0712": "旅行の際は、パスポートを必ず《持参》するように注意された。",
    "n2-vocab_reading-0714": "計算結果の小数点以下は《四捨五入》して、整数で報告してください。",
    "n2-vocab_reading-0715": "彼は《始終》携帯電話をいじっていて、会話に集中していなかった。",
    "n2-vocab_reading-0716": "先生が急用で来られなかったので、一時間目は《自習》になった。",
    "n2-vocab_reading-0717": "夜が更けるにつれて、街の騒音も次第に《静まって》きた。",
    "n2-vocab_reading-0718": "パソコン作業が長いと《姿勢》が悪くなり、肩や首が痛くなる。",
    "n2-vocab_reading-0719": "彼は《自然科学》に興味を持ち、大学では物理学を専攻した。",
    "n2-vocab_reading-0720": "私たちは《子孫》のために美しい地球を残さなければならない。",
    "n2-vocab_reading-0721": "東京の《下町》には、古くからの商店街が今も残っている。",
    "n2-vocab_reading-0722": "この地域では住民《自治》の活動が盛んで、多くのボランティアが参加している。",
    "n2-vocab_reading-0723": "一人暮らしを始めて、初めて家事の大変さを《実感》した。",
    "n2-vocab_reading-0724": "梅雨の時期は《湿気》が多くて、部屋の中がべたべたする。",
    "n2-vocab_reading-0725": "看護学校では、三年目に病院での《実習》が行われる。",
    "n2-vocab_reading-0726": "彼はこれまでの《実績》が評価されて、部長に昇進した。",
}

# Batch 14 sentences
sentences_14 = {
    "n2-vocab_reading-0727": "今日は《湿度》が高くて、ジョギングをするとすぐに汗をかく。",
    "n2-vocab_reading-0728": "彼は毎朝三時間、小説の《執筆》に集中している。",
    "n2-vocab_reading-0729": "雑誌で見るより《実物》のほうがずっと美しいと思った。",
    "n2-vocab_reading-0730": "このアプリは《実用》性が高く、毎日の生活に役立っている。",
    "n2-vocab_reading-0731": "この問題を解決した《実例》をいくつか紹介します。",
    "n2-vocab_reading-0732": "彼女は《失恋》してからしばらく元気がなかったが、最近やっと立ち直ったようだ。",
    "n2-vocab_reading-0733": "《指定》された時間に会議室に集まってください。",
    "n2-vocab_reading-0734": "東京にはJRのほかに多くの《私鉄》が走っている。",
    "n2-vocab_reading-0735": "この公園では毎日たくさんの《児童》が遊んでいる。",
    "n2-vocab_reading-0736": "最近は電子マネーが普及して、《紙幣》を使う機会が減った。",
    "n2-vocab_reading-0737": "スポンジをしっかり《絞っ》てから、机を拭いてください。",
    "n2-vocab_reading-0738": "彼女の服装はいつも《地味》だが、センスが良いと評判だ。",
    "n2-vocab_reading-0739": "レポートの《締切》は来週の金曜日なので、急いで仕上げなければならない。",
    "n2-vocab_reading-0740": "申し込みは今月末で《締め切る》予定ですので、お早めにお願いします。",
    "n2-vocab_reading-0741": "雨の日は洗濯物が《湿って》しまい、乾きにくい。",
    "n2-vocab_reading-0742": "大学では《社会科学》を専攻し、主に経済学と社会学を学んだ。",
    "n2-vocab_reading-0743": "台所の《蛇口》が壊れてしまい、水が止まらなくなった。",
    "n2-vocab_reading-0744": "彼は自分の《弱点》を克服するために、毎日努力を続けている。",
    "n2-vocab_reading-0745": "電車の中で《車掌》がアナウンスを流し、次の駅を知らせた。",
    "n2-vocab_reading-0746": "美術の授業で、学校の裏庭に出て《写生》をした。",
    "n2-vocab_reading-0747": "今朝の新聞の《社説》に、環境問題について詳しく書かれていた。",
    "n2-vocab_reading-0749": "彼の《洒落》はいつも面白くて、会議の雰囲気を和やかにしてくれる。",
    "n2-vocab_reading-0750": "毎月の家賃は大家さんが直接《集金》に来る。",
    "n2-vocab_reading-0751": "明日の朝八時に駅前に《集合》することになっている。",
    "n2-vocab_reading-0752": "子供の頃、三年間《習字》教室に通っていた。",
    "n2-vocab_reading-0753": "古い屋根の《修繕》には思ったより費用がかかると言われた。",
    "n2-vocab_reading-0754": "リビングの《絨毯》を新しいものに買い替えようと思っている。",
    "n2-vocab_reading-0755": "このバスは《終点》で折り返し、また駅前に戻ります。",
    "n2-vocab_reading-0756": "駅《周辺》にはたくさんのお店やレストランがある。",
    "n2-vocab_reading-0757": "演奏会は午後九時に《終了》し、観客から大きな拍手が送られた。",
}

# Batch 15 sentences
sentences_15 = {
    "n2-vocab_reading-0759": "宇宙空間では《重力》がほとんどないため、体が浮いてしまう。",
    "n2-vocab_reading-0760": "日本語の《熟語》を覚えるには、漢字の意味を理解することが大切だ。",
    "n2-vocab_reading-0761": "《祝日》には多くの人が公園やショッピングモールに出かける。",
    "n2-vocab_reading-0762": "彼女は来月、大学の《受験》を控えていて、毎日遅くまで勉強している。",
    "n2-vocab_reading-0763": "今朝は電車が遅れて、《出勤》時間に間に合わなかった。",
    "n2-vocab_reading-0764": "国語の授業で、主語と《述語》の関係について学んだ。",
    "n2-vocab_reading-0765": "来週大阪に《出張》することになったので、新幹線の予約をした。",
    "n2-vocab_reading-0766": "適度な運動は健康に良く、《寿命》を延ばす効果があると言われている。",
    "n2-vocab_reading-0767": "文化祭の劇で、彼女は見事に《主役》を演じきった。",
    "n2-vocab_reading-0768": "電話の《受話器》を取ると、聞き覚えのある声がした。",
    "n2-vocab_reading-0769": "血液の《循環》を良くするために、毎日軽い運動をするようにしている。",
    "n2-vocab_reading-0770": "交番の《巡査》が道に迷ったお年寄りに親切に道を教えていた。",
    "n2-vocab_reading-0771": "書類に目を通したら、《順々》に次の係に回してください。",
    "n2-vocab_reading-0772": "料理は《順序》よく準備しないと、時間がかかってしまう。",
    "n2-vocab_reading-0773": "彼女は《純情》な性格で、人の話をすぐに信じてしまうところがある。",
    "n2-vocab_reading-0774": "子供の《純粋》な質問に、大人は時々答えに困ってしまう。",
    "n2-vocab_reading-0777": "祖父は《将棋》が大好きで、週末にはよく友達と対戦している。",
    "n2-vocab_reading-0778": "やかんから湯気が立ち、窓ガラスが《蒸気》で曇ってしまった。",
    "n2-vocab_reading-0780": "彼は《消極的》な性格なので、自分から意見を言うことはほとんどない。",
    "n2-vocab_reading-0781": "コンテストで一等賞を取り、《賞金》を家族への旅行に使った。",
    "n2-vocab_reading-0782": "日本の伝統的な家屋では、窓に《障子》が使われていることが多い。",
    "n2-vocab_reading-0783": "来月《上旬》に新しい商品の発売を予定している。",
    "n2-vocab_reading-0784": "この問題は対応が遅れると、さらに大きな混乱を《生ずる》恐れがある。",
    "n2-vocab_reading-0785": "《小数》点の計算は、整数よりも細かい注意が必要だ。",
    "n2-vocab_reading-0786": "駅前の《商店》街は週末になると多くの買い物客で賑わう。",
    "n2-vocab_reading-0787": "このカメラは自動で《焦点》を合わせてくれるので、初心者にも使いやすい。",
    "n2-vocab_reading-0788": "傷口を《消毒》してから、絆創膏を貼ってください。",
    "n2-vocab_reading-0791": "《消防署》では二十四時間体制で消防士が待機している。",
    "n2-vocab_reading-0792": "長くなりましたので、詳細な説明は《省略》させていただきます。",
    "n2-vocab_reading-0793": "この段落は内容が重複しているので、《省略》しても問題ないだろう。",
}

# Load the original batch files to get the correct ID mapping
def load_ids(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        items = json.load(f)
    return {item["id"]: item["idx"] for item in items}

ids_13 = load_ids("/home/tetsuya/Development/openjlpt/repair_workdir/batch_13.json")
ids_14 = load_ids("/home/tetsuya/Development/openjlpt/repair_workdir/batch_14.json")
ids_15 = load_ids("/home/tetsuya/Development/openjlpt/repair_workdir/batch_15.json")

def build_output(sentences, ids):
    output = {}
    for id_key in ids:
        if id_key in sentences:
            output[id_key] = sentences[id_key]
        else:
            print(f"WARNING: Missing sentence for {id_key}")
    return output

output_13 = build_output(sentences_13, ids_13)
output_14 = build_output(sentences_14, ids_14)
output_15 = build_output(sentences_15, ids_15)

with open("/home/tetsuya/Development/openjlpt/repair_workdir/sentences_13.json", "w", encoding="utf-8") as f:
    json.dump(output_13, f, ensure_ascii=False, indent=2)

with open("/home/tetsuya/Development/openjlpt/repair_workdir/sentences_14.json", "w", encoding="utf-8") as f:
    json.dump(output_14, f, ensure_ascii=False, indent=2)

with open("/home/tetsuya/Development/openjlpt/repair_workdir/sentences_15.json", "w", encoding="utf-8") as f:
    json.dump(output_15, f, ensure_ascii=False, indent=2)

print("All 3 files written successfully.")
print(f"Batch 13: {len(output_13)} sentences")
print(f"Batch 14: {len(output_14)} sentences")
print(f"Batch 15: {len(output_15)} sentences")
print(f"Total: {len(output_13) + len(output_14) + len(output_15)} sentences")
