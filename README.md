# sensitive-words-packer

一个轻量的本地敏感词脱敏工具：用户输入敏感词列表（或自定义规则），对指定目录下的文本文件进行脱敏处理，输出到指定目录；可打包为 Windows 单文件 `.exe` 与 NSIS 安装包。

## v0.2.0 新增特性

相比 v0.1.0：
- **GUI 界面**（tkinter 零依赖）：解决 v0.1.0 双击闪退问题，双击 `swp.exe` 直接打开可视化窗口
- **Excel 词表支持**（.xlsx）：支持按列名/列字母/列号读取
- **批量任务配置**（JSON）：一次跑多组「输入 → 输出 + 配置」任务
- **v0.1.0 闪退修复**：GUI 启动条件为「无 TTY 时」（双击 .exe 场景），保留 `--cli` 走命令行

## 核心特性

- **双脱敏模式**：
  1. **敏感词模式** —— 用户输入敏感词列表，支持「精确匹配」/「模糊匹配」两种策略
  2. **规则模式** —— 用户输入正则表达式规则（如手机号、邮箱、身份证）
- **多格式支持**：`.txt` / `.md`（直接读写）；`.docx`（python-docx 保留段落+表格）；`.pdf`（pypdf 读取 + reportlab 重写 PDF + 同时输出同名 .docx 双产物）
- **多格式输入源**：`.txt` 词表 + `.xlsx` Excel 词表（v0.2.0）+ `.json` 规则
- **批量任务**：JSON 任务清单一次跑多组脱敏（v0.2.0）
- **同格式输出**：输入是 docx 输出 docx；输入是 PDF 同时输出 `name.pdf` + `name.docx`（双产物）
- **可配置通配符**：默认 `***`，可改为 `[已脱敏]` / `<REMOVED>` 等
- **GUI 优先**（双击 .exe 启动窗口）+ CLI 兼容（`--cli` 标志）
- **Windows 安装包**：PyInstaller + NSIS

## 目录结构

```
sensitive-words-packer/
├── src/
│   ├── __init__.py
│   ├── core.py             # 脱敏核心逻辑
│   ├── cli.py              # 入口（dispatcher：CLI 或 GUI）
│   ├── gui.py              # tkinter GUI
│   ├── file_handlers.py    # 多格式文件读写
│   ├── excel_handler.py    # .xlsx 词表读取（v0.2.0）
│   └── batch.py            # 批量任务执行器（v0.2.0）
├── sample/
│   ├── input/              # 演示输入文件
│   └── config/             # 演示配置（words.txt / rules.json / words_demo.xlsx / batch_example.json）
├── scripts/
│   ├── build_exe.sh        # PyInstaller 打包 .exe
│   ├── build_exe.bat       # Windows 打包脚本
│   ├── installer.nsi       # NSIS 安装包脚本
│   ├── gen_sample_pdf.py
│   └── gen_sample_excel.py # 生成演示 Excel 词表（v0.2.0）
├── build/                  # PyInstaller 中间产物
├── dist/                   # 最终 .exe 输出
├── tests/                  # 单元测试
│   ├── test_core.py
│   ├── test_excel.py       # v0.2.0
│   └── test_batch.py       # v0.2.0
├── docs/
│   ├── USER_GUIDE.md
│   └── BUILD.md
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd /Users/apple/sensitive-words-packer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 核心依赖：python-docx + pypdf + reportlab + openpyxl + pyinstaller
# GUI 用 tkinter（标准库自动包含）
```

### 2. 三种使用方式

#### 方式 A：GUI（v0.2.0 推荐 / 解决 v0.1.0 闪退）

直接双击 `swp.exe` 启动 GUI 窗口：
- 选择输入路径（文件或目录）
- 选择输出目录
- 选择敏感词列表（.txt）/ Excel 词表（.xlsx）/ 规则文件（.json）
- 选择脱敏模式（精确/模糊/正则）
- 自定义通配符
- 点击「开始脱敏」

#### 方式 B：CLI（命令行 / 脚本批处理）

