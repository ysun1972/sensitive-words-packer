#!/bin/bash
# 一键跑演示
# 处理 sample/input → sample/output，使用 sample/config 配置
set -e
cd "$(dirname "$0")/.."
python3 src/cli.py \
  -i sample/input \
  -o sample/output \
  --words sample/config/words.txt \
  --rules sample/config/rules.json \
  --mode exact,rule \
  --wildcard "***"
