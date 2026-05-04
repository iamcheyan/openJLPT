#!/bin/bash
# 修复 vocab_kanji 和 vocab_context 的模板题数据
# 用法: bash fix_vocab_data.sh
#
# 会自动循环运行直到所有 pending 词汇处理完毕:
#   1. 先跑 vocab_kanji (漢字の表記)
#   2. 完成后自动跑 vocab_context (文脈判断)
#   3. 每批 3 个词，崩溃自动重启

set -e
cd "$(dirname "$0")"

echo "=== 词汇题数据修复 ==="
echo "开始时间: $(date)"
echo ""

run_section() {
    local section_id="$1"
    local section_name="$2"
    local log_file="/tmp/vocab_${section_id}_gen.log"

    echo ">>> 开始生成: ${section_name} (${section_id})"
    echo ">>> 日志: ${log_file}"
    echo ""

    while true; do
        python3 generate_bank.py --only "$section_id" 2>&1 | tee -a "$log_file"
        rc=${PIPESTATUS[0]}

        if [ $rc -ne 0 ]; then
            echo "[WARN] 生成器异常退出 (code=$rc)，2 秒后重试..."
            sleep 2
            continue
        fi

        # 检查是否还有 pending
        pending=$(python3 -c "
import json
with open('data/generation-state/n2-vocabulary.json') as f:
    s = json.load(f)
print(sum(1 for v in s.values() if v.get('${section_id}') == 'pending'))
")

        if [ "$pending" -eq 0 ]; then
            echo "✓ ${section_name} 全部完成!"
            break
        fi

        echo "[INFO] ${section_name} 还剩 ${pending} 个 pending，继续..."
        sleep 1
    done
}

run_section "vocab_reading" "① 漢字の読み方"
run_section "vocab_kanji" "② 漢字の表記"
run_section "vocab_context" "③ 文脈判断"
run_section "vocab_synonym" "④ 言い換え類義"
run_section "vocab_usage" "⑤ 用法"

echo ""
echo "=== 全部完成! ==="
echo "结束时间: $(date)"
