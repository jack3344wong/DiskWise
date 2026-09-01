# DiskWise 项目交接提示词

> **使用说明：** 将以下内容完整复制到新的聊天窗口中，即可继续项目开发。

---

## 复制以下内容到新聊天窗口：

```
我正在开发一个 Windows 桌面应用 DiskWise（磁盘智理），基于 Python 3.14 + PyQt5 + SQLite。

项目路径：C:\Users\JackA\Desktop\DiskWise_Project

请先阅读以下文件了解项目当前状态：
1. PROJECT_REPORT.md — 完整的进度报告
2. ui_previews/ 目录下的 4 张 HTML 预览图（01_home.html ~ 04_recycle.html）

当前已完成的核心工作：
✅ 文件名搜索 Bug 修复（SQL 参数顺序问题）
✅ Treemap 空间可视化（SpaceSniffer 风格，支持逐级下钻）
✅ 文件删除权限提升（使用 Windows SHFileOperationW API，无需重启）
✅ UI 修复（返回按钮、图例撞色、滚动条）
✅ 4 张 Minimalism 风格 UI 预览图

接下来需要做的工作（按优先级）：

1. 【测试验证】运行程序测试以下功能：
   - 文件名搜索"产业"是否返回正确结果
   - 磁盘扫描 → 空间可视化 → 点击下钻 → 返回上级
   - 右键 Treemap 色块 → 打开/属性/复制
   - 删除受保护文件时是否弹出 UAC 权限提示（不重启程序）

2. 【UI 决策】查看 ui_previews/ 下的 4 张 Minimalism 预览图，决定是否：
   - 采纳 Minimalism 风格并应用到实际代码
   - 保持当前 UI 风格
   - 部分采纳某些设计元素

3. 【代码提交】如果测试通过，提交代码到 GitHub：
   - Git 代理已配置：http.proxy = http://127.0.0.1:7897
   - 远程仓库：https://github.com/jack3344wong/DiskWise.git
   - 建议提交信息："feat: Treemap 可视化 + 权限修复 + UI 优化 (v1.0.1)"

4. 【打包发布】使用 PyInstaller 打包：
   - 单文件：pyinstaller packaging\DiskWise-OneFile.spec
   - 安装程序：pyinstaller packaging\DiskWise.spec && iscc packaging\DiskWise.iss

5. 【后续优化】（可选）
   - 内容搜索索引速度优化
   - 视频/音频预览支持
   - 深色模式
   - 其他用户反馈的 Bug

请先阅读 PROJECT_REPORT.md，然后告诉我你准备好了，我们再开始下一步。
```

---

## 快速参考信息

### 项目结构
```
DiskWise_Project/
├── src/                    # 源代码
│   ├── main.py
│   ├── main_window.py
│   ├── treemap_widget.py   # 新增
│   ├── disk_scanner.py
│   ├── quick_search.py     # 已修复
│   └── fulltext_search.py
├── ui_previews/            # UI 预览图
├── packaging/              # 打包配置
└── PROJECT_REPORT.md       # 进度报告
```

### 关键修改文件
- `src/quick_search.py` — 第 85-86 行 SQL 参数修复
- `src/treemap_widget.py` — 全新 Treemap 组件（420 行）
- `src/main_window.py` — Treemap 集成 + Shell API 删除
- `src/disk_scanner.py` — 添加 folder_tree 数据
- `src/main.py` — 管理员权限启动处理

### 运行命令
```bash
cd C:\Users\JackA\Desktop\DiskWise_Project
.venv\Scripts\activate
python src\main.py
```

### Git 信息
- 分支：master
- 远程：https://github.com/jack3344wong/DiskWise.git
- 代理：http://127.0.0.1:7897

### 已知问题
- Treemap 大目录只显示大块（已优化：显示所有子项）
- 内容搜索首次索引较慢（43s，已优化增量更新）

---

**提示：** 将此文件和新聊天窗口一起保存，方便随时查阅。
