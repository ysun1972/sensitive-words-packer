#!/bin/bash
# PyInstaller 打包脚本（v0.2.0 — 含 GUI）
# macOS/Linux 上构建 Windows .exe 需要 Wine 或在 Windows 上运行
# 建议在 Windows 上执行本脚本

set -e

APP_NAME="swp"  # Sensitive Words Packer 缩写
ENTRY="src/cli.py"

# 1) 清理
rm -rf build dist
echo "✓ 清理 build/ dist/"

# 2) PyInstaller 打包
# --onefile: 单文件 .exe
# --windowed: Windows 下不弹 console（GUI 模式）
# --name: 输出文件名
# --add-data: 附带 sample 目录（用于演示）
# --collect-all: 完整收集子模块/资源
pyinstaller \
  --onefile \
  --windowed \
  --name "$APP_NAME" \
  --add-data "sample:sample" \
  --hidden-import core \
  --hidden-import cli \
  --hidden-import gui \
  --hidden-import batch \
  --hidden-import excel_handler \
  --hidden-import file_handlers \
  --hidden-import docx \
  --hidden-import pypdf \
  --hidden-import reportlab \
  --hidden-import reportlab.pdfbase.cidfonts \
  --hidden-import reportlab.pdfbase._fontdata \
  --collect-all docx \
  --collect-all reportlab \
  --collect-all openpyxl \
  --collect-all tkinter \
  "$ENTRY"

# 3) 移动到 dist
mkdir -p dist
mv "$APP_NAME.exe" dist/ 2>/dev/null || mv "$APP_NAME" dist/ 2>/dev/null
echo ""
echo "✓ 打包完成: dist/$APP_NAME(.exe)"
echo ""
echo "macOS/Linux 用户：需要 Wine 跑 .exe，或直接在 Windows 上执行本脚本"
echo "Windows 用户：双击 dist/$APP_NAME.exe 启动 GUI"
