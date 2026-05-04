const fs = require('fs');
const path = require('path');

const addTranslations = (fileName, translations) => {
    const filePath = path.join(__dirname, '..', 'data', 'n2', fileName);
    if (!fs.existsSync(filePath)) return;
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    data.questions.forEach((q, index) => {
        if (translations[q.id]) {
            q.translation = translations[q.id];
        } else if (translations[index]) {
            q.translation = translations[index];
        }
    });
    
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`Added translations to ${fileName}`);
};

// Reading Short Translations
const shortTrans = {
    "n2-reading_short-001": "最近日本年轻人的海外旅行非常有人气。特别是欧洲国家，其原因是由于文化差异带来的新鲜感。",
    "n2-reading_short-002": "在这个快节奏的社会中，很多人感到压力。缓解压力的方法有很多，比如运动、冥想或者听音乐。",
    "n2-reading_short-003": "由于健康意识的提高，越来越多的人开始关注饮食。低脂、低糖的食品在超市里非常畅销。",
    "n2-reading_short-014": "【图书馆通知】从下个月开始，馆内将进行空调设备施工。施工期间可能会产生噪音，如果您想在安静的环境下阅读，请使用别馆的学习室。此外，施工期间不会闭馆，但部分书架的进入将受到限制。感谢您的理解与配合。",
    "n2-reading_short-015": "常听人说“现在的年轻人没有毅力”。但这真的是事实吗？现代年轻人只是倾向于避开无意义的辛苦，对于自己感到有价值的事情，他们会发挥出惊人的集中力和持久力。时代变了，毅力的对象和形式也会改变。不应仅凭旧标准来判断当今一代。",
    "n2-reading_short-016": "【新商品推迟发售通知】原定于本月15日发售的新商品“樱花拿铁”，由于订单量超过预期，导致原材料难以确保。诚为抱歉，发售将推迟至下月1日。对于给预约客户带来的巨大困扰，我们深表歉意。",
    "n2-reading_short-017": "在选择工作时，重视年薪和福利是理所当然的。然而，最重要的难道不是“这份工作对自己是否有意义”这一点吗？无论薪水再高，如果感受不到成就感，长期坚持工作在精神上是很痛苦的。当自己的价值观与工作内容一致时，人才能最大限度地发挥能力。",
    "n2-reading_short-018": "【垃圾收集日变更】从下月起，每月第2、第4个星期三的“不可燃垃圾”收集日，将变更至与每周五的“塑料资源”同一天。但是，由于垃圾车是分开来的，请注意不要混在一起投放。另外，请在早上8点前投放到指定地点。请遵守规则，配合美化城市。"
};

// Reading Medium Translations
const mediumTrans = {
    "n2-reading_medium-001": "日本文化包含和式庭院、传统武术、茶道等。这些象征着日本传统，日本人在这些文化中感受到了和谐的精神。",
    "n2-reading_medium-016": "“工作生活平衡”一词流行已久，但最近“工作生活融合”这一理念备受关注。这并非将工作与生活视为对立的两方进行切分，而是将其整合（Integration），从而提高整个人生的满意度。例如，将兴趣知识运用到工作中，或者让工作中的人际关系丰富私人生活。随着数字技术的进步，人们不再受场所和时间的束缚，这推动了这一理念。当然，对于公私界限完全消失也存在不安。但是，既然工作和生活都是由“自己”这一独立个体进行的活动，那么让它们相互产生积极影响的形式，或许才是未来理想的生活方式。",
    "n2-reading_medium-017": "日本的食品浪费问题很严重。明明还能吃却被丢弃的食品每年达数百万吨。背景是消费者对“新鲜度”的过度期待，以及零售业“三分之一规则”的惯例。即从制造日到保质期分为三段，过了前三分之一就不能进货，过了中间三分之一就从柜台撤下。但这并无科学依据。近年来环保意识提高，这一规则正在被重新审视。低价销售临期食品的“食品共享”应用也很受欢迎。我们消费者也不应被外观和日期迷惑，需要用自己的感官来判断是否真的不能吃了。"
};

addTranslations('reading_short.json', shortTrans);
addTranslations('reading_medium.json', mediumTrans);
