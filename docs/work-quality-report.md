# OpenJLPT 工作质量报告

更新时间：2026-05-04

## 当前状态

- 本地仓库分支：`master`
- 主要运行目录将迁移到：`192.168.3.62:/home/tetsuya/Development/openjlpt`
- `.env` 已复制到 62 服务器，但不会提交到 Git。
- `data/generation-state/n2-vocabulary.json` 已从 62 修复后的状态同步回本地。

## 已完成

- `output/template.html` 已改为使用 `kuromoji` 运行时生成 furigana。
- `.target-word` 内的作答目标会被保护，不显示注音。
- `generate_bank.py` 已支持：
  - 模型健康检查，自动筛掉不可用 provider。
  - Gemini native REST 调用。
  - 词汇题 `vocab_reading` / `vocab_kanji` 审核通过后立即写入 `data/n2/*.json`。
  - 词汇题按 `target` 去重，避免重复入库。
  - 每次成功/失败后立即保存 `data/generation-state/n2-vocabulary.json`。
  - 启动时自动修复旧状态里 `generated` 但 JSON 中缺题的记录。
- 62 服务器上旧运行残留状态已修复：362 个缺题的 `generated` 记录已重置为 `pending`。

## 当前数据质量

- 62 服务器修复后状态：
  - `vocab_reading`: `pending` 1429, `failed` 65, `generated` 1
  - `vocab_kanji`: `pending` 1495
- `data/n2/vocab_reading.json` 当前仍只有 9 题，且历史数据中 `謙虚` 有重复 target。
- 新脚本会阻止未来重复 target 继续入库，但不会自动删除历史重复题。

## 已知风险

- 旧版本长跑进程已经生成但未落盘的题无法恢复，因为题目内容只存在于旧 Python 进程内存中。
- `config.json` 中部分 provider 当前不可用：
  - `ark` 返回 HTTP 404。
  - `gemini` 在 62 上返回模型 404。
  - `nvidia` 偶发 timeout。
- 词汇题生成依赖至少两个可用模型：一个生成，一个审核。
- `save_to_json` 是读 JSON 后覆盖写，单进程运行安全；不要同时开多个 `generate_bank.py` 写同一题型。

## 迁移后建议命令

```sh
cd ~/Development/openjlpt
git status
python3 -m py_compile generate_bank.py
python3 generate_bank.py --only vocab_reading vocab_kanji
```

## 后续建议

- 先修 `config.json` 中不可用 provider，保证至少 3 个稳定模型可用。
- 清理 `data/n2/vocab_reading.json` 中历史重复 target。
- 给 `generate_bank.py` 增加 `--repair-state` 命令，避免用假 `--only` 参数触发修复。
- 将运行日志输出到 `logs/` 或使用 `tee` 保存，方便追踪每轮失败原因。
