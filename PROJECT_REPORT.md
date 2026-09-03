# FileCare（文件管家）项目进度报告

**报告日期：** 2026年9月2日

**项目版本：** v1.1.0（可发布构建）

**项目路径：** `C:\Users\Jack\Desktop\diskwise_project`

**GitHub 仓库：** https://github.com/jack3344wong/diskwise

---

## 一、项目概述

**文件管家 / FileCare**是一款面向非技术用户（体制内文员）的 Windows 文件管理桌面工具，基于 **Python + PyQt5 + SQLite** 开发；Win7 发布构建固定使用 64 位 Python 3.8.10。核心功能包括：

- 🧹 大文件清理（扫描大文件/文件夹，提供清理建议）
- 📊 空间可视化（Treemap 风格，显示所有文件和文件夹）
- 🔍 文件名搜索（类 Everything，实时搜索）
- 📄 文档内容搜索（类 Anytxt，PDF/Word/Excel/PPT）
- 🗑️ 回收站管理（恢复/永久删除）

**目标用户：** 体制内工作人员，不熟悉技术，需要简单直观的文件管理工具。

---

## 二、v1.1.0 版本更新（2026-09-02）

### 2.1 品牌升级

| 变更项 | 旧值 | 新值 |
|--------|------|------|
| 软件名称 | 文件管家 / FileCare | **文件管家 / FileCare** |
| 图标 | 磁盘相关图标 | 蓝色文件夹 + 橙色放大镜（方案二） |
| 定位 | 磁盘空间分析工具 | 文件管理 + 空间清理工具 |

**图标设计说明：**
- 蓝色渐变文件夹（稳重，符合体制内审美）
- 白色文件卡片 + 蓝色线条（表示文档）
- 金色星点装饰
- 橙色放大镜（表示查找功能）

### 2.2 功能拆分

将原"磁盘空间扫描"功能拆分为两个独立模块：

#### 🧹 大文件清理
- **目的：** 有针对性地清理大文件
- **功能：**
  - 设置大小阈值（默认 100MB）
  - 设置显示数量限制（默认 100 个）
  - 4 个标签页：大文件、大文件夹、清理建议、垃圾文件
  - 提供删除/移至回收站操作
- **扫描参数：** `threshold_mb=100`, `top_n=100`

#### 📊 空间可视化
- **目的：** 直观查看所有文件和文件夹的占用情况
- **功能：**
  - 无大小阈值限制（显示所有文件）
  - 无数量限制（显示所有文件夹）
  - Treemap 可视化，支持逐级下钻
  - 右键菜单：打开文件夹、查看属性、复制路径
- **扫描参数：** `threshold_mb=0.001`（约 1KB），`top_n=100000`

### 2.3 Bug 修复

| 编号 | 问题描述 | 修复方案 | 状态 |
|------|---------|---------|------|
| BUG-001 | 点击"快速搜索"跳转到空间可视化 | 修复导航索引：快速搜索 3→4，回收站 4→5 | ✅ 已修复 |
| BUG-002 | 点击"回收站管理"跳转到快速搜索 | 同上 | ✅ 已修复 |
| BUG-003 | Treemap 下钻时程序闪退 | 将递归实现改为迭代（显式栈），避免深目录爆栈 | ✅ 已修复 |
| BUG-004 | 空间可视化只显示部分文件夹 | 保留所有扫描节点，空目录/无权限节点使用最小可见布局尺寸，并增加回归测试 | ✅ 已修复 |

### 2.4 技术优化

| 优化项 | 说明 |
|--------|------|
| Treemap 布局算法 | 从递归改为迭代，支持 20000+ 子项不闪退 |
| 大目录聚合 | 超过 3000 子项时聚合为"其他 N 项"，防止卡顿 |
| 隐藏文件显示 | 确保所有文件（含隐藏）都进入可视化树 |
| 扫描性能 | 20000 子项布局 0.7s，5000 子项聚合保护 0.03s |

