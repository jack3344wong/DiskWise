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
# 烟测不应触发真实磁盘的后台索引；索引完整性由独立测试覆盖。
DiskMonitor._auto_rebuild_index_on_startup = lambda self: None
DiskMonitor._show_first_index_notice = lambda self: None
w = DiskMonitor()
w.show()
app.processEvents()

# ── 页面切换 ──
for idx, name, fn in [
    (0, "首页", w._show_home_view),
    (1, "文件管理", w._show_browse_view),
    (2, "大文件清理", w._show_scan_view),
    (3, "空间可视化", w._show_visualization_view),
    (4, "快速搜索", w._show_search_view),
    (5, "回收站管理", w._show_recycle_view),
]:
    fn()
    app.processEvents()
    assert w._main_stack.currentIndex() == idx, f"{name} 页面切换失败: {w._main_stack.currentIndex()}"
    print(f"✅ {name} (index {idx}) 切换正常")

assert w._search_result_tree.headerItem().text(3) == "文件类型"
print("✅ 文件名搜索包含文件类型列")
assert any(chip.text() == "文件夹" for chip in w._format_chips)
print("✅ 搜索格式包含文件夹筛选")
assert not w._search_filter_hint_btn.isVisible()
print("✅ 文件夹筛选提示默认隐藏")

# ── 回收站数据：使用隔离的临时目录，绝不触碰用户真实回收站 ──
temp_recycle = tempfile.TemporaryDirectory(prefix="ui_recycle_", dir=".")
recycle = os.path.abspath(temp_recycle.name)
w.file_operations = FileOperations(recycle)
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

# 搜索结果的复制/剪切使用 Windows 资源管理器兼容的文件剪贴板格式。
drop_effect = 'application/x-qt-windows-mime;value="Preferred DropEffect"'
w._set_search_result_clipboard(f1, cut=False)
mime = QApplication.clipboard().mimeData()
assert os.path.normcase(os.path.abspath(mime.urls()[0].toLocalFile())) == os.path.normcase(f1)
assert int.from_bytes(bytes(mime.data(drop_effect)), "little") == 1
w._set_search_result_clipboard(f1, cut=True)
mime = QApplication.clipboard().mimeData()
assert int.from_bytes(bytes(mime.data(drop_effect)), "little") == 2
print("✅ 搜索结果复制/剪切剪贴板格式正确")

# 勾选全部
w._rb_set_all(True)
app.processEvents()
assert len(w._rb_checked_items()) == 2
print("✅ 全选功能正常")

# 清理测试文件
os.remove(f1); os.remove(f2); os.remove(f1 + ".meta.json")
temp_recycle.cleanup()
print("\n🎉 所有页面 + 回收站功能离屏验证通过")
w.close()
