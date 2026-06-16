"""
敏感词脱敏工具 - 简易 GUI（tkinter + ttk）

特性：
- 单文件 / 目录输入
- 敏感词列表（.txt）
- Excel 词表（.xlsx）
- 规则文件（.json）
- 模式多选（精确 / 模糊 / 规则）
- 自定义通配符
- 实时日志（后台线程 + 队列避免 UI 冻结）
- 批量配置（JSON 任务清单）
- 全局异常捕获 → 写 stderr.log + 状态栏提示

设计：tkinter 是 Python 标准库，PyInstaller --onefile 自动打包，
无需 --hidden-import tkinter。
"""
from __future__ import annotations

import queue
import sys
import threading
import traceback
from pathlib import Path

# 允许直接 python src/gui.py
sys.path.insert(0, str(Path(__file__).parent))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from core import SensitiveWordRedactor, load_words_file, load_rules_file
from excel_handler import load_excel_words
from file_handlers import supported_extensions
from batch import run_batch, BatchTask, run_task


APP_TITLE = "敏感词脱敏工具 v0.2.0"
SUPPORTED = " ".join(supported_extensions())


class RedactorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("820x680")
        self.root.minsize(720, 560)

        # 后台线程通信
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None

        # 状态变量
        self.var_input = tk.StringVar()
        self.var_output = tk.StringVar()
        self.var_words = tk.StringVar()
        self.var_excel = tk.StringVar()
        self.var_rules = tk.StringVar()
        self.var_batch = tk.StringVar()
        self.var_wildcard = tk.StringVar(value="***")
        self.mode_exact = tk.BooleanVar(value=True)
        self.mode_fuzzy = tk.BooleanVar(value=False)
        self.mode_rule = tk.BooleanVar(value=True)
        self.var_status = tk.StringVar(value="就绪")

        self._build_ui()
        self._poll_log_queue()

    # ---------------- UI 构建 ----------------

    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        # 顶部说明
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, **pad)
        ttk.Label(
            top,
            text=f"支持格式：{SUPPORTED}",
            foreground="#666",
        ).pack(side=tk.LEFT)

        # 模式 notebook
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, **pad)

        self._build_single_tab(nb)
        self._build_batch_tab(nb)

        # 底部：日志 + 状态栏
        log_frame = ttk.LabelFrame(self.root, text="运行日志")
        log_frame.pack(fill=tk.BOTH, expand=True, **pad)
        self.txt_log = scrolledtext.ScrolledText(
            log_frame, height=12, wrap=tk.WORD, font=("Menlo", 10)
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.txt_log.config(state=tk.DISABLED)

        # 状态栏
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_bar, textvariable=self.var_status, anchor=tk.W).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=2
        )

    def _build_single_tab(self, nb: ttk.Notebook):
        tab = ttk.Frame(nb)
        nb.add(tab, text="单次脱敏")

        # 输入/输出
        row = 0
        ttk.Label(tab, text="输入路径（文件/目录）：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_input).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_input).grid(row=row, column=2, **pad)

        row += 1
        ttk.Label(tab, text="输出目录：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_output).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_output).grid(row=row, column=2, **pad)

        # 配置
        row += 1
        ttk.Separator(tab, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=8
        )

        row += 1
        ttk.Label(tab, text="敏感词列表（.txt）：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_words).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_words).grid(row=row, column=2, **pad)

        row += 1
        ttk.Label(tab, text="Excel 词表（.xlsx）：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_excel).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_excel).grid(row=row, column=2, **pad)

        row += 1
        ttk.Label(tab, text="规则文件（.json）：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_rules).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_rules).grid(row=row, column=2, **pad)

        # 模式 + 通配符
        row += 1
        ttk.Separator(tab, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=8
        )

        row += 1
        ttk.Label(tab, text="脱敏模式：").grid(row=row, column=0, sticky=tk.W, **pad)
        mode_frame = ttk.Frame(tab)
        mode_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, **pad)
        ttk.Checkbutton(mode_frame, text="精确匹配", variable=self.mode_exact).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(mode_frame, text="模糊匹配", variable=self.mode_fuzzy).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(mode_frame, text="正则规则", variable=self.mode_rule).pack(side=tk.LEFT, padx=4)

        row += 1
        ttk.Label(tab, text="通配符：").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_wildcard, width=20).grid(
            row=row, column=1, sticky=tk.W, **pad
        )

        # 按钮
        row += 1
        ttk.Separator(tab, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=8
        )

        row += 1
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=row, column=0, columnspan=3, **pad)
        ttk.Button(btn_frame, text="开始脱敏", command=self._start_single).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=4)

        tab.columnconfigure(1, weight=1)

    def _build_batch_tab(self, nb: ttk.Notebook):
        tab = ttk.Frame(nb)
        nb.add(tab, text="批量任务")

        ttk.Label(
            tab,
            text="通过 JSON 任务清单一次跑多组脱敏任务，每任务可独立配置词表/规则/模式。\n"
                 "JSON 格式参见菜单「帮助」或 README.md。",
            foreground="#444",
            justify=tk.LEFT,
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, **pad)

        ttk.Label(tab, text="批量配置（.json）：").grid(row=1, column=0, sticky=tk.W, **pad)
        ttk.Entry(tab, textvariable=self.var_batch).grid(row=1, column=1, sticky=tk.EW, **pad)
        ttk.Button(tab, text="选择...", command=self._pick_batch).grid(row=1, column=2, **pad)

        ttk.Button(tab, text="生成示例配置", command=self._gen_batch_template).grid(
            row=2, column=1, sticky=tk.W, **pad
        )

        ttk.Separator(tab, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=3, sticky=tk.EW, pady=8
        )

        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=4, column=0, columnspan=3, **pad)
        ttk.Button(btn_frame, text="开始批量", command=self._start_batch).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=4)

        tab.columnconfigure(1, weight=1)

    # ---------------- 文件选择 ----------------

    def _pick_input(self):
        # 允许选文件或目录
        path = filedialog.askopenfilename(title="选择输入文件（取消选目录）")
        if not path:
            path = filedialog.askdirectory(title="或选择输入目录")
        if path:
            self.var_input.set(path)

    def _pick_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.var_output.set(path)

    def _pick_words(self):
        path = filedialog.askopenfilename(
            title="选择敏感词列表", filetypes=[("文本", "*.txt"), ("所有", "*.*")]
        )
        if path:
            self.var_words.set(path)

    def _pick_excel(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 词表", filetypes=[("Excel", "*.xlsx"), ("所有", "*.*")]
        )
        if path:
            self.var_excel.set(path)

    def _pick_rules(self):
        path = filedialog.askopenfilename(
            title="选择规则文件", filetypes=[("JSON", "*.json"), ("所有", "*.*")]
        )
        if path:
            self.var_rules.set(path)

    def _pick_batch(self):
        path = filedialog.askopenfilename(
            title="选择批量配置", filetypes=[("JSON", "*.json"), ("所有", "*.*")]
        )
        if path:
            self.var_batch.set(path)

    def _gen_batch_template(self):
        out = filedialog.asksaveasfilename(
            title="保存批量配置示例",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="batch_example.json",
        )
        if not out:
            return
        template = {
            "_comment": "sensitive-words-packer 批量任务示例；删除 _comment 行",
            "tasks": [
                {
                    "name": "示例任务 1 - 文本脱敏",
                    "input": "./input/marketing",
                    "output": "./output/marketing",
                    "words": "./config/words.txt",
                    "rules": "./config/rules.json",
                    "mode": "exact,rule",
                    "wildcard": "***",
                    "log": "marketing.log",
                },
                {
                    "name": "示例任务 2 - Excel 词表",
                    "input": "./input/finance",
                    "output": "./output/finance",
                    "excel": "./config/words_finance.xlsx",
                    "excel_sheet": "Sheet1",
                    "excel_column": "敏感词",
                    "rules": "./config/rules_finance.json",
                    "mode": "exact,fuzzy,rule",
                    "wildcard": "[REDACTED]",
                },
            ],
        }
        Path(out).write_text(
            __import__("json").dumps(template, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.var_batch.set(out)
        self._log(f"已生成批量配置示例: {out}")

    # ---------------- 后台任务 ----------------

    def _start_single(self):
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("提示", "有任务正在运行，请等待完成")
            return

        input_path = self.var_input.get().strip()
        output_dir = self.var_output.get().strip()
        if not input_path or not output_dir:
            messagebox.showerror("错误", "请填写输入路径和输出目录")
            return

        # 收集模式
        modes: list[str] = []
        if self.mode_exact.get():
            modes.append("word-exact")
        if self.mode_fuzzy.get():
            modes.append("word-fuzzy")
        if self.mode_rule.get():
            modes.append("rule")
        if not modes:
            messagebox.showerror("错误", "请至少启用一个脱敏模式")
            return

        # 加载配置
        try:
            words: list[str] = []
            if self.var_words.get().strip():
                words.extend(load_words_file(self.var_words.get().strip()))
            if self.var_excel.get().strip():
                words.extend(load_excel_words(self.var_excel.get().strip()))
            rules = load_rules_file(self.var_rules.get().strip()) if self.var_rules.get().strip() else []
        except Exception as e:
            messagebox.showerror("加载配置失败", str(e))
            return

        if not words and not rules:
            messagebox.showerror("错误", "请至少提供敏感词列表、Excel 词表或规则文件之一")
            return

        wildcard = self.var_wildcard.get() or "***"
        redactor = SensitiveWordRedactor(words=words, rules=rules, wildcard=wildcard)
        self._log(f"[配置] {len(words)} 词 | {len(rules)} 规则 | 模式 {modes} | 通配符 {wildcard!r}")

        # 后台线程跑
        self.var_status.set("处理中...")
        self.worker = threading.Thread(
            target=self._run_single_worker,
            args=(Path(input_path), Path(output_dir), redactor, modes),
            daemon=True,
        )
        self.worker.start()

    def _run_single_worker(self, input_path: Path, output_dir: Path,
                           redactor: SensitiveWordRedactor, modes: list[str]):
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            files = [input_path] if input_path.is_file() else \
                [p for p in input_path.rglob("*") if p.is_file()]
            self.log_queue.put(f"[扫描] {len(files)} 个文件")
            total = 0
            log_lines: list[str] = []
            for f in files:
                self.log_queue.put(f"  → {f.name}")
                # 复用 cli.process_file 等价逻辑（避免循环 import 改在此处 inline）
                from file_handlers import get_handler, copy_file
                handler = get_handler(f)
                if handler is None:
                    outs = copy_file(f, output_dir)
                    self.log_queue.put(f"    [⤳ 复制] {f.name}（不支持格式）")
                    continue
                try:
                    text = handler.read(f)
                    result = redactor.redact(text, source_file=f.name, modes=modes)
                    outs = handler.write(output_dir / f.name, result.redacted_text)
                    n = len(result.matches)
                    total += n
                    extra = ""
                    if len(outs) > 1:
                        extra = " [+ " + ", ".join(o.name for o in outs[1:]) + "]"
                    self.log_queue.put(f"    [✓ 完成] {f.name}  {n} 处匹配{extra}")
                    for m in result.matches:
                        log_lines.append(
                            f"[{m.mode}{':' + m.rule_name if m.rule_name else ''}] "
                            f"{m.file}:{m.line}  '{m.original}' -> '{m.replacement}'"
                        )
                except Exception as e:
                    self.log_queue.put(f"    [✗ 失败] {f.name}  {e}")
            # 写审计日志
            log_path = output_dir / "run.log"
            log_path.write_text(
                f"# sensitive-words-packer 审计日志\n"
                f"# 输入: {input_path}\n"
                f"# 模式: {modes}\n"
                f"# 文件数: {len(files)} | 总匹配: {total}\n"
                f"\n" + "\n".join(log_lines),
                encoding="utf-8",
            )
            self.log_queue.put(f"[完成] 输出目录: {output_dir}")
            self.log_queue.put(f"[完成] 总匹配: {total} 处 | 审计日志: {log_path}")
            self.log_queue.put("__STATUS__done__")
        except Exception as e:
            self.log_queue.put(f"[错误] {e}")
            self.log_queue.put(traceback.format_exc())
            self.log_queue.put("__STATUS__done__")

    def _start_batch(self):
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("提示", "有任务正在运行，请等待完成")
            return
        cfg = self.var_batch.get().strip()
        if not cfg:
            messagebox.showerror("错误", "请选择批量配置文件")
            return

        self.var_status.set("批量处理中...")
        self.worker = threading.Thread(
            target=self._run_batch_worker, args=(cfg,), daemon=True
        )
        self.worker.start()

    def _run_batch_worker(self, cfg_path: str):
        try:
            def progress(idx, total, name):
                self.log_queue.put(f"[批量] ({idx}/{total}) {name}")
            results = run_batch(cfg_path, progress_cb=progress)
            ok = sum(1 for r in results if r.status == "ok")
            err = sum(1 for r in results if r.status != "ok")
            for r in results:
                if r.status == "ok":
                    self.log_queue.put(
                        f"  [✓ {r.task.name}] {r.files} 文件 / {r.matches} 匹配"
                    )
                else:
                    self.log_queue.put(f"  [✗ {r.task.name}] {r.error}")
            self.log_queue.put(f"[批量完成] 成功 {ok} | 失败 {err}")
            self.log_queue.put("__STATUS__done__")
        except Exception as e:
            self.log_queue.put(f"[批量错误] {e}")
            self.log_queue.put(traceback.format_exc())
            self.log_queue.put("__STATUS__done__")

    # ---------------- 日志 + 状态 ----------------

    def _log(self, msg: str):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _clear_log(self):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == "__STATUS__done__":
                    self.var_status.set("就绪")
                else:
                    self._log(msg)
        except queue.Empty:
            pass
        # 100ms 后再轮询
        self.root.after(100, self._poll_log_queue)


def main():
    """GUI 入口；异常兜底写 stderr.log 便于排错"""
    try:
        root = tk.Tk()
        # Windows 下 ttk 主题
        try:
            style = ttk.Style()
            if "vista" in style.theme_names():
                style.theme_use("vista")
            elif "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass
        RedactorGUI(root)
        root.mainloop()
    except Exception as e:
        # GUI 启动失败时也要让用户看到错误
        err = traceback.format_exc()
        try:
            Path("stderr.log").write_text(err, encoding="utf-8")
        except Exception:
            pass
        print(err, file=sys.stderr)
        try:
            messagebox.showerror("启动失败", f"{e}\n\n详见 stderr.log")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
