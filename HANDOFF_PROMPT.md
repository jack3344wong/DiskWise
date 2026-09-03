# Codex 交接文档 - FileCare（文件管家）项目

## 项目背景

**文件管家**是一款面向体制内非技术用户的 Windows 文件管理工具，目标是帮助用户：
1. 清理大文件和垃圾文件
2. 可视化查看磁盘空间占用
3. 快速搜索文件

技术栈：Python + PyQt5 + SQLite。Win7 发布构建固定使用 64 位 Python 3.8.10。

---

## 当前状态

### ✅ 已完成功能

1. **品牌升级**
   - 软件名：磁盘智理 → 文件管家
   - 图标：蓝色文件夹 + 橙色放大镜（方案二）

2. **功能拆分**
   - **大文件清理**：有阈值（100MB）和数量限制（100个），用于清理
   - **空间可视化**：无限制，显示所有文件和文件夹

3. **Bug 修复**
   - 导航索引错误（快速搜索/回收站跳转错误）
   - Treemap 下钻闪退（递归改迭代）

4. **性能优化**
   - Treemap 布局算法改为迭代实现
   - 支持 20000+ 子项不闪退
   - 大目录聚合保护（>3000 项聚合为"其他 N 项"）

5. **发布与安装**
   - 软件英文名、窗口标题、EXE、图标和安装器已统一为 FileCare。
   - 安装器内嵌预加载动画，安装阶段索引约 20 秒，首次启动后台继续完成剩余索引。
   - 支持可选桌面快捷方式、开始菜单文件夹和“卸载软件”入口。
   - 已生成 `installer-output/FileCare-Setup-1.1.0.exe`，当前电脑上的旧安装已卸载。

---

## 空间可视化问题处理结果

历史问题：空间可视化曾漏显示空目录、隐藏目录和无权限目录。

当前已保留所有扫描节点，并为零大小或无权限节点提供最小可见布局尺寸。

`test_treemap_visibility.py` 与 `test_hidden_files.py` 已通过，验证模拟根目录 22 项和 Users 下 3 项均进入布局且可见。

**根本原因分析：**

1. **权限问题**
   - 某些系统文件夹（如 `$Recycle.Bin`、`System Volume Information`）因权限不足无法访问
   - 扫描时这些文件夹大小为 0，虽然给了虚拟尺寸 100 字节，但可能仍被过滤

2. **渲染过滤**
   - `treemap_widget.py:325-327` 中有过滤逻辑：
     ```python
     if draw_rect.width() < 1 or draw_rect.height() < 1:
         continue
     ```
   - 即使给了虚拟尺寸，如果布局后实际尺寸仍 < 1 像素，会被跳过

3. **聚合逻辑**
   - `treemap_widget.py:265-281` 中，超过 3000 子项时会聚合
   - 但当前只有 14 个子项，不是聚合问题

---

## 后续建议

空间可视化的历史排查方案如下，仅在回归测试失败时参考；当前实现已通过可见性测试，不需要重复执行这些旧方案。

### 方案 1：增大虚拟尺寸 + 最小渲染尺寸

**修改位置：** `src/treemap_widget.py`

**步骤：**

1. **增大虚拟尺寸**（第 282-284 行）
   ```python
    # 当前代码
    items.append({"node": c, "size": max(size, 100)})
    # 改为更大的值
   items.append({"node": c, "size": max(size, 1000)})
   ```

2. **确保最小渲染尺寸**（第 325-327 行）
   ```python
   # 当前代码
    if draw_rect.width() < 1 or draw_rect.height() < 1:
        continue
    # 改为确保最小尺寸
   min_size = 20  # 最小 20x20 像素
   if draw_rect.width() < min_size or draw_rect.height() < min_size:
       # 强制最小尺寸
       draw_rect = QRectF(
           draw_rect.x(), draw_rect.y(),
           max(draw_rect.width(), min_size),
           max(draw_rect.height(), min_size)
       )
   ```

3. **添加"空文件夹"标识**（第 339-356 行）
   ```python
   # 在绘制文字时，检查是否为空文件夹
   if size == 0:
       painter.drawText(rect, Qt.AlignCenter, f"{name}\n(空文件夹)")
   ```

### 方案 2：检查扫描逻辑

**修改位置：** `src/disk_scanner.py`

**步骤：**

1. **检查权限错误处理**（第 136-158 行）
   ```python
   # 当前代码
    except PermissionError:
        continue
    # 改为记录错误并给虚拟大小
   except PermissionError:
       result["errors"].append({
           "path": dirpath,
           "error": "Permission denied"
       })
       # 给一个虚拟大小，确保能显示
       folder_size = 1000
   ```

2. **检查隐藏文件处理**
   - 确认 `disk_scanner.py` 中没有过滤隐藏文件的逻辑
   - 当前代码应该已经包含所有文件（含隐藏）

### 方案 3：调试定位

**建议的调试步骤：**

