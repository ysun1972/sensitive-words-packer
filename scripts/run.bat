@echo off
REM Windows 启动器 - 双击即可使用（需先 build_exe.bat 打包）
chcp 65001 >nul
title Sensitive Words Packer

echo ====================================
echo  敏感词脱敏工具 v0.1.0
echo ====================================
echo.

REM 检查 swp.exe 是否存在
if not exist "%~dp0dist\swp.exe" (
  echo [错误] 找不到 dist\swp.exe，请先运行 scripts\build_exe.bat 打包
  pause
  exit /b 1
)

REM 默认处理 sample/input/ → sample/output/
if "%1"=="" (
  "%~dp0dist\swp.exe" ^
    -i "%~dp0sample\input" ^
    -o "%~dp0sample\output" ^
    --words "%~dp0sample\config\words.txt" ^
    --rules "%~dp0sample\config\rules.json" ^
    --mode exact,fuzzy,rule ^
    --wildcard "***"
) else (
  "%~dp0dist\swp.exe" %*
)

pause
