"""
sensitive-words-packer 命令行入口
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接 python src/cli.py 运行
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    SensitiveWordRedactor,
    load_words_file,
    load_rules_file,
    WordMatch,
)
from file_handlers import get_handler, copy_file, supported_extensions


def process_file(
    src: Path,
    dst_dir: Path,
    redactor: SensitiveWordRedactor,
    modes: list[str],
    log_lines: list[str],
) -> dict:
    """处理单个文件，返回统计"""
    handler = get_handler(src)
    dst = dst_dir / src.name
    stats = {"file": str(src), "status": "skipped", "matches": 0, "outputs": []}

    if handler is None:
        # 不支持格式：直接复制
        outs = copy_file(src, dst_dir)
        stats["status"] = "copied"
        stats["outputs"] = [str(o) for o in outs]
        return stats

    try:
        text = handler.read(src)
    except Exception as e:
        stats["status"] = f"read-error: {e}"
        return stats

    result = redactor.redact(text, source_file=src.name, modes=modes)
    try:
        outs = handler.write(dst, result.redacted_text)
    except Exception as e:
        stats["status"] = f"write-error: {e}"
        return stats

    stats["status"] = "ok"
    stats["matches"] = len(result.matches)
    stats["outputs"] = [str(o) for o in outs]
    for m in result.matches:
        log_lines.append(
            f"[{m.mode}{':' + m.rule_name if m.rule_name else ''}] "
            f"{m.file}:{m.line}  '{m.original}' -> '{m.replacement}'"
        )
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="敏感词脱敏工具 - 输入文件/目录，输出脱敏后文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 精确匹配 + 规则模式
  python cli.py -i input.txt -o output/ --words words.txt --rules rules.json

  # 模糊匹配
  python cli.py -i ./docs -o ./docs_clean --words words.txt --mode fuzzy

  # 仅规则模式（不传 --words）
  python cli.py -i input.txt -o output/ --rules rules.json --mode rule
        """,
    )
    parser.add_argument("-i", "--input", required=True, help="输入文件或目录")
    parser.add_argument("-o", "--output", required=True, help="输出目录")
    parser.add_argument("--words", help="敏感词列表文件（.txt，每行一个）")
    parser.add_argument("--rules", help="规则文件（.json，正则列表）")
    parser.add_argument(
        "--mode",
        default="exact,rule",
        help="脱敏模式（逗号分隔）：exact / fuzzy / rule，默认 exact,rule",
    )
    parser.add_argument(
        "--wildcard", default="***",
        help="脱敏通配符（默认 ***）",
    )
    parser.add_argument(
        "--log", default="run.log",
        help="审计日志路径（默认 run.log）",
    )
    args = parser.parse_args()

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

    # 加载敏感词与规则
    words = load_words_file(args.words) if args.words else []
    rules = load_rules_file(args.rules) if args.rules else []
    if not words and not rules:
        print("错误：必须提供 --words 或 --rules 至少一个")
        sys.exit(1)

    redactor = SensitiveWordRedactor(words=words, rules=rules, wildcard=args.wildcard)
    print(f"已加载 {len(words)} 个敏感词，{len(rules)} 条规则")
    print(f"启用模式: {', '.join(modes)}")
    print(f"通配符: {args.wildcard}")

    # 收集输入文件
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = [p for p in input_path.rglob("*") if p.is_file()]
    else:
        print(f"错误：输入路径不存在: {input_path}")
        sys.exit(1)

    print(f"待处理文件数: {len(files)}")
    print(f"支持格式: {', '.join(supported_extensions())}")

    # 处理
    log_lines: list[str] = []
    total_matches = 0
    for f in files:
        stats = process_file(f, output_dir, redactor, modes, log_lines)
        total_matches += stats["matches"]
        flag = "✓" if stats["status"] == "ok" else ("⤳" if stats["status"] == "copied" else "✗")
        match_info = f"  ({stats['matches']} 处)" if stats["matches"] else ""
        # 多产物显示：例如 report.pdf → report.pdf + report.docx
        outputs_info = ""
        if stats.get("outputs") and len(stats["outputs"]) > 1:
            extra = [Path(o).name for o in stats["outputs"][1:]]
            outputs_info = f"  [+] {', '.join(extra)}"
        print(f"  {flag} {f.name}  [{stats['status']}]{match_info}{outputs_info}")

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
