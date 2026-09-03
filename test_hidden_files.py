# -*- coding: utf-8 -*-
"""验证隐藏文件夹/隐藏文件进入 folder_tree。"""
import os, sys, time, tempfile, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from PyQt5.QtWidgets import QApplication
from disk_scanner import DiskScannerThread

app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory(prefix="hidden_", dir=".") as tmp:
    root = Path(tmp).resolve()
    (root / "visible.txt").write_text("hi")
    (root / ".hidden.txt").write_text("secret")          # dotfile (Unix 习惯隐藏)
    (root / "hidden_dir").mkdir()
    (root / "hidden_dir" / "inner.txt").write_text("x")
    (root / "visible_dir").mkdir()
    (root / "visible_dir" / "data.txt").write_text("y")

    # Windows 属性级隐藏（attrib +h）
    for p in [root / ".hidden.txt", root / "hidden_dir"]:
        r = subprocess.run(["attrib", "+h", str(p)], capture_output=True)
        if r.returncode != 0:
            print("attrib 失败:", r.stderr.decode(errors="ignore"))

    scanner = DiskScannerThread(str(root), threshold_mb=0.001, top_n=100)
    received = []
    scanner.finished_signal.connect(received.append)
    scanner.start()
    while scanner.isRunning():
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    result = received[0]

    tree = result["folder_tree"]
    child_names = [c["name"] for c in tree.get("children", [])]

    # 递归收集所有节点
    def walk(node, depth=0):
        yield node
        for c in node.get("children", []):
            yield from walk(c)

    all_nodes = list(walk(tree))
    all_names = [n["name"] for n in all_nodes]

    print("根下直接子项:", child_names)
    print("全部节点名:", all_names)

    assert ".hidden.txt" in child_names, "隐藏文件缺失！"
    assert "hidden_dir" in child_names, "隐藏文件夹缺失！"
    assert "visible.txt" in child_names
    assert "visible_dir" in child_names
    assert "inner.txt" in all_names, "隐藏文件夹内部文件缺失！"
    assert "data.txt" in all_names
    print("OK 隐藏文件夹/隐藏文件均已进入可视化树")
    print("ALL PASS")