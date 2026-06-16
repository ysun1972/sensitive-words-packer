# sensitive-words-packer (v0.2.2)

> **本版本仅供 IDE / 命令行环境使用，不打包 .exe**。
> 适合在开发环境（VSCode / PyCharm / macOS / Linux）中直接 `python` 跑，方便调试。

一个轻量的本地敏感词脱敏工具：用户输入敏感词列表（或自定义规则），对指定目录下的文本文件进行脱敏处理，输出到指定目录。

## v0.2.2 新增特性

相比 v0.2.1：
- **🚀 启动时自动依赖检查 + 安装**：GUI 启动时检查 `python-docx / pypdf / reportlab / openpyxl`，缺哪个自动 `pip install`（默认清华源）
- **📝 GUI 内置敏感词编辑器**：直接编辑保存 `.txt`，支持加载/新建/插入示例
- **🔧 GUI 内置规则编辑器**：表格化编辑 `rules.json`，支持添加/删除/上移/下移/双击编辑
- **📊 GUI 内置 Excel 词表编辑器**：表格化编辑 `.xlsx`，支持添加行/列/重命名/删除
- **5 个 tab**：单次脱敏 / 批量任务 / 敏感词编辑 / 规则编辑 / Excel 编辑

## 核心特性

- **两种脱敏模式**：
  1. **敏感词模式** —— 用户输入敏感词列表，支持「精确匹配」/「模糊匹配」两种策略
  2. **规则模式** —— 用户输入正则表达式规则（如手机号、邮箱、身份证）
- **多格式支持**：`.txt` / `.md`（直接读写）；`.docx`（python-docx 保留段落+表格）；`.pdf`（pypdf 读取 + reportlab 重写 PDF + 同时输出同名 .docx 双产物）
- **多格式输入源**：`.txt` 词表 + `.xlsx` Excel 词表 + `.json` 规则
- **批量任务**：JSON 任务清单一次跑多组脱敏
- **GUI 模式**（tkinter，零依赖）—— 命令行启动 `python src/gui.py`
- **可配置通配符**：默认 `***`，可改为 `[已脱敏]` / `<REMOVED>` 等

## 目录结构

```
sensitive-words-packer/
├── src/
│   ├── core.py             # 脱敏核心逻辑
│   ├── cli.py              # 命令行入口（dispatcher：无 TTY → GUI）
│   ├── gui.py              # tkinter GUI（v0.2.0+）
│   ├── file_handlers.py    # 多格式文件读写
│   ├── excel_handler.py    # .xlsx 词表读取（v0.2.0+）
│   └── batch.py            # 批量任务执行器（v0.2.0+）
├── sample/
│   ├── input/              # 演示输入文件
│   └── config/             # 演示配置（words.txt / rules.json / words_demo.xlsx / batch_example.json）
├── scripts/
│   ├── gen_sample_pdf.py   # 生成演示 PDF
│   ├── gen_sample_excel.py # 生成演示 Excel 词表
│   └── demo.sh             # 一键跑演示
├── docs/USER_GUIDE.md
├── requirements.txt
├── tests/                  # 单元测试（21 个）
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd /Users/apple/sensitive-words-packer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

核心依赖：python-docx + pypdf + reportlab + openpyxl
GUI 用 tkinter（Python 标准库，无需安装）

### 2. 三种使用方式

#### 方式 A：GUI（推荐）

```bash
python src/gui.py
```

弹出 tkinter 窗口：
- 选择输入路径（文件或目录）
- 选择输出目录
- 选择敏感词列表（.txt）/ Excel 词表（.xlsx）/ 规则文件（.json）
- 选择脱敏模式（精确/模糊/正则）
- 自定义通配符
- 点击「开始脱敏」

#### 方式 B：CLI（命令行 / 脚本）

```bash
# 单文件
python src/cli.py -i input.txt -o output/ \
  --words sample/config/words.txt --mode exact --wildcard "***"

# 整个目录
python src/cli.py -i ./input -o ./output \
  --words sample/config/words.txt --mode fuzzy --wildcard "***" \
  --rules sample/config/rules.json

