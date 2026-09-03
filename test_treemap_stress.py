# -*- coding: utf-8 -*-
"""极端情况验证：20000 子项布局 + TreemapWidget 聚合保护。"""
import sys, time, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from PyQt5.QtCore import QRectF
from treemap_widget import _squarify, TreemapWidget
from PyQt5.QtWidgets import QApplication

random.seed(7)
items = [{"node": {"name": f"file_{i}.dat", "size": 1}, "size": max(1, int(random.lognormvariate(12, 3)))} for i in range(20000)]
rect = QRectF(2, 2, 1240, 560)

t0 = time.time()
res = _squarify(items, rect)
dt = time.time() - t0
covered = sum(r["rect"].width() * r["rect"].height() for r in res)
print(f"20000 项布局: {dt:.3f}s, 输出 {len(res)} 块, 覆盖率 {covered/(1240*560)*100:.1f}%")
assert len(res) == 20000
assert covered > 0.999 * 1240 * 560
print("OK 20000 子项迭代布局成功，无爆栈无丢块")

app = QApplication.instance() or QApplication([])
w = TreemapWidget()
w.resize(1200, 600)
node = {
    "name": "root", "path": "C:/", "size": 10**12,
    "children": [{"name": f"child_{i}", "path": f"C:/child_{i}", "size": 10**6 + i, "is_file": True, "children": []}
                 for i in range(5000)]
}
t0 = time.time()
w.set_data(node)
dt = time.time() - t0
names = [item["node"]["name"] for item in w._layout_result]
assert len(names) == 3000, f"预期聚合后 3000 项, 实际 {len(names)}"
other = [n for n in names if n.startswith("其他")]
print(f"布局 5000 子项(聚合保护): {dt:.3f}s, 色块 {len(names)}, 聚合块: {other}")
print("OK 聚合保护生效")
print("ALL PASS")