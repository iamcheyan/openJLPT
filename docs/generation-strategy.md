# 题库生成策略

最后更新：2026-05-04

## 核心原则

题库生成不应该让模型自由选择考点，而应该由本地资源文件驱动：

```text
本地资源表
-> 选择尚未生成的词汇/语法点
-> 模型只负责写句子、干扰项、解析
-> 本地程序校验事实和结构
-> 审核通过后写入题库
-> 记录生成状态，后续只生成未完成项
```

这样可以降低幻觉、避免重复生成，并且能统计每个级别的覆盖率。

## 词汇题生成

适用题型：

- `vocab_reading`：① 漢字の読み方
- `vocab_kanji`：② 漢字の表記

主数据源：

```text
resources/vocabulary/n2.csv
```

字段含义：

```text
jmdict_seq,kana,kanji,waller_definition
```

生成逻辑：

### ① 漢字の読み方

用 `kanji` 作为目标词，用 `kana` 作为正确答案。

示例：

```text
目标词：掲載
正确读音：けいさい

句子：今回発表した新商品の広告が、雑誌に《掲載》された。
选项：けいさい / けさい / けっさい / けいざい
答案：けいさい
```

### ② 漢字の表記

用 `kana` 作为目标词，用 `kanji` 作为正确答案。

示例：

```text
目标读音：けいさい
正确表记：掲載

句子：広告が雑誌に《けいさい》された。
选项：掲載 / 掲栽 / 計裁 / 啓載
答案：掲載
```

## 正确答案来源

正确答案必须来自本地 CSV，不能让模型决定：

- `vocab_reading.answer` 必须对应 `kana`
- `vocab_kanji.answer` 必须对应 `kanji`

模型只负责：

- 写自然的日语句子
- 设计干扰项
- 写中文解析

本地程序负责校验：

- 目标词是否来自对应级别的 vocabulary CSV
- 正确答案是否唯一
- 选项是否为 4 个
- 选项是否重复
- `answer` 是否在合法范围内
- 题目是否已经生成过

## 状态文件

不建议直接修改 `resources/vocabulary/n2.csv`。它是上游资源文件，应该保持干净。

建议新增状态文件：

```text
data/generation-state/n2-vocabulary.json
```

推荐用 `jmdict_seq` 做 key：

```json
{
  "1234560": {
    "kana": "けいさい",
    "kanji": "掲載",
    "level": "N2",
    "vocab_reading": true,
    "vocab_kanji": true
  }
}
```

这样可以：

- 断点续跑
- 避免重复生成
- 分别追踪读音题和表记题
- 统计覆盖率

不是每个词都适合两个题型，例如：

- 没有汉字写法的词不适合 `vocab_kanji`
- 过于简单或多音歧义严重的词需要跳过或人工确认

## 语法题生成

适用题型：

- `grammar_fill`：⑥ 文の文法
- `grammar_order`：⑦ 文の組み立て
- `grammar_passage`：⑧ 文章の文法

主数据源：

```text
resources/grammar/n2.json
```

该文件是 N2 语法点资源表，包含：

- `id`
- `pattern`
- `level`
- `meaning_en`
- `meaning_detailed`
- `formation`
- `formation_notes`
- `formality`
- `related`
- `examples`

生成逻辑：

```text
选择一个尚未生成的 grammar point
-> 根据 pattern 和 formation 生成题目
-> 使用 related 或相近语法设计干扰项
-> 本地校验 JSON 结构
-> 审核通过后标记该语法点已生成
```

示例：

```text
语法点：～にあたって

题目：卒業（　）、先生に感謝の気持ちを伝えた。
选项：
1. にあたって
2. にかけて
3. によって
4. に反して
```

## 语法状态文件

建议新增：

```text
data/generation-state/n2-grammar.json
```

结构示例：

```json
{
  "ni-atatte": {
    "pattern": "～にあたって",
    "level": "N2",
    "grammar_fill": true,
    "grammar_order": false,
    "grammar_passage": false
  }
}
```

这样可以按语法点追踪不同题型覆盖情况。

## 注意事项

`resources/grammar/n2.json` 来自公开数据集，不是 JLPT 官方权威语法表，也不是 native speaker 最终审定版。它适合用作候选考点和生成约束，但正式题库仍需要：

- 本地结构校验
- 模型审核
- 抽样人工检查
- 对明显错误进行黑名单或修正

## 推荐优先级

第一阶段先做：

```text
vocab_reading
vocab_kanji
grammar_fill
```

原因：

- 数据源明确
- 正确答案容易本地校验
- 成本低
- 适合快速扩大题库覆盖率

第二阶段再做：

```text
grammar_order
grammar_passage
reading_short
reading_medium
reading_long
reading_search
```

这些题型更依赖文章自然度、逻辑一致性和人工审核，不能只靠简单资源表批量生成。
