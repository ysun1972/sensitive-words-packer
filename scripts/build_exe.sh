#!/bin/bash
# PyInstaller 打包脚本 - macOS/Linux 上构建 Windows .exe 需要 Wine 或在 Windows 上运行
# 建议在 Windows 上执行本脚本（直接 python + PyInstaller）

set -e

APP_NAME="swp"  # Sensitive Words Packer 缩写
ENTRY="src/cli.py"
ICON=""  # 可选: assets/icon.ico

# 1) 清理
rm -rf build dist
echo "✓ 清理 build/ dist/"

# 2) PyInstaller 打包
# --onefile: 单文件 .exe
# --name: 输出文件名
# --add-data: 附带 sample 目录（用于演示）
# --collect-all reportlab: 包含 reportlab 全部字体和 cid 数据
pyinstaller \
  --onefile \
  --name "$APP_NAME" \
  --add-data "sample:sample" \
  --hidden-import docx \
  --hidden-import pypdf \
  --hidden-import reportlab \
  --hidden-import reportlab.pdfbase.cidfonts \
  --hidden-import reportlab.pdfbase._fontdata \
  --collect-all docx \
  --collect-all reportlab \
  $ICON \
  "$ENTRY"

# 3) 移动到 dist
mkdir -p dist
mv "$APP_NAME.exe" dist/ 2>/dev/null || mv "$APP_NAME" dist/ 2>/dev/null
echo ""
echo "✓ 打包完成: dist/$APP_NAME(.exe)"
echo ""
echo "macOS/Linux 用户：需要 Wine 跑 .exe，或直接在 Windows 上执行本脚本"
echo "Windows 用户：直接运行 dist/$APP_NAME.exe 即可"
