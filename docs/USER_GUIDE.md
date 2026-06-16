# 用户手册 (v0.2.1 - IDE 专用)

## 快速上手

### 1. 安装依赖

```bash
cd /Users/apple/sensitive-words-packer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. GUI 模式

```bash
python src/gui.py
```

弹出 tkinter 窗口，操作流程参见 [README.md](../README.md)。

### 3. CLI 模式

#### 3.1 单文件/目录处理

```bash
# 单个文件
python src/cli.py -i input.txt -o output/ \
  --words words.txt --mode exact --wildcard "***"

# 整个目录
python src/cli.py -i ./input -o ./output \
  --words words.txt --rules rules.json --mode exact,fuzzy,rule
```

#### 3.2 Excel 词表

```bash
# 按列名
python src/cli.py -i ./input -o ./output \
  --excel words.xlsx --excel-column "敏感词"

# 按列字母
python src/cli.py -i ./input -o ./output \
  --excel words.xlsx --excel-column "C"

# 按列号（从 0 开始）
python src/cli.py -i ./input -o ./output \
  --excel words.xlsx --excel-column 2

# 指定 Sheet
python src/cli.py -i ./input -o ./output \
  --excel words.xlsx --excel-sheet "财务词表" --excel-column "账号"
```

#### 3.3 批量任务

```bash
python src/cli.py --batch tasks.json
```

JSON 格式：
```json
{
  "tasks": [
    {
      "name": "市场部",
      "input": "./input/marketing",
      "output": "./output/marketing",
      "words": "./config/words_marketing.txt",
      "rules": "./config/rules_common.json",
      "mode": "exact,rule",
      "wildcard": "***",
      "log": "marketing.log"
    },
    {
      "name": "财务部（Excel 词表）",
      "input": "./input/finance",
      "output": "./output/finance",
      "excel": "./config/words_finance.xlsx",
      "excel_sheet": "敏感词",
      "excel_column": "敏感词",
      "rules": "./config/rules_finance.json",
      "mode": "exact,fuzzy,rule",
      "wildcard": "[REDACTED]"
    }
  ]
}
```

### 4. IDE 调试

- **VSCode**：打开 `src/cli.py` 或 `src/gui.py`，设断点，按 F5
- **PyCharm**：同上
- **Jupyter**：
  ```python
  import sys
  sys.path.insert(0, '/Users/apple/sensitive-words-packer/src')
  from core import SensitiveWordRedactor
  r = SensitiveWordRedactor(words=['张三'], rules=[])
  result = r.redact("客户张三和张三三", modes=['word-exact'])
  print(result.redacted_text)  # "客户***和***"
  ```

### 5. 运行测试

```bash
python tests/test_core.py     # 8 个核心测试
python tests/test_excel.py    # 7 个 Excel 测试
python tests/test_batch.py    # 6 个批量任务测试
# 合计 21 个测试
```

## 敏感词列表格式

### TXT 格式（每行一个）

```
# 这是注释
张三
李四
13800138000
admin@company.com
```

### Excel 格式

| 部门 | 类型 | 敏感词 |
| --- | --- | --- |
| 市场部 | 客户 | AcmeCorp |
| 财务部 | 账号 | 6225880137460000 |

读取规则：
- 默认取第 1 列
- 可用 `--excel-column "列名"` 指定（按 header）
- 可用 `--excel-column "C"` 按列字母
- 可用 `--excel-column 2` 按列号（从 0 开始）
- 自动跳过首行表头

## 规则文件格式

```json
{
  "rules": [
    {
      "name": "中国大陆手机号",
      "pattern": "(?<!\\d)1[3-9]\\d{9}(?!\\d)",
      "replacement": "[手机号]"
    }
  ]
}
```

**边界提示**：
- 纯 ASCII 词可用 `\b...\b` 词边界
- 中文场景下 `\b` 在中文字符与数字间不工作，建议使用 `(?<!\d)` / `(?!\d)`

## 脱敏模式说明

| 模式 | 适用 | 边界 |
| --- | --- | --- |
| 精确匹配 | 完整词组 | ASCII 用 `\b`；中文直接匹配 |
| 模糊匹配 | 同音/变体 | 中间允许 0-2 个字符 |
| 正则规则 | 通用模式 | 用户完全控制 |

## v0.1.0 / v0.2.0 历史问题

- v0.1.0 swp.exe 双击闪退（CLI 程序 0.1s 退出）
- v0.2.0 引入 GUI + 打包，但 PyInstaller `--windowed` 下 `sys.stdout=None` 引发崩溃
- v0.2.0 删除 `src/__init__.py` 后 `import core` 失败

**v0.2.1 干脆只做 IDE 模式**，避免所有打包相关问题。

## 常见问题

### Q: 中文边界匹配不上？
A: 中文无空格分词，建议用 `(?<!\d)...(?!\d)` 替代 `\b`。

### Q: Excel 列识别错误？
A: 确认首行是表头（字符串），数据从第 2 行开始。列名区分大小写。

### Q: 想要 .exe 怎么办？
A: v0.2.1 不再支持。自行打包时**不要**保留 `src/__init__.py`，否则 PyInstaller 会把 `src/` 当 package 导致 `import core` 失败。建议改用 `--onedir` 模式（比 `--onefile` 稳）。

### Q: GUI 启动报错 NameError？
A: v0.2.1 已修复 `pad` 变量未传递问题。如仍报错请更新代码。
