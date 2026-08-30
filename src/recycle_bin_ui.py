# -*- coding: utf-8 -*-
"""回收站管理界面 - PyQt5 增强版 (Recycle Bin Manager Dialog)"""
import os
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QFrame, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt

from file_operations import FileOperations


RECYCLE_STYLESHEET = """
QDialog {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #e8edf5, stop:1 #d5dce8);
}
QFrame#rbCard {
    background: #ffffff;
    border-radius: 10px;
    padding: 24px;
}
QLabel#rbTitle {
    font-size: 18px;
    font-weight: bold;
    color: #2c3e50;
    padding-bottom: 12px;
}
QListWidget#rbList {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
    color: #444444;
    outline: none;
    background: #fafbfc;
}
QListWidget#rbList::item {
    padding: 8px 12px;
    margin: 2px 0;
    border-radius: 6px;
}
QListWidget#rbList::item:hover {
    background: #eef4fb;
    color: #2a6cb6;
}
QListWidget#rbList::item:selected {
    background: #4a90e2;
    color: white;
}
QPushButton#rbRestore {
    background: #4a90e2;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#rbRestore:hover { background: #357abd; }
QPushButton#rbDelete {
    background: #fafbfc;
    border: 1px solid #dddddd;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    color: #444444;
}
QPushButton#rbDelete:hover {
    background: #e74c3c;
    color: white;
    border-color: #e74c3c;
}
QPushButton#rbClose {
    background: #f0f2f5;
    border: 1px solid #dddddd;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    color: #555555;
}
QPushButton#rbClose:hover { background: #e4e7ec; }
QLabel#rbStatus {
    font-size: 11px;
    color: #888888;
    padding-top: 8px;
}
"""


class RecycleBinDialog(QDialog):
    """回收站管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("回收站管理")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)
        self.setStyleSheet(RECYCLE_STYLESHEET)

        recycle_path = os.path.join(os.path.expanduser("~"), ".recycle_bin")
        self.file_ops = FileOperations(recycle_path)

        self._build_ui()
        self._load_items()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("rbCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel("回收站管理")
        title.setObjectName("rbTitle")
        card_layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("rbList")
        card_layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_restore = QPushButton("还原选中")
        btn_restore.setObjectName("rbRestore")
        btn_restore.setCursor(Qt.PointingHandCursor)
        btn_restore.clicked.connect(self._restore_selected)
        btn_row.addWidget(btn_restore)

        btn_delete = QPushButton("永久删除")
        btn_delete.setObjectName("rbDelete")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.clicked.connect(self._permanent_delete)
        btn_row.addWidget(btn_delete)

        btn_row.addStretch()

        btn_close = QPushButton("关闭")
        btn_close.setObjectName("rbClose")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        card_layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("rbStatus")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)

    def _load_items(self):
        """加载回收站内容"""
        self.list_widget.clear()
        try:
            recycle_path = self.file_ops.recycle_bin_path
            if not os.path.exists(recycle_path):
                self.status_label.setText("回收站为空")
                return

            items = sorted(os.listdir(recycle_path))
            for name in items:
                full = os.path.join(recycle_path, name)
                try:
                    size = os.path.getsize(full)
                    mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(full)))
                    display = f"{name}    ({self._fmt_size(size)})    删除于 {mtime}"
                except OSError:
                    display = name

                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, full)
                self.list_widget.addItem(item)

            self.status_label.setText(f"共 {self.list_widget.count()} 个项目")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    @staticmethod
    def _fmt_size(n):
        try:
            n = float(n)
        except (TypeError, ValueError):
            return "?"
        for u in ("B", "KB", "MB", "GB"):
            if n < 1024 or u == "GB":
                return f"{n:.1f} {u}" if u != "B" else f"{n:.0f} B"
            n /= 1024
        return f"{n:.1f} GB"

    def _restore_selected(self):
        selected = self.list_widget.selectedItems()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要还原的项目")
            return
        try:
            path = selected[0].data(Qt.UserRole)
            name = os.path.basename(path)
            target = os.path.join(os.path.expanduser("~"), "Desktop", name)
            ok, msg = self.file_ops.restore_from_recycle_bin(path, target)
            if ok:
                QMessageBox.information(self, "成功", f"已还原到:\n{target}")
                self._load_items()
            else:
                QMessageBox.critical(self, "还原失败", msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _permanent_delete(self):
        selected = self.list_widget.selectedItems()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要删除的项目")
            return
        reply = QMessageBox.question(
            self, "确认永久删除",
            "此操作不可恢复，确定要永久删除吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            path = selected[0].data(Qt.UserRole)
            os.remove(path)
            QMessageBox.information(self, "成功", "已永久删除")
            self._load_items()
        except Exception as e:
            QMessageBox.critical(self, "删除失败", str(e))
