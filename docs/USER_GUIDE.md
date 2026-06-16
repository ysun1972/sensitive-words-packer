# 用户手册

## 快速上手

### 1. 命令行（CLI）

```bash
# 处理单个文件
python src/cli.py -i input.txt -o output.txt \
  --words words.txt --mode exact --wildcard "***"

# 处理整个目录（混合 .txt/.md/.docx）
python src/cli.py -i ./input -o ./output \
  --words words.txt --rules rules.json \
  --mode exact,fuzzy,rule
```

### 2. Windows 双击

1. 在 Windows 上执行 `scripts/build_exe.bat` 打包
2. 双击 `scripts/run.bat` → 自动处理 `sample/input/` → `sample/output/`

### 3. 安装包

在 Windows 上：
1. `scripts/build_exe.bat` 生成 `dist/swp.exe`
2. 安装 NSIS 后执行：`makensis scripts/installer.nsi`
3. 产物：`dist/Sensitive Words Packer-Setup-0.1.0.exe`

## 敏感词列表格式

`words.txt` 每行一个，支持 `#` 开头注释：

```text
# 客户名称
张三
李四

# 内部代号
ProjectPhoenix
```

## 规则文件格式

`rules.json` 是 JSON 数组，每条规则含 name / pattern / replacement：

```json
[
  {
    "name": "手机号",
    "pattern": "\\b1[3-9]\\d{9}\\b",
    "replacement": "[手机号]"
  }
]
```

- **pattern**：标准 Python 正则
- **replacement**：替换文本，可包含 `\1` 等反向引用
- 多个规则按数组顺序应用

## 模式说明

| 模式 | 描述 | 示例 |
|------|------|------|
| `exact` | 精确匹配（整词边界）| `张三` → `***` |
| `fuzzy` | 模糊匹配（首尾字固定，中间允许 0-2 字）| `张三三` → `***` |
| `rule` | 规则模式（正则）| `18612345678` → `[手机号]` |

`--mode` 可多选逗号分隔：`--mode exact,fuzzy,rule`（默认 `exact,rule`）

## 脱敏通配符

通过 `--wildcard` 自定义（默认 `***`）：

- 适合合规审计：`[已脱敏]` / `[REDACTED]`
- 适合留空：`（此处已删除）`
- 适合反审查（**不推荐**）：`*` / `〇`

## 输出格式

- 输入 `.txt` → 输出 `.txt`（UTF-8 编码）
- 输入 `.md` → 输出 `.md`
- 输入 `.docx` → 输出 `.docx`（段落 + 表格内容脱敏）
- 输入 `.pdf` → 输出**双产物**（模式 C）：
  - **主产物** `name.pdf`：reportlab 重建的简化版 PDF（保留文件名/扩展名，便于交付）
  - **副产物** `name.docx`：同脱敏文本的 Word 文档，便于用户继续编辑/排版
- 不支持格式（如 `.xlsx`/`.pptx`）→ 原样复制到输出目录

### PDF 脱敏重要说明（双产物模式 C）

PDF 是二进制格式（字体子集 + 坐标 + 内容流），无法"原地替换"敏感词。本工具采用：

1. **读取**：pypdf 逐页提取纯文本
2. **脱敏**：在内存中对文本应用敏感词 / 规则
3. **重建（双产物）**：
   - 主 PDF：reportlab 重新生成（内置 STSong-Light 中文字体，**无需额外字体文件**）
   - 副 docx：python-docx 写入（用户可继续编辑）

**为何同时输出 PDF + docx？**
- PDF 主产物便于直接交付（保留 .pdf 扩展名）
- docx 副产物便于后续编辑（避免用户重新手打脱敏内容）
- 用户可任选其一

⚠️ **限制**：
- 原 PDF 的页眉页脚、表格、图表、嵌入图片、字体样式会丢失
- 输出 PDF 是简化的纯文本流（A4 / 10pt / 中文字体）
- **扫描版 PDF**（图片型）无文本层，`read()` 返回空字符串
- 复杂版式 PDF 建议直接打开 `name.docx` 副产物编辑

## 审计日志

每次处理后生成 `run.log`，记录：
- 输入路径、模式、通配符
- 每个文件每处匹配：文件名、行号、原文、替换、模式

## 性能与限制

- 单文件建议 ≤ 50 MB（docx 模式 ≥ 200 MB 会较慢）
- 并发：v0.1 单进程顺序处理；v0.2 计划支持多进程
- 内存：192kWh LFP 级别文章（1-2MB）瞬时完成

## 常见问题

**Q：模糊匹配会不会误伤正常词？**
A：会的。模糊匹配只匹配**首尾相同且长度差异 ≤ 2** 的情形。生产建议用 `exact` 为主，`fuzzy` 为辅。

**Q：能否不打包直接用？**
A：可以，直接用 `python src/cli.py` 即可，无需 PyInstaller。

**Q：能否用于绕过平台审核？**
A：不能。工具默认只做合规遮蔽；如需「反审查绕过」能力，请自行扩展并自负法律责任。

**Q：PDF 脱敏后版式变了怎么办？**
A：是的，PDF 脱敏会丢失原版式（页眉页脚、图表、字体样式）。如需保留版式，建议先手动将 PDF 转为 .docx 再脱敏。

**Q：能否处理 Excel（.xlsx）？**
A：v0.1 不支持。v0.2 计划通过 `openpyxl` 扩展。

**Q：扫描版 PDF 怎么处理？**
A：扫描版 PDF 是图片，没有文本层。需要先用 OCR（如 Tesseract / PaddleOCR）转文本版 PDF 或 .docx 再脱敏。
