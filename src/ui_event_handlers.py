# -*- coding: utf-8 -*-
"""用户界面优化和事件处理 - 辅助工具与样式常量 (UI Utilities & Style Constants)"""
import os
from PyQt5.QtWidgets import QMessageBox


class UIEvents:
    """
    UI 事件辅助类。
    主要的事件处理已整合到 DiskMonitor 主窗口中，
    此类提供可复用的通用 UI 操作。
    """

    def __init__(self, parent_window=None):
        self.parent = parent_window

    @staticmethod
    def show_info(parent, title, message):
        """显示信息对话框"""
        try:
            QMessageBox.information(parent, title, message)
        except Exception as e:
            print(f"[UIEvents] show_info 失败: {e}")

    @staticmethod
    def show_warning(parent, title, message):
        """显示警告对话框"""
        try:
            QMessageBox.warning(parent, title, message)
        except Exception as e:
            print(f"[UIEvents] show_warning 失败: {e}")

    @staticmethod
    def show_error(parent, title, message):
        """显示错误对话框"""
        try:
            QMessageBox.critical(parent, title, message)
        except Exception as e:
            print(f"[UIEvents] show_error 失败: {e}")

    @staticmethod
    def confirm(parent, title, message):
        """确认对话框，返回 True/False"""
        try:
            reply = QMessageBox.question(
                parent, title, message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
        except Exception as e:
            print(f"[UIEvents] confirm 失败: {e}")
            return False

    @staticmethod
    def get_file_extension(file_path):
        """安全获取文件扩展名"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            return ext.lstrip(".")
        except Exception:
            return ""

    @staticmethod
    def truncate_path(path, max_len=60):
        """截断过长路径用于显示"""
        if len(path) <= max_len:
            return path
        head = path[:max_len // 3]
        tail = path[-(max_len // 3 * 2):]
        return f"{head}...{tail}"