1. **添加日志**
   在 `treemap_widget.py` 的 `_layout()` 方法中添加：
   ```python
   print(f"子项数量: {len(children)}")
   for c in children:
       print(f"  {c['name']}: size={c.get('size', 0)}")
   ```

2. **检查布局结果**
   在 `_layout()` 返回前添加：
   ```python
   print(f"布局结果数量: {len(self._layout_result)}")
   for item in self._layout_result:
       rect = item["rect"]
       print(f"  {item['node']['name']}: {rect.width()}x{rect.height()}")
   ```

3. **运行测试**
   ```bash
   python test_hidden_files.py
   ```
   确认隐藏文件是否进入树结构

---

## 代码位置索引

### 关键文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/main_window.py` | ~2600 | 主窗口，包含所有页面 |
| `src/treemap_widget.py` | ~445 | Treemap 可视化组件 |
| `src/disk_scanner.py` | ~290 | 磁盘扫描引擎 |

### 关键代码位置

**空间可视化相关：**
- `main_window.py:1156-1289` - `_build_visualization_page()` 方法
- `main_window.py:2350-2456` - 可视化事件处理方法
- `treemap_widget.py:245-302` - `_layout()` 布局计算
- `treemap_widget.py:308-376` - `paintEvent()` 渲染逻辑

**扫描相关：**
- `disk_scanner.py:122-290` - `run()` 扫描主逻辑
- `disk_scanner.py:136-158` - 目录遍历和权限处理
- `disk_scanner.py:186-199` - 文件叶子节点添加

---

## 测试方法

### 搬到另一台电脑前

复制整个项目目录（包括 `assets/`、`packaging/`、`requirements-win7.txt`、测试文件和两份本交接文档）。不必复制 `build/`、`dist/`、`.build-python38/` 等本机生成目录；在目标机按下方 Win7 发布环境重新安装依赖并构建。用户的索引和回收站数据位于用户目录下的 `.diskwise`，不在项目目录中。

### 运行现有测试

```bash
# 布局算法测试
python test_squarify_check.py

# 端到端测试
python test_e2e_treemap.py

# UI 冒烟测试
python test_ui_smoke.py

# 压力测试（20000 子项）
python test_treemap_stress.py

# 隐藏文件测试
python test_hidden_files.py

# 空目录/无权限节点可见性
python test_treemap_visibility.py

# 快速搜索与全文搜索完整性
python test_quick_search_completeness.py
python test_fulltext_search.py

# Win7 构建门禁
python test_win7_compatibility.py
```

### 手动测试步骤

1. 启动程序：`python src/main.py`
2. 点击"空间可视化"标签
3. 选择 C:\ 目录，点击"开始扫描"
4. 观察是否显示所有 14 个项目
5. 点击 Users 文件夹下钻
6. 观察是否显示 3 个项目（Default、Jack、公用）

---

## 运行环境

```bash
# 日常开发环境（Python 3.10+ 可用）
python -m pip install -r requirements.txt
python src/main.py

# Win7 发布环境：64 位 Python 3.8.10 + 锁定依赖
python -m pip install -r requirements-win7.txt
python -m PyInstaller --noconfirm --clean packaging/FileCare.spec
& "C:\Program Files\Inno Setup 7\ISCC.exe" packaging/FileCare.iss
```

**依赖：**
- Win7 构建依赖见 `requirements-win7.txt`（PyQt5 5.15.10、PyQt5-Qt5 5.15.2、PyInstaller 5.13.2 等）
- 日常开发依赖见 `requirements.txt`
- pypdf>=3.0
- python-docx>=0.8
- openpyxl>=3.0
- python-pptx>=0.6
- striprtf>=0.0.20

---

## Git 信息

```
分支：master
远程：https://github.com/jack3344wong/diskwise.git
代理：http://127.0.0.1:7897
```

**未提交的修改：**
- `src/main.py` - 软件名改为"文件管家"
- `src/main_window.py` - 功能拆分 + 导航修复
- `src/treemap_widget.py` - 迭代布局 + 虚拟尺寸优化
- `src/disk_scanner.py` - 显示所有文件
- `assets/filecare.ico` - 新图标
- `packaging/FileCare.iss` - 软件名更新

---

## 下一步计划

### 优先级 1：发布验收

1. 在干净的 Windows 7 SP1 x64 虚拟机中安装并启动。
2. 验证安装阶段首批索引时间、首次启动后台续建和快速搜索完整性。
3. 验证空间可视化、搜索结果操作、快捷方式和卸载。

### 优先级 2：优化用户体验

1. 下钻时路径框和状态栏同步更新
2. 添加加载进度提示
3. 优化大目录的渲染性能

### 优先级 3：测试与发布

1. 全面测试所有功能
2. 提交代码到 GitHub
3. 打包发布 v1.1.0

---

## 联系方式

如有问题，请查看：
- `PROJECT_REPORT.md` - 详细项目报告
- `test_*.py` - 测试用例
- `ui_previews/` - UI 设计预览

---

**交接时间：** 2026-09-02

**交接人：** Hermes Agent

**接手人：** Codex / 下一台电脑上的维护者
