"""
sensitive-words-packer v0.2.1 命令行入口

仅在 IDE / 命令行环境下使用；GUI 模式请显式运行 `python src/gui.py`。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接 python src/cli.py
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    SensitiveWordRedactor,
    load_words_file,
    load_rules_file,
)
from file_handlers import get_handler, copy_file, supported_extensions
from excel_handler import load_excel_words
from batch import run_batch


def main():
    parser = argparse.ArgumentParser(
        description="敏感词脱敏工具 v0.2.1 - 命令行模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模式:
  - 单文件:   python cli.py -i in.txt -o out/ --words w.txt
  - 批量:     python cli.py --batch tasks.json
  - 仅规则:   python cli.py -i in.txt -o out/ --rules r.json --mode rule
  - Excel:    python cli.py -i in.txt -o out/ --excel words.xlsx
        """,
    )
    parser.add_argument("-i", "--input", help="输入文件或目录")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--words", help="敏感词列表文件（.txt，每行一个）")
    parser.add_argument("--excel", help="Excel 词表（.xlsx）")
    parser.add_argument("--excel-sheet", help="Excel 工作表名/索引")
    parser.add_argument("--excel-column", help="Excel 列名/列字母/列号")
    parser.add_argument("--rules", help="规则文件（.json，正则列表）")
    parser.add_argument("--batch", help="批量任务配置（.json）")
    parser.add_argument(
        "--mode", default="exact,rule",
        help="脱敏模式（逗号分隔）：exact / fuzzy / rule，默认 exact,rule",
    )
    parser.add_argument("--wildcard", default="***", help="脱敏通配符（默认 ***）")
    parser.add_argument("--log", default="run.log", help="审计日志路径（默认 run.log）")
    args = parser.parse_args()

    # ---- 批量模式 ----
    if args.batch:
        results = run_batch(args.batch)
        for r in results:
            status = "✓" if r.status == "ok" else "✗"
            extra = f" ({r.error})" if r.error else ""
            print(f"  {status} {r.task.name}: {r.status}{extra}")
        return

    # ---- 单文件模式 ----
    if not args.input or not args.output:
        parser.print_help()
        print("\n错误：单文件模式必须提供 -i 和 -o", file=sys.stderr)
        sys.exit(1)

    # 解析模式
    mode_map = {"exact": "word-exact", "fuzzy": "word-fuzzy", "rule": "rule"}
    modes = []
    for m in args.mode.split(","):
        m = m.strip()
        if m in mode_map:
            modes.append(mode_map[m])
        elif m in mode_map.values():
            modes.append(m)
        else:
            print(f"警告：未知模式 '{m}'（应为 exact/fuzzy/rule）")
    if not modes:
        print("错误：至少启用一个模式")
        sys.exit(1)

    # 加载敏感词
    words: list[str] = []
    if args.words:
        words.extend(load_words_file(args.words))
    if args.excel:
        try:
            sheet = args.excel_sheet
            if sheet and sheet.lstrip("-").isdigit():
                sheet = int(sheet)
            column = args.excel_column
            if column and column.lstrip("-").isdigit():
                column = int(column)
            words.extend(load_excel_words(args.excel, sheet=sheet, column=column))
        except Exception as e:
            print(f"错误：加载 Excel 失败: {e}")
            sys.exit(1)

    # 加载规则
    rules = load_rules_file(args.rules) if args.rules else []
    if not words and not rules:
        print("错误：必须提供 --words/--excel/--rules 至少一个")
        sys.exit(1)

    redactor = SensitiveWordRedactor(words=words, rules=rules, wildcard=args.wildcard)
    print(f"已加载 {len(words)} 个敏感词，{len(rules)} 条规则")
    print(f"启用模式: {', '.join(modes)}")
    print(f"通配符: {args.wildcard}")

    # 收集输入
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [input_path] if input_path.is_file() else \
        [p for p in input_path.rglob("*") if p.is_file()]
    print(f"待处理文件数: {len(files)}")
    print(f"支持格式: {', '.join(supported_extensions())}")

    # 处理
    log_lines: list[str] = []
    total_matches = 0
    for f in files:
        handler = get_handler(f)
        if handler is None:
            outs = copy_file(f, output_dir)
            print(f"  ⤳ {f.name}  [copied]")
            continue
        try:
            text = handler.read(f)
        except Exception as e:
            print(f"  ✗ {f.name}  [read-error: {e}]")
            continue
        result = redactor.redact(text, source_file=f.name, modes=modes)
        try:
            outs = handler.write(output_dir / f.name, result.redacted_text)
        except Exception as e:
            print(f"  ✗ {f.name}  [write-error: {e}]")
            continue
        total_matches += len(result.matches)
        extra = ""
        if len(outs) > 1:
            extra = "  [+] " + ", ".join(o.name for o in outs[1:])
        match_info = f"  ({len(result.matches)} 处)" if result.matches else ""
        print(f"  ✓ {f.name}  [ok]{match_info}{extra}")
        for m in result.matches:
            log_lines.append(
                f"[{m.mode}{':' + m.rule_name if m.rule_name else ''}] "
                f"{m.file}:{m.line}  '{m.original}' -> '{m.replacement}'"
            )

    # 写审计日志
    log_path = output_dir / args.log
    log_path.write_text(
        f"# sensitive-words-packer 审计日志\n"
        f"# 输入: {input_path}\n"
        f"# 模式: {modes}\n"
        f"# 通配符: {args.wildcard}\n"
        f"# 敏感词数: {len(words)} | 规则数: {len(rules)}\n"
        f"# 文件数: {len(files)} | 总匹配: {total_matches}\n"
        f"\n" + "\n".join(log_lines),
        encoding="utf-8",
    )

    print(f"\n完成：{len(files)} 个文件 → {output_dir}")
    print(f"总匹配: {total_matches} 处")
    print(f"审计日志: {log_path}")


if __name__ == "__main__":
    main()
