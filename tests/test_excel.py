"""Excel 词表模块测试"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import openpyxl
from excel_handler import load_excel_words


def _make_xlsx(path, rows, sheet_name="Sheet1"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    wb.save(path)


def test_simple_first_column():
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["# 注释"],
        [],
        ["张三"],
        ["李四"],
        ["王五"],
    ])
    words = load_excel_words(path)
    assert words == ["张三", "李四", "王五"]
    print("✓ test_simple_first_column")


def test_header_row_auto_skip():
    """首行是表头 → 自动跳过"""
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["姓名", "部门", "敏感词"],
        ["张三", "市场", "张三"],
        ["李四", "财务", "李四"],
    ])
    # 默认取第 1 列（"姓名"）的"张三" "李四" 也算（都是字符串）
    # 但因为首行是 header 应跳过，所以是 "张三", "李四"
    words = load_excel_words(path)
    assert words == ["张三", "李四"]
    print("✓ test_header_row_auto_skip")


def test_named_column():
    """按列名取"""
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["姓名", "部门", "敏感词"],
        ["张三", "市场", "secretA"],
        ["李四", "财务", "secretB"],
    ])
    words = load_excel_words(path, column="敏感词")
    assert words == ["secretA", "secretB"]
    print("✓ test_named_column")


def test_letter_column():
    """按列字母取"""
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["A 列", "B 列", "C 列"],
        ["a1", "b1", "c1"],
        ["a2", "b2", "c2"],
    ])
    words = load_excel_words(path, column="C")
    assert words == ["c1", "c2"]
    print("✓ test_letter_column")


def test_index_column():
    """按列号取"""
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["# 标题行"],
        ["x", "y", "z"],
        ["1", "2", "3"],
    ])
    # 标题行只有 1 列非空，仍是字符串 header → 自动跳过
    words = load_excel_words(path, column=2)  # 第 3 列
    assert words == ["z", "3"]
    print("✓ test_index_column")


def test_dedup():
    with __import__("tempfile").NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _make_xlsx(path, [
        ["张三"],
        ["张三"],
        ["李四"],
    ])
    words = load_excel_words(path)
    assert words == ["张三", "李四"]
    print("✓ test_dedup")


def test_missing_file():
    assert load_excel_words("/nonexistent/file.xlsx") == []
    print("✓ test_missing_file")


if __name__ == "__main__":
    test_simple_first_column()
    test_header_row_auto_skip()
    test_named_column()
    test_letter_column()
    test_index_column()
    test_dedup()
    test_missing_file()
    print("\n全部 Excel 测试通过 ✓")
