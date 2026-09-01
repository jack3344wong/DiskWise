# DiskWise 项目进度报告

**报告日期：** 2026年9月2日  
**项目版本：** v1.0.1（开发中）  
**项目路径：** `C:\Users\JackA\Desktop\DiskWise_Project`  
**GitHub 仓库：** https://github.com/jack3344wong/DiskWise

---

## 一、项目概述

DiskWise（磁盘智理）是一款面向非技术用户（文员）的 Windows 磁盘管理桌面工具，基于 **Python 3.14 + PyQt5 + SQLite** 开发。核心功能包括：

- 📊 磁盘空间扫描与可视化
- 🔍 文件名搜索（类 Everything）
- 📄 文档内容搜索（类 Anytxt）
- 🗑️ 回收站管理
- 📁 文件预览

---

## 二、已完成功能清单

### 2.1 核心功能（已完成 ✓）

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 磁盘空间扫描 | ✅ 已完成 | 扫描大文件、大文件夹、垃圾文件 |
| 空间可视化 (Treemap) | ✅ 已完成 | SpaceSniffer 风格，支持逐级下钻/返回 |
| 文件名搜索 | ✅ 已完成 | 实时搜索、SQLite 索引、结果排序 |
| 文件内容搜索 | ✅ 已完成 | PDF/DOCX/XLSX/PPTX/RTF 内容提取 |
| 文件预览 | ✅ 已完成 | 右侧面板预览文档内容 |
| 回收站管理 | ✅ 已完成 | 恢复/永久删除/清空 |
| 右键菜单 | ✅ 已完成 | Treemap 右键：打开/属性/复制/下钻 |
| 多语言支持 | ✅ 已完成 | 中文/英文切换 |

### 2.2 本次开发完成的任务（v1.0.1）

#### ✅ Bug 修复

| 编号 | 问题描述 | 修复方案 | 验证状态 |
|------|---------|---------|---------|
| BUG-001 | 文件名搜索"产业"返回0条结果 | 修复 SQL 参数插入顺序（`insert` → `append`） | ✅ 已验证 |

#### ✅ 新功能开发

| 编号 | 功能描述 | 涉及文件 | 状态 |
|------|---------|---------|------|
| FEAT-001 | Treemap 空间可视化（SpaceSniffer 风格） | `treemap_widget.py`（新建）, `disk_scanner.py`, `main_window.py` | ✅ 已完成 |
| FEAT-002 | Treemap 逐级下钻 + 返回上级 | `treemap_widget.py` | ✅ 已完成 |
| FEAT-003 | Treemap 右键菜单（打开/属性/复制/下钻） | `treemap_widget.py`, `main_window.py` | ✅ 已完成 |
| FEAT-004 | 文件删除权限提升（Windows Shell API） | `main_window.py` | ✅ 已完成 |

#### ✅ UI/UX 修复

| 编号 | 问题描述 | 修复方案 | 状态 |
|------|---------|---------|------|
| UX-001 | 返回上级按钮不响应 | 添加历史栈 + 导航信号 | ✅ 已修复 |
| UX-002 | 底部图例撞色看不清 | 分离色块与文字，使用深色文字 | ✅ 已修复 |
| UX-003 | Treemap 显示所有子项（无滚动条） | 移除 QScrollArea，自适应视口 | ✅ 已修复 |

---

## 三、技术架构

### 3.1 文件结构

```
DiskWise_Project/
├── src/
│   ├── main.py                 # 程序入口，单实例管理
│   ├── main_window.py          # 主窗口 UI（~1800行）
│   ├── treemap_widget.py       # Treemap 可视化组件（~420行）
│   ├── disk_scanner.py         # 磁盘扫描引擎
│   ├── quick_search.py         # 文件名搜索引擎
│   ├── fulltext_search.py      # 内容搜索引擎
│   ├── file_operations.py      # 文件操作（删除/回收站）
│   ├── file_association.py     # 文件关联识别
│   └── web_search.py           # 在线搜索集成
├── assets/                     # 图标资源
├── packaging/
│   ├── DiskWise.spec           # PyInstaller 打包配置
│   ├── DiskWise-OneFile.spec   # 单文件打包配置
│   └── DiskWise.iss            # Inno Setup 安装程序
├── ui_previews/                # Minimalism UI 预览图
│   ├── 01_home.html
│   ├── 02_search.html
│   ├── 03_scan.html
│   └── 04_recycle.html
├── requirements.txt
└── PROJECT_REPORT.md           # 本报告
```

