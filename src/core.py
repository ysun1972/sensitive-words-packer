"""
sensitive-words-packer 核心脱敏模块

支持两种脱敏模式：
1. 敏感词模式（精确 / 模糊）
2. 规则模式（正则表达式）
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class WordMatch:
    """单条匹配记录（用于审计日志）"""
    file: str
    line: int
    original: str
    replacement: str
    mode: str  # 'word-exact' / 'word-fuzzy' / 'rule'
    rule_name: str | None = None


@dataclass
class RedactionResult:
    """脱敏结果"""
    redacted_text: str
    matches: list[WordMatch] = field(default_factory=list)


@dataclass
class Rule:
    """自定义脱敏规则（正则）"""
    name: str
    pattern: str
    replacement: str = "***"
    flags: int = re.IGNORECASE

    def compile(self) -> re.Pattern:
        # 直接用用户提供的 pattern，\b 等边界由用户自己处理
        return re.compile(self.pattern, self.flags)


class SensitiveWordRedactor:
    """
    核心脱敏器
    模式：
      - 加载敏感词列表（每行一个）
      - 加载规则列表（JSON 中的正则）
      - 对文本依次应用：精确词 → 模糊词 → 规则
    """

    def __init__(
        self,
        words: Iterable[str] | None = None,
        rules: Iterable[Rule] | None = None,
        wildcard: str = "***",
    ):
        self.wildcard = wildcard
        # 过滤空词、去重
        self.words: list[str] = [w.strip() for w in (words or []) if w and w.strip()]
        # 按词长降序排列，优先匹配长词（避免 "张三三" 优先匹配 "张三"）
        self.words.sort(key=len, reverse=True)
        self.rules: list[Rule] = list(rules or [])

    def add_words(self, words: Iterable[str]) -> None:
        for w in words:
            w = w.strip()
            if w and w not in self.words:
                self.words.append(w)
        self.words.sort(key=len, reverse=True)

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def _redact_word_exact(self, text: str, source_file: str = "") -> tuple[str, list[WordMatch]]:
        """精确匹配：整词边界"""
        matches: list[WordMatch] = []
        for word in self.words:
            if not word:
                continue
            # 用 \b 处理中英文混合（re 默认对中文无 \b 效果，特殊处理）
            pattern = self._build_exact_pattern(word)
            new_text, n = pattern.subn(self.wildcard, text)
            if n > 0:
                # 找出每处匹配的位置（行号）
                for m in pattern.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    matches.append(WordMatch(
                        file=source_file,
                        line=line_no,
                        original=m.group(),
                        replacement=self.wildcard,
                        mode="word-exact",
                    ))
                text = new_text
        return text, matches

    def _redact_word_fuzzy(self, text: str, source_file: str = "") -> tuple[str, list[WordMatch]]:
        """模糊匹配：跳过中间字符（用于同音/变体）"""
        matches: list[WordMatch] = []
        for word in self.words:
            if not word or len(word) < 2:
                continue
            # 构造模糊 pattern：word[0] + 任意 0-2 字符 + word[1] + 任意 0-2 字符 + ... + word[-1]
            fuzzy_pattern = self._build_fuzzy_pattern(word)
            new_text, n = fuzzy_pattern.subn(self.wildcard, text)
            if n > 0:
                for m in fuzzy_pattern.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    matches.append(WordMatch(
                        file=source_file,
                        line=line_no,
                        original=m.group(),
                        replacement=self.wildcard,
                        mode="word-fuzzy",
                    ))
                text = new_text
        return text, matches

    def _redact_rules(self, text: str, source_file: str = "") -> tuple[str, list[WordMatch]]:
        """规则模式：正则替换"""
        matches: list[WordMatch] = []
        for rule in self.rules:
            pattern = rule.compile()
            new_text, n = pattern.subn(rule.replacement, text)
            if n > 0:
                for m in pattern.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    matches.append(WordMatch(
                        file=source_file,
                        line=line_no,
                        original=m.group(),
                        replacement=rule.replacement,
                        mode="rule",
                        rule_name=rule.name,
                    ))
                text = new_text
        return text, matches

    def redact(self, text: str, source_file: str = "", modes: list[str] | None = None) -> RedactionResult:
        """
        主入口
        modes: 子集 ['word-exact', 'word-fuzzy', 'rule']，默认全开
        """
        modes = modes or ["word-exact", "word-fuzzy", "rule"]
        all_matches: list[WordMatch] = []
        out = text

        if "word-exact" in modes and self.words:
            out, m = self._redact_word_exact(out, source_file)
            all_matches.extend(m)
        if "word-fuzzy" in modes and self.words:
            out, m = self._redact_word_fuzzy(out, source_file)
            all_matches.extend(m)
        if "rule" in modes and self.rules:
            out, m = self._redact_rules(out, source_file)
            all_matches.extend(m)

        return RedactionResult(redacted_text=out, matches=all_matches)

    # ---- 内部工具 ----

    @staticmethod
    def _build_exact_pattern(word: str) -> re.Pattern:
        """
        构造整词匹配 pattern。
        - 全 ASCII：用 \b 词边界，避免匹配到 "foobar" 中的 "foo"
        - 含中文：直接 re.escape，不加边界（中文无空格分词，
          加 lookbehind/lookahead 容易误伤正常中文文本）
        """
        escaped = re.escape(word)
        if word.isascii():
            return re.compile(rf"\b{escaped}\b")
        return re.compile(escaped)

    @staticmethod
    def _build_fuzzy_pattern(word: str) -> re.Pattern:
        """
        构造模糊匹配 pattern：保留首尾字，中间允许 0-2 个任意字符。
        例：'张三' → r'张.{0,2}三'
        """
        if len(word) == 1:
            return re.compile(re.escape(word))
        chars = list(word)
        middle = ".".join([r".{0,2}"] * (len(chars) - 2)) if len(chars) > 2 else ""
        pattern_str = re.escape(chars[0])
        if middle:
            pattern_str += middle
        pattern_str += re.escape(chars[-1])
        return re.compile(pattern_str)


# ---- 工具函数 ----

def load_words_file(path: str | Path) -> list[str]:
    """从 .txt 加载敏感词列表（每行一个，支持 # 注释）"""
    p = Path(path)
    if not p.exists():
        return []
    words: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words.append(line)
    return words


def load_rules_file(path: str | Path) -> list[Rule]:
    """从 .json 加载规则列表
    支持两种 JSON 结构：
    1. 直接数组：[{"name":..., "pattern":..., ...}, ...]
    2. 带 "rules" 键的包装：{"rules": [...]}
    """
    import json
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    items = data["rules"] if isinstance(data, dict) and "rules" in data else data
    rules: list[Rule] = []
    for item in items:
        rules.append(Rule(
            name=item["name"],
            pattern=item["pattern"],
            replacement=item.get("replacement", "***"),
            flags=re.IGNORECASE,
        ))
    return rules
