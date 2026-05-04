import json

# JLPT N1 vocabulary reading items batch 06 (idx 511-610)
# Generate one natural N1-level sentence per target word, marked with 《》

sentences = {
    # idx 511
    "n1-vocab_reading-0511": "書留郵便の《受け取り》には本人確認が必要となる場合がある。",
    # idx 512
    "n1-vocab_reading-0512": "株式市場の《動き》を注視していれば、投資のタイミングが見極められるだろう。",
    # idx 513
    "n1-vocab_reading-0513": "日本海側では春先になると《潮》の香りが一層強くなる。",
    # idx 514
    "n1-vocab_reading-0514": "議論の《渦》に巻き込まれ、彼は自分の意見を見失ってしまった。",
    # idx 515
    "n1-vocab_reading-0515": "予約で席が《埋まる》のは時間の問題だと担当者は冷ややかに言った。",
    # idx 516
    "n1-vocab_reading-0516": "彼の話はことごとく誇張ばかりで、周囲からは《嘘つき》の烙印を押されている。",
    # idx 517
    "n1-vocab_reading-0517": "企画の《打ち合わせ》は来週の月曜日に設定されている。",
    # idx 518
    "n1-vocab_reading-0518": "事前に工程を《打ち合わせる》ことで、無駄な手間を省くことができる。",
    # idx 519
    "n1-vocab_reading-0519": "彼は私の主張を一方的に《打ち消し》しようとしたが、私は折れなかった。",
    # idx 520
    "n1-vocab_reading-0520": "彼女は研究に《打ち込む》あまり、睡眠時間すら惜しんでいる。",
    # idx 521
    "n1-vocab_reading-0521": "夏祭りの夜店で《団扇》を買い求め、涼を取ることにした。",
    # idx 522
    "n1-vocab_reading-0522": "請求書の《内訳》を確認したところ、不審な項目が含まれていた。",
    # idx 523
    "n1-vocab_reading-0523": "消費者の《訴え》を受けて、メーカーはようやく製品の回収に踏み切った。",
    # idx 524
    "n1-vocab_reading-0524": "梅雨の時期はどこもかしこも《鬱陶しい》湿気で満ちている。",
    # idx 525
    "n1-vocab_reading-0525": "原本と《写し》を睨み合わせて、誤記がないか慎重に照合した。",
    # idx 526
    "n1-vocab_reading-0526": "長年追い求めてきた夢が叶った今、心の中は《空ろ》な感覚でいっぱいだ。",
    # idx 527
    "n1-vocab_reading-0527": "彼は悲劇的な状況にあっても動じることなく、まさに大《器》の人物だ。",
    # idx 528
    "n1-vocab_reading-0528": "《雨天》にもかかわらず、マラソン大会は予定通り決行された。",
    # idx 529
    "n1-vocab_reading-0529": "彼女の通訳としての《腕前》は、プロフェッショナルとして申し分ない。",
    # idx 530
    "n1-vocab_reading-0530": "寒い冬の日には、熱々の《饂飩》が何よりのご馳走である。",
    # idx 531
    "n1-vocab_reading-0531": "上司は部下に早期の決断を《促す》あまり、かえって彼らを委縮させてしまった。",
    # idx 532
    "n1-vocab_reading-0532": "深夜のオフィスで、サーバーが《唸る》ような低い音を立てている。",
    # idx 533
    "n1-vocab_reading-0533": "彼は成果を全て自分の手柄だと《自惚れ》ているが、周囲の支援があってのことだ。",
    # idx 534
    "n1-vocab_reading-0534": "世の中はそんなに《甘い》ものではないと、父はいつも口癖のように言っていた。",
    # idx 535
    "n1-vocab_reading-0535": "彼の抜群の運動神経は《生まれつき》のものであり、並大抵の努力では追い越せない。",
    # idx 536
    "n1-vocab_reading-0536": "船は《海路》を南へと進み、やがて水平線の彼方へと消えていった。",
    # idx 537
    "n1-vocab_reading-0537": "長年の経験が新たな発想を《産む》ことは、往々にしてあるものだ。",
    # idx 538
    "n1-vocab_reading-0538": "このICチップは製品の各部位に《埋め込む》ことが可能だ。",
    # idx 539
    "n1-vocab_reading-0539": "母の手作りの《梅干》は、塩気と酸味のバランスが絶妙だ。",
    # idx 540
    "n1-vocab_reading-0540": "彼が辞職した《末》に、後任を誰にするかで社内は紛糾した。",
    # idx 541
    "n1-vocab_reading-0541": "あの作家の新作は《売り出し》と同時に完売した。",
    # idx 542
    "n1-vocab_reading-0542": "創業者が自ら開発した商品を世に《売り出す》までには、十年近い歳月を要した。",
    # idx 543
    "n1-vocab_reading-0543": "工事現場からの騒音が《五月蝿い》と近隣住民から苦情が殺到した。",
    # idx 544
    "n1-vocab_reading-0544": "新製品の《売れ行き》が芳しくなく、在庫が大量に残ってしまった。",
    # idx 545
    "n1-vocab_reading-0545": "彼の《浮気》が原因で、長年続いた結婚生活は終わりを告げた。",
    # idx 546
    "n1-vocab_reading-0546": "交渉の場では、常に《上手》に立つ者こそが主導権を握るものだ。",
    # idx 547
    "n1-vocab_reading-0547": "今月の売上高は、目標値を大幅に《上回る》見込みである。",
    # idx 548
    "n1-vocab_reading-0548": "庭の片隅に薔薇が《植わる》ことになり、春には見事な花を咲かせるだろう。",
    # idx 549
    "n1-vocab_reading-0549": "この地域では《運送》業界の人材不足が深刻化している。",
    # idx 550
    "n1-vocab_reading-0550": "バスの《運賃》が来月から値上げされるという知らせに、利用者からは嘆きの声が上がった。",
    # idx 551
    "n1-vocab_reading-0551": "その計画には予算不足、人材不足、《云々》の問題が山積している。",
    # idx 552
    "n1-vocab_reading-0552": "彼は《運命》に翻弄されながらも、決して希望を手放さなかった。",
    # idx 553
    "n1-vocab_reading-0553": "《運輸》省の発表によれば、来年度の公共交通機関の整備予算は倍増するという。",
    # idx 554
    "n1-vocab_reading-0554": "このシステムの《運用》には専門的な知識が必要とされる。",
    # idx 555
    "n1-vocab_reading-0555": "今回の《会》をもって、この研究会は解散することになった。",
    # idx 556
    "n1-vocab_reading-0556": "物理学では、《重》と質量の概念を厳密に区別する必要がある。",
    # idx 557
    "n1-vocab_reading-0557": "水族館で《鱝》が優雅に泳ぐ姿に見入ってしまった。",
    # idx 558
    "n1-vocab_reading-0558": "《映写》機の調子が悪く、映画の上映開始が遅れてしまった。",
    # idx 559
    "n1-vocab_reading-0559": "看板には《英字》で店名が記されている。",
    # idx 560
    "n1-vocab_reading-0560": "公衆《衛生》の観点から、駅構内のすべての手すりが抗菌加工されている。",
    # idx 561
    "n1-vocab_reading-0561": "監視カメラの《映像》には、不審な人物が映っていた。",
    # idx 562
    "n1-vocab_reading-0562": "この実験に用いる《液》は、摂氏八十度まで加熱すると変色する性質がある。",
    # idx 563
    "n1-vocab_reading-0563": "彼女は主《役》を射止めるべく、連日遅くまで稽古に励んでいる。",
    # idx 564
    "n1-vocab_reading-0564": "書庫では貴重な資料を《閲覧》する際に、必ず手袋の着用が義務付けられている。",
    # idx 565
    "n1-vocab_reading-0565": "ワイシャツの《襟》が黄ばんでいたので、漂白剤に浸してから洗濯した。",
    # idx 566
    "n1-vocab_reading-0566": "彼女との《縁》が切れてからというもの、どこか心にぽっかりと穴が開いたようだ。",
    # idx 567
    "n1-vocab_reading-0567": "料理の最後に《塩》をひとつまみ加えることで、味がぐっと引き締まる。",
    # idx 568
    "n1-vocab_reading-0568": "彼女が身につけている真珠のネックレスは、上品な《艶》を放っている。",
    # idx 569
    "n1-vocab_reading-0569": "祖父は庭《園》の手入れを日課にしており、四季折々の花が絶えない。",
    # idx 570
    "n1-vocab_reading-0570": "両国間の関係を《円滑》に進めるためには、率直な対話が不可欠だ。",
    # idx 571
    "n1-vocab_reading-0571": "古い日本家屋には《縁側》があり、そこに座って庭を眺めるのが彼の至福の時間だった。",
    # idx 572
    "n1-vocab_reading-0572": "《沿岸》地域では高潮に対する防災対策の強化が急務となっている。",
    # idx 573
    "n1-vocab_reading-0573": "彼の《婉曲》な言い回しは、かえって相手に誤解を与えかねない。",
    # idx 574
    "n1-vocab_reading-0574": "消防署では定期的に避難《演習》が実施されている。",
    # idx 575
    "n1-vocab_reading-0575": "あの映画監督の《演出》は、細部にまで徹底的にこだわることで知られている。",
    # idx 576
    "n1-vocab_reading-0576": "彼が舞台で主役を《演じる》姿には、観客全員が圧倒された。",
    # idx 577
    "n1-vocab_reading-0577": "彼は観客の前で即興劇を《演ずる》ことにためらいを覚えなかった。",
    # idx 578
    "n1-vocab_reading-0578": "《沿線》には桜並木が続いており、春には花見客で賑わう。",
    # idx 579
    "n1-vocab_reading-0579": "彼女は知人から《縁談》を持ちかけられたが、まだ結婚の意志はないと断った。",
    # idx 580
    "n1-vocab_reading-0580": "《遠方》からわざわざ足を運んでくださった皆様に、心より感謝申し上げます。",
    # idx 581
    "n1-vocab_reading-0581": "あの夫婦は何事においても話し合いを欠かさず、《円満》な関係を築いている。",
    # idx 582
    "n1-vocab_reading-0582": "猫は《尾》を立てて歩いている。",
    # idx 583
    "n1-vocab_reading-0583": "本日《於》いては、特別な行事が行われる予定である。",
    # idx 584
    "n1-vocab_reading-0584": "私の《甥》は今年小学校に入学したばかりだ。",
    # idx 585
    "n1-vocab_reading-0585": "相手に結論を急かすように《追い込む》のは、交渉の戦略として有効な手段だ。",
    # idx 586
    "n1-vocab_reading-0586": "この店のラーメンは《美味しい》と評判で、いつも行列が絶えない。",
    # idx 587
    "n1-vocab_reading-0587": "不良社員を会社から《追い出す》措置を取らざるを得なかった。",
    # idx 588
    "n1-vocab_reading-0588": "昨年度《於いて》は、売上が前期比で十パーセント増加した。",
    # idx 589
    "n1-vocab_reading-0589": "先生は今日も教室に《お出でになる》と聞いて、生徒たちは緊張の面持ちだった。",
    # idx 590
    "n1-vocab_reading-0590": "人は誰しも《老いる》ことを避けられないものである。",
    # idx 591
    "n1-vocab_reading-0591": "《応急》処置として、まず傷口を清潔な布で圧迫して止血した。",
    # idx 592
    "n1-vocab_reading-0592": "《黄金》比は、美術や建築の分野で古くから美の基準とされてきた。",
    # idx 593
    "n1-vocab_reading-0593": "《黄色》信号は注意を促す合図であり、決して無視してはならない。",
    # idx 594
    "n1-vocab_reading-0594": "採用《応募》の締め切りは今月末とされている。",
    # idx 595
    "n1-vocab_reading-0595": "《大方》の予想に反して、その新興企業は巨大企業を買収した。",
    # idx 596
    "n1-vocab_reading-0596": "彼は《大柄》な体格を活かしてラグビーで大活躍している。",
    # idx 597
    "n1-vocab_reading-0597": "彼の話は《大げさ》な誇張が多く、真に受ける者は誰もいない。",
    # idx 598
    "n1-vocab_reading-0598": "親会社の《大事》を決めるのは、取締役会の役割である。",
    # idx 599
    "n1-vocab_reading-0599": "《大ざっぱ》な見積もりではあるが、改修費用は百万円を超えるだろう。",
    # idx 600
    "n1-vocab_reading-0600": "報告書の《大筋》に間違いはないが、細部のデータにいくつか誤りが見つかった。",
    # idx 601
    "n1-vocab_reading-0601": "秋の《大空》には、鴈がV字になって渡っていく様子が見えた。",
    # idx 602
    "n1-vocab_reading-0602": "政府は《大幅》な税制改正を来年度に実施する方針を固めた。",
    # idx 603
    "n1-vocab_reading-0603": "記録的な豪雨により、川が氾濫して《大水》に見舞われた地域もある。",
    # idx 604
    "n1-vocab_reading-0604": "この情報を《公》にするかどうかは、まだ決まっていない。",
    # idx 605
    "n1-vocab_reading-0605": "彼の成功は、両親の支えの《お蔭》であることは言うまでもない。",
    # idx 606
    "n1-vocab_reading-0606": "《お蔭様で》無事に退院することができました。ご親切に感謝いたします。",
    # idx 607
    "n1-vocab_reading-0607": "彼の言動は時として《可笑しい》ほどに真面目で、周囲の笑いを誘う。",
    # idx 608
    "n1-vocab_reading-0608": "未成年が法律を《犯す》と、成人とは異なる処遇が適用される。",
    # idx 609
    "n1-vocab_reading-0609": "ウイルスが人間の細胞に《侵す》メカニズムを解明する研究が進んでいる。",
    # idx 610
    "n1-vocab_reading-0610": "今日の夕飯の《お菜》は、肉じゃがとほうれん草の胡麻和えだ。",
}

# Validate: we must have 100 entries
assert len(sentences) == 100, f"Expected 100 sentences, got {len(sentences)}"

# Write output
with open("/home/tetsuya/Development/openjlpt/repair_workdir/sentences_n1_06.json", "w", encoding="utf-8") as f:
    json.dump(sentences, f, ensure_ascii=False, indent=2)

print(f"Written {len(sentences)} sentences to sentences_n1_06.json")

# Print missing IDs for verification
import json as j
with open("/home/tetsuya/Development/openjlpt/repair_workdir/n1_batch_06.json", "r") as f:
    items = j.load(f)

all_ids = {item["id"] for item in items}
generated_ids = set(sentences.keys())
missing = all_ids - generated_ids
extra = generated_ids - all_ids
if missing:
    print(f"Missing IDs: {sorted(missing)}")
if extra:
    print(f"Extra IDs: {sorted(extra)}")
if not missing and not extra:
    print("All IDs matched correctly.")
