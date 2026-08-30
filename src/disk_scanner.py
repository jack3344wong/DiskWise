# -*- coding: utf-8 -*-
"""安全、可取消的磁盘空间扫描线程。"""
from __future__ import annotations

import ctypes
import os
import time
from collections import defaultdict
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal


FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_ATTRIBUTE_OFFLINE = 0x1000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000


def _allocated_size(path: str, logical_size: int, attributes: int = 0) -> int:
    """读取 Windows 实际分配空间；云端占位文件不会被打开或下载。"""
    if attributes & (FILE_ATTRIBUTE_OFFLINE | FILE_ATTRIBUTE_RECALL_ON_OPEN |
                     FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS):
        return 0
    try:
        high = ctypes.c_ulong(0)
        ctypes.set_last_error(0)
        low = ctypes.windll.kernel32.GetCompressedFileSizeW(str(path), ctypes.byref(high))
        if low == 0xFFFFFFFF and ctypes.get_last_error() != 0:
            return logical_size
        return (high.value << 32) | low
    except Exception:
        return logical_size


def _protected_path(path: str) -> bool:
    norm = os.path.normcase(os.path.abspath(path))
    protected = [
        os.environ.get("WINDIR", r"C:\Windows"),
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("ProgramData", r"C:\ProgramData"),
    ]
    return any(norm == os.path.normcase(p) or norm.startswith(os.path.normcase(p) + os.sep)
               for p in protected if p)


def _suggestion(path: str, mtime: float, cloud_only: bool):
    """返回保守的清理建议；不确定时不建议删除。"""
    lower = path.lower()
    name = os.path.basename(lower)
    ext = os.path.splitext(name)[1]
    age_days = max(0, int((time.time() - mtime) / 86400))
    if _protected_path(path):
        return "不建议删除", "系统或程序目录中的文件，只建议人工检查", "可能影响系统或软件运行"
    if cloud_only or any(k in lower for k in ("onedrive", "dropbox", "google drive", "icloud")):
        return "谨慎处理", "云盘或同步目录中的文件", "删除可能同步到云端和其他设备"
    temp_root = os.path.normcase(os.environ.get("TEMP", ""))
    in_temp = bool(temp_root and os.path.normcase(path).startswith(temp_root + os.sep))
    in_cache = any(part.lower() in {"cache", "caches", "temp", "tmp"} for part in Path(path).parts)
    if (in_temp or in_cache) and age_days >= 7:
        return "通常可清理", f"临时或缓存文件，已 {age_days} 天未修改", "个别软件可能需要重新生成缓存"
    if ext in {".tmp", ".temp", ".dmp"} and age_days >= 7:
        return "通常可清理", f"临时文件，已 {age_days} 天未修改", "请确认相关程序已关闭"
    if ext in {".log", ".bak", ".old"} and age_days >= 30:
        return "可以重点检查", f"日志或备份文件，已 {age_days} 天未修改", "可能包含排障或恢复所需信息"
    if ext in {".iso", ".msi", ".zip", ".7z", ".rar", ".exe"} and age_days >= 90:
        return "可以重点检查", f"大型安装包或压缩包，已 {age_days} 天未修改", "确认不再需要安装或归档后再删除"
    return None


def _garbage_candidate(path: str, mtime: float, cloud_only: bool):
    """Return a conservative, explainable junk-file record or None."""
    if cloud_only or _protected_path(path):
        return None
    lower = path.lower()
    name = os.path.basename(lower)
    ext = os.path.splitext(name)[1]
    age_days = max(0, int((time.time() - mtime) / 86400))
    temp_root = os.path.normcase(os.environ.get("TEMP", ""))
    in_temp = bool(temp_root and os.path.normcase(path).startswith(temp_root + os.sep))
    parts = {part.lower() for part in Path(path).parts}
    in_cache = bool(parts & {"cache", "caches", "__pycache__", "thumbcache"})
    if name in {"thumbs.db", "desktop.ini"}:
        return {"category": "系统缩略图", "level": "通常可清理", "reason": "系统可自动重新生成", "risk": "可能导致缩略图重新生成", "safe_to_clean": True}
    if in_temp or ext in {".tmp", ".temp", ".dmp", ".crdownload", ".part", ".swp"}:
        if age_days >= 1:
            return {"category": "临时文件", "level": "通常可清理", "reason": f"已 {age_days} 天未修改的临时文件", "risk": "请确认相关程序已关闭", "safe_to_clean": True}
    if in_cache and age_days >= 7:
        return {"category": "缓存文件", "level": "通常可清理", "reason": f"已 {age_days} 天未修改的缓存", "risk": "软件可能需要重新生成缓存", "safe_to_clean": True}
    if ext in {".log", ".bak", ".old"} and age_days >= 30:
        return {"category": "日志/备份", "level": "谨慎处理", "reason": f"已 {age_days} 天未修改", "risk": "可能包含排障或恢复所需信息", "safe_to_clean": False}
    return None


