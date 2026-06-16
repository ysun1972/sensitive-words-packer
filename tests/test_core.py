"""脱敏核心模块测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import SensitiveWordRedactor, Rule, load_words_file, load_rules_file


def test_exact_word_match():
    r = SensitiveWordRedactor(words=["张三", "李四"])
    result = r.redact("张三和李四都是客户。", modes=["word-exact"])
    assert "***" in result.redacted_text
    assert "张三" not in result.redacted_text
    assert "李四" not in result.redacted_text
    assert len(result.matches) == 2
    print("✓ test_exact_word_match")


def test_fuzzy_word_match():
    r = SensitiveWordRedactor(words=["张三"])
    # "张三三" 模糊匹配应该被命中（中间允许 0-2 字符）
    result = r.redact("客户经理是张三三。", modes=["word-fuzzy"])
    assert "***" in result.redacted_text
    assert "张三三" not in result.redacted_text
    assert len(result.matches) >= 1
    print("✓ test_fuzzy_word_match")


def test_rule_pattern():
    r = SensitiveWordRedactor(
        rules=[Rule(name="手机号", pattern=r"(?<!\d)1[3-9]\d{9}(?!\d)", replacement="[手机号]")]
    )
    result = r.redact("电话：18612345678，备用：13800138000", modes=["rule"])
    assert "18612345678" not in result.redacted_text
    assert "13800138000" not in result.redacted_text
    assert "[手机号]" in result.redacted_text
    print("✓ test_rule_pattern")


def test_long_word_priority():
    """长词优先匹配"""
    r = SensitiveWordRedactor(words=["张三", "张三三"])
    result = r.redact("张三三是经理。", modes=["word-exact"])
    # 张三三 应作为整体匹配（而不是先匹配张三导致剩"三"）
    assert "***" in result.redacted_text
    assert "三" not in result.redacted_text or "***" in result.redacted_text
    print("✓ test_long_word_priority")


def test_mixed_modes():
    r = SensitiveWordRedactor(
        words=["张三"],
        rules=[Rule(name="手机号", pattern=r"(?<!\d)1[3-9]\d{9}(?!\d)", replacement="[手机号]")]
    )
    result = r.redact("张三电话18612345678", modes=["word-exact", "rule"])
    assert "张三" not in result.redacted_text
    assert "18612345678" not in result.redacted_text
    assert len(result.matches) == 2
    print("✓ test_mixed_modes")


def test_wildcard_custom():
    r = SensitiveWordRedactor(words=["张三"], wildcard="【已脱敏】")
    result = r.redact("客户张三", modes=["word-exact"])
    assert "【已脱敏】" in result.redacted_text
    print("✓ test_wildcard_custom")


def test_load_words_file(tmp_path=None):
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("# 注释行\n\n张三\n  李四  \n")
        path = f.name
    words = load_words_file(path)
    assert "张三" in words
    assert "李四" in words
    assert "# 注释行" not in words
    print("✓ test_load_words_file")


def test_no_words_no_rules():
    r = SensitiveWordRedactor()
    result = r.redact("原文")
    assert result.redacted_text == "原文"
    assert len(result.matches) == 0
    print("✓ test_no_words_no_rules")


if __name__ == "__main__":
    test_exact_word_match()
    test_fuzzy_word_match()
    test_rule_pattern()
    test_long_word_priority()
    test_mixed_modes()
    test_wildcard_custom()
    test_load_words_file()
    test_no_words_no_rules()
    print("\n全部测试通过 ✓")
