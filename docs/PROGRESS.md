# OpenJLPT 项目进度

> 最后更新: 2026-05-03

## 项目概述

一个完全离线的 JLPT（日本语能力考试）模拟考试 App，架构为 **WebView + 静态 HTML/JS + 本地 JSON**，部署在 GitHub Pages 上。

## 当前阶段：N2 题库构建

### 已完成

1. **项目结构搭建**
   - GitHub 仓库 `iamcheyan/openJLPT` 已创建
   - `.gitignore` 正确过滤 `.env`（API密钥保护）
   - `.env` 包含3个API供应商的密钥

2. **资源文件** (`resources/`)
   - `vocabulary/n1-n5.csv` — 8,298 词汇（stephenmk/yomitan-jlpt-vocab）
   - `grammar/n1-n5.json` — 595 语法点（jkindrix/japanese-language-data）
   - `kanji/jlpt-kanji.json` — 2,136 汉字（AnchorI/jlpt-kanji-dictionary）

3. **API 供应商**（配置驱动，8个供应商）
   - 智谱AI: `glm-4-flash` — 稳定，审核模型首选
   - 火山ARK: `doubao-seed-2-0-pro`
   - 小米MiMo: `mimo-v2.5-pro`
   - Google Gemini: `gemini-1.5-flash`
   - Kimi (Moonshot): `kimi-latest`
   - NVIDIA NIM: `llama-3.1-nemotron-70b-instruct`
   - OpenRouter: `gpt-4o-mini` 等
   - 所有供应商通过 `config.json` 配置，不再硬编码

4. **N2 题库 JSON Schema** (`docs/json-schema.md`)
   - 12种题型的完整结构定义
   - 包含 `generated_by`、`reviewed_by`、`review_explanation` 字段
   - 每个题型有完整示例（含审核解析）

5. **出题程序** (`generate_bank.py` + `config.json`)
   - 配置驱动：`config.json` 定义所有供应商、模型、生成/审核流水线
   - 双模型审核流程：生成→校验→审核→入库
   - 支持 `--only` 参数单独补跑某题型
   - 自动跳过密钥缺失或失效的供应商
   - 自动校验：选项去重、答案范围、题型特定规则
   - 嵌套结构校验（grammar_order的fragments、reading的questions数组等）

6. **N2 模拟考试页面** (`index.html`)
   - 从 12 个 JSON 题库实时加载组卷
   - 支持 105 分钟倒计时、分区答题、解答栏跳转
   - 自动判分、分部统计、错题复习、localStorage 进度保存
   - 响应式设计，适配手机和桌面

7. **N2 题库当前状态** (`data/n2/`)

| 题型 | 文件 | 当前题数 | 试卷需要 |
|------|------|---------|---------|
| ① 漢字の読み方 | vocab_reading.json | 4 | 5 |
| ② 漢字の表記 | vocab_kanji.json | 4 | 5 |
| ③ 文脈規定 | vocab_context.json | 6 | 7 |
| ④ 言い換え・類義 | vocab_synonym.json | 6 | 5 |
| ⑤ 用法 | vocab_usage.json | 6 | 5 |
| ⑥ 文の文法 | grammar_fill.json | 6 | 12 |
| ⑦ 文の組み立て | grammar_order.json | 2 | 5 |
| ⑧ 文章の文法 | grammar_passage.json | 2 | 5 |
| ⑨ 短文読解 | reading_short.json | 5 | 5 |
| ⑩ 中文読解 | reading_medium.json | 2 | 8 |
| ⑪ 長文読解 | reading_long.json | 1 | 4 |
| ⑫ 情報検索 | reading_search.json | 1 | 2 |
| **合计** | | **45** | **~68** |

### 已知问题

- ARK API 今天出现 404 错误，可能是临时问题
- 部分题型题量不足一张完整试卷，需要继续补充
- MiMo 偶尔生成重复选项（校验器已能拦截）
- grammar_order（句子排序）题型3个模型都容易出格式错误（fragments数量不对）

### 题库中每道题的结构

```json
{
  "id": "n2-vocab_reading-001",
  "level": "N2",
  "question_type": "vocab_reading",
  "sentence": "...",
  "options": ["...", "...", "...", "..."],
  "answer": 0,
  "explanation": "...",
  "generated_by": "ark:Doubao-Seed-2.0-Pro",
  "reviewed_by": "zhipu",
  "review_explanation": "详细的中文解析...",
  "verified": true,
  "created_at": "2026-05-03T21:00:00"
}
```

### 参考文档

- `docs/json-schema.md` — JSON 结构定义（12种题型）
- `docs/jlpt-n2-official-sample-questions.md` — 官方真题参考
- `docs/jlpt-official-pdfs/` — 9份官方N2 PDF
- `试卷结构.md` — N2试卷结构说明

## 下一步计划

1. **补全题库** — 继续运行 `generate_bank.py` 补充题量不足的题型
2. **拼卷 HTML** — ✅ 已完成 (`index.html`)
3. **交互功能** — ✅ 已完成（做题、105分钟计时、判分、解析、localStorage记录）
4. **后续扩展** — N3-N5 题库

## 关键文件清单

```
openjlpt/
├── .env                    # API密钥（不提交）
├── .env.example            # API密钥模板（可提交）
├── .gitignore              # 正确过滤.env
├── config.json             # 模型供应商与流水线配置
├── generate_bank.py        # 题库生成程序（配置驱动）
├── generate_exam.py        # 直接出卷程序（v2，备用）
├── index.html              # N2 模拟考试页面（从 JSON 题库实时组卷）
├── test_api.py             # API连通性测试
├── PROGRESS.md             # 本文件
├── 试卷结构.md              # N2试卷结构
├── data/n2/*.json          # N2题库（12个JSON文件）
├── docs/
│   ├── json-schema.md      # JSON结构定义
│   ├── jlpt-n2-official-sample-questions.md
│   └── jlpt-official-pdfs/
├── resources/              # 词汇/语法/汉字资源
└── output/                 # 之前生成的HTML试卷（v1）
```
