@echo off
REM Windows 上打包 .exe（前提：pip install pyinstaller python-docx pypdf reportlab）
chcp 65001 >nul

if not exist src\cli.py (
  echo [错误] 请在项目根目录运行
  pause
  exit /b 1
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller ^
  --onefile ^
  --name swp ^
  --add-data "sample;sample" ^
  --hidden-import docx ^
  --hidden-import pypdf ^
  --hidden-import reportlab ^
  --hidden-import reportlab.pdfbase.cidfonts ^
  --hidden-import reportlab.pdfbase._fontdata ^
  --collect-all docx ^
  --collect-all reportlab ^
  src\cli.py

if exist dist\swp.exe (
  echo.
  echo [完成] dist\swp.exe
) else (
  echo [失败] 打包未生成 dist\swp.exe
)
pause
