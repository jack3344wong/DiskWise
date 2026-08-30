# 磁盘智理 / DiskWise

<div align="center">

**Windows 磁盘空间分析与智能文件搜索工具**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

</div>

## 📖 项目简介

磁盘智理是一款专为非技术背景办公人员设计的 Windows 磁盘管理工具。它集成了磁盘空间分析、快速文件搜索（类 Everything）、文档内容搜索（类 Anytxt）和文件预览等功能，帮助用户高效管理磁盘空间和快速定位文件。

## ✨ 核心功能

### 🔍 快速文件搜索（类 Everything）
- 基于 SQLite 的文件名索引系统
- 毫秒级搜索响应
- 支持通配符搜索（`*` 和 `?`）
- 支持路径前缀和多扩展名过滤
- 增量索引机制，只索引新增或修改的文件

### 📄 文档内容搜索（类 Anytxt）
- 基于 SQLite FTS5 的全文索引
- 支持 35 种文件格式（PDF、Word、Excel、PPT、TXT 等）
- 搜索结果高亮显示匹配片段
- 支持中文搜索（使用 LIKE 子串匹配）
- 启动时自动重建索引（后台执行）

### 👁️ 文件预览
- 点击文件即可预览内容
- 搜索关键词黄色背景高亮显示
- 支持多种文档格式预览

### 💾 磁盘空间分析
- 扫描大文件和大文件夹
- 识别文件来源软件与默认打开程序
- 给出保守的删除建议
- 云盘同步风险提示

### 🗑️ 回收站管理
- 安全的文件删除（移至回收站）
- 支持永久删除（需确认）
- 打开文件所在目录
- 复制文件路径

## 🖥️ 界面预览

### 主界面
- **工具栏导航**：首页、刷新、磁盘空间扫描、快速搜索、回收站管理
- **左侧文件浏览器**：磁盘/目录导航，文件列表
- **中央工作区**：文件详情/扫描结果/搜索结果
- **右侧预览面板**：文档内容预览（支持关键词高亮）
- **底部状态栏**：磁盘使用情况、当前目录信息

### 搜索界面
- **双标签页设计**：文件名搜索 / 内容搜索
- **实时搜索**：输入时自动触发（300ms 防抖）
- **搜索范围**：全局搜索 / 当前目录 / 选择目录
- **文件格式过滤**：文档/图片/视频/音频/压缩包/自定义
- **结果排序**：支持点击列头排序，列宽可调整

## 🚀 快速开始

### 环境要求
- Windows 10/11
- Python 3.11+
- Git（可选，用于版本控制）

### 安装步骤

#### 方式一：运行源码（推荐开发者）

1. **克隆仓库**
```bash
git clone https://github.com/jack3344wong/DiskWise.git
cd DiskWise
```

2. **创建虚拟环境**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行程序**
```bash
python src/main.py
```

#### 方式二：便携版（推荐普通用户）

1. 从 [Releases](https://github.com/jack3344wong/DiskWise/releases/latest) 页面下载：
   - **DiskWise-Setup-1.0.0.exe**（安装包，推荐）- 有安装向导，自动创建桌面快捷方式
   - **DiskWise-Portable-1.0.0.zip**（便携版）- 解压后运行 `DiskWise.exe`
2. 运行安装程序或解压后双击 `DiskWise.exe`

## 📦 打包发布

### 使用 PyInstaller 打包

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装 PyInstaller（如未安装）
pip install pyinstaller

# 打包
pyinstaller packaging/DiskWise.spec
```

打包完成后，可执行文件在 `dist/DiskWise/` 目录。

### 创建便携版 ZIP

```bash
cd dist
# Windows PowerShell
Compress-Archive -Path DiskWise -DestinationPath DiskWise-Portable-1.0.0.zip
```

## 🛠️ 技术栈

- **Python 3.11+** - 主要开发语言
- **PyQt5** - GUI 框架
- **SQLite** - 本地数据库（文件名索引 + FTS5 全文索引）
- **pypdf** - PDF 解析
- **python-docx** - Word 文档解析
- **openpyxl** - Excel 解析
- **python-pptx** - PowerPoint 解析
- **striprtf** - RTF 解析
- **psutil** - 系统信息获取

## 📁 项目结构

```
DiskWise_Project/
├── src/                          # 源代码
│   ├── main.py                   # 程序入口
│   ├── main_window.py            # 主窗口 UI
│   ├── quick_search.py           # 快速文件名搜索引擎
│   ├── fulltext_search.py        # 全文搜索引擎
│   ├── content_extractor.py      # 文档内容提取器
│   ├── disk_scanner.py           # 磁盘空间扫描
│   ├── file_association.py       # 文件关联识别
│   ├── file_operations.py        # 文件操作
│   ├── recycle_bin_ui.py         # 回收站 UI
│   └── web_search.py             # 网络搜索
├── assets/                       # 资源文件
│   └── diskwise.ico              # 应用图标
├── packaging/                    # 打包配置
│   └── DiskWise.spec             # PyInstaller 配置
├── requirements.txt              # Python 依赖
├── README.md                     # 项目说明
├── HANDOVER.md                   # 交接文档
└── .gitignore                    # Git 忽略规则
```

## 📝 使用说明

### 磁盘空间扫描
1. 点击工具栏"磁盘空间扫描"按钮
2. 选择扫描范围（当前目录/当前磁盘/选择目录）
3. 设置最小文件大小和最多显示数量
4. 点击"开始扫描"
5. 查看扫描结果：大文件、大文件夹、清理建议、垃圾文件

### 快速文件名搜索
1. 点击工具栏"快速搜索"按钮
2. 选择"📄 文件名搜索"标签页
3. 在搜索框输入关键词（支持通配符 `*` 和 `?`）
4. 实时显示搜索结果
5. 点击结果可预览文件内容

### 文档内容搜索
1. 点击工具栏"快速搜索"按钮
2. 选择"📖 内容搜索"标签页
3. 在搜索框输入关键词
4. 实时显示包含该关键词的文档
5. 点击结果可预览文档内容，关键词高亮显示

### 索引管理
- **刷新索引**：增量更新，只索引新增或修改的文件
- **重建索引**：删除旧索引并重新扫描所有文件
- **自动重建**：程序启动时自动在后台重建索引

## ⚠️ 安全说明

- 程序不会在扫描完成后自动删除文件
- 系统目录、软件目录和云盘同步目录会显示额外风险提示
- 永久删除不可恢复，请在确认备份和同步状态后使用
- 索引数据存储在 `~/.diskwise/` 目录，可安全删除

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Everything](https://www.voidtools.com/) - 快速文件搜索的灵感来源
- [Anytxt Searcher](https://anytxt.net/) - 文档内容搜索的灵感来源
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的 GUI 框架

## 📮 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。

---

<div align="center">

**Made with ❤️ for Windows Users**

</div>