### 2.5 快速搜索与安装流程

- 文件名索引覆盖所有本地磁盘可访问项目，支持隐藏文件、取消后继续和陈旧索引清理。
- 双击搜索结果使用默认程序打开；右键提供打开、选择打开方式、复制、剪切等操作。
- 安装阶段仅建立约 20 秒的首批索引，未完成部分由首次启动后台继续建立。
- 安装器动画在向导内部播放，使用预加载换帧降低闪烁；任务栏、桌面快捷方式和开始菜单入口使用 FileCare 图标。
- 安装器提供桌面快捷方式、开始菜单文件夹及“卸载软件”入口的可选项。

---

## 三、当前文件结构

```
diskwise_project/
├── src/
│   ├── main.py                    # 程序入口
│   ├── main_window.py             # 主窗口（~2600行）
│   ├── treemap_widget.py          # Treemap 可视化组件（~445行）
│   ├── disk_scanner.py            # 磁盘扫描引擎
│   ├── quick_search.py            # 文件名搜索
│   ├── fulltext_search.py         # 内容搜索
│   ├── file_operations.py         # 文件操作
│   ├── file_association.py        # 文件关联识别
│   └── web_search.py              # 在线搜索
├── assets/
│   ├── filecare.ico               # 应用图标（多尺寸）
│   ├── filecare-256.png           # 256px 图标
│   └── filecare-logo.png          # Logo
├── packaging/
│   ├── FileCare.spec              # PyInstaller 配置
│   └── FileCare.iss               # Inno Setup 安装程序
├── test_*.py                      # 测试文件
├── requirements.txt
├── PROJECT_REPORT.md              # 本报告
└── HANDOFF_PROMPT.md              # Codex 交接文档
```

---

## 四、空间可视化问题处理结果

### 🔴 高优先级：空间可视化显示不全

历史上 C:\ 根目录和 C:\Users 下的空目录、隐藏目录或无权限目录曾因尺寸过小/扫描异常没有形成可见色块。

当前已保留所有扫描节点，并为零大小或无权限节点提供最小可见布局尺寸；`test_treemap_visibility.py` 已验证模拟 C:\ 根目录 22 项和 Users 下 3 项均进入布局且可见，`test_hidden_files.py` 已验证隐藏文件/文件夹进入树结构。

权限不足的目录会保留节点，并显示“无法访问，未统计内容”状态。后续改动应先运行上述两个可视化回归测试。

**建议的解决方案方向：**
1. 在 `_layout()` 中，给 0 大小项更大的虚拟尺寸（如 1000 字节）
2. 在 `paintEvent()` 中，确保最小色块也能渲染（至少 20x20 像素）
3. 对 0 大小项添加特殊标识（如"空文件夹"或"无权限"）
4. 检查 `disk_scanner.py` 中的权限处理逻辑，确保错误被正确记录

**相关代码位置：**
- `src/treemap_widget.py:282-284` - 虚拟尺寸设置
- `src/treemap_widget.py:325-327` - 渲染过滤逻辑
- `src/disk_scanner.py:136-158` - 目录遍历和权限处理

---

## 五、技术架构

### 5.1 页面栈结构

```
_main_stack (QStackedWidget)
├── index 0: 首页 (_home_page)
├── index 1: 文件管理 (_browse_page)
├── index 2: 大文件清理 (_scan_page)
├── index 3: 空间可视化 (_visualization_page)
├── index 4: 快速搜索 (_search_page)
└── index 5: 回收站管理 (_recycle_page)
```

### 5.2 导航方法索引

```python
_show_home_view()         → setCurrentIndex(0)
_show_browse_view()       → setCurrentIndex(1)
_show_scan_view()         → setCurrentIndex(2)
_show_visualization_view()→ setCurrentIndex(3)
_show_search_view()       → setCurrentIndex(4)
_show_recycle_view()      → setCurrentIndex(5)
```

### 5.3 Treemap 关键技术

