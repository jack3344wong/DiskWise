# -*- coding: utf-8 -*-
"""磁盘智理 / DiskWise 完整主窗口。"""
from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path

import psutil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QAbstractSpinBox, QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QMainWindow, QMenu, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QSpinBox, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from disk_scanner import DiskScannerThread
from file_association import FileAssociation
from file_operations import FileOperations
from web_search import WebSearch
from quick_search import QuickSearchEngine
from fulltext_search import FullTextSearchEngine
from content_extractor import ContentExtractor


APP_NAME_ZH = "磁盘智理"
APP_NAME_EN = "DiskWise"
ASSET_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets"
APP_ICON_PATH = ASSET_DIR / "diskwise.ico"


class _TriangleSpinMixin:
    """Paint unambiguous triangular increment/decrement affordances over Qt's spin buttons."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        right = self.rect().right()
        left = max(0, right - 24)
        mid = self.rect().center().y()
        painter.fillRect(left, self.rect().top() + 1, right - left, self.rect().height() - 2,
                         self.palette().base())
        painter.setPen(QtGui.QPen(QtGui.QColor("#d7dce2")))
        painter.drawLine(left, self.rect().top() + 3, left, self.rect().bottom() - 3)
        painter.setPen(Qt.NoPen)
        color = self.palette().color(QtGui.QPalette.ButtonText)
        painter.setBrush(color)
        painter.drawPolygon(QtGui.QPolygon([
            QtCore.QPoint(right - 15, mid - 2), QtCore.QPoint(right - 5, mid - 2),
            QtCore.QPoint(right - 10, mid - 8)
        ]))
        painter.drawPolygon(QtGui.QPolygon([
            QtCore.QPoint(right - 15, mid + 2), QtCore.QPoint(right - 5, mid + 2),
            QtCore.QPoint(right - 10, mid + 8)
        ]))


class TriangleDoubleSpinBox(_TriangleSpinMixin, QDoubleSpinBox):
    pass


class TriangleSpinBox(_TriangleSpinMixin, QSpinBox):
    pass

TRANSLATIONS = {
    "zh": {
        "app_name": APP_NAME_ZH, "refresh": "刷新", "space_scan": "磁盘空间扫描", "recycle_bin": "回收站管理",
        "search": "搜索当前目录...", "language": "语言", "language_zh": "中文", "language_en": "English", "back": "返回上一位置", "up": "返回上级目录", "root": "返回磁盘根目录",
        "file_details": "文件详情", "scan_tab": "空间扫描", "detail_title": "文件与软件详情", "disk_usage": "磁盘使用情况",
        "name": "名称", "full_path": "完整路径", "size": "大小", "mtime": "修改时间", "item_type": "项目类型",
        "source": "来源/同步软件", "relation": "与软件的关系", "default_app": "默认打开程序", "confidence": "识别可信度",
        "evidence": "判断依据", "delete_advice": "删除建议", "identify": "识别关联软件", "online": "在线核验软件",
        "open_location": "打开所在目录", "move_recycle": "移至回收站", "current_dir": "当前目录", "current_drive": "当前磁盘",
        "choose_dir": "选择目录", "min_size": "最小文件大小(MB)", "max_results": "最多显示", "start_scan": "开始扫描",
        "cancel_scan": "取消扫描", "scan_intro": "选择范围后开始扫描；程序不会自动删除任何文件。请特别留意云盘同步风险。",
        "large_files": "大文件", "large_folders": "大文件夹", "cleanup_advice": "清理建议", "junk_files": "垃圾/临时文件", "clean_selected": "清理选中垃圾", "copy_path": "复制路径",
        "quick_search": "快速搜索", "search_mode_name": "文件名搜索", "search_mode_content": "内容搜索",
        "search_placeholder": "输入关键词搜索...", "search_hint_name": "支持通配符 * 和 ?，如 *.pdf、report*、ext:xlsx",
        "search_hint_content": "搜索文档内容，支持 PDF、Word、Excel、PPT、TXT 等格式",
        "index_status": "索引状态", "index_build": "构建索引", "index_cancel": "取消索引",
        "index_rebuild": "重建索引", "index_none": "尚未构建索引，点击「构建索引」开始",
        "index_building": "正在构建索引...", "index_complete": "索引完成", "index_count": "已索引",
        "preview_title": "文档预览", "preview_hint": "点击搜索结果预览内容", "preview_no_support": "该文件类型不支持预览",
        "search_results": "搜索结果", "no_results": "未找到匹配结果", "result_count": "共 {count} 条结果",
        "open_file": "打开文件", "open_folder": "打开所在目录",
    },
    "en": {
        "app_name": APP_NAME_EN, "refresh": "Refresh", "space_scan": "Disk Space Scan", "recycle_bin": "Recycle Bin",
        "search": "Search current folder...", "language": "Language", "language_zh": "Chinese", "language_en": "English", "back": "Previous Location", "up": "Parent Folder", "root": "Drive Root",
        "file_details": "File Details", "scan_tab": "Space Scan", "detail_title": "File & Software Details", "disk_usage": "Disk Usage",
        "name": "Name", "full_path": "Full Path", "size": "Size", "mtime": "Modified", "item_type": "Item Type",
        "source": "Source / Sync Software", "relation": "Software Relationship", "default_app": "Default App", "confidence": "Confidence",
        "evidence": "Evidence", "delete_advice": "Deletion Advice", "identify": "Identify Software", "online": "Verify Online",
        "open_location": "Open Location", "move_recycle": "Move to Recycle Bin", "current_dir": "Current Folder", "current_drive": "Current Drive",
        "choose_dir": "Choose Folder", "min_size": "Minimum Size (MB)", "max_results": "Max Results", "start_scan": "Start Scan",
        "cancel_scan": "Cancel Scan", "scan_intro": "Choose a location to scan. No files are deleted automatically. Review cloud-sync risks carefully.",
        "large_files": "Large Files", "large_folders": "Large Folders", "cleanup_advice": "Cleanup Advice", "junk_files": "Junk / Temp Files", "clean_selected": "Clean Selected Junk", "copy_path": "Copy Path",
        "quick_search": "Quick Search", "search_mode_name": "Name Search", "search_mode_content": "Content Search",
        "search_placeholder": "Type to search...", "search_hint_name": "Wildcards * and ? supported, e.g. *.pdf, report*, ext:xlsx",
        "search_hint_content": "Search inside documents: PDF, Word, Excel, PPT, TXT and more",
        "index_status": "Index Status", "index_build": "Build Index", "index_cancel": "Cancel Indexing",
        "index_rebuild": "Rebuild Index", "index_none": "No index yet. Click 'Build Index' to start.",
        "index_building": "Building index...", "index_complete": "Index complete", "index_count": "Indexed",
        "preview_title": "Document Preview", "preview_hint": "Click a result to preview content", "preview_no_support": "This file type is not previewable",
        "search_results": "Search Results", "no_results": "No matching results", "result_count": "{count} results",
        "open_file": "Open File", "open_folder": "Open Location",
    },
}


def format_size(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "未知"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return "未知"


def format_time(timestamp):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    except Exception:
        return "未知"


STYLESHEET = """
QMainWindow { background:#e8edf5; }
QFrame#sidebar, QFrame#card { background:white; border-radius:10px; }
QFrame#toolbar { background:white; border-bottom:1px solid #dfe3e8; min-height:54px; max-height:54px; }
QLabel#title { font-size:17px; font-weight:700; color:#26384a; padding:10px; }
QLabel#sectionTitle { font-size:16px; font-weight:700; color:#26384a; padding:4px 0 10px 0; }
QLabel#key { color:#73808c; font-size:12px; }
QLabel#value { color:#263238; font-size:12px; }
QLabel#pathBar { background:#f7f9fb; border:1px solid #dfe3e8; border-radius:6px; padding:7px 9px; color:#52606d; }
QPushButton { min-height:30px; padding:4px 11px; border-radius:6px; border:1px solid #d7dce2; background:#fff; color:#34495e; }
QPushButton:hover { border-color:#4a90e2; background:#eef5fd; }
QPushButton:disabled { color:#adb5bd; background:#f1f3f5; }
QPushButton#primary { background:#4a90e2; color:white; border-color:#4a90e2; }
QPushButton#danger:hover { background:#e74c3c; color:white; border-color:#e74c3c; }
QPushButton#action, QPushButton#deleteAction { min-height:40px; padding:8px 14px; text-align:left; }
QPushButton#deleteAction:hover { background:#e74c3c; color:white; border-color:#e74c3c; }
QTreeWidget { background:white; border:1px solid #e1e5ea; border-radius:7px; alternate-background-color:#f8fafc; }
QTreeWidget::item { min-height:27px; padding:3px; }
QTreeWidget::item:selected { background:#4a90e2; color:white; }
QHeaderView::section { background:#f4f6f8; border:none; border-bottom:1px solid #dfe3e8; padding:7px; font-weight:600; color:#52606d; }
QLineEdit, QComboBox { min-height:30px; border:1px solid #d7dce2; border-radius:6px; padding:2px 8px; background:white; }
QSpinBox, QDoubleSpinBox { min-height:30px; border:1px solid #d7dce2; border-radius:6px; padding:2px 8px; background:white; }
QComboBox QAbstractItemView {
    background:#ffffff;
    color:#26384a;
    border:1px solid #b9c7d6;
    outline:0;
    selection-background-color:rgba(74,144,226,55);
    selection-color:#163a59;
}
QComboBox QAbstractItemView::item { min-height:28px; padding:4px 8px; color:#26384a; }
QComboBox QAbstractItemView::item:hover { background:rgba(74,144,226,38); color:#163a59; }
QComboBox QAbstractItemView::item:selected { background:rgba(74,144,226,72); color:#163a59; }
QMenu { background:white; color:#26384a; border:1px solid #cfd8e2; padding:5px; }
QMenu::item { padding:7px 28px 7px 10px; border-radius:4px; }
QMenu::item:selected { background:rgba(74,144,226,45); color:#163a59; }
QTabWidget::pane { border:0; }
QTabBar::tab { padding:9px 18px; color:#52606d; }
QTabBar::tab:selected { color:#2f78c4; border-bottom:2px solid #4a90e2; }
QProgressBar { border:0; background:#e9edf2; border-radius:5px; min-height:10px; max-height:10px; text-align:center; }
QProgressBar::chunk { background:#4a90e2; border-radius:5px; }
"""


class DiskMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = "zh"
        self._i18n_widgets = {}
        self.setWindowTitle(APP_NAME_ZH)
        if APP_ICON_PATH.is_file():
            self.setWindowIcon(QtGui.QIcon(str(APP_ICON_PATH)))
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)
        self.current_path = os.path.abspath(os.sep)
        self._full_path = self.current_path
        self._nav_history = []
        self._scanner_thread = None
        self._scan_path = self.current_path
        self._last_identity = None
        self._detail_path = None
        self.web_search = WebSearch("bing")
        self.file_operations = FileOperations(os.path.join(os.path.expanduser("~"), ".recycle_bin"))
        self.quick_search_engine = QuickSearchEngine()
        self.fulltext_search_engine = FullTextSearchEngine()
        self.content_extractor = ContentExtractor()
        self._search_timer = None
        self._build_ui()
        self._apply_language()
        self._navigate_to(self.current_path, add_history=False)
        self._update_disk_usage()
        # 启动时自动重建索引
        QtCore.QTimer.singleShot(1000, self._auto_rebuild_index_on_startup)

    def _icon(self, enum):
        return self.style().standardIcon(enum)

    def _tr(self, key):
        return TRANSLATIONS[self.language].get(key, key)

    def _register_text(self, key, widget):
        self._i18n_widgets.setdefault(key, []).append(widget)
        return widget

    def _change_language(self, index):
        self.language = "en" if index == 1 else "zh"
        self._apply_language()

    def _apply_language(self):
        for key, widgets in self._i18n_widgets.items():
            for widget in widgets:
                widget.setText(self._tr(key))
        self.setWindowTitle(self._tr("app_name"))
        QtWidgets.QApplication.setApplicationDisplayName(self._tr("app_name"))
        self.search_box.setPlaceholderText(self._tr("search"))
        self._language_combo.setItemText(0, self._tr("language_zh"))
        self._language_combo.setItemText(1, self._tr("language_en"))
        self._language_combo.setToolTip(self._tr("language"))
        # 扫描结果标签页
        self._scan_result_tabs.setTabText(0, self._tr("large_files"))
        self._scan_result_tabs.setTabText(1, self._tr("large_folders"))
        self._scan_result_tabs.setTabText(2, self._tr("cleanup_advice"))
        self._scan_result_tabs.setTabText(3, self._tr("junk_files"))
        if self.language == "zh":
            self.tree.setHeaderLabels(["名称", "大小"])
            self._large_files.setHeaderLabels(["名称", "实际占用", "逻辑大小", "修改时间", "来源软件", "完整路径"])
            self._large_folders.setHeaderLabels(["文件夹", "实际占用", "逻辑大小", "文件数", "子文件夹数", "来源软件", "完整路径"])
            self._suggestions.setHeaderLabels(["建议等级", "名称", "可释放空间", "原因", "风险", "完整路径"])
            self._garbage_files.setHeaderLabels(["类别", "名称", "实际占用", "修改时间", "建议", "风险", "完整路径"])
        else:
            self.tree.setHeaderLabels(["Name", "Size"])
            self._large_files.setHeaderLabels(["Name", "Allocated", "Logical Size", "Modified", "Source Software", "Full Path"])
            self._large_folders.setHeaderLabels(["Folder", "Allocated", "Logical Size", "Files", "Subfolders", "Source Software", "Full Path"])
            self._suggestions.setHeaderLabels(["Level", "Name", "Reclaimable", "Reason", "Risk", "Full Path"])
            self._garbage_files.setHeaderLabels(["Category", "Name", "Allocated", "Modified", "Advice", "Risk", "Full Path"])
        for index in range(self._drive_combo.count()):
            root = self._drive_combo.itemData(index)
            self._drive_combo.setItemText(index, (f"Drive {root}" if self.language == "en" else f"磁盘 {root}"))
        count = self.tree.topLevelItemCount()
        self._status_label.setText((f"Current folder: {self.current_path}    Items: {count}" if self.language == "en" else f"当前目录：{self.current_path}    项目数：{count}"))
        if self._detail_path and os.path.exists(self._detail_path):
            self._show_detail(self._detail_path, os.path.isdir(self._detail_path))

    def _button(self, text, icon, slot, object_name=""):
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.setIcon(self._icon(icon))
        button.setCursor(Qt.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(slot)
        return button

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QFrame(); toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar); tb.setContentsMargins(18, 8, 18, 8); tb.setSpacing(9)
        logo = QLabel()
        if APP_ICON_PATH.is_file(): logo.setPixmap(QtGui.QIcon(str(APP_ICON_PATH)).pixmap(30, 30))
        tb.addWidget(logo)
        title = self._register_text("app_name", QLabel()); title.setObjectName("title"); tb.addWidget(title)
        tb.addSpacing(10)
        
        # 首页按钮
        self._home_btn = QPushButton("首页")
        self._home_btn.setIcon(self._icon(QtWidgets.QStyle.SP_ComputerIcon))
        self._home_btn.setCursor(Qt.PointingHandCursor)
        self._home_btn.clicked.connect(self._show_detail_view)
        tb.addWidget(self._home_btn)
        
        self._scan_btn = self._register_text("space_scan", self._button("", QtWidgets.QStyle.SP_DriveHDIcon, self._show_scan_view))
        self._search_toolbar_btn = self._register_text("quick_search", self._button("", QtWidgets.QStyle.SP_FileDialogContentsView, self._show_search_view))
        recycle = self._register_text("recycle_bin", self._button("", QtWidgets.QStyle.SP_TrashIcon, self._open_recycle_bin))
        tb.addWidget(self._scan_btn); tb.addWidget(self._search_toolbar_btn); tb.addWidget(recycle); tb.addStretch()
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setMinimumWidth(240); self.search_box.textChanged.connect(self._on_search); tb.addWidget(self.search_box)
        self._language_label = self._register_text("language", QLabel())
        self._language_combo = QComboBox(); self._language_combo.addItems(["中文", "English"]); self._language_combo.setFixedWidth(94); self._language_combo.currentIndexChanged.connect(self._change_language)
        tb.addWidget(self._language_label); tb.addWidget(self._language_combo)
        root.addWidget(toolbar)

        body = QHBoxLayout(); body.setContentsMargins(16, 16, 16, 12); body.setSpacing(16)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setMinimumWidth(260); sidebar.setMaximumWidth(320)
        side = QVBoxLayout(sidebar); side.setContentsMargins(12, 12, 12, 12); side.setSpacing(7)
        self._btn_back = self._button("返回上一位置", QtWidgets.QStyle.SP_ArrowBack, self._go_back_history)
        self._btn_up = self._button("返回上级目录", QtWidgets.QStyle.SP_ArrowUp, self._go_up)
        self._btn_root = self._button("返回磁盘根目录", QtWidgets.QStyle.SP_ComputerIcon, self._go_root)
        self._register_text("back", self._btn_back); self._register_text("up", self._btn_up); self._register_text("root", self._btn_root)
        side.addWidget(self._btn_back); side.addWidget(self._btn_up); side.addWidget(self._btn_root)
        self._drive_combo = QComboBox(); self._drive_combo.setToolTip("选择磁盘")
        self._populate_drives(); self._drive_combo.currentIndexChanged.connect(self._on_drive_selected); side.addWidget(self._drive_combo)
        self._path_bar = QLabel(self.current_path); self._path_bar.setObjectName("pathBar"); self._path_bar.setToolTip(self.current_path); side.addWidget(self._path_bar)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["名称", "大小"]); self.tree.setColumnCount(2)
        self.tree.setRootIsDecorated(False); self.tree.setAlternatingRowColors(True); self.tree.setTextElideMode(Qt.ElideRight)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        header = self.tree.header(); header.setStretchLastSection(False); header.setSectionResizeMode(0, QHeaderView.Stretch); header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.itemClicked.connect(self._on_item_clicked); self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self._on_context_menu)
        side.addWidget(self.tree, 1); body.addWidget(sidebar)

        # 使用 QStackedWidget 替代 QTabWidget
        self._main_stack = QtWidgets.QStackedWidget()
        self._detail_page = self._build_detail_page()
        self._scan_page = self._build_scan_page()
        self._search_page = self._build_search_page()
        self._main_stack.addWidget(self._detail_page)  # index 0
        self._main_stack.addWidget(self._scan_page)    # index 1
        self._main_stack.addWidget(self._search_page)  # index 2
        self._main_stack.setCurrentIndex(0)  # 默认显示文件详情
        body.addWidget(self._main_stack, 1)
        
        # 磁盘使用情况（底部横向条）
        self._disk_bar_container = QFrame()
        self._disk_bar_container.setObjectName("card")
        self._disk_bar_container.setMaximumHeight(60)
        disk_bar_layout = QHBoxLayout(self._disk_bar_container)
        disk_bar_layout.setContentsMargins(18, 12, 18, 12)
        disk_bar_layout.setSpacing(24)
        self._disk_bars_layout = disk_bar_layout
        root.addLayout(body, 1)
        root.addWidget(self._disk_bar_container)
        
        self._status_label = QLabel("就绪"); self._status_label.setStyleSheet("padding:5px 20px;color:#65717d;background:#f7f9fb;border-top:1px solid #dfe3e8;")
        root.addWidget(self._status_label)

    def _build_detail_page(self):
        """构建文件详情页面（左侧元数据 + 右侧预览）"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 左侧：文件元数据
        card = QFrame()
        card.setObjectName("card")
        detail = QVBoxLayout(card)
        detail.setContentsMargins(24, 20, 24, 20)
        detail.setSpacing(12)
        
        t = self._register_text("detail_title", QLabel())
        t.setObjectName("sectionTitle")
        detail.addWidget(t)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        self._info_labels = {}
        rows = [
            ("name", "name"), ("full_path", "path"), ("size", "size"), ("mtime", "mtime"),
            ("item_type", "ftype"), ("source", "sync"), ("relation", "relation"),
            ("default_app", "assoc"), ("confidence", "confidence"), ("evidence", "evidence"),
            ("delete_advice", "advice")
        ]
        for row, (label_key, key) in enumerate(rows):
            left = self._register_text(label_key, QLabel())
            left.setObjectName("key")
            value = QLabel("—")
            value.setObjectName("value")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(left, row, 0, Qt.AlignTop)
            grid.addWidget(value, row, 1)
            self._info_labels[key] = value
        grid.setColumnStretch(1, 1)
        detail.addLayout(grid)
        
        actions = QGridLayout()
        actions.setSpacing(10)
        self._btn_identify = self._register_text("identify", self._button("", QtWidgets.QStyle.SP_FileLinkIcon, self._query_association, "action"))
        self._btn_online = self._register_text("online", self._button("", QtWidgets.QStyle.SP_DriveNetIcon, self._online_verify, "action"))
        self._btn_open = self._register_text("open_location", self._button("", QtWidgets.QStyle.SP_DirOpenIcon, self._open_containing_folder, "action"))
        self._btn_delete = self._register_text("move_recycle", self._button("", QtWidgets.QStyle.SP_TrashIcon, self._delete_selected, "deleteAction"))
        for button in (self._btn_identify, self._btn_online, self._btn_open, self._btn_delete):
            button.setMinimumHeight(42)
        actions.addWidget(self._btn_identify, 0, 0)
        actions.addWidget(self._btn_online, 0, 1)
        actions.addWidget(self._btn_open, 1, 0)
        actions.addWidget(self._btn_delete, 1, 1)
        detail.addLayout(actions)
        detail.addStretch()
        layout.addWidget(card, 1)
        
        # 右侧：文档预览
        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(24, 20, 24, 20)
        preview_layout.setSpacing(12)
        
        preview_title = self._register_text("preview_title", QLabel())
        preview_title.setObjectName("sectionTitle")
        preview_layout.addWidget(preview_title)
        
        self._detail_preview_text = QtWidgets.QPlainTextEdit()
        self._detail_preview_text.setReadOnly(True)
        self._detail_preview_text.setStyleSheet(
            "QPlainTextEdit { background:#fafbfc; border:1px solid #e1e5ea; border-radius:6px; "
            "font-family:Consolas,'Microsoft YaHei',monospace; font-size:13px; }"
        )
        self._detail_preview_text.setPlaceholderText(self._tr("preview_hint"))
        preview_layout.addWidget(self._detail_preview_text, 1)
        
        layout.addWidget(preview_card, 1)
        return page

    def _build_scan_page(self):
        page = QWidget(); outer = QVBoxLayout(page); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(12)
        controls = QFrame(); controls.setObjectName("card"); c = QVBoxLayout(controls); c.setContentsMargins(18, 14, 18, 14)
        row1 = QHBoxLayout(); self._scan_path_label = QLabel(self._scan_path); self._scan_path_label.setObjectName("pathBar"); self._scan_path_label.setToolTip(self._scan_path); row1.addWidget(self._scan_path_label, 1)
        current = self._register_text("current_dir", QPushButton()); current.clicked.connect(self._scan_use_current)
        drive = self._register_text("current_drive", QPushButton()); drive.clicked.connect(self._scan_use_drive)
        choose = self._register_text("choose_dir", QPushButton()); choose.clicked.connect(self._scan_choose_folder)
        row1.addWidget(current); row1.addWidget(drive); row1.addWidget(choose); c.addLayout(row1)
        row2 = QHBoxLayout(); row2.addWidget(self._register_text("min_size", QLabel())); self._threshold = TriangleDoubleSpinBox(); self._threshold.setObjectName("thresholdSpin"); self._threshold.setRange(0, 102400); self._threshold.setValue(100); self._threshold.setDecimals(0); self._threshold.setButtonSymbols(QAbstractSpinBox.UpDownArrows); row2.addWidget(self._threshold)
        row2.addWidget(self._register_text("max_results", QLabel())); self._top_n = TriangleSpinBox(); self._top_n.setObjectName("topNSpin"); self._top_n.setRange(10, 2000); self._top_n.setValue(100); self._top_n.setButtonSymbols(QAbstractSpinBox.UpDownArrows); row2.addWidget(self._top_n)
        self._scan_start = self._register_text("start_scan", self._button("", QtWidgets.QStyle.SP_MediaPlay, self._start_scan, "primary"))
        self._scan_cancel = self._register_text("cancel_scan", self._button("", QtWidgets.QStyle.SP_MediaStop, self._cancel_scan)); self._scan_cancel.setEnabled(False)
        row2.addWidget(self._scan_start); row2.addWidget(self._scan_cancel); row2.addStretch(); c.addLayout(row2)
        self._scan_progress = QProgressBar(); self._scan_progress.setRange(0, 1); self._scan_progress.setValue(0); self._scan_progress.setFixedHeight(10); self._scan_progress.setTextVisible(False); c.addWidget(self._scan_progress)
        self._scan_status = self._register_text("scan_intro", QLabel()); self._scan_status.setWordWrap(True); self._scan_status.setMinimumHeight(40); c.addWidget(self._scan_status); outer.addWidget(controls)

        results = QTabWidget(); self._large_files = self._result_tree(["名称", "实际占用", "逻辑大小", "修改时间", "来源软件", "完整路径"])
        self._large_folders = self._result_tree(["文件夹", "实际占用", "逻辑大小", "文件数", "子文件夹数", "来源软件", "完整路径"])
        self._suggestions = self._result_tree(["建议等级", "名称", "可释放空间", "原因", "风险", "完整路径"])
        self._garbage_files = self._result_tree(["类别", "名称", "实际占用", "修改时间", "建议", "风险", "完整路径"])
        self._scan_result_tabs = results
        results.addTab(self._large_files, ""); results.addTab(self._large_folders, ""); results.addTab(self._suggestions, ""); results.addTab(self._garbage_files, "")
        outer.addWidget(results, 1)
        actions = QHBoxLayout(); actions.addStretch()
        open_btn = self._register_text("open_location", QPushButton()); open_btn.clicked.connect(self._open_scan_result)
        copy_btn = self._register_text("copy_path", QPushButton()); copy_btn.clicked.connect(self._copy_scan_result)
        delete_btn = self._register_text("move_recycle", QPushButton()); delete_btn.setObjectName("danger"); delete_btn.clicked.connect(self._delete_scan_result)
        clean_btn = self._register_text("clean_selected", QPushButton()); clean_btn.setObjectName("danger"); clean_btn.clicked.connect(self._clean_junk_selected)
        actions.addWidget(open_btn); actions.addWidget(copy_btn); actions.addWidget(clean_btn); actions.addWidget(delete_btn); outer.addLayout(actions)
        return page

    def _result_tree(self, headers):
        tree = QTreeWidget(); tree.setHeaderLabels(headers); tree.setAlternatingRowColors(True); tree.setTextElideMode(Qt.ElideMiddle)
        tree.header().setSectionResizeMode(QHeaderView.ResizeToContents); tree.header().setStretchLastSection(True)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pos, target=tree: self._on_scan_context_menu(target, pos))
        tree.itemDoubleClicked.connect(lambda *_: self._open_scan_result()); return tree

    def _build_search_page(self):
        """构建快速搜索页面（文件名搜索 + 内容搜索 + 预览）"""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        # ── 搜索控制区 ──
        controls = QFrame(); controls.setObjectName("card")
        c = QVBoxLayout(controls); c.setContentsMargins(18, 14, 18, 14)

        # 搜索模式标签页（替代下拉菜单）
        self._search_tabs = QTabWidget()
        self._search_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #d7dce2; border-radius: 6px; padding: 0; }
            QTabBar::tab { padding: 8px 16px; margin-right: 4px; }
            QTabBar::tab:selected { background: #4a90e2; color: white; border-radius: 4px; }
        """)
        
        # 标签页1：文件名搜索
        name_search_page = QWidget()
        name_layout = QVBoxLayout(name_search_page)
        name_layout.setContentsMargins(8, 8, 8, 8)
        name_hint = QLabel("按文件名搜索，支持通配符 * 和 ?")
        name_hint.setStyleSheet("color:#73808c; font-size:12px;")
        name_layout.addWidget(name_hint)
        name_layout.addStretch()
        self._search_tabs.addTab(name_search_page, "📄 文件名搜索")
        
        # 标签页2：内容搜索
        content_search_page = QWidget()
        content_layout = QVBoxLayout(content_search_page)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_hint = QLabel("搜索文档内容（PDF、Word、Excel、PPT、TXT 等）")
        content_hint.setStyleSheet("color:#73808c; font-size:12px;")
        content_layout.addWidget(content_hint)
        content_layout.addStretch()
        self._search_tabs.addTab(content_search_page, "📖 内容搜索")
        
        # 标签页切换事件
        self._search_tabs.currentChanged.connect(self._on_search_tab_changed)
        c.addWidget(self._search_tabs)

        # 搜索输入框（共享）
        search_row = QHBoxLayout()
        self._search_input = QtWidgets.QLineEdit()
        self._search_input.setPlaceholderText("输入关键词搜索...")
        self._search_input.setMinimumHeight(36)
        self._search_input.textChanged.connect(self._on_search_query_changed)
        search_row.addWidget(self._search_input, 1)

        self._search_btn = QPushButton("搜索")
        self._search_btn.setMinimumHeight(36)
        self._search_btn.setMinimumWidth(80)
        self._search_btn.clicked.connect(self._do_search)
        self._search_btn.setStyleSheet("QPushButton { background: #4a90e2; color: white; border: none; border-radius: 6px; font-weight: 600; } QPushButton:hover { background: #357abd; }")
        search_row.addWidget(self._search_btn)
        c.addLayout(search_row)

        # 过滤条件行
        filter_row = QHBoxLayout()
        
        # 搜索范围
        filter_row.addWidget(QLabel("搜索范围："))
        self._search_scope_combo = QComboBox()
        self._search_scope_combo.addItems(["🌐 全局搜索", "📂 当前目录", "📂 选择目录..."])
        self._search_scope_combo.setFixedWidth(150)
        self._search_scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        filter_row.addWidget(self._search_scope_combo)
        
        filter_row.addSpacing(20)
        
        # 文件格式
        filter_row.addWidget(QLabel("文件格式："))
        self._search_format_combo = QComboBox()
        self._search_format_combo.addItems([
            "全部格式",
            "📄 文档 (PDF/Word/Excel/PPT)",
            "🖼 图片 (JPG/PNG/GIF/BMP)",
            "🎬 视频 (MP4/AVI/MKV)",
            "🎵 音频 (MP3/WAV/FLAC)",
            "📦 压缩包 (ZIP/RAR/7Z)",
            "⚙️ 自定义扩展名..."
        ])
        self._search_format_combo.setFixedWidth(200)
        self._search_format_combo.currentIndexChanged.connect(self._on_format_changed)
        filter_row.addWidget(self._search_format_combo)
        
        filter_row.addStretch()
        c.addLayout(filter_row)

        # 索引状态行
        index_row = QHBoxLayout()
        self._index_status_label = QLabel(self._tr("index_none"))
        self._index_status_label.setStyleSheet("color:#52606d; font-size:12px;")
        index_row.addWidget(self._index_status_label, 1)

        # 刷新索引按钮（增量更新）
        self._refresh_index_btn = QPushButton("🔄 刷新索引")
        self._refresh_index_btn.setFixedHeight(30)
        self._refresh_index_btn.clicked.connect(self._refresh_index)
        self._refresh_index_btn.setEnabled(False)
        index_row.addWidget(self._refresh_index_btn)

        # 重建索引按钮（强制重建）
        self._rebuild_index_btn = QPushButton("🔨 重建索引")
        self._rebuild_index_btn.setFixedHeight(30)
        self._rebuild_index_btn.clicked.connect(self._rebuild_index)
        self._rebuild_index_btn.setEnabled(False)
        self._rebuild_index_btn.setStyleSheet("QPushButton { color: #e67e22; border: 1px solid #e67e22; } QPushButton:hover { background: #fef5ec; }")
        index_row.addWidget(self._rebuild_index_btn)

        # 取消索引按钮
        self._cancel_index_btn = self._register_text("index_cancel", self._button("", QtWidgets.QStyle.SP_DialogCancelButton, self._cancel_index))
        self._cancel_index_btn.setFixedHeight(30)
        self._cancel_index_btn.setEnabled(False)
        index_row.addWidget(self._cancel_index_btn)

        c.addLayout(index_row)

        # 进度条
        self._search_progress = QProgressBar()
        self._search_progress.setRange(0, 1)
        self._search_progress.setValue(0)
        self._search_progress.setVisible(False)
        c.addWidget(self._search_progress)

        outer.addWidget(controls)

        # ── 搜索结果 + 预览（左右分栏） ──
        split = QtWidgets.QSplitter(Qt.Horizontal)

        # 左侧：结果列表
        left = QFrame(); left.setObjectName("card")
        left_layout = QVBoxLayout(left); left_layout.setContentsMargins(12, 12, 12, 12)

        self._search_result_count = QLabel("")
        self._search_result_count.setStyleSheet("color:#52606d; font-size:12px; padding-bottom:4px;")
        left_layout.addWidget(self._search_result_count)

        self._search_result_tree = QTreeWidget()
        self._search_result_tree.setHeaderLabels([self._tr("name"), self._tr("size"), self._tr("mtime"), self._tr("full_path")])
        self._search_result_tree.setAlternatingRowColors(True)
        self._search_result_tree.setTextElideMode(Qt.ElideMiddle)
        # 设置列宽可调整
        self._search_result_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self._search_result_tree.header().setStretchLastSection(True)
        # 启用点击列头排序
        self._search_result_tree.setSortingEnabled(True)
        self._search_result_tree.header().setSortIndicatorShown(True)
        self._search_result_tree.itemClicked.connect(self._on_search_result_clicked)
        self._search_result_tree.itemDoubleClicked.connect(self._on_search_result_double_clicked)
        self._search_result_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._search_result_tree.customContextMenuRequested.connect(self._on_search_result_context_menu)
        left_layout.addWidget(self._search_result_tree, 1)

        split.addWidget(left)

        # 右侧：预览面板
        right = QFrame(); right.setObjectName("card")
        right.setMinimumWidth(320)
        right_layout = QVBoxLayout(right); right_layout.setContentsMargins(12, 12, 12, 12)

        preview_title = self._register_text("preview_title", QLabel())
        preview_title.setObjectName("sectionTitle")
        right_layout.addWidget(preview_title)

        self._preview_text = QtWidgets.QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setStyleSheet("QTextEdit { background:#fafbfc; border:1px solid #e1e5ea; border-radius:6px; font-family:Consolas,'Microsoft YaHei',monospace; font-size:13px; }")
        self._preview_text.setPlaceholderText(self._tr("preview_hint"))
        right_layout.addWidget(self._preview_text, 1)

        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split, 1)
        return page

    def _show_search_tab(self):
        """兼容旧引用"""
        self._show_search_view()

    def _on_search_mode_changed(self, index):
        """搜索模式切换（文件名/内容）- 兼容旧调用"""
        self._on_search_tab_changed(index)

    def _on_search_tab_changed(self, index):
        """搜索标签页切换（文件名/内容）"""
        if index == 0:
            self._search_input.setPlaceholderText("输入文件名搜索，支持通配符 * 和 ?")
        else:
            self._search_input.setPlaceholderText("输入文档内容关键词搜索...")
        # 切换后自动重新搜索
        if self._search_input.text().strip():
            self._do_search()

    def _on_scope_changed(self, index):
        """搜索范围变化"""
        if index == 2:  # 选择目录
            folder = QFileDialog.getExistingDirectory(self, "选择搜索目录", self.current_path)
            if folder:
                self._search_scope_combo.setItemText(2, f"📂 {folder}")
            else:
                self._search_scope_combo.setCurrentIndex(0)
        # 范围变化后重新搜索
        if self._search_input.text().strip():
            self._do_search()

    def _on_format_changed(self, index):
        """文件格式变化"""
        if index == 6:  # 自定义扩展名
            ext, ok = QInputDialog.getText(self, "自定义扩展名", "请输入扩展名（如 .pdf,.docx）:")
            if ok and ext:
                self._search_format_combo.setItemText(6, f"⚙️ {ext}")
            else:
                self._search_format_combo.setCurrentIndex(0)
        # 格式变化后重新搜索
        if self._search_input.text().strip():
            self._do_search()

    def _get_search_filters(self):
        """获取当前搜索过滤条件"""
        # 搜索范围
        scope_index = self._search_scope_combo.currentIndex()
        path_filter = ""
        if scope_index == 1:  # 当前目录
            path_filter = self.current_path
        elif scope_index == 2:  # 选择的目录
            text = self._search_scope_combo.itemText(2)
            if text.startswith("📂 "):
                path_filter = text[2:]
        
        # 文件格式
        format_index = self._search_format_combo.currentIndex()
        ext_filter = ""
        if format_index == 1:  # 文档
            ext_filter = ".pdf,.docx,.xlsx,.pptx,.txt"
        elif format_index == 2:  # 图片
            ext_filter = ".jpg,.jpeg,.png,.gif,.bmp,.webp"
        elif format_index == 3:  # 视频
            ext_filter = ".mp4,.avi,.mkv,.mov,.wmv"
        elif format_index == 4:  # 音频
            ext_filter = ".mp3,.wav,.flac,.aac,.ogg"
        elif format_index == 5:  # 压缩包
            ext_filter = ".zip,.rar,.7z,.tar,.gz"
        elif format_index == 6:  # 自定义
            text = self._search_format_combo.itemText(6)
            if text.startswith("⚙️ "):
                ext_filter = text[3:]
        
        return path_filter, ext_filter

    def _on_search_query_changed(self, text):
        """输入变化时启动防抖定时器（300ms）"""
        if self._search_timer:
            self._search_timer.stop()
        self._search_timer = QtCore.QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._search_timer.start(300)

    def _do_search(self):
        """执行搜索"""
        if self._search_timer:
            self._search_timer.stop()

        query = self._search_input.text().strip()
        if not query:
            self._search_result_tree.clear()
            self._search_result_count.setText("")
            self._preview_text.clear()
            return

        mode = self._search_tabs.currentIndex()
        if mode == 0:
            self._do_name_search(query)
        else:
            self._do_content_search(query)

    def _do_name_search(self, query):
        """文件名搜索"""
        if not self.quick_search_engine.is_indexed:
            self._search_result_count.setText(self._tr("index_none"))
            self._search_result_tree.clear()
            return

        path_filter, ext_filter = self._get_search_filters()
        results = self.quick_search_engine.search(query, max_results=500, path_filter=path_filter, ext_filter=ext_filter)
        self._populate_search_results(results)

    def _do_content_search(self, query):
        """内容搜索"""
        if not self.fulltext_search_engine.is_indexed:
            self._search_result_count.setText(self._tr("index_none"))
            self._search_result_tree.clear()
            return

        path_filter, ext_filter = self._get_search_filters()
        results = self.fulltext_search_engine.search(query, max_results=200, path_filter=path_filter, ext_filter=ext_filter)
        self._populate_search_results(results, is_content=True)

    def _populate_search_results(self, results, is_content=False):
        """填充搜索结果到树控件"""
        self._search_result_tree.clear()

        if not results:
            self._search_result_count.setText(self._tr("no_results"))
            return

        for item_data in results:
            path = item_data.get("path", "")
            name = item_data.get("name", os.path.basename(path))
            size = item_data.get("size", 0)
            mtime = item_data.get("mtime", 0)
            snippet = item_data.get("snippet", "")

            display_name = name
            if is_content and snippet:
                # 内容搜索显示 snippet 作为 tooltip
                display_name = name

            # 格式化修改时间
            mtime_str = format_time(mtime) if mtime else ""

            tree_item = QTreeWidgetItem([
                display_name,
                format_size(size),
                mtime_str,
                path
            ])
            tree_item.setData(0, Qt.UserRole, path)
            tree_item.setData(0, Qt.UserRole + 1, snippet if is_content else "")
            tree_item.setData(2, Qt.UserRole + 2, mtime)  # 存储原始时间戳用于排序
            tree_item.setToolTip(0, snippet if is_content else path)
            tree_item.setToolTip(3, path)
            self._search_result_tree.addTopLevelItem(tree_item)

        count_text = self._tr("result_count").replace("{count}", str(len(results)))
        self._search_result_count.setText(count_text)

    def _on_search_result_clicked(self, item, column):
        """点击搜索结果时预览内容，并高亮搜索关键词"""
        path = item.data(0, Qt.UserRole)
        snippet = item.data(0, Qt.UserRole + 1)
        if not path:
            return

        # 获取当前搜索关键词
        query = self._search_input.text().strip()

        # 内容搜索模式：优先显示完整文件内容（高亮关键词）
        mode = self._search_tabs.currentIndex()
        if mode == 1:
            # 内容搜索 — 提取完整文件内容并高亮
            if self.content_extractor.can_extract(path):
                try:
                    content = self.content_extractor.extract_preview(path, max_chars=10000)
                    if content:
                        self._preview_text.setHtml(self._highlight_html(content[:10000], query))
                    else:
                        self._preview_text.setPlainText(self._tr("preview_no_support"))
                except Exception as e:
                    self._preview_text.setPlainText(f"预览失败: {e}")
            else:
                self._preview_text.setPlainText(self._tr("preview_no_support"))
            return

        # 文件名搜索模式：提取文件内容预览
        if self.content_extractor.can_extract(path):
            try:
                content = self.content_extractor.extract_preview(path, max_chars=8000)
                if content:
                    self._preview_text.setHtml(self._highlight_html(content[:8000], query))
                else:
                    self._preview_text.setPlainText(self._tr("preview_no_support"))
            except Exception as e:
                self._preview_text.setPlainText(f"预览失败: {e}")
        else:
            self._preview_text.setPlainText(self._tr("preview_no_support"))

    def _highlight_html(self, text: str, keyword: str) -> str:
        """将文本转为 HTML，并用黄色背景高亮关键词。"""
        if not keyword:
            # 无关键词时，转义纯文本返回
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        # 先转义 HTML 特殊字符
        import html as html_mod
        escaped = html_mod.escape(text)
        # 转义关键词中的特殊字符用于正则
        keyword_esc = re.escape(keyword)
        # 大小写不敏感替换，用 <span> 标记高亮
        pattern = re.compile(keyword_esc, re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f'<span style="background-color:#fff3b0; color:#d44900; font-weight:600;">{m.group(0)}</span>',
            escaped
        )
        # 换行转 <br>
        escaped = escaped.replace("\n", "<br>")
        return escaped

    def _on_search_result_double_clicked(self, item, column):
        """双击搜索结果打开文件"""
        path = item.data(0, Qt.UserRole)
        if path and os.path.exists(path):
            try:
                if os.path.isdir(path):
                    os.startfile(path)
                else:
                    os.startfile(os.path.dirname(path))
            except Exception as e:
                QMessageBox.warning(self, "打开失败", str(e))

    def _on_search_result_context_menu(self, pos):
        """搜索结果右键菜单"""
        item = self._search_result_tree.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        if not path:
            return

        menu = QMenu(self)
        open_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DirOpenIcon), self._tr("open_folder"))
        copy_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DialogSaveButton), self._tr("copy_path"))
        delete_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_TrashIcon), self._tr("move_recycle"))

        chosen = menu.exec_(self._search_result_tree.viewport().mapToGlobal(pos))
        if chosen == open_action:
            try:
                if os.path.isdir(path):
                    os.startfile(path)
                else:
                    os.startfile(os.path.dirname(path))
            except Exception as e:
                QMessageBox.warning(self, "打开失败", str(e))
        elif chosen == copy_action:
            QtWidgets.QApplication.clipboard().setText(path)
        elif chosen == delete_action:
            self._delete_path(path)

    def _refresh_index(self):
        """刷新索引（增量更新）"""
        mode = self._search_tabs.currentIndex()

        if mode == 0:
            # 文件名索引
            if self.quick_search_engine.is_indexing():
                return
            self._search_progress.setVisible(True)
            self._search_progress.setRange(0, 0)
            self._index_status_label.setText(self._tr("index_building"))
            self._refresh_index_btn.setEnabled(False)
            self._rebuild_index_btn.setEnabled(False)
            self._cancel_index_btn.setEnabled(True)

            thread = self.quick_search_engine.start_indexing(incremental=True)
            thread.progress_signal.connect(self._on_name_index_progress)
            thread.finished_signal.connect(self._on_name_index_finished)
            thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))
        else:
            # 内容索引
            if self.fulltext_search_engine.is_indexing():
                return
            self._search_progress.setVisible(True)
            self._search_progress.setRange(0, 0)
            self._index_status_label.setText(self._tr("index_building"))
            self._refresh_index_btn.setEnabled(False)
            self._rebuild_index_btn.setEnabled(False)
            self._cancel_index_btn.setEnabled(True)

            thread = self.fulltext_search_engine.start_indexing(force_reindex=False)
            thread.progress_signal.connect(self._on_content_index_progress)
            thread.finished_signal.connect(self._on_content_index_finished)
            thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))

    def _rebuild_index(self):
        """重建索引（强制重建）"""
        reply = QMessageBox.question(
            self,
            "确认重建索引",
            "重建索引将删除现有索引并重新扫描所有文件，这可能需要较长时间。\n\n确定要重建索引吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        mode = self._search_tabs.currentIndex()

        if mode == 0:
            # 文件名索引
            if self.quick_search_engine.is_indexing():
                self.quick_search_engine.cancel_indexing()
            self._search_progress.setVisible(True)
            self._search_progress.setRange(0, 0)
            self._index_status_label.setText(self._tr("index_building"))
            self._refresh_index_btn.setEnabled(False)
            self._rebuild_index_btn.setEnabled(False)
            self._cancel_index_btn.setEnabled(True)

            thread = self.quick_search_engine.force_rebuild()
            thread.progress_signal.connect(self._on_name_index_progress)
            thread.finished_signal.connect(self._on_name_index_finished)
            thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))
        else:
            # 内容索引
            if self.fulltext_search_engine.is_indexing():
                self.fulltext_search_engine.cancel_indexing()
            self._search_progress.setVisible(True)
            self._search_progress.setRange(0, 0)
            self._index_status_label.setText(self._tr("index_building"))
            self._refresh_index_btn.setEnabled(False)
            self._rebuild_index_btn.setEnabled(False)
            self._cancel_index_btn.setEnabled(True)

            thread = self.fulltext_search_engine.force_reindex()
            thread.progress_signal.connect(self._on_content_index_progress)
            thread.finished_signal.connect(self._on_content_index_finished)
            thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))

    def _auto_rebuild_index_on_startup(self):
        """启动时自动重建两个索引（文件名 + 内容）。"""
        # 先重建文件名索引
        if not self.quick_search_engine.is_indexing():
            name_thread = self.quick_search_engine.force_rebuild()
            name_thread.progress_signal.connect(self._on_name_index_progress)
            name_thread.finished_signal.connect(self._on_name_index_finished)
            name_thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))

        # 同时重建内容索引
        if not self.fulltext_search_engine.is_indexing():
            self._search_progress.setVisible(True)
            self._search_progress.setRange(0, 0)
            self._index_status_label.setText(self._tr("index_building"))
            self._refresh_index_btn.setEnabled(False)
            self._rebuild_index_btn.setEnabled(False)
            self._cancel_index_btn.setEnabled(True)

            content_thread = self.fulltext_search_engine.force_reindex()
            content_thread.progress_signal.connect(self._on_content_index_progress)
            content_thread.finished_signal.connect(self._on_content_index_finished)
            content_thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "索引错误", msg))

    def _cancel_index(self):
        """取消索引"""
        mode = self._search_tabs.currentIndex()
        if mode == 0:
            self.quick_search_engine.cancel_indexing()
        else:
            self.fulltext_search_engine.cancel_indexing()
        self._cancel_index_btn.setEnabled(False)

    def _on_name_index_progress(self, count, current_path):
        """文件名索引进度"""
        self._index_status_label.setText(f"{self._tr('index_building')} ({count} files)")

    def _on_name_index_finished(self, total, elapsed):
        """文件名索引完成"""
        self._search_progress.setVisible(False)
        self._index_status_label.setText(f"{self._tr('index_complete')}: {total} files ({elapsed:.1f}s)")
        self._refresh_index_btn.setEnabled(True)
        self._rebuild_index_btn.setEnabled(True)
        self._cancel_index_btn.setEnabled(False)
        # 自动触发搜索
        if self._search_input.text().strip():
            self._do_search()

    def _on_content_index_progress(self, current, total, current_file):
        """内容索引进度"""
        if total > 0:
            self._search_progress.setRange(0, total)
            self._search_progress.setValue(current)
        self._index_status_label.setText(f"{self._tr('index_building')} ({current}/{total})")

    def _on_content_index_finished(self, total, elapsed):
        """内容索引完成"""
        self._search_progress.setVisible(False)
        self._search_progress.setRange(0, 1)
        self._index_status_label.setText(f"{self._tr('index_complete')}: {total} documents ({elapsed:.1f}s)")
        self._refresh_index_btn.setEnabled(True)
        self._rebuild_index_btn.setEnabled(True)
        self._cancel_index_btn.setEnabled(False)
        # 自动触发搜索
        if self._search_input.text().strip():
            self._do_search()

    def _update_search_index_status(self):
        """更新索引状态显示"""
        mode = self._search_tabs.currentIndex()
        if mode == 0:
            if self.quick_search_engine.is_indexed:
                count = self.quick_search_engine.total_files
                last_time = self.quick_search_engine.last_index_time
                time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_time)) if last_time else "未知"
                self._index_status_label.setText(f"索引已就绪：{count} 个文件 · 上次更新 {time_str}")
                self._refresh_index_btn.setEnabled(True)
                self._rebuild_index_btn.setEnabled(True)
            else:
                self._index_status_label.setText(self._tr("index_none"))
                self._refresh_index_btn.setEnabled(False)
                self._rebuild_index_btn.setEnabled(False)
        else:
            if self.fulltext_search_engine.is_indexed:
                count = self.fulltext_search_engine.total_documents
                last_time = self.fulltext_search_engine.last_index_time
                time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_time)) if last_time else "未知"
                self._index_status_label.setText(f"索引已就绪：{count} 个文档 · 上次更新 {time_str}")
                self._refresh_index_btn.setEnabled(True)
                self._rebuild_index_btn.setEnabled(True)
            else:
                self._index_status_label.setText(self._tr("index_none"))
                self._refresh_index_btn.setEnabled(False)
                self._rebuild_index_btn.setEnabled(False)

    def _available_drives(self):
        roots = []
        try:
            for part in psutil.disk_partitions(all=False):
                drive, _ = os.path.splitdrive(part.mountpoint)
                root = drive.upper() + os.sep if drive else part.mountpoint
                if os.path.isdir(root) and root not in roots: roots.append(root)
        except Exception: pass
        if os.name == "nt":
            try:
                import ctypes
                mask = ctypes.windll.kernel32.GetLogicalDrives()
                for i in range(26):
                    root = f"{chr(65+i)}:{os.sep}"
                    if mask & (1 << i) and os.path.isdir(root) and root not in roots: roots.append(root)
            except Exception: pass
        return sorted(roots)

    def _populate_drives(self):
        self._drive_combo.blockSignals(True); self._drive_combo.clear()
        for root in self._available_drives(): self._drive_combo.addItem(f"磁盘 {root}", root)
        self._drive_combo.blockSignals(False)

    def _navigate_to(self, path, add_history=True):
        target = os.path.abspath(os.path.normpath(path))
        if not os.path.isdir(target):
            QMessageBox.warning(self, "导航失败", f"目录不存在或无法访问：\n{target}"); return False
        if add_history and os.path.normcase(target) != os.path.normcase(self.current_path):
            self._nav_history.append(self.current_path); self._nav_history = self._nav_history[-100:]
        self.current_path = target; self.refresh_folder(); return True

    def refresh_folder(self):
        self.tree.clear(); count = 0
        try:
            entries = sorted(os.scandir(self.current_path), key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
            for entry in entries:
                try:
                    is_dir = entry.is_dir(follow_symlinks=False); size = 0 if is_dir else entry.stat(follow_symlinks=False).st_size
                    item = QTreeWidgetItem([entry.name, "—" if is_dir else format_size(size)])
                    item.setIcon(0, self._icon(QtWidgets.QStyle.SP_DirIcon if is_dir else QtWidgets.QStyle.SP_FileIcon))
                    item.setData(0, Qt.UserRole, entry.path); item.setData(1, Qt.UserRole, is_dir); item.setToolTip(0, entry.name); self.tree.addTopLevelItem(item); count += 1
                except OSError: continue
        except (PermissionError, OSError) as exc:
            QMessageBox.warning(self, "读取失败", f"{self.current_path}\n{exc}")
        self._update_nav_state()
        self._status_label.setText((f"Current folder: {self.current_path}    Items: {count}" if self.language == "en" else f"当前目录：{self.current_path}    项目数：{count}"))

    def _update_nav_state(self):
        anchor = Path(self.current_path).anchor; at_root = os.path.normcase(self.current_path.rstrip("\\/")) == os.path.normcase(anchor.rstrip("\\/"))
        self._btn_up.setEnabled(not at_root); self._btn_root.setEnabled(not at_root); self._btn_back.setEnabled(bool(self._nav_history))
        self._full_path = self.current_path; self._path_bar.setToolTip(self._full_path); self._refresh_path_elide()
        drive = os.path.splitdrive(self.current_path)[0]
        self._drive_combo.blockSignals(True)
        for i in range(self._drive_combo.count()):
            if os.path.normcase(os.path.splitdrive(self._drive_combo.itemData(i))[0]) == os.path.normcase(drive): self._drive_combo.setCurrentIndex(i); break
        self._drive_combo.blockSignals(False)

    def _refresh_path_elide(self):
        width = max(40, self._path_bar.width() - 18); self._path_bar.setText(self._path_bar.fontMetrics().elidedText(self._full_path, Qt.ElideMiddle, width))

    def resizeEvent(self, event):
        super().resizeEvent(event); QtCore.QTimer.singleShot(0, self._refresh_path_elide)

    def _go_back_history(self):
        if self._nav_history: self._navigate_to(self._nav_history.pop(), False)

    def _go_up(self):
        parent = str(Path(self.current_path).parent)
        if os.path.normcase(parent) != os.path.normcase(self.current_path): self._navigate_to(parent)

    def _go_root(self):
        root = Path(self.current_path).anchor
        if root: self._navigate_to(root)

    def _on_drive_selected(self, index):
        root = self._drive_combo.itemData(index)
        if root and os.path.normcase(os.path.splitdrive(root)[0]) != os.path.normcase(os.path.splitdrive(self.current_path)[0]): self._navigate_to(root)

    def _on_double_click(self, item, _column):
        if item.data(1, Qt.UserRole): self._navigate_to(item.data(0, Qt.UserRole))

    def _on_item_clicked(self, item, _column): self._show_detail(item.data(0, Qt.UserRole), item.data(1, Qt.UserRole))

    def _deletion_advice(self, path, is_dir, identity):
        norm = os.path.normcase(os.path.abspath(path))
        protected = [os.environ.get("WINDIR", r"C:\Windows"), os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), os.environ.get("ProgramData", r"C:\ProgramData")]
        is_protected = any(p and (norm == os.path.normcase(p) or norm.startswith(os.path.normcase(p) + os.sep)) for p in protected)
        cloud = identity.sync_software not in ("普通本地文件或文件夹", "Local file or folder")
        if self.language == "en":
            if is_protected: return "Do not delete: this item is inside a system or installed-program directory and deletion may break Windows or an application."
            if "OneDriveTemp" in path: return "Do not delete manually: this is a OneDrive temporary sync location. Deletion may interrupt synchronization or be recreated automatically."
            if cloud: return "Use caution: this item is managed by sync software. Deletion may also remove it from the cloud and other devices."
            if is_dir: return "Review first: deleting this folder also deletes all files and subfolders inside it."
            ext = os.path.splitext(path)[1].lower()
            if ext in {".tmp", ".temp", ".dmp"}: return "Usually safe after closing related apps, but temporary recovery or diagnostic data may be lost."
            if ext in {".log", ".bak", ".old"}: return "Review first: it may contain troubleshooting information or a backup needed for recovery."
            return "No clear safe-cleanup signature was found. Confirm the file's purpose and backup status before deleting it."
        if is_protected: return "不建议删除：该项目位于系统或已安装程序目录，删除可能导致 Windows 或软件无法正常运行。"
        if "onedrivetemp" in path.lower(): return "不建议手动删除：这是 OneDrive 临时同步位置，删除可能中断同步，也可能被系统自动重新创建。"
        if cloud: return "谨慎处理：该项目由同步软件管理，删除操作可能同步到云端和其他设备。"
        if is_dir: return "请先检查：删除文件夹会同时删除其中的全部文件和子文件夹。"
        ext = os.path.splitext(path)[1].lower()
        if ext in {".tmp", ".temp", ".dmp"}: return "通常可在关闭相关软件后删除，但可能丢失临时恢复或诊断数据。"
        if ext in {".log", ".bak", ".old"}: return "建议先检查：文件可能包含排障记录或恢复所需备份。"
        return "未发现明确的安全清理特征。删除前请确认文件用途、备份状态及是否仍被软件使用。"

    def _localized_identity(self, identity):
        if self.language == "zh":
            return identity.sync_software, identity.relation, identity.default_app, "；".join(identity.evidence) or "无可靠证据"
        sync_map = {
            "普通本地文件或文件夹": "Local file or folder",
            "未识别": "Unknown",
            "Microsoft OneDrive 工作或学校版": "Microsoft OneDrive Work or School",
        }
        sync = sync_map.get(identity.sync_software, identity.sync_software)
        relation_map = {
            "未发现已知软件或同步目录": "No known software or sync location detected",
            "OneDrive 个人版临时同步目录": "OneDrive Personal temporary sync location",
            "OneDrive 临时同步目录": "OneDrive temporary sync location",
            "已安装软件目录或其子目录": "Installed application directory or subdirectory",
        }
        relation = relation_map.get(identity.relation, identity.relation)
        app_map = {
            "不适用": "Not applicable",
            "未识别（文件没有扩展名）": "Unknown (file has no extension)",
        }
        app = app_map.get(identity.default_app, identity.default_app)
        evidence = "; ".join(identity.evidence) if identity.evidence else "No reliable evidence"
        evidence_replacements = {
            "路径位于 OneDriveTemp": "Path is inside OneDriveTemp",
            "检测到 -Personal 账户特征": "Detected the -Personal account marker",
            "Windows Shell 默认应用关联": "Windows Shell default-app association",
            "未匹配本机同步根目录、安装记录或已知软件路径": "No local sync root, installed-app record, or known software path matched",
        }
        for chinese, english in evidence_replacements.items():
            evidence = evidence.replace(chinese, english)
        return sync, relation, app, evidence

    def _folder_size(self, path):
        """Calculate a folder's logical size without following links/reparse points."""
        total = 0
        try:
            for root, dirs, files in os.walk(path, topdown=True, followlinks=False):
                dirs[:] = [name for name in dirs if not os.path.islink(os.path.join(root, name))]
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        if not os.path.islink(file_path):
                            total += os.stat(file_path, follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            return 0
        return total

    def _show_detail(self, path, is_dir):
        try:
            self._detail_path = path
            stat = os.stat(path, follow_symlinks=False); identity = FileAssociation(path).get_detailed_identity(); self._last_identity = identity
            sync, relation, default_app, evidence = self._localized_identity(identity)
            ext = os.path.splitext(path)[1].lower()
            item_type = ("Folder" if is_dir else (f"{ext} file" if ext else "File without extension")) if self.language == "en" else ("文件夹" if is_dir else (f"{ext} 文件" if ext else "无扩展名文件"))
            logical_size = self._folder_size(path) if is_dir else stat.st_size
            values = {
                "name": os.path.basename(path), "path": path, "size": format_size(logical_size),
                "mtime": format_time(stat.st_mtime), "ftype": item_type,
                "sync": sync, "relation": relation, "assoc": default_app + (f"\n{identity.app_path}" if identity.app_path else ""),
                "confidence": f"{identity.confidence*100:.0f}%", "evidence": evidence,
                "advice": self._deletion_advice(path, is_dir, identity),
            }
            for key, value in values.items(): self._info_labels[key].setText(value); self._info_labels[key].setToolTip(value)
            
            # 更新预览面板
            if hasattr(self, '_detail_preview_text'):
                if is_dir:
                    self._detail_preview_text.setPlainText("（文件夹无法预览）")
                elif self.content_extractor.can_extract(path):
                    try:
                        content = self.content_extractor.extract_preview(path, max_chars=10000)
                        if content:
                            self._detail_preview_text.setPlainText(content[:10000])
                        else:
                            self._detail_preview_text.setPlainText(self._tr("preview_no_support"))
                    except Exception as e:
                        self._detail_preview_text.setPlainText(f"预览失败: {e}")
                else:
                    self._detail_preview_text.setPlainText(self._tr("preview_no_support"))
        except Exception as exc: self._info_labels["name"].setText(f"读取失败：{exc}")

    def _selected_path(self, show_message=True):
        items = self.tree.selectedItems()
        if items: return items[0].data(0, Qt.UserRole)
        if show_message: QMessageBox.information(self, "提示", "请先选择文件或文件夹")
        return None

    def _query_association(self):
        path = self._selected_path()
        if not path: return
        self._show_association_for(path)

    def _show_association_for(self, path):
        info = FileAssociation(path).get_detailed_identity(); self._show_detail(path, os.path.isdir(path))
        sync, relation, app, evidence = self._localized_identity(info)
        if self.language == "en":
            text = (f"Item: {os.path.basename(path)}\n\nSource / sync software: {sync}\nRelationship: {relation}\n"
                    f"Default app: {app}\nExecutable: {info.app_path or 'Not applicable'}\n"
                    f"Confidence: {info.confidence*100:.0f}%\nEvidence: {evidence}")
            QMessageBox.information(self, "Software Identification", text)
        else:
            text = (f"项目：{os.path.basename(path)}\n\n来源/同步软件：{sync}\n关系：{relation}\n"
                    f"默认打开程序：{app}\n程序路径：{info.app_path or '不适用'}\n"
                    f"可信度：{info.confidence*100:.0f}%\n判断依据：{evidence}")
            QMessageBox.information(self, "关联软件识别结果", text)

    def _online_verify(self):
        path = self._selected_path()
        if not path: return
        self._online_verify_path(path)

    def _online_verify_path(self, path):
        info = FileAssociation(path).get_detailed_identity(); query = info.online_query
        if not query: QMessageBox.information(self, "在线核验", "没有可安全发送的查询词。完整路径和个人信息不会上传。"); return
        if QMessageBox.question(self, "在线核验", f"将只把以下查询词发送给搜索引擎，不发送完整路径或文件内容：\n\n{query}\n\n继续吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            if not self.web_search.search_online(query): QMessageBox.warning(self, "在线核验", "无法打开浏览器")

    def _open_containing_folder(self):
        path = self._selected_path()
        if path:
            try: os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
            except OSError as exc: QMessageBox.warning(self, "打开失败", str(exc))

    def _delete_path(self, path):
        if not path: return False
        if QMessageBox.question(self, "确认移至回收站", f"确定要移动以下项目吗？\n\n{path}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return False
        ok, message = self.file_operations.move_to_recycle_bin(path)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "操作结果", message)
        if ok: self.refresh_folder()
        return ok

    def _permanent_delete_path(self, path):
        if not path or not os.path.lexists(path):
            QMessageBox.warning(self, "永久删除", "所选路径已经不存在。")
            return False
        warning = ("永久删除后无法从回收站恢复。\n"
                   "如果项目位于 OneDrive、Dropbox 等同步目录，也可能从云端和其他设备删除。\n\n"
                   f"确定永久删除以下项目吗？\n\n{path}")
        if QMessageBox.question(self, "确认永久删除", warning, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return False
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            QMessageBox.information(self, "永久删除", "所选项目已永久删除。")
            return True
        except Exception as exc:
            QMessageBox.critical(self, "永久删除失败", str(exc))
            return False

    def _delete_selected(self): self._delete_path(self._selected_path())

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        self.tree.setCurrentItem(item); menu = QMenu(self)
        texts = (["Identify Software", "Verify Online", "Copy Full Path", "Open Location", "Move to Recycle Bin"] if self.language == "en" else
                 ["识别关联软件", "在线核验软件", "复制完整路径", "打开所在目录", "移至回收站"])
        identify = menu.addAction(self._icon(QtWidgets.QStyle.SP_FileLinkIcon), texts[0])
        online = menu.addAction(self._icon(QtWidgets.QStyle.SP_DriveNetIcon), texts[1])
        copy = menu.addAction(self._icon(QtWidgets.QStyle.SP_DialogSaveButton), texts[2])
        menu.addSeparator(); open_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DirOpenIcon), texts[3])
        delete = menu.addAction(self._icon(QtWidgets.QStyle.SP_TrashIcon), texts[4])
        chosen = menu.exec_(self.tree.mapToGlobal(pos))
        if chosen == identify: self._query_association()
        elif chosen == online: self._online_verify()
        elif chosen == copy: QtWidgets.QApplication.clipboard().setText(item.data(0, Qt.UserRole))
        elif chosen == open_action: self._open_containing_folder()
        elif chosen == delete: self._delete_selected()

    def _on_search(self, text):
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()): self.tree.topLevelItem(i).setHidden(bool(text and text not in self.tree.topLevelItem(i).text(0).lower()))

    def _update_disk_usage(self):
        """更新磁盘使用情况（底部横向条）"""
        # 清除旧的磁盘条
        while self._disk_bars_layout.count():
            item = self._disk_bars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        first = True
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            
            if not first:
                # 添加分隔线
                divider = QFrame()
                divider.setFrameShape(QFrame.VLine)
                divider.setStyleSheet("color: #e1e5ea;")
                divider.setMaximumHeight(24)
                self._disk_bars_layout.addWidget(divider)
            first = False
            
            # 磁盘标签
            label_text = f"{part.mountpoint}  {format_size(usage.used)} / {format_size(usage.total)} ({usage.percent:.1f}%)"
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px; color: #52606d; white-space: nowrap;")
            label.setToolTip(label_text)
            self._disk_bars_layout.addWidget(label)
            
            # 进度条
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(int(usage.percent * 10))
            bar.setToolTip(label_text)
            bar.setFixedWidth(120)
            bar.setFixedHeight(10)
            # 根据使用率设置颜色
            if usage.percent >= 90:
                bar.setStyleSheet("QProgressBar { border:0; background:#e9edf2; border-radius:5px; } QProgressBar::chunk { background:#e74c3c; border-radius:5px; }")
            elif usage.percent >= 75:
                bar.setStyleSheet("QProgressBar { border:0; background:#e9edf2; border-radius:5px; } QProgressBar::chunk { background:#e67e22; border-radius:5px; }")
            self._disk_bars_layout.addWidget(bar)

    def _show_scan_view(self):
        """切换到磁盘空间扫描视图"""
        self._main_stack.setCurrentIndex(1)
        self._scan_use_current()
        self._highlight_toolbar_button(self._scan_btn)

    def _show_search_view(self):
        """切换到快速搜索视图"""
        self._main_stack.setCurrentIndex(2)
        self._update_search_index_status()
        self._search_input.setFocus()
        self._highlight_toolbar_button(self._search_toolbar_btn)

    def _show_detail_view(self):
        """切换到文件详情视图"""
        self._main_stack.setCurrentIndex(0)
        self._highlight_toolbar_button(None)
    
    def _highlight_toolbar_button(self, active_btn):
        """高亮显示当前激活的工具栏按钮"""
        # 重置所有按钮样式
        for btn in [self._scan_btn, self._search_toolbar_btn]:
            btn.setStyleSheet("")
            btn.setProperty("class", "")
        
        # 高亮当前按钮
        if active_btn:
            active_btn.setStyleSheet("QPushButton { background-color: #4a90e2; color: white; border: 1px solid #4a90e2; }")
            active_btn.setProperty("class", "active")

    def _set_scan_path(self, path):
        self._scan_path = os.path.abspath(path); self._scan_path_label.setText(self._scan_path_label.fontMetrics().elidedText(self._scan_path, Qt.ElideMiddle, max(200, self._scan_path_label.width()-20))); self._scan_path_label.setToolTip(self._scan_path)

    def _scan_use_current(self): self._set_scan_path(self.current_path)
    def _scan_use_drive(self): self._set_scan_path(Path(self.current_path).anchor or self.current_path)
    def _scan_choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择扫描目录", self.current_path)
        if path: self._set_scan_path(path)

    def _start_scan(self):
        if self._scanner_thread and self._scanner_thread.isRunning(): return
        self._large_files.clear(); self._large_folders.clear(); self._suggestions.clear(); self._garbage_files.clear()
        self._scanner_thread = DiskScannerThread(self._scan_path, self._threshold.value(), self._top_n.value())
        self._scanner_thread.progress_signal.connect(self._scan_progress_update); self._scanner_thread.status_signal.connect(self._scan_status_update)
        self._scanner_thread.finished_signal.connect(self._scan_finished); self._scanner_thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "扫描错误", msg))
        self._scan_start.setEnabled(False); self._scan_cancel.setEnabled(True); self._scan_progress.setRange(0, 0); self._scan_status.setText((f"Scanning: {self._scan_path}" if self.language == "en" else f"正在扫描：{self._scan_path}")); self._scanner_thread.start()

    def _cancel_scan(self):
        if self._scanner_thread and self._scanner_thread.isRunning(): self._scanner_thread.cancel(); self._scan_status.setText("Cancelling scan safely..." if self.language == "en" else "正在安全取消扫描..."); self._scan_cancel.setEnabled(False)

    def _scan_progress_update(self, current, total):
        if total > 0: self._scan_progress.setRange(0, total); self._scan_progress.setValue(current)
        self._scan_status.setText((f"Scanned {current} files" if self.language == "en" else f"已扫描 {current} 个文件"))

    def _scan_status_update(self, path): self._scan_status.setText((f"Scanning: {path}" if self.language == "en" else f"正在扫描：{path}"))

    def _scan_finished(self, result):
        self._scan_start.setEnabled(True); self._scan_cancel.setEnabled(False); self._scan_progress.setRange(0, 1); self._scan_progress.setValue(1)
        if result.get("cancelled"):
            self._scan_status.setText((f"Scan cancelled after {result['total_files']} files" if self.language == "en" else f"扫描已取消，已处理 {result['total_files']} 个文件")); return
        for data in result["large_files"]:
            source = FileAssociation(data["path"]).get_detailed_identity().sync_software
            item = QTreeWidgetItem([data["name"], format_size(data["allocated"]), format_size(data["size"]), format_time(data["mtime"]), source, data["path"]]); item.setData(0, Qt.UserRole, data["path"]); self._large_files.addTopLevelItem(item)
        for data in result["large_folders"]:
            source = FileAssociation(data["path"]).get_detailed_identity().sync_software
            item = QTreeWidgetItem([data["name"], format_size(data["allocated"]), format_size(data["size"]), str(data["file_count"]), str(data["folder_count"]), source, data["path"]]); item.setData(0, Qt.UserRole, data["path"]); self._large_folders.addTopLevelItem(item)
        for data in result["suggestions"]:
            item = QTreeWidgetItem([data["level"], data["name"], format_size(data["allocated"]), data["reason"], data["risk"], data["path"]]); item.setData(0, Qt.UserRole, data["path"]); self._suggestions.addTopLevelItem(item)
        for data in result.get("garbage_files", []):
            item = QTreeWidgetItem([data["category"], data["name"], format_size(data["allocated"]), format_time(data["mtime"]), data["level"], data["risk"], data["path"]])
            item.setData(0, Qt.UserRole, data["path"]); item.setData(0, Qt.UserRole + 1, bool(data.get("safe_to_clean"))); self._garbage_files.addTopLevelItem(item)
        if self.language == "en":
            self._scan_status.setText(f"Complete: {result['total_files']} files, {result['total_folders']} folders; allocated {format_size(result['total_allocated'])}; skipped {result['skipped_reparse']} reparse points; {len(result['errors'])} errors")
        else:
            self._scan_status.setText(f"扫描完成：{result['total_files']} 个文件，{result['total_folders']} 个文件夹；实际占用 {format_size(result['total_allocated'])}；跳过重解析点 {result['skipped_reparse']} 个；错误 {len(result['errors'])} 个")

    def _active_scan_tree(self):
        widget = QtWidgets.QApplication.focusWidget()
        if isinstance(widget, QTreeWidget) and widget in (self._large_files, self._large_folders, self._suggestions, self._garbage_files): return widget
        return (self._large_files, self._large_folders, self._suggestions)[self._main_tabs.currentWidget().findChild(QTabWidget).currentIndex()] if False else self._large_files

    def _scan_result_path(self):
        for tree in (self._large_files, self._large_folders, self._suggestions, self._garbage_files):
            if tree.hasFocus() and tree.selectedItems(): return tree.selectedItems()[0].data(0, Qt.UserRole)
        for tree in (self._large_files, self._large_folders, self._suggestions, self._garbage_files):
            if tree.selectedItems(): return tree.selectedItems()[0].data(0, Qt.UserRole)
        QMessageBox.information(self, "提示", "请先选择扫描结果"); return None

    def _open_scan_result(self):
        path = self._scan_result_path()
        if path:
            try: os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
            except OSError as exc: QMessageBox.warning(self, "打开失败", str(exc))
    def _copy_scan_result(self):
        path = self._scan_result_path()
        if path: QtWidgets.QApplication.clipboard().setText(path)
    def _delete_scan_result(self): self._delete_path(self._scan_result_path())

    def _clean_junk_selected(self):
        items = self._garbage_files.selectedItems()
        if not items:
            QMessageBox.information(self, "提示", "请先选择要清理的垃圾文件。")
            return
        paths = [item.data(0, Qt.UserRole) for item in items if item.data(0, Qt.UserRole)]
        if not paths:
            return
        prompt = ("确定将选中的垃圾/临时文件移至回收站吗？\n\n" + "\n".join(paths[:12]) +
                  (f"\n……共 {len(paths)} 项" if len(paths) > 12 else ""))
        if QMessageBox.question(self, "确认清理", prompt, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        moved = 0
        for path in paths:
            ok, _ = self.file_operations.move_to_recycle_bin(path)
            if ok:
                moved += 1
                item = next((i for i in items if i.data(0, Qt.UserRole) == path), None)
                if item:
                    self._garbage_files.takeTopLevelItem(self._garbage_files.indexOfTopLevelItem(item))
        QMessageBox.information(self, "清理结果", f"已将 {moved} 项移至回收站。")

    def _on_scan_context_menu(self, tree, pos):
        item = tree.itemAt(pos)
        if not item:
            return
        tree.setCurrentItem(item)
        item.setSelected(True)
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        menu = QMenu(self)
        texts = (["Search Associated Software", "Show Associated Software", "Move to Recycle Bin", "Delete Permanently", "Open Path", "Copy Path"] if self.language == "en" else
                 ["搜索关联程序", "显示关联程序", "选择删除（移至回收站）", "永久删除", "打开路径", "复制路径"])
        search_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DriveNetIcon), texts[0])
        show_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_FileLinkIcon), texts[1])
        menu.addSeparator()
        recycle_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_TrashIcon), texts[2])
        permanent_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_MessageBoxCritical), texts[3])
        menu.addSeparator()
        open_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DirOpenIcon), texts[4])
        copy_action = menu.addAction(self._icon(QtWidgets.QStyle.SP_DialogSaveButton), texts[5])
        chosen = menu.exec_(tree.viewport().mapToGlobal(pos))
        if chosen == search_action:
            self._online_verify_path(path)
        elif chosen == show_action:
            self._show_association_for(path)
        elif chosen == recycle_action:
            if self._delete_path(path):
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
        elif chosen == permanent_action:
            if self._permanent_delete_path(path):
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
        elif chosen == open_action:
            try:
                os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
            except OSError as exc:
                QMessageBox.warning(self, "打开失败", str(exc))
        elif chosen == copy_action:
            QtWidgets.QApplication.clipboard().setText(path)

    def _open_recycle_bin(self):
        try:
            from recycle_bin_ui import RecycleBinDialog
            RecycleBinDialog(self).exec_()
        except Exception as exc: QMessageBox.warning(self, "回收站管理", str(exc))

    def closeEvent(self, event):
        if self._scanner_thread and self._scanner_thread.isRunning(): self._scanner_thread.cancel(); self._scanner_thread.wait(2000)
        super().closeEvent(event)


# 保留新旧入口名称兼容性。
FileTreeWindow = DiskMonitor
