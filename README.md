# sensitive-words-packer

一个轻量的本地敏感词脱敏工具：用户输入敏感词列表（或自定义规则），对指定目录下的文本文件进行脱敏处理，输出到指定目录；可打包为 Windows 单文件 `.exe` 与 NSIS 安装包。

## 核心特性

- **双脱敏模式**：
  1. **敏感词模式** —— 用户输入敏感词列表，支持「精确匹配」/「模糊匹配」两种策略
  2. **规则模式** —— 用户输入正则表达式规则（如手机号、邮箱、身份证）
- **多格式支持**：`.txt` / `.md`（直接读写）；`.docx`（python-docx 保留段落+表格）；`.pdf`（pypdf 读取 + reportlab 重写 PDF + 同时输出同名 .docx 双产物）
- **同格式输出**：输入是 docx 输出 docx；输入是 PDF 同时输出 `name.pdf` + `name.docx`（双产物）
- **可配置通配符**：默认 `***`，可改为 `[已脱敏]` / `<REMOVED>` 等
- **CLI 优先**（带 `.bat` 启动器）
- **Windows 安装包**：PyInstaller + NSIS

## 目录结构

```
sensitive-words-packer/
├── src/
│   ├── __init__.py
│   ├── core.py             # 脱敏核心逻辑
│   ├── cli.py              # 命令行入口
│   ├── gui.py              # (可选) 简易 Tkinter GUI
│   └── file_handlers.py    # 多格式文件读写
├── sample/
│   ├── input/              # 演示输入文件
│   └── config/             # 演示配置（敏感词.txt + 规则.json）
├── scripts/
│   ├── build_exe.sh        # PyInstaller 打包 .exe
│   ├── build_installer.sh  # NSIS 打安装包
│   └── run.bat             # Windows 启动器
├── build/                  # PyInstaller 中间产物
├── dist/                   # 最终 .exe / .msi 输出
├── tests/                  # 单元测试
├── docs/
│   └── USER_GUIDE.md
├── requirements.txt
├── setup.py                # PyInstaller 配置
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd /Users/apple/sensitive-words-packer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 核心依赖：python-docx + pypdf + reportlab + pyinstaller
```

依赖说明：
- **python-docx**：处理 `.docx`
- **pypdf**：提取 `.pdf` 文本
- **reportlab**：重建 `.pdf`（内置 STSong-Light 中文字体，无需额外字体文件）
- **pyinstaller**：打包 `.exe`

### 2. 准备配置

**敏感词列表**（`sample/config/words.txt`，每行一个）：

```
张三
13800138000
example.com
```

**规则文件**（`sample/config/rules.json`）：

```json
[
  {"name": "手机号", "pattern": "\\b1[3-9]\\d{9}\\b", "replacement": "***"},
  {"name": "邮箱", "pattern": "\\b[\\w.]+@[\\w.]+\\b", "replacement": "***"}
]
```

### 3. 运行脱敏

```bash
# 单个文件
python src/cli.py -i input.txt -o output.txt \
  --words sample/config/words.txt --mode exact --wildcard "***"

# 整个目录
python src/cli.py -i ./input -o ./output \
  --words sample/config/words.txt --mode fuzzy --wildcard "***" \
  --rules sample/config/rules.json
```

### 4. 打包为 Windows .exe

```bash
bash scripts/build_exe.sh       # 输出到 dist/swp.exe
bash scripts/build_installer.sh # 输出到 dist/SensitiveWordsPacker-Setup.exe
```

## 设计原则

- **本地优先**：所有处理在本地完成，文件不离开用户机器
- **合规优先**：默认仅做遮蔽（`***`），不提供「反检测/绕过平台审核」能力
- **可审计**：所有替换记录写入日志 `dist/run.log`，便于复核
- **可扩展**：新增文件格式只需在 `file_handlers.py` 加一个 handler

## CI/CD

- **CI 测试**：每次 push 自动跑 3 平台 × 3 Python 版本测试（`.github/workflows/ci-test.yml`）
- **Windows .exe 打包**：推 `v*` tag 自动触发 → 生成 .exe + 创建 GitHub Release（`.github/workflows/build-windows.yml`）
- **手动触发**：GitHub Actions → Run workflow → 可选发布 Release

## 详细文档

- [用户手册](docs/USER_GUIDE.md)
- [打包说明](docs/BUILD.md)

## 许可证

仅供合法合规的数据脱敏用途使用。请勿用于规避内容审核、传播违法信息等场景。