| 技术点 | 实现方式 |
|--------|---------|
| 布局算法 | Squarified Treemap（迭代实现） |
| 下钻/返回 | 历史栈 `_history` |
| 大目录保护 | 超过 3000 子项聚合为"其他 N 项" |
| 颜色映射 | 按大小分 5 档（>10GB, 1-10GB, 100MB-1GB, 10-100MB, <10MB） |

---

## 六、运行与测试

### 6.1 开发环境运行

```bash
cd C:\Users\Jack\Desktop\diskwise_project
python src/main.py
```

### 6.2 运行测试

```bash
# 布局算法测试
python test_squarify_check.py

# 端到端测试
python test_e2e_treemap.py

# UI 冒烟测试
python test_ui_smoke.py

# 压力测试
python test_treemap_stress.py

# 隐藏文件测试
python test_hidden_files.py
python test_treemap_visibility.py
python test_quick_search_completeness.py
python test_fulltext_search.py
python test_win7_compatibility.py
```

### 6.3 打包命令

```bash
# 单文件 exe
pyinstaller packaging/FileCare-OneFile.spec

# 安装程序
pyinstaller packaging/FileCare.spec
iscc packaging/FileCare.iss
```

当前安装包：`installer-output\\FileCare-Setup-1.1.0.exe`；SHA-256：
`291FD4CD772FAC4C27D4F49A7DB9EA625E8E2F706CA63A3937D8C78A5AA5B479`。

---

## 七、Git 状态

```
分支：master
最近提交：以当前工作区为准（改名与发布构建尚未提交）
远程仓库：https://github.com/jack3344wong/diskwise.git
```

### 未提交的修改

- `src/main.py` - 应用标识、图标和英文名统一为 FileCare
- `src/main_window.py` - 功能拆分 + 导航修复
- `src/treemap_widget.py` - 迭代布局 + 虚拟尺寸优化
- `src/disk_scanner.py` - 显示所有文件
- `assets/filecare.ico` - 新图标
- `assets/filecare-256.png` - 新图标
- `assets/filecare-logo.png` - 新图标
- `packaging/FileCare.iss` - FileCare 安装器、动画与索引阶段
- `installer-output/FileCare-Setup-1.1.0.exe` - 已生成的安装包（被 gitignore 忽略）

### Git 代理配置

```
http.proxy = http://127.0.0.1:7897
https.proxy = http://127.0.0.1:7897
```

---

## 八、下一步计划

### 8.1 交接后的建议工作

1. **在干净的 Windows 7 SP1 x64 环境验收**：安装、启动、索引续建、快速搜索、空间可视化和卸载。

2. **优化空间可视化体验**
   - 下钻时路径框和状态栏同步更新
   - 添加加载进度提示
   - 优化大目录的渲染性能

3. **测试与发布**
   - 全面测试所有功能
   - 提交代码到 GitHub
   - 打包发布 v1.1.0

### 8.2 未来规划

- [ ] 深色模式
- [ ] 文件去重检测
- [ ] 云盘同步风险提示
- [ ] 更多文件类型预览支持

---

## 九、总结

**v1.1.0 已完成：**
1. ✅ 品牌升级：磁盘智理 → 文件管家 / FileCare
2. ✅ 图标更新：方案二（蓝色文件夹 + 橙色放大镜）
3. ✅ 功能拆分：大文件清理 + 空间可视化
4. ✅ 导航修复：快速搜索和回收站索引
5. ✅ Treemap 优化：迭代布局，支持大目录
6. ✅ 隐藏文件：确保所有文件都显示
7. ✅ 快速搜索完整性、搜索结果操作和索引续建
8. ✅ Win7 SP1 x64 发布构建与 FileCare 安装包

**发布前建议：**
- 在干净的 Windows 7 SP1 x64 环境进行最终安装、启动、索引和卸载验收。

项目已具备发布 v1.1.0 的基础条件；安装包已生成，正式发布前建议完成 Win7 SP1 x64 干净环境验收。
