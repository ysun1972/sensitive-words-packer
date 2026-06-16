#!/bin/bash
# 一键构建 - macOS/Linux 上仅生成源码包，Windows 上才能生成 .exe
# (PyInstaller 跨平台需 Wine 或 GitHub Actions)
set -e
cd "$(dirname "$0")/.."

echo "=== 安装依赖 ==="
python3 -m pip install -r requirements.txt

echo ""
echo "=== 运行测试 ==="
PYTHONPATH=src python3 -m pytest tests/ -v 2>&1 || PYTHONPATH=src python3 tests/test_core.py

echo ""
echo "=== 处理 sample（演示）==="
python3 src/cli.py \
  -i sample/input \
  -o sample/output \
  --words sample/config/words.txt \
  --rules sample/config/rules.json \
  --mode exact,fuzzy,rule \
  --wildcard "***"

echo ""
echo "✓ 完成。查看 sample/output/ 获取脱敏结果"
