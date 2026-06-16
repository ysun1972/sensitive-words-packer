# 用户手册 (v0.2.0)

## 快速上手

### 1. GUI 模式（推荐 / 解决 v0.1.0 闪退）

直接双击 `swp.exe` 启动 GUI 窗口：

1. **输入路径**：点击「选择...」选择文件或目录
2. **输出目录**：点击「选择...」选择输出位置
3. **敏感词列表（.txt）**：可选，每行一个词
4. **Excel 词表（.xlsx）**：可选，支持按列名/列字母/列号
5. **规则文件（.json）**：可选，正则表达式规则
6. **脱敏模式**：勾选 精确匹配 / 模糊匹配 / 正则规则
7. **通配符**：默认 `***`，可改为 `[已脱敏]` 等
8. **点击「开始脱敏」**

### 2. 命令行（CLI）

#### 2.1 单文件/目录处理

```bash
# 单个文件
python src/cli.py --cli -i input.txt -o output/ \
  --words words.txt --mode exact --wildcard "***"

# 整个目录
python src/cli.py --cli -i ./input -o ./output \
  --words words.txt --rules rules.json --mode exact,fuzzy,rule
```

#### 2.2 Excel 词表（v0.2.0）

```bash
# 按列名
python src/cli.py --cli -i ./input -o ./output \
  --excel words.xlsx --excel-column "敏感词"

# 按列字母
python src/cli.py --cli -i ./input -o ./output \
  --excel words.xlsx --excel-column "C"

# 按列号（从 0 开始）
python src/cli.py --cli -i ./input -o ./output \
  --excel words.xlsx --excel-column 2

# 指定 Sheet
python src/cli.py --cli -i ./input -o ./output \
  --excel words.xlsx --excel-sheet "财务词表" --excel-column "账号"
```

#### 2.3 批量任务（v0.2.0）

```bash
# 跑批量配置
python src/cli.py --cli --batch tasks.json
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

### 3. Windows 双击

1. 在 Windows 上执行 `scripts\build_exe.bat` 打包
2. 产物 `dist\swp.exe` —— **双击启动 GUI**
3. 命令行模式：在 cmd 中执行 `swp.exe --cli -i ... -o ...`

### 4. 安装包

在 Windows 上：
1. `scripts\build_exe.bat` 生成 `dist\swp.exe`
2. 安装 NSIS 后执行：`makensis scripts\installer.nsi`
3. 产物：`dist\Sensitive Words Packer-Setup-0.2.0.exe`

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

## v0.1.0 闪退问题

**症状**：双击 `swp.exe` 后黑窗一闪就消失，工具「打不开」

**根因**：v0.1.0 的 `swp.exe` 是 PyInstaller 打包的 CLI 程序，0.1s 内执行完 main() 立即退出

**修复**（v0.2.0）：
- 双击 `swp.exe` 启动 GUI 窗口（tkinter）
- 命令行模式需显式加 `--cli` 标志

## 常见问题

### Q: 打包后体积大（约 30MB）？
A: 包含了 reportlab 全套字体（支持中文 PDF）和 openpyxl + python-docx。如不需要 PDF 副产物可裁剪。

### Q: 中文边界匹配不上？
A: 中文无空格分词，建议用 `(?<!\d)...(?!\d)` 替代 `\b`。

### Q: Excel 列识别错误？
A: 确认首行是表头（字符串），数据从第 2 行开始。列名区分大小写。

### Q: 双击 .exe 还是闪退？
A: 确认打包用了 `--windowed` 标志（v0.2.0 workflow 已加）。如仍闪退，查看 `stderr.log`。
