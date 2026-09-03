# -*- coding: utf-8 -*-
"""回归验证：超大目录旁的空目录和小文件也必须形成可见色块。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication  # noqa: E402
from treemap_widget import TreemapWidget  # noqa: E402


app = QApplication.instance() or QApplication([])


def assert_visible(children, expected_names):
    widget = TreemapWidget()
    widget.resize(1240, 400)
    root = {"name": "root", "path": "C:\\", "size": sum(
        child.get("size", 0) for child in children), "children": children}
    widget.set_data(root)
    app.processEvents()

    layout = {item["node"]["name"]: item["rect"]
              for item in widget._layout_result}
    assert set(layout) == set(expected_names)
    for name, rect in layout.items():
        assert rect.width() > 1 and rect.height() > 1, \
            f"{name} 仍不可见: {rect.width()} x {rect.height()}"
    return layout


users_children = [
    {"name": "Jack", "path": r"C:\Users\Jack", "size": 50 * 1024 ** 3,
     "children": [{"name": "data", "size": 1, "children": []}]},
    {"name": "Default", "path": r"C:\Users\Default", "size": 0,
     "scan_status": "无法访问，未统计内容", "children": []},
    {"name": "Public", "path": r"C:\Users\Public", "size": 1024,
     "children": []},
]
users_layout = assert_visible(users_children, ["Jack", "Default", "Public"])
print("Users 可见性布局:",
      {name: (round(rect.width(), 1), round(rect.height(), 1))
       for name, rect in users_layout.items()})

# 模拟 C:\ 根目录：大项有几十 GB，同级还有多个空目录/无权目录。
root_sizes = [50, 24, 13, 8.5, 6.3, 6.2, 5.0, 3.4]
root_children = [
    {"name": f"large_{i}", "path": rf"C:\large_{i}",
     "size": int(size * 1024 ** 3), "children": []}
    for i, size in enumerate(root_sizes)
]
root_children.extend(
    {"name": f"small_{i}", "path": rf"C:\small_{i}", "size": 0,
     "scan_status": "无法访问，未统计内容", "children": []}
    for i in range(14)
)
root_layout = assert_visible(root_children,
                             [item["name"] for item in root_children])
print("C:\\ 根目录 22 项全部可见，最小边:",
      round(min(min(rect.width(), rect.height())
                for rect in root_layout.values()), 1), "px")
print("ALL PASS")
