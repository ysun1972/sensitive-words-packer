"""
依赖检查与自动安装（纯标准库实现）

被 GUI 启动时调用，避免用户没装 python-docx / pypdf / reportlab / openpyxl
时直接报 ModuleNotFoundError。

设计要点：
- 纯标准库（subprocess + importlib.util.find_spec），不依赖 pip API
- 默认走清华源，国内安装速度友好
- 实时把 pip 输出通过 progress_cb 回调给 GUI
- 失败抛 InstallError，包含 pip 返回码与最后一段 stderr
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from typing import Callable, Optional


# 这 4 个包是 requirements.txt 里的核心依赖
REQUIRED_PACKAGES: list[str] = [
    "python-docx",
    "pypdf",
    "reportlab",
    "openpyxl",
]

# 清华源（中国大陆常用；海外会被自动回退到 PyPI）
MIRROR_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
MIRROR_TRUSTED_HOST = "pypi.tuna.tsinghua.edu.cn"

ProgressCallback = Optional[Callable[[str], None]]


class InstallError(RuntimeError):
    """pip 安装失败时抛出"""

    def __init__(self, returncode: int, message: str):
        self.returncode = returncode
        super().__init__(
            f"pip 安装失败（返回码 {returncode}）: {message.strip()[:500]}"
        )


# pip 包名 → Python import 名 的映射
_PKG_TO_IMPORT = {
    "python-docx": "docx",
    "pypdf": "pypdf",
    "reportlab": "reportlab",
    "openpyxl": "openpyxl",
}


def _import_name(pkg: str) -> str:
    return _PKG_TO_IMPORT.get(pkg, pkg)


def check_deps() -> dict[str, bool]:
    """
    检查必需依赖是否已安装。

    Returns:
        dict[str, bool]: 包名 -> 是否已安装
        例：{"python-docx": True, "pypdf": False, "reportlab": True, "openpyxl": True}
    """
    result: dict[str, bool] = {}
    for pkg in REQUIRED_PACKAGES:
        # find_spec 不需要真正 import，缺失时返回 None
        try:
            result[pkg] = importlib.util.find_spec(_import_name(pkg)) is not None
        except (ImportError, ValueError):
            result[pkg] = False
    return result


def missing_deps(report: dict[str, bool] | None = None) -> list[str]:
    """返回缺失包列表（按 REQUIRED_PACKAGES 顺序）"""
    report = report or check_deps()
    return [pkg for pkg in REQUIRED_PACKAGES if not report.get(pkg, False)]


def install_deps(
    missing: list[str],
    progress_cb: ProgressCallback = None,
    use_mirror: bool = True,
) -> None:
    """
    用 subprocess 调 pip 安装缺失包。

    Args:
        missing: 需要安装的包名列表
        progress_cb: 进度回调，传入 pip 的每一行输出
        use_mirror: True=走清华源；False=走默认 PyPI

    Raises:
        InstallError: pip 返回非 0 时
        FileNotFoundError: 系统找不到 python/pip 时
    """
    if not missing:
        return

    def emit(line: str) -> None:
        if progress_cb:
            try:
                progress_cb(line)
            except Exception:
                # 回调里出错不能影响安装
                pass

    # 构造命令：python -m pip install [-i 清华源 --trusted-host] <pkg>...
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if use_mirror:
        cmd += ["-i", MIRROR_INDEX_URL, "--trusted-host", MIRROR_TRUSTED_HOST]
    cmd += list(missing)

    emit(f"$ {' '.join(cmd)}")

    # Windows 下默认编码可能是 cp936/cp1252，强制 UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        # 用 Popen 实时拿输出；unbuffered + 文本模式
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并到 stdout
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"找不到 python 可执行文件: {sys.executable}\n"
            f"请确认 Python 已安装并加入 PATH。原始错误: {e}"
        )

    assert proc.stdout is not None
    last_lines: list[str] = []
    for line in proc.stdout:
        line = line.rstrip()
        emit(line)
        last_lines.append(line)
        # 保留最后 20 行用于错误报告
        if len(last_lines) > 20:
            last_lines.pop(0)

    proc.wait()
    if proc.returncode != 0:
        raise InstallError(
            returncode=proc.returncode or -1,
            message="\n".join(last_lines) or "无输出",
        )

    emit(f"[完成] {len(missing)} 个包安装成功")
