# 打包与发布

## 路径 A：macOS / Linux 开发 → Windows 发布

在 macOS / Linux 上**无法**直接生成 `.exe`（PyInstaller 需要目标平台的 libc）。

### A1: GitHub Actions 自动构建（推荐，本项目采用）

**已配置 2 个 workflow**（`.github/workflows/`）：

#### 1. `build-windows.yml` - Windows .exe 打包 + Release 发布

**触发条件**：
- 推送 `v*` tag（如 `v0.1.0`）→ 自动打包 + 创建 GitHub Release
- 手动触发（workflow_dispatch）→ 手动打包 + 可选发布

**使用步骤**：

```bash
# 1. 提交代码到 main 分支
git add .
git commit -m "feat: 完成 v0.1.0"
git push origin main

# 2. 创建 tag 触发自动构建
git tag v0.1.0
git push origin v0.1.0

# 3. GitHub Actions 自动：
#    - 运行单元测试
#    - PyInstaller 打包为 swp.exe
#    - 上传 artifact（无 tag 时只上传）
#    - 推送 tag 时创建 GitHub Release + 上传 zip
```

**手动触发**：
1. GitHub 仓库 → Actions → Build Windows EXE
2. Run workflow → 选 `publish_release=true`（可选创建 release）

#### 2. `ci-test.yml` - 多平台多版本测试

每次 push / PR 自动跑 3 平台 × 3 Python 版本的测试矩阵（9 组合）。

### A2: Wine + PyInstaller（不推荐，复杂）

需要先装 Wine + Python for Wine，配置繁琐，不推荐。

### A3: 直接在 Windows 上构建

最简单：把代码 push 到 GitHub，在 Windows VM / 物理机上：

```cmd
git clone <repo>
cd sensitive-words-packer
pip install -r requirements.txt
scripts\build_exe.bat
```

## 路径 B：Windows 端构建流程

### 步骤 1：准备环境

- 安装 Python 3.10+（勾选「Add to PATH」）
- 安装 NSIS 3.0+（添加到 PATH）
- 准备图标：`assets/icon.ico`（建议 256x256 多尺寸 ICO）

### 步骤 2：打包 .exe

```cmd
scripts\build_exe.bat
```

产物：`dist\swp.exe`（单文件，约 30-50 MB）

### 步骤 3：打 NSIS 安装包

1. 准备 `assets\installer.bmp`（侧栏图 164x314，24bit）
2. 准备 `assets\header.bmp`（顶部图 55x55，24bit）
3. 准备 `assets\icon.ico`（应用图标，多尺寸）
4. 执行：

```cmd
"C:\Program Files (x86)\NSIS\makensis.exe" scripts\installer.nsi
```

产物：`dist\Sensitive Words Packer-Setup-0.1.0.exe`（约 20-30 MB 压缩）

### 步骤 4：测试

把 Setup-*.exe 拷到干净的 Windows 10/11 虚拟机：
- 安装 → 桌面有快捷方式
- 开始菜单有「卸载」入口
- 双击 swp.exe → 弹窗或执行脱敏
- 控制面板「程序和功能」可卸载

## 跨平台兼容性

| 平台 | 状态 |
|------|------|
| Windows 10 | ✓ 已测试 |
| Windows 11 | ✓ 应兼容 |
| Windows 7 / 8 | △ PyInstaller 6.0 默认弃用 Win7，Win8 可用 Win7 兼容模式 |
| macOS | △ 仅 CLI 可用，打 .exe 需 Wine / CI |
| Linux | △ 仅 CLI 可用 |

## 代码签名（可选）

为避免 SmartScreen 警告，建议用代码签名证书：

```cmd
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com dist\swp.exe
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com "dist\Sensitive Words Packer-Setup-0.1.0.exe"
```

## 减小体积

- 用 UPX 压缩：`pyinstaller --upx-dir /path/to/upx ...`
- 排除未用模块：`pyinstaller --exclude-module matplotlib ...`
- 改用 PyInstaller 目录模式（`--onedir`）启动更快，体积差不多

## 常见错误

**Q：打包后 exe 报 "Failed to load python.dll"**
A：用 `--onedir` 模式而非 `--onefile`，或检查是否 32/64 位混用。

**Q：exe 启动慢（5-10 秒）**
A：`--onedir` 模式启动更快；或用 `nuitka` 替代 PyInstaller（编译型，启动 < 1 秒）。

**Q：docx 打包后报错 "No module named docx"**
A：确保 `--hidden-import docx --collect-all docx` 两项都加。