class DiskScannerThread(QThread):
    """一次遍历生成大文件、递归文件夹大小和清理建议。"""

    progress_signal = pyqtSignal(int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, root_path, threshold_mb=100.0, top_n=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_path = os.path.abspath(root_path)
        self.threshold_bytes = max(0, int(float(threshold_mb) * 1024 * 1024))
        self.top_n = max(1, int(top_n))
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def _empty_result(self, cancelled=False):
        return {
            "root_path": self.root_path, "cancelled": cancelled,
            "total_files": 0, "total_folders": 0, "total_size": 0,
            "total_allocated": 0, "large_files": [], "large_folders": [],
            "suggestions": [], "garbage_files": [], "errors": [], "skipped_reparse": 0,
        }

    def run(self):
        result = self._empty_result()
        if not os.path.isdir(self.root_path):
            self.error_signal.emit(f"扫描路径不存在或不是目录：{self.root_path}")
            self.finished_signal.emit(result)
            return

        own_sizes = defaultdict(int)
        own_allocated = defaultdict(int)
        own_file_counts = defaultdict(int)
        parents = {}
        file_ids = set()
        try:
            def on_walk_error(exc):
                result["errors"].append({"path": getattr(exc, "filename", self.root_path), "error": str(exc)})

            for root, dirs, files in os.walk(self.root_path, topdown=True, onerror=on_walk_error, followlinks=False):
                if self._cancel_requested:
                    result["cancelled"] = True
                    break
                self.status_signal.emit(root)
                result["total_folders"] += 1
                kept_dirs = []
                for name in dirs:
                    full = os.path.join(root, name)
                    try:
                        st = os.stat(full, follow_symlinks=False)
                        attrs = getattr(st, "st_file_attributes", 0)
                        if os.path.islink(full) or attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                            result["skipped_reparse"] += 1
                            continue
                        kept_dirs.append(name)
                        parents[full] = root
                    except OSError as exc:
                        result["errors"].append({"path": full, "error": str(exc)})
                dirs[:] = kept_dirs
                for name in files:
                    if self._cancel_requested:
                        result["cancelled"] = True
                        break
                    path = os.path.join(root, name)
                    try:
                        st = os.stat(path, follow_symlinks=False)
                        attrs = getattr(st, "st_file_attributes", 0)
                        if os.path.islink(path) or attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                            result["skipped_reparse"] += 1
                            continue
                        identity = (getattr(st, "st_dev", 0), getattr(st, "st_ino", 0))
                        if identity != (0, 0) and identity in file_ids:
                            continue
                        file_ids.add(identity)
                        logical = int(st.st_size)
                        allocated = _allocated_size(path, logical, attrs)
                        cloud_only = bool(attrs & (FILE_ATTRIBUTE_OFFLINE |
                                                   FILE_ATTRIBUTE_RECALL_ON_OPEN |
                                                   FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS))
                        own_sizes[root] += logical
                        own_allocated[root] += allocated
                        own_file_counts[root] += 1
                        result["total_files"] += 1
                        result["total_size"] += logical
                        result["total_allocated"] += allocated
                        if logical >= self.threshold_bytes:
                            result["large_files"].append({
                                "name": name, "path": path, "size": logical,
                                "allocated": allocated, "mtime": st.st_mtime,
                                "extension": os.path.splitext(name)[1].lower() or "无扩展名",
                                "cloud_only": cloud_only,
                            })
                        advice = _suggestion(path, st.st_mtime, cloud_only)
                        if advice and logical >= self.threshold_bytes:
                            level, reason, risk = advice
                            result["suggestions"].append({
                                "path": path, "name": name, "size": logical,
                                "allocated": allocated, "level": level,
                                "reason": reason, "risk": risk,
                            })
                        garbage = _garbage_candidate(path, st.st_mtime, cloud_only)
                        if garbage:
                            result["garbage_files"].append({
                                "path": path, "name": name, "size": logical,
                                "allocated": allocated, "mtime": st.st_mtime, **garbage,
                            })
                        if result["total_files"] % 25 == 0:
                            self.progress_signal.emit(result["total_files"], 0)
                    except (PermissionError, OSError) as exc:
                        result["errors"].append({"path": path, "error": str(exc)})

            totals = dict(own_sizes)
            allocated_totals = dict(own_allocated)
            file_totals = dict(own_file_counts)
            folder_totals = defaultdict(int)
            all_dirs = set(totals) | set(parents) | {self.root_path}
            for directory in sorted(all_dirs, key=lambda p: p.count(os.sep), reverse=True):
                parent = parents.get(directory)
                if parent:
                    totals[parent] = totals.get(parent, 0) + totals.get(directory, 0)
                    allocated_totals[parent] = allocated_totals.get(parent, 0) + allocated_totals.get(directory, 0)
                    file_totals[parent] = file_totals.get(parent, 0) + file_totals.get(directory, 0)
                    folder_totals[parent] += 1 + folder_totals.get(directory, 0)
            result["large_folders"] = [
                {"name": os.path.basename(path) or path, "path": path,
                 "size": totals.get(path, 0), "allocated": allocated_totals.get(path, 0),
                 "file_count": file_totals.get(path, 0), "folder_count": folder_totals.get(path, 0)}
                for path in all_dirs if totals.get(path, 0) >= self.threshold_bytes
            ]
            result["large_files"].sort(key=lambda x: x["allocated"], reverse=True)
            result["large_folders"].sort(key=lambda x: x["allocated"], reverse=True)
            result["suggestions"].sort(key=lambda x: x["allocated"], reverse=True)
            result["garbage_files"].sort(key=lambda x: x["allocated"], reverse=True)
            result["large_files"] = result["large_files"][:self.top_n]
            result["large_folders"] = result["large_folders"][:self.top_n]
            result["suggestions"] = result["suggestions"][:self.top_n]
            result["garbage_files"] = result["garbage_files"][:self.top_n]
            self.progress_signal.emit(result["total_files"], result["total_files"])
            self.finished_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))
            self.finished_signal.emit(result)
