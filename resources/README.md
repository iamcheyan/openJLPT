# OpenJLPT 题库资源统计

## 一、目录结构

```
resources/
├── vocabulary/          ← 词汇
│   ├── n5.csv
│   ├── n4.csv
│   ├── n3.csv
│   ├── n2.csv
│   └── n1.csv
├── grammar/             ← 语法
│   ├── n5.json
│   ├── n4.json
│   ├── n3.json
│   ├── n2.json
│   └── n1.json
└── kanji/               ← 汉字
    └── jlpt-kanji.json
```

---

## 二、词汇（vocabulary）

来源：[stephenmk/yomitan-jlpt-vocab](https://github.com/stephenmk/yomitan-jlpt-vocab)（⭐130）

| 级别 | 词汇量 | 文件大小 |
|------|--------|---------|
| N5 | 685词 | 24KB |
| N4 | 641词 | 25KB |
| N3 | 1,731词 | 89KB |
| N2 | 1,813词 | 95KB |
| N1 | 3,428词 | 199KB |
| **合计** | **8,298词** | **432KB** |

数据格式（CSV）：
```
jmdict_seq,kana,kanji,waller_definition
1198180,あう,会う,to meet
1381380,あお,青,blue
```

字段说明：
| 字段 | 说明 |
|------|------|
| jmdict_seq | JMdict词典编号 |
| kana | 假名读音 |
| kanji | 汉字写法（部分词无汉字） |
| waller_definition | 英文释义 |

---

## 三、语法（grammar）

来源：[jkindrix/japanese-language-data](https://github.com/jkindrix/japanese-language-data)（⭐3）

| 级别 | 语法点数 | 文件大小 |
|------|---------|---------|
| N5 | 77个 | 121KB |
| N4 | 89个 | 162KB |
| N3 | 130个 | 241KB |
| N2 | 149个 | 261KB |
| N1 | 150个 | 249KB |
| **合计** | **595个** | **1,034KB** |

数据格式（JSON）：
```json
{
  "id": "you-da-appearance",
  "pattern": "Plain form + ようだ",
  "level": "N3",
  "meaning_en": "appears / seems (evidence-based, formal)",
  "meaning_detailed": "ようだ expresses an inference...",
  "formation": "V plain / i-adj + ようだ. Na-adj + な + ようだ...",
  "formation_notes": ["Note the different connectors..."],
  "formality": "neutral",
  "related": ["mitai-looks-like", "sou-da-appearance"],
  "examples": [
    {
      "japanese": "誰もいないようだ。",
      "english": "It seems nobody is here."
    }
  ]
}
```

字段说明：
| 字段 | 说明 |
|------|------|
| id | 语法点唯一标识 |
| pattern | 语法接续模式，如「Noun + です」 |
| level | JLPT级别 |
| meaning_en | 英文释义（简短） |
| meaning_en | 英文释义（详细用法说明） |
| formation | 接续方式 |
| formation_notes | 接续注意事项 |
| formality | 正式程度（formal / casual / neutral） |
| related | 相关语法点 |
| examples | 例句数组（日英对照） |

---

## 四、汉字（kanji）

来源：[AnchorI/jlpt-kanji-dictionary](https://github.com/AnchorI/jlpt-kanji-dictionary)（⭐26）

| 级别 | 汉字数 |
|------|--------|
| N5 | 80个 |
| N4 | 170个 |
| N3 | 370个 |
| N2 | 380个 |
| N1 | 1,135个 |
| **合计** | **2,136个** |

数据格式（JSON）：
```json
{
  "id": 1,
  "kanji": "人",
  "strokes": 2,
  "jlpt": "N5",
  "description": "人 is a Japanese kanji that means person."
}
```

---

## 五、资源总览

| 类型 | 总量 | 文件总大小 |
|------|------|-----------|
| 词汇 | 8,298词 | 432KB |
| 语法 | 595个 | 1,034KB |
| 汉字 | 2,136个 | 736KB |
| **合计** | — | **2,202KB（约2.2MB）** |

---

## 六、待办

- [ ] 词汇数据只有英文释义，是否需要补充中文释义？
- [ ] 语法数据只有英文释义，是否需要补充中文释义？
- [ ] 确定从哪个级别开始生成题库（建议N3）
- [ ] 确定题型和出题方式
