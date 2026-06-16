@echo off
REM Windows 上打包 .exe（v0.2.0 — 含 GUI）
REM 前提：pip install pyinstaller python-docx pypdf reportlab openpyxl
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
  --windowed ^
  --name swp ^
  --add-data "sample;sample" ^
  --hidden-import core ^
  --hidden-import cli ^
  --hidden-import gui ^
  --hidden-import batch ^
  --hidden-import excel_handler ^
  --hidden-import file_handlers ^
  --hidden-import docx ^
  --hidden-import pypdf ^
  --hidden-import reportlab ^
  --hidden-import reportlab.pdfbase.cidfonts ^
  --hidden-import reportlab.pdfbase._fontdata ^
  --collect-all docx ^
  --collect-all reportlab ^
  --collect-all openpyxl ^
  --collect-all tkinter ^
  src\cli.py

if exist dist\swp.exe (
  echo.
  echo [完成] dist\swp.exe
  echo 双击 swp.exe 启动 GUI；命令行用 swp.exe --cli ...
) else (
  echo [失败] 打包未生成 dist\swp.exe
)
pause
