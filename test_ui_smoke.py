# -*- coding: utf-8 -*-
"""离屏验证：所有页面切换 + 回收站页面数据加载（无 GUI 自动化依赖）。"""
import os, sys, tempfile, time
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent / "src"))
import main  # noqa: F401  (设置 Qt 插件路径)
from main_window import DiskMonitor  # noqa: E402
from file_operations import FileOperations  # noqa: E402

app = QApplication.instance() or QApplication([])
w = DiskMonitor()
w.show()
app.processEvents()

# ── 页面切换 ──
for idx, name, fn in [
    (0, "首页", w._show_home_view),
    (1, "文件管理", w._show_browse_view),
    (2, "磁盘空间扫描", w._show_scan_view),
    (3, "快速搜索", w._show_search_view),
    (4, "回收站管理", w._show_recycle_view),
]:
    fn()
    app.processEvents()
    assert w._main_stack.currentIndex() == idx, f"{name} 页面切换失败: {w._main_stack.currentIndex()}"
    print(f"✅ {name} (index {idx}) 切换正常")

# ── 回收站数据：先清空，再造 2 个文件 + 1 个元数据 ──
recycle = w.file_operations.recycle_bin_path
import shutil
if os.path.isdir(recycle):
    shutil.rmtree(recycle)
os.makedirs(recycle, exist_ok=True)
f1 = os.path.join(recycle, "测试报告.docx")
f2 = os.path.join(recycle, "photo.jpg")
with open(f1, "wb") as f: f.write(b"x" * 1024)
with open(f2, "wb") as f: f.write(b"y" * 2048)
import json
with open(f1 + ".meta.json", "w", encoding="utf-8") as f:
    json.dump({"origin_path": "D:\\Work\\测试报告.docx", "deleted_at": time.time() - 86400}, f, ensure_ascii=False)

w._rb_load_items()
app.processEvents()
count = w._rb_tree.topLevelItemCount()
print(f"✅ 回收站加载 {count} 项")
assert count == 2, f"应为 2 项，实际 {count}"
assert w._rb_summary_labels["rb_files_count"].text() == "2"
assert w._rb_summary_labels["rb_space_used"].text() == "3.0 KB"
print("✅ 汇总卡片数据正确")

# 勾选全部
w._rb_set_all(True)
app.processEvents()
assert len(w._rb_checked_items()) == 2
print("✅ 全选功能正常")

# 清理测试文件
os.remove(f1); os.remove(f2); os.remove(f1 + ".meta.json")
print("\n🎉 所有页面 + 回收站功能离屏验证通过")
w.close()
