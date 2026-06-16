"""批量任务模块测试"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from batch import load_batch_config, run_task, BatchTask


def _write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_load_config():
    cfg = {
        "tasks": [
            {"name": "t1", "input": "a", "output": "b", "words": "w.txt", "mode": "exact,rule"},
            {"name": "t2", "input": "c", "output": "d", "rules": "r.json", "mode": "rule"},
        ]
    }
    with __import__("tempfile").NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(cfg, f)
        path = f.name

    tasks = load_batch_config(path)
    assert len(tasks) == 2
    assert tasks[0].name == "t1"
    assert tasks[0].mode == "exact,rule"
    assert tasks[0].wildcard == "***"
    assert tasks[1].rules == "r.json"
    print("✓ test_load_config")


def test_load_config_array():
    """直接数组结构（无 tasks 键）"""
    cfg = [
        {"name": "t1", "input": "a", "output": "b"},
    ]
    with __import__("tempfile").NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(cfg, f)
        path = f.name
    tasks = load_batch_config(path)
    assert len(tasks) == 1
    print("✓ test_load_config_array")


def test_run_task_basic(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 输入文件
        in_dir = tmp / "in"
        in_dir.mkdir()
        _write(in_dir / "doc.txt", "张三和李四参加了会议。")
        # 敏感词
        words = tmp / "words.txt"
        _write(words, "张三\n李四\n")
        # 任务
        task = BatchTask(
            name="basic",
            input=str(in_dir),
            output=str(tmp / "out"),
            words=str(words),
            mode="exact,rule",
            wildcard="***",
        )
        result = run_task(task)
        assert result.status == "ok", f"task failed: {result.error}"
        assert result.files == 1
        assert result.matches == 2
        # 检查输出
        out = tmp / "out" / "doc.txt"
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "张三" not in content
        assert "李四" not in content
        assert "***" in content
        print("✓ test_run_task_basic")


def test_run_task_missing_input():
    task = BatchTask(
        name="missing",
        input="/nonexistent/path",
        output="/tmp/should/not/be/created",
        words="x",
    )
    result = run_task(task)
    assert result.status == "error"
    assert "不存在" in result.error
    print("✓ test_run_task_missing_input")


def test_run_task_no_config():
    """没提供任何词/规则 → 错误"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        in_dir = tmp / "in"
        in_dir.mkdir()
        _write(in_dir / "x.txt", "hello")
        task = BatchTask(
            name="empty",
            input=str(in_dir),
            output=str(tmp / "out"),
        )
        result = run_task(task)
        assert result.status == "error"
        assert "至少" in result.error
        print("✓ test_run_task_no_config")


def test_run_task_custom_wildcard():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        in_dir = tmp / "in"
        in_dir.mkdir()
        _write(in_dir / "x.txt", "张三 ok")
        words = tmp / "w.txt"
        _write(words, "张三\n")
        task = BatchTask(
            name="wc",
            input=str(in_dir),
            output=str(tmp / "out"),
            words=str(words),
            wildcard="【已脱敏】",
        )
        result = run_task(task)
        assert result.status == "ok"
        out = (tmp / "out" / "x.txt").read_text(encoding="utf-8")
        assert "【已脱敏】" in out
        print("✓ test_run_task_custom_wildcard")


if __name__ == "__main__":
    test_load_config()
    test_load_config_array()
    test_run_task_basic()
    test_run_task_missing_input()
    test_run_task_no_config()
    test_run_task_custom_wildcard()
    print("\n全部批量任务测试通过 ✓")
