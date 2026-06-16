"""deps.py 单元测试（不真装包，用 monkeypatch mock subprocess）"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from deps import (
    check_deps,
    missing_deps,
    install_deps,
    InstallError,
    REQUIRED_PACKAGES,
    MIRROR_INDEX_URL,
)


def test_check_deps_returns_dict():
    """check_deps 返回 dict，键覆盖全部 REQUIRED_PACKAGES"""
    report = check_deps()
    assert isinstance(report, dict)
    for pkg in REQUIRED_PACKAGES:
        assert pkg in report, f"缺少 {pkg}"
        assert isinstance(report[pkg], bool)
    print("✓ test_check_deps_returns_dict")


def test_missing_deps():
    """missing_deps 返回 list"""
    report = check_deps()
    miss = missing_deps(report)
    assert isinstance(miss, list)
    # 当前环境应该装好了 pypdf/reportlab/openpyxl（之前对话装过）
    # python-docx 也在之前对话装过
    # 但这取决于实际环境，只验证格式
    for pkg in miss:
        assert pkg in REQUIRED_PACKAGES
    print(f"✓ test_missing_deps  (missing: {miss})")


def test_install_empty_list_is_noop():
    """空列表不调 subprocess"""
    called = []
    def fake_popen(*a, **kw):
        called.append((a, kw))
    import deps as deps_mod
    orig = deps_mod.subprocess.Popen
    deps_mod.subprocess.Popen = fake_popen
    try:
        install_deps([])
        assert called == [], f"should not call Popen, got {called}"
        # 带 progress_cb
        install_deps([], progress_cb=lambda x: None)
        assert called == []
    finally:
        deps_mod.subprocess.Popen = orig
    print("✓ test_install_empty_list_is_noop")


def test_install_uses_mirror(monkeypatch=None):
    """install_deps(use_mirror=True) 应包含清华源参数"""
    captured_cmd = []

    class FakeProc:
        returncode = 0
        def __init__(self, cmd, **kw):
            captured_cmd.extend(cmd)
        def wait(self):
            pass
        @property
        def stdout(self):
            # 返回空迭代器（不真的读行）
            return iter([])

    import deps as deps_mod
    monkeypatch_obj = sys.modules.get("_pytest.monkeypatch")  # 简单方式：手动 patch
    orig = deps_mod.subprocess.Popen
    deps_mod.subprocess.Popen = FakeProc
    try:
        install_deps(["fake-pkg"], use_mirror=True)
        assert MIRROR_INDEX_URL in captured_cmd, f"未使用清华源: {captured_cmd}"
        assert "--trusted-host" in captured_cmd
        assert "fake-pkg" in captured_cmd
    finally:
        deps_mod.subprocess.Popen = orig
    print("✓ test_install_uses_mirror")


def test_install_no_mirror():
    """use_mirror=False 不加 -i 参数"""
    captured_cmd = []

    class FakeProc:
        returncode = 0
        def __init__(self, cmd, **kw):
            captured_cmd.extend(cmd)
        def wait(self):
            pass
        @property
        def stdout(self):
            return iter([])

    import deps as deps_mod
    orig = deps_mod.subprocess.Popen
    deps_mod.subprocess.Popen = FakeProc
    try:
        install_deps(["fake-pkg"], use_mirror=False)
        assert MIRROR_INDEX_URL not in captured_cmd, f"不应使用清华源: {captured_cmd}"
        assert "fake-pkg" in captured_cmd
    finally:
        deps_mod.subprocess.Popen = orig
    print("✓ test_install_no_mirror")


def test_install_failure_raises():
    """pip 返回非 0 抛 InstallError"""
    class FakeProc:
        returncode = 1
        def __init__(self, *a, **kw):
            pass
        def wait(self):
            pass
        @property
        def stdout(self):
            return iter(["ERROR: could not find fake-pkg\n"])

    import deps as deps_mod
    orig = deps_mod.subprocess.Popen
    deps_mod.subprocess.Popen = FakeProc
    try:
        try:
            install_deps(["fake-pkg"])
        except InstallError as e:
            assert e.returncode == 1
            assert "fake-pkg" in str(e) or "返回码" in str(e)
            print("✓ test_install_failure_raises")
            return
        raise AssertionError("expected InstallError")
    finally:
        deps_mod.subprocess.Popen = orig


def test_install_progress_callback():
    """progress_cb 应被多次调用"""
    lines = []

    class FakeProc:
        returncode = 0
        def __init__(self, *a, **kw):
            pass
        def wait(self):
            pass
        @property
        def stdout(self):
            return iter(["Collecting fake-pkg\n", "Installing fake-pkg\n"])

    import deps as deps_mod
    orig = deps_mod.subprocess.Popen
    deps_mod.subprocess.Popen = FakeProc
    try:
        install_deps(["fake-pkg"], progress_cb=lines.append)
        assert any("Collecting" in l for l in lines)
        assert any("Installing" in l for l in lines)
        assert any("[完成]" in l for l in lines)
        print(f"✓ test_install_progress_callback  ({len(lines)} lines)")
    finally:
        deps_mod.subprocess.Popen = orig


if __name__ == "__main__":
    test_check_deps_returns_dict()
    test_missing_deps()
    test_install_empty_list_is_noop()
    test_install_uses_mirror()
    test_install_no_mirror()
    test_install_failure_raises()
    test_install_progress_callback()
    print("\n全部 deps 测试通过 ✓")