# Excel 词表
python src/cli.py -i ./input -o ./output \
  --excel sample/config/words_demo.xlsx --excel-column "敏感词" \
  --mode exact,rule --wildcard "***"

# 批量任务
python src/cli.py --batch sample/config/batch_example.json
```

> 注：v0.2.0 引入的 `--cli` 标志在 v0.2.1 已不再需要（dispatcher 已取消 TTY 判断逻辑，命令行模式是默认行为）。GUI 仅在显式 `python src/gui.py` 启动。

#### 方式 C：IDE 调试

- **VSCode / PyCharm**：直接打开 `src/cli.py` 或 `src/gui.py`，设断点，F5 运行
- **Jupyter**：`from core import SensitiveWordRedactor; r = SensitiveWordRedactor(words=[...])`

### 3. 运行测试

```bash
python tests/test_core.py     # 8 个核心测试
python tests/test_excel.py    # 7 个 Excel 测试
python tests/test_batch.py    # 6 个批量任务测试
# 合计 21 个测试
```

### 4. 一键跑演示

```bash
bash scripts/demo.sh
# 等价于：
# python src/cli.py -i sample/input -o sample/output \
#   --words sample/config/words.txt \
#   --rules sample/config/rules.json \
#   --mode exact,rule --wildcard "***"
```

## 配置示例

**敏感词列表**（`sample/config/words.txt`）：

```
张三
13800138000
example.com
```

**Excel 词表**（`sample/config/words_demo.xlsx`）：

| 部门 | 类型 | 敏感词 |
| --- | --- | --- |
| 市场部 | 客户 | AcmeCorp |
| 财务部 | 账号 | 6225880137460000 |
| 研发部 | 代号 | ProjectPhoenix |

读取方式：
- `python src/cli.py --excel words.xlsx` → 取第 1 列
- `--excel-column "敏感词"` → 按 header 列名
- `--excel-column "C"` → 按列字母
- `--excel-column 2` → 按列号（0-based）

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

**批量配置**（`sample/config/batch_example.json`）：

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

## 版本演进

| 版本 | 特性 | 备注 |
| --- | --- | --- |
| v0.1.0 | CLI 基础 + .txt/.md/.docx/.pdf 多格式 | 双击 .exe 闪退 |
| v0.2.0 | + GUI（tkinter）+ Excel 词表 + 批量任务 | 打包 .exe 复杂 |
| v0.2.1 | IDE / 命令行专用，移除打包相关 | 删除 __init__.py |
| **v0.2.2** | **+ 启动自动装依赖 + 3 个内置编辑器** | **当前版本** |

v0.2.2 主要新增：
- `src/deps.py`：`check_deps()` + `install_deps()`，缺啥装啥
- `src/gui.py`：3 个新 tab（敏感词/规则/Excel 编辑器），用 `EditableTreeview` 实现双击编辑
- `DepsInstallDialog` Toplevel 弹窗，pip 实时输出到滚动文本框
- 38 个单元测试（新增 17 个：7 deps + 10 gui）

## 常见问题

### Q: 想双击 .exe 跑怎么办？
A: v0.2.1 不再支持打包。**推荐**：用 IDE 调试，或写一个 shell 脚本一键跑。

### Q: 打包 .exe 怎么搞？
A: 参考 v0.2.0 的 commit 089e06a（含完整 PyInstaller + NSIS 配置），但自行处理：
- 不要保留 `src/__init__.py`（v0.2.1 已删）
- 改用 `--onedir` 模式比 `--onefile` 更稳
- 在 Windows 真机验证 stdout=None 场景

### Q: 中文边界匹配不上？
A: 中文无空格分词，建议用 `(?<!\d)...(?!\d)` 替代 `\b`。

### Q: Excel 列识别错误？
A: 确认首行是表头（字符串），数据从第 2 行开始。列名区分大小写。

## 详细文档

- [用户手册](docs/USER_GUIDE.md)

## 许可证

仅供合法合规的数据脱敏用途使用。请勿用于规避内容审核、传播违法信息等场景。