### 3.2 关键技术点

| 技术点 | 实现方式 |
|--------|---------|
| Treemap 布局 | Squarified Treemap 算法 |
| 文件删除权限 | Windows `SHFileOperationW` API（自动弹出 UAC） |
| 文件索引 | SQLite FTS5 全文搜索 |
| 内容提取 | pypdf, python-docx, openpyxl, python-pptx, striprtf |
| 单实例管理 | `QLocalServer` + `QLocalSocket` |
| 打包 | PyInstaller（onefile）+ Inno Setup |

---

## 四、已知问题与待办事项

### 4.1 待优化项

| 优先级 | 问题 | 建议方案 |
|--------|------|---------|
| 🟡 中 | Treemap 大目录只显示少数大块，小块不可见 | 已完成：显示所有子项，自适应视口 |
| 🟡 中 | 内容搜索索引速度慢（首次 43s） | 增量更新已实现，可进一步优化 |
| 🟢 低 | 预览面板不支持视频/音频 | 可后续添加 |
| 🟢 低 | 无深色模式 | Minimalism 预览已设计，待实现 |

### 4.2 UI 优化方向

已生成 4 张 **Minimalism 风格** HTML 预览图：
- `01_home.html` — 首页：磁盘卡片 + 快捷操作
- `02_search.html` — 快速搜索：搜索栏 + 筛选芯片 + 结果列表
- `03_scan.html` — 空间可视化：Treemap 色块 + 图例
- `04_recycle.html` — 回收站管理：统计卡片 + 文件表格

**下一步：** 根据用户反馈选择是否将 Minimalism 风格应用到实际代码。

---

## 五、Git 状态

```
分支：master
最近提交：de0d3bc docs: 更新 README，添加 v1.0.1 更新日志
远程仓库：https://github.com/jack3344wong/DiskWise.git
标签：v1.0.0
```

### 未提交的本地修改：
- `src/quick_search.py` — 文件名搜索参数修复
- `src/treemap_widget.py` — 新建 Treemap 组件
- `src/disk_scanner.py` — 添加 folder_tree 层级数据
- `src/main_window.py` — Treemap 集成 + 权限修复
- `src/main.py` — 管理员权限启动处理
- `ui_previews/` — 4 张 UI 预览图
- `packaging/*.spec` — 打包配置

### Git 代理配置：
```
http.proxy = http://127.0.0.1:7897
https.proxy = http://127.0.0.1:7897
```

---

## 六、运行与打包

### 开发环境运行
```bash
cd C:\Users\JackA\Desktop\DiskWise_Project
.venv\Scripts\activate
python src\main.py
```

### 打包命令
```bash
# 单文件 exe（~58MB）
pyinstaller packaging\DiskWise-OneFile.spec

# 安装程序
pyinstaller packaging\DiskWise.spec
iscc packaging\DiskWise.iss
```

---

## 七、总结

DiskWise v1.0.1 已完成以下核心改进：
1. **文件名搜索 Bug 修复** — 搜索"产业"现在正确返回 12 条结果
2. **空间可视化 Treemap** — SpaceSniffer 风格，支持逐级下钻/返回/右键菜单
3. **删除权限提升** — 使用 Windows Shell API，无需重启程序
4. **UI 优化** — 修复返回按钮、图例撞色、滚动条问题
5. **Minimalism 预览** — 4 张全新 UI 设计方案

项目已具备发布 v1.0.1 的条件，建议用户测试后提交代码到 GitHub。
