# 文件管家 / FileCare

<div align="center">

**面向 Windows 的磁盘空间分析、文件管理与本地搜索工具**

[![Version](https://img.shields.io/badge/version-1.1.0-4a90e2.svg)](CHANGES.md)
[![Python](https://img.shields.io/badge/release%20runtime-Python%203.8-blue.svg)](requirements-win7.txt)
[![Platform](https://img.shields.io/badge/Windows-7%20SP1%20x64%2B-lightgrey.svg)](packaging/README.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

## 项目简介

文件管家是一款本地运行的 Windows 文件管理工具，适合希望直观查看磁盘占用、
快速定位文件并安全清理空间的用户。文件名索引和文档内容索引均保存在本机，
无需上传文件内容。

## 主要功能

- 文件管理：浏览、预览、复制路径及安全删除文件。
- 大文件清理：分析大文件、大文件夹和可解释的清理建议。
- 空间可视化：以 Treemap 展示目录中的文件与文件夹，可逐级下钻。
- 快速搜索：完整索引可访问的磁盘目录项，支持通配符、格式和路径过滤。
- 搜索结果操作：默认程序打开、选择打开方式、复制、剪切及打开所在目录。
- 内容搜索：本地检索 PDF、Word、Excel、PowerPoint、RTF 和常见文本文件。
- 回收站管理：查看、恢复或清理软件回收站中的项目。

## 普通用户安装

从 GitHub Releases 下载 `FileCare-Setup-1.1.0.exe`，双击后按向导安装即可，
不需要另行安装 Python 或其他运行环境。

安装器提供以下可选项：

- 创建桌面快捷方式；
- 创建开始菜单文件夹，内含启动入口和“卸载软件”入口。

安装过程中会以无边框动画卡片展示扫描效果，并以当前登录用户身份在最多约
20 秒内建立首批文件名索引。软件首次启动后会在后台继续补全其余索引。

## 系统要求

- Windows 7 SP1 64 位，或更新的 64 位 Windows；
- 建议至少 4 GB 内存；
- 未安装 SP1 的 Windows 7 和 32 位 Windows 暂不支持。

## 从源码运行

开发环境建议使用 64 位 Python 3.8.10，以便与发布构建保持一致：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-win7.txt
python src\main.py
```

日常开发若使用其他 Python 版本，可安装 `requirements.txt`；最终发布必须使用
`requirements-win7.txt` 中锁定的版本。

## 测试

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python test_win7_compatibility.py
python test_quick_search_completeness.py
python test_fulltext_search.py
python test_ui_smoke.py
```

测试不会删除用户真实文件；界面烟测使用隔离的临时回收站和测试用户目录。

## 构建安装包

```powershell
python -m PyInstaller --clean --noconfirm packaging\FileCare.spec
& "C:\Program Files\Inno Setup 7\ISCC.exe" packaging\FileCare.iss
```

生成的单文件安装包位于 `installer-output\FileCare-Setup-1.1.0.exe`。完整的
Win7 发布环境和验收要求见 [packaging/README.md](packaging/README.md)。

## 项目结构

```text
src/                    应用源代码
assets/                 图标与安装动画资源
packaging/              PyInstaller 与 Inno Setup 配置
tools/                  可重复生成资源的辅助工具
test_*.py               功能和兼容性回归测试
requirements.txt        日常开发依赖
requirements-win7.txt   Win7 发布锁定依赖
```

## 安全与隐私

- 索引数据库位于当前用户的 `~/.diskwise/` 目录。
- 扫描完成后不会自动删除文件。
- 永久删除操作需要用户明确确认，且不可恢复。
- 云盘、系统目录和程序目录会显示额外风险提示。

## 许可证

本项目采用 [MIT License](LICENSE)。问题和改进建议可通过 GitHub Issues 提交。
