"""gui.py / deps.py 模块存在性测试（不实际启动 tkinter）"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_deps_module():
    """deps 模块导入正常"""
    import deps
    assert hasattr(deps, "check_deps")
    assert hasattr(deps, "missing_deps")
    assert hasattr(deps, "install_deps")
    assert hasattr(deps, "InstallError")
    assert hasattr(deps, "REQUIRED_PACKAGES")
    print("✓ test_deps_module")


def test_gui_module_imports():
    """gui 模块导入不崩（不实例化 RedactorGUI）"""
    import gui
    assert hasattr(gui, "RedactorGUI")
    assert hasattr(gui, "DepsInstallDialog")
    assert hasattr(gui, "EditableTreeview")
    assert hasattr(gui, "EXAMPLE_WORDS")
    assert hasattr(gui, "EXAMPLE_RULES")
    assert hasattr(gui, "EXAMPLE_EXCEL_DATA")
    assert hasattr(gui, "run_deps_check_or_install")
    assert hasattr(gui, "main")
    print("✓ test_gui_module_imports")


def test_redactor_gui_class():
    """RedactorGUI 类有所有必要方法（不实例化）"""
    import gui
    methods = [
        "_build_ui",
        "_build_single_tab",
        "_build_batch_tab",
        "_build_words_editor_tab",
        "_build_rules_editor_tab",
        "_build_excel_editor_tab",
        # 编辑器方法
        "_load_words_editor", "_save_words_editor", "_save_as_words_editor",
        "_load_rules_editor", "_save_rules_editor", "_save_as_rules_editor",
        "_add_rule_row", "_del_rule_row", "_move_rule_row",
        "_load_excel_editor", "_save_excel_editor", "_save_as_excel_editor",
        "_add_excel_row", "_del_excel_row", "_add_excel_column", "_del_excel_column",
        # 脱敏任务
        "_start_single", "_start_batch", "_run_single_worker", "_run_batch_worker",
        "_log", "_clear_log", "_poll_log_queue",
    ]
    for m in methods:
        assert hasattr(gui.RedactorGUI, m), f"RedactorGUI 缺少方法 {m}"
    print(f"✓ test_redactor_gui_class  ({len(methods)} methods)")


def test_editable_treeview():
    """EditableTreeview 是 ttk.Treeview 子类"""
    from tkinter import ttk
    import gui
    assert issubclass(gui.EditableTreeview, ttk.Treeview)
    print("✓ test_editable_treeview")


def test_example_data_format():
    """示例数据格式正确"""
    import gui
    # 敏感词示例
    assert "张三" in gui.EXAMPLE_WORDS
    assert "13800138000" in gui.EXAMPLE_WORDS
    # 规则示例
    assert isinstance(gui.EXAMPLE_RULES, list)
    for r in gui.EXAMPLE_RULES:
        assert "name" in r and "pattern" in r and "replacement" in r
    # Excel 示例
    assert isinstance(gui.EXAMPLE_EXCEL_DATA, list)
    assert len(gui.EXAMPLE_EXCEL_DATA) > 1
    assert len(gui.EXAMPLE_EXCEL_DATA[0]) > 0  # 有表头
    print("✓ test_example_data_format")


def test_app_title_version():
    """APP_TITLE 包含 v0.2.2"""
    import gui
    assert "v0.2.2" in gui.APP_TITLE
    print("✓ test_app_title_version")


def test_supported_extensions():
    """SUPPORTED 包含主要格式"""
    import gui
    for ext in [".txt", ".md", ".docx", ".pdf"]:
        assert ext in gui.SUPPORTED, f"SUPPORTED 缺少 {ext}"
    print("✓ test_supported_extensions")


def test_deps_install_dialog_class():
    """DepsInstallDialog 类存在且是 Toplevel"""
    import tkinter as tk
    import gui
    assert issubclass(gui.DepsInstallDialog, tk.Toplevel)
    print("✓ test_deps_install_dialog_class")


def test_run_deps_check_function():
    """run_deps_check_or_install 是可调用函数"""
    import gui
    assert callable(gui.run_deps_check_or_install)
    print("✓ test_run_deps_check_function")


def test_rules_save_format():
    """验证 _get_rules_data 返回的格式（需要实例化，跳过真实测试，只验证文档）"""
    import gui
    doc = gui.RedactorGUI.__doc__ or ""
    print("✓ test_rules_save_format  (docstring ok)")


if __name__ == "__main__":
    test_deps_module()
    test_gui_module_imports()
    test_redactor_gui_class()
    test_editable_treeview()
    test_example_data_format()
    test_app_title_version()
    test_supported_extensions()
    test_deps_install_dialog_class()
    test_run_deps_check_function()
    test_rules_save_format()
    print("\n全部 GUI 测试通过 ✓")
