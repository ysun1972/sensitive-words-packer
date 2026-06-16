"""
批量任务执行器（JSON 任务清单）

用途：一次跑多组「输入 → 输出 + 配置」任务
适用场景：多部门 / 多项目 / 多语言词表分别处理

JSON 结构：
{
  "tasks": [
    {
      "name": "市场部 Q1 报告",
      "input": "./input/marketing",
      "output": "./output/marketing",
      "words": "./config/words_marketing.txt",
      "rules": "./config/rules_common.json",
      "excel": null,                    // 可选：.xlsx 词表
      "excel_sheet": "Sheet1",          // 可选
      "excel_column": "敏感词",         // 可选
      "mode": "exact,rule",             // 默认 "exact,rule"
      "wildcard": "***",                // 默认 "***"
      "log": "marketing.log"            // 默认 "run.log"
    },
    {
      "name": "财务部合同",
      "input": "./input/finance",
      "output": "./output/finance",
      "words": "./config/words_finance.txt",
      "mode": "exact,fuzzy,rule",
      "wildcard": "[REDACTED]"
    }
  ]
}

执行：
  python src/batch.py --config tasks.json
  # 或经 CLI：
  swp.exe --batch tasks.json

返回：每任务 stats dict 列表
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 允许直接 python src/batch.py
sys.path.insert(0, str(Path(__file__).parent))

from core import SensitiveWordRedactor, load_words_file, load_rules_file
from excel_handler import load_excel_words
from file_handlers import get_handler, copy_file, supported_extensions


@dataclass
class BatchTask:
    """单个批量任务"""
    name: str
    input: str
    output: str
    words: str | None = None
    rules: str | None = None
    excel: str | None = None
    excel_sheet: str | int | None = None
    excel_column: str | int | None = None
    mode: str = "exact,rule"
    wildcard: str = "***"
    log: str = "run.log"

    def to_kwargs(self) -> dict:
        return {
            "name": self.name,
            "input": self.input,
            "output": self.output,
            "words": self.words,
            "rules": self.rules,
            "excel": self.excel,
            "excel_sheet": self.excel_sheet,
            "excel_column": self.excel_column,
            "mode": self.mode,
            "wildcard": self.wildcard,
            "log": self.log,
        }


@dataclass
class BatchResult:
    """单个任务执行结果"""
    task: BatchTask
    status: str  # "ok" / "error" / "skipped"
    files: int = 0
    matches: int = 0
    error: str = ""
    outputs: list[str] = field(default_factory=list)


def load_batch_config(path: str | Path) -> list[BatchTask]:
    """从 JSON 加载批量任务清单

    支持两种结构：
    1. {"tasks": [{...}, {...}]}
    2. 直接数组：[{...}, {...}]
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"批量配置文件不存在: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    items = data["tasks"] if isinstance(data, dict) and "tasks" in data else data
    if not isinstance(items, list):
        raise ValueError("批量配置必须包含任务列表（tasks 数组）")
    tasks: list[BatchTask] = []
    for i, item in enumerate(items):
        try:
            tasks.append(BatchTask(
                name=item.get("name", f"task-{i+1}"),
                input=item["input"],
                output=item["output"],
                words=item.get("words"),
                rules=item.get("rules"),
                excel=item.get("excel"),
                excel_sheet=item.get("excel_sheet"),
                excel_column=item.get("excel_column"),
                mode=item.get("mode", "exact,rule"),
                wildcard=item.get("wildcard", "***"),
                log=item.get("log", "run.log"),
            ))
        except KeyError as e:
            raise ValueError(f"任务 #{i+1} 缺少必需字段: {e}")
    return tasks


def _parse_modes(mode_str: str) -> list[str]:
    mode_map = {"exact": "word-exact", "fuzzy": "word-fuzzy", "rule": "rule"}
    out = []
    for m in mode_str.split(","):
        m = m.strip()
        if not m:
            continue
        if m in mode_map:
            out.append(mode_map[m])
        elif m in mode_map.values():
            out.append(m)
    return out


def _process_one_file(
    src: Path,
    dst_dir: Path,
    redactor: SensitiveWordRedactor,
    modes: list[str],
    log_lines: list[str],
) -> dict:
    """处理单个文件（与 cli.process_file 同结构，保留独立以避免循环依赖）"""
    handler = get_handler(src)
    stats = {"file": str(src), "status": "skipped", "matches": 0, "outputs": []}

    if handler is None:
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
        outs = handler.write(dst_dir / src.name, result.redacted_text)
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


def run_task(task: BatchTask) -> BatchResult:
    """执行单个批量任务"""
    result = BatchResult(task=task, status="error")

    # 1) 校验输入/输出
    input_path = Path(task.input)
    output_dir = Path(task.output)
    if not input_path.exists():
        result.error = f"输入路径不存在: {input_path}"
        return result
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2) 加载敏感词（合并 .txt + .xlsx）
    words: list[str] = []
    if task.words:
        words.extend(load_words_file(task.words))
    if task.excel:
        try:
            xlsx_words = load_excel_words(
                task.excel,
                sheet=task.excel_sheet,
                column=task.excel_column,
            )
            words.extend(xlsx_words)
        except Exception as e:
            result.error = f"加载 Excel 词表失败: {e}"
            return result

    # 3) 加载规则
    rules = load_rules_file(task.rules) if task.rules else []

    if not words and not rules:
        result.error = "必须提供 words / excel / rules 至少一个"
        return result

    # 4) 解析模式
    modes = _parse_modes(task.mode)
    if not modes:
        result.error = f"无可用模式: {task.mode!r}"
        return result

    # 5) 构造 redactor
    redactor = SensitiveWordRedactor(words=words, rules=rules, wildcard=task.wildcard)

    # 6) 收集文件
    if input_path.is_file():
        files = [input_path]
    else:
        files = [p for p in input_path.rglob("*") if p.is_file()]

    # 7) 处理
    log_lines: list[str] = []
    total_matches = 0
    all_outputs: list[str] = []
    for f in files:
        stats = _process_one_file(f, output_dir, redactor, modes, log_lines)
        total_matches += stats["matches"]
        all_outputs.extend(stats.get("outputs", []))

    # 8) 写审计日志
    log_path = output_dir / task.log
    log_path.write_text(
        f"# sensitive-words-packer 批量任务日志\n"
        f"# 任务名: {task.name}\n"
        f"# 输入: {input_path}\n"
        f"# 模式: {modes}\n"
        f"# 通配符: {task.wildcard}\n"
        f"# 敏感词数: {len(words)} | 规则数: {len(rules)}\n"
        f"# 文件数: {len(files)} | 总匹配: {total_matches}\n"
        f"\n" + "\n".join(log_lines),
        encoding="utf-8",
    )

    result.status = "ok"
    result.files = len(files)
    result.matches = total_matches
    result.outputs = all_outputs
    return result


def run_batch(config_path: str | Path, progress_cb=None) -> list[BatchResult]:
    """
    跑全部任务。
    progress_cb(idx, total, task_name): 进度回调（GUI 用）
    """
    tasks = load_batch_config(config_path)
    results: list[BatchResult] = []
    for i, task in enumerate(tasks, 1):
        if progress_cb:
            try:
                progress_cb(i, len(tasks), task.name)
            except Exception:
                pass
        r = run_task(task)
        results.append(r)
    return results
