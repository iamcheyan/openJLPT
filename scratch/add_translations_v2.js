const fs = require('fs');
const path = require('path');

const addTranslations = (fileName, translations) => {
    const filePath = path.join(__dirname, '..', 'data', 'n2', fileName);
    if (!fs.existsSync(filePath)) return;
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    data.questions.forEach((q, index) => {
        if (translations[q.id]) {
            q.translation = translations[q.id];
        }
    });
    
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`Added translations to ${fileName}`);
};

// Reading Long Translations
const longTrans = {
    "n2-reading_long-001": "在众多的日本传统工艺品中，漆器尤为出名。漆器是指在木头或纸做的器皿上，涂上从漆树中提取的漆液并加工而成的工艺品。漆器不仅美观，还具有很强的防水性和耐久性，作为日常生活用品被广泛使用了很长时间。",
    "n2-reading_long-003": "虽然常说“失败乃成功之母”，但这句话只有在正确分析失败并将其运用于下一次时才能发挥作用。失败本身并无价值。重要的是失败后如何行动。\n许多人在失败时会责怪自己，并在那里停止思考。然而，优秀的学习者和研究者会将失败视为“数据”。冷静观察为何不顺利，并建立下一个假设。通过重复这一循环，就能稳步接近目标。\n在教育场合也是如此。对于在考试中取得低分的学生，不应只针对分数，而是要一起思考在哪里遇到了阻碍，这种姿态才能真正提高学力。将失败视为耻辱的文化可能会夺走挑战的意欲。作为整个社会，被要求培养一种包容失败并鼓励从中学习的氛围。",
    "n2-reading_long-015": "语言是随时代变化的生物。曾经被视为误用的表达，在被许多人使用的过程中获得了市民权（认可），并被收录进词典的情况并不少见。对此，“日语正在变乱”的叹息声总是存在。然而，如果语言的作用在于“沟通”，那么演变成那个时代的人们最容易传达的形式，难道不是一种自然的趋势吗？\n例如，作为年轻人口语出现的“やばい”一词，过去只有否定含义，但现在在表示“出色”的语境中也被广泛使用。像这样，通过给一个单词增加新的含义，也有拓宽表现力的一面。当然，在公共场合和商务场合，使用传统正确日语的能力是不可或缺的。能够根据情况切换语言，才称得上是真正的语言能力。\n重要的是，不应仅仅拒绝变化，而是要努力理解为什么那个词会产生，为什么受欢迎。语言的变化也是映照那个时代人们价值观和感觉的镜子。我们在接受变化的同时，也应努力不忘语言的美感和深度。"
};

// Reading Search Translations
const searchTrans = {
    "n2-reading_search-011": "【樱花体育中心利用指南】\n・开馆时间：9:00-21:00\n・闭馆日：每周一（如遇节假日则顺延至翌日）、年末年初\n・费用：\n  - 健身房：500日元（市内居住者：300日元）\n  - 游泳池：600日元（市内居住者：400日元）\n  - 通票：800日元（市内居住者：600日元）\n・备注：\n  1. 市内居住者请出示可确认地址的证件。\n  2. 65岁以上者费用减半。\n  3. 团体利用（10人以上）需提前1周预约。",
    "n2-reading_search-012": "【向日葵英语学校课程一览】\n1. 初级课程：周一、周四 18:00-19:00（月费 10,000日元）\n2. 中级课程：周二、周五 19:00-20:00（月费 12,000日元）\n3. 商务课程：周三、周六 20:00-21:00（月费 15,000日元）\n・优惠活动：\n  - 家庭入会：第2人起月费打8折\n  - 学生优惠：全课程月费减免2,000日元\n  - 介绍制度：向介绍人和被介绍人双方赠送3,000日元礼券\n※各项优惠不可并用。"
};

// Grammar Passage Translations (Samples)
const passageTrans = {
    "n2-grammar_passage-001": "他刚刚开始一份新工作，想详细了解工作内容。但是，详细情况目前还不清楚。",
    "n2-grammar_passage-006": "在新项目开始之际，全体团队成员举行了会议。领导说：“虽然这次计划非常困难，但如果成功，有望获得巨大的利益。”在推进准备的过程中，虽然也发生了预料之外的问题，但最终还是达成了目标。",
    "n2-grammar_passage-010": "通过留学，我得以拓宽了视野。在异国他乡生活的过程中，我（第一次）重新认识到了日本的优点。以此为契机，我将来想从事国际性的工作。"
};

addTranslations('reading_long.json', longTrans);
addTranslations('reading_search.json', searchTrans);
addTranslations('grammar_passage.json', passageTrans);
