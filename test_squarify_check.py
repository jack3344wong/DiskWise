# -*- coding: utf-8 -*-
"""验证 _squarify 布局算法是否丢块/越界（空间可视化显示不全排查）"""
import sys
from pathlib import Path
from PyQt5.QtCore import QRectF

sys.path.insert(0, str(Path(__file__).parent / "src"))
from treemap_widget import _squarify  # noqa: E402

children = [
    ("Users", 45.7e9), ("Windows", 23.8e9), ("Program Files", 8.9e9),
    ("Program Files (x86)", 8.0e9), ("ProgramData", 3.7e9),
    ("Python314", 0.5e9), ("inetpub", 0.01e9), ("AMD", 0.002e9),
    ("PerfLogs", 0.0001e9), ("Recovery", 0.3e9), ("$Recycle.Bin", 0.8e9),
    ("$AV_NLL", 0.001e9), ("Documents and Settings", 0.0),
    ("OneDriveTemp", 0.02e9), ("System Volume Information", 0.4e9),
    ("MSI", 1.2e9), ("IObit", 0.3e9), ("NVIDIA", 2.1e9),
    ("Intel", 0.05e9), ("pagefile_dir", 0.1e9), ("hiberfil_dir", 0.05e9),
]
items = [{"node": {"name": n}, "size": max(int(s), 1)} for n, s in children]
rect = QRectF(2, 2, 1240, 560)
res = _squarify(items, rect)
print(f"输入 {len(items)} 项，输出 {len(res)} 块")
covered = sum(r["rect"].width() * r["rect"].height() for r in res)
print(f"画布面积: {rect.width()*rect.height():.0f}  布局覆盖: {covered:.0f}  覆盖率: {covered/(rect.width()*rect.height())*100:.1f}%")
names = {r["node"]["name"] for r in res}
missing = {n for n, _ in children} - names
print("丢失的文件夹:", missing if missing else "无")
oob = [r["node"]["name"] for r in res
       if r["rect"].right() > rect.right() + 0.5 or r["rect"].bottom() > rect.bottom() + 0.5
       or r["rect"].left() < rect.left() - 0.5 or r["rect"].top() < rect.top() - 0.5]
print("超出画布的块:", oob if oob else "无")
tiny = [(r["node"]["name"], round(r["rect"].width(),1), round(r["rect"].height(),1)) for r in res
        if r["rect"].width() < 3 or r["rect"].height() < 3]
print("极小块(<3px):", tiny if tiny else "无")

# 第二轮：更极端的 100 项数据（模拟最多显示 100）
import random
random.seed(42)
items2 = [{"node": {"name": f"f{i}"}, "size": max(1, int(random.lognormvariate(15, 3)))} for i in range(100)]
res2 = _squarify(items2, QRectF(0, 0, 900, 500))
print(f"\n100 项测试：输入 100，输出 {len(res2)}")
covered2 = sum(r["rect"].width() * r["rect"].height() for r in res2)
print(f"覆盖率: {covered2/(900*500)*100:.1f}%")
names2 = {r["node"]["name"] for r in res2}
print("丢失:", 100 - len(names2))