```bash
# 单个文件
python src/cli.py --cli -i input.txt -o output/ \
  --words sample/config/words.txt --mode exact --wildcard "***"

# 整个目录
python src/cli.py --cli -i ./input -o ./output \
  --words sample/config/words.txt --mode fuzzy --wildcard "***" \
  --rules sample/config/rules.json

# Excel 词表（v0.2.0）
python src/cli.py --cli -i ./input -o ./output \
  --excel sample/config/words_demo.xlsx --excel-column "敏感词" \
  --mode exact,rule --wildcard "***"

# 批量任务（v0.2.0）
python src/cli.py --cli --batch sample/config/batch_example.json
```

#### 方式 C：打包成 .exe（Windows）

```bash
# Windows 上
scripts\build_exe.bat
# 产物：dist\swp.exe — 双击启动 GUI
```

## 配置示例

**敏感词列表**（`sample/config/words.txt`，每行一个）：

```
张三
13800138000
example.com
```

**Excel 词表**（`sample/config/words_demo.xlsx`，v0.2.0）：

| 部门 | 类型 | 敏感词 |
| --- | --- | --- |
| 市场部 | 客户 | AcmeCorp |
| 财务部 | 账号 | 6225880137460000 |
| 研发部 | 代号 | ProjectPhoenix |

**规则文件**（`sample/config/rules.json`）：

```json
{
  "rules": [
    {"name": "中国大陆手机号", "pattern": "(?<!\\d)1[3-9]\\d{9}(?!\\d)", "replacement": "[手机号]"},
    {"name": "电子邮箱", "pattern": "[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}", "replacement": "[邮箱]"},
    {"name": "18 位身份证号", "pattern": "(?<!\\d)\\d{17}[\\dXx](?!\\d)", "replacement": "[身份证]"}
  ]
}
```

**批量配置**（`sample/config/batch_example.json`，v0.2.0）：

```json
{
  "tasks": [
    {
      "name": "市场部 Q1 报告",
      "input": "./sample/input",
      "output": "./sample/output_marketing",
      "words": "./sample/config/words.txt",
      "rules": "./sample/config/rules.json",
      "mode": "exact,rule",
      "wildcard": "***",
      "log": "marketing.log"
    },
    {
      "name": "财务部合同",
      "input": "./sample/input",
      "output": "./sample/output_finance",
      "excel": "./sample/config/words_demo.xlsx",
      "excel_sheet": "敏感词",
      "excel_column": "敏感词",
      "mode": "exact,rule",
      "wildcard": "[REDACTED]"
    }
  ]
}
```

## 设计原则

- **本地优先**：所有处理在本地完成，文件不离开用户机器
- **合规优先**：默认仅做遮蔽（`***`），不提供「反检测/绕过平台审核」能力
- **可审计**：所有替换记录写入日志 `run.log`，便于复核
- **可扩展**：新增文件格式只需在 `file_handlers.py` 加一个 handler

## v0.1.0 → v0.2.0 闪退问题修复记录

**根因**：`swp.exe` 是 PyInstaller `--onefile` 打包 `src/cli.py`（纯 argparse CLI）。双击 .exe 时：
- 进程在 0.1s 内执行完 `main()` 立即退出
- Windows 没机会显示 console 窗口
- 用户看到「黑窗一闪就消失」误以为崩溃

**修复**（v0.2.0）：
1. `src/cli.py` 改为 dispatcher：检测 stdout/stderr 是否为 TTY
2. 非 TTY（双击 .exe）→ 启动 `src/gui.py`（tkinter 窗口）
3. 有 `--cli` 标志或有参数 → 走命令行模式
4. 打包时加 `--windowed`（Windows 下不弹 console）

## CI/CD

- **CI 测试**：每次 push 自动跑 3 平台 × 3 Python 版本测试（`.github/workflows/ci-test.yml`）
- **Windows .exe 打包**：推 `v*` tag 自动触发 → 生成 .exe + 创建 GitHub Release（`.github/workflows/build-windows.yml`）
- **手动触发**：GitHub Actions → Run workflow → 可选发布 Release

## 详细文档

- [用户手册](docs/USER_GUIDE.md)
- [打包说明](docs/BUILD.md)

## 许可证

仅供合法合规的数据脱敏用途使用。请勿用于规避内容审核、传播违法信息等场景。
