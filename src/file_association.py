# -*- coding: utf-8 -*-
"""文件来源软件与默认打开程序识别。"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import dataclasses
import os
import re
import winreg
from pathlib import Path
from typing import List


@dataclasses.dataclass
class FileIdentityInfo:
    sync_software: str = "普通本地文件或文件夹"
    relation: str = "未发现已知软件或同步目录"
    default_app: str = "不适用"
    app_path: str = ""
    evidence: List[str] = dataclasses.field(default_factory=list)
    confidence: float = 0.35
    online_query: str = ""

    def to_summary(self):
        return self.default_app if self.default_app != "不适用" else self.sync_software


class FileAssociation:
    """结合本机安装信息、路径特征和 Shell 关联识别软件。"""

    _installed_cache = None
    _KNOWN = [
        (("onedrive", "onedrivetemp"), "Microsoft OneDrive", "OneDrive 同步或临时同步目录"),
        (("dropbox",), "Dropbox", "Dropbox 同步目录"),
        (("google drive", "googledrive", "drivefs"), "Google Drive", "Google Drive 同步目录"),
        (("icloud",), "Apple iCloud", "iCloud 同步目录"),
        (("jetbrains", "pycharm", "idea", "webstorm", "clion", "rider"), "JetBrains", "JetBrains 开发工具目录"),
        (("adobe", "photoshop", "illustrator", "premiere pro", "after effects"), "Adobe Creative Cloud", "Adobe 软件或数据目录"),
        (("microsoft office", "microsoft 365", "office16"), "Microsoft 365 / Office", "Office 软件目录"),
        (("visual studio code", "microsoft vs code", "vscode"), "Visual Studio Code", "VS Code 软件或数据目录"),
        (("visual studio",), "Microsoft Visual Studio", "Visual Studio 软件目录"),
        (("google\\chrome", "google/chrome", "chrome"), "Google Chrome", "Chrome 软件或数据目录"),
        (("microsoft\\edge", "microsoft/edge", "msedge"), "Microsoft Edge", "Edge 软件或数据目录"),
        (("mozilla", "firefox"), "Mozilla Firefox", "Firefox 软件或数据目录"),
        (("nvidia",), "NVIDIA", "NVIDIA 驱动或软件目录"),
        (("amd", "radeon"), "AMD", "AMD 驱动或软件目录"),
        (("intel",), "Intel", "Intel 驱动或软件目录"),
        (("tencent", "wechat", "weixin"), "腾讯 / 微信", "腾讯软件或数据目录"),
        (("dingtalk",), "钉钉", "钉钉软件或数据目录"),
        (("lark", "feishu"), "飞书", "飞书软件或数据目录"),
        (("anaconda", "miniconda"), "Anaconda / Miniconda", "Python 环境目录"),
        (("python",), "Python", "Python 运行环境或项目目录"),
        (("nodejs", "node.js", "npm-cache"), "Node.js", "Node.js 运行环境或缓存目录"),
        (("docker",), "Docker Desktop", "Docker 软件或数据目录"),
        (("android studio", ".android"), "Android Studio", "Android 开发工具或数据目录"),
        (("unity",), "Unity", "Unity 编辑器或项目目录"),
        (("unreal engine", "epic games"), "Epic Games / Unreal Engine", "Epic 或 Unreal 目录"),
        (("steam", "steamapps"), "Steam", "Steam 软件或游戏库目录"),
        (("github desktop",), "GitHub Desktop", "GitHub Desktop 目录"),
        (("7-zip",), "7-Zip", "7-Zip 软件目录"),
        (("winrar",), "WinRAR", "WinRAR 软件目录"),
    ]
    _EXE_NAMES = {
        "notepad.exe": "Windows 记事本", "chrome.exe": "Google Chrome",
        "msedge.exe": "Microsoft Edge", "firefox.exe": "Mozilla Firefox",
        "winword.exe": "Microsoft Word", "excel.exe": "Microsoft Excel",
        "powerpnt.exe": "Microsoft PowerPoint", "code.exe": "Visual Studio Code",
        "pycharm64.exe": "JetBrains PyCharm", "idea64.exe": "JetBrains IntelliJ IDEA",
        "photoshop.exe": "Adobe Photoshop", "acrord32.exe": "Adobe Acrobat Reader",
        "7zfm.exe": "7-Zip", "winrar.exe": "WinRAR",
    }

    def __init__(self, file_path=""):
        self.file_path = os.path.abspath(file_path) if file_path else ""

    def get_associated_program(self):
        info = self.get_detailed_identity()
        if info.default_app == "不适用":
            return info.sync_software
        return f"{info.default_app}（{info.app_path}）" if info.app_path else info.default_app

    def get_detailed_identity(self):
        info = FileIdentityInfo()
        if not self.file_path or not os.path.exists(self.file_path):
            info.sync_software = "未识别"
            info.relation = "路径不存在"
            info.confidence = 0.0
            return info
        self._detect_origin(info)
        if os.path.isfile(self.file_path):
            self._identify_default_app(info)
        info.online_query = self._safe_online_query(info)
        return info

    def _detect_origin(self, info):
        path_norm = os.path.normcase(self.file_path)
        lower = self.file_path.lower()

        for label, root in self._sync_roots():
            root_norm = os.path.normcase(os.path.abspath(root))
            if path_norm == root_norm or path_norm.startswith(root_norm + os.sep):
                info.sync_software = label
                info.relation = f"位于 {label} 配置的同步目录"
                info.evidence.append(f"匹配本机同步根目录：{root}")
                info.confidence = 0.98
                return
        if "onedrivetemp" in lower:
            personal = "-personal" in lower
            info.sync_software = "Microsoft OneDrive Personal" if personal else "Microsoft OneDrive"
            info.relation = "OneDrive 个人版临时同步目录" if personal else "OneDrive 临时同步目录"
            info.evidence.extend(["路径位于 OneDriveTemp", "检测到 -Personal 账户特征"] if personal else ["路径位于 OneDriveTemp"])
            info.confidence = 0.95
            return

        for install_path, display_name, publisher in self._installed_programs():
            install_norm = os.path.normcase(install_path)
            if install_norm and (path_norm == install_norm or path_norm.startswith(install_norm + os.sep)):
                info.sync_software = display_name
                info.relation = "已安装软件目录或其子目录"
                info.evidence.append(f"匹配 Windows 已安装程序：{display_name}" + (f"（{publisher}）" if publisher else ""))
                info.confidence = 0.93
                return

        for keys, name, relation in self._KNOWN:
            if any(key in lower for key in keys):
                info.sync_software = name
                info.relation = relation
                info.evidence.append(f"路径特征匹配：{next(k for k in keys if k in lower)}")
                info.confidence = 0.72
                return

        info.evidence.append("未匹配本机同步根目录、安装记录或已知软件路径")

    @classmethod
    def _sync_roots(cls):
        roots = []
        for env_name, label in (("OneDrive", "Microsoft OneDrive"),
                                ("OneDriveConsumer", "Microsoft OneDrive Personal"),
                                ("OneDriveCommercial", "Microsoft OneDrive 工作或学校版"),
                                ("Dropbox", "Dropbox"), ("GoogleDrive", "Google Drive")):
            value = os.environ.get(env_name)
            if value and os.path.isdir(value):
                roots.append((label, value))
        try:
            base = r"Software\Microsoft\OneDrive\Accounts"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base) as accounts:
                for i in range(winreg.QueryInfoKey(accounts)[0]):
                    account = winreg.EnumKey(accounts, i)
                    with winreg.OpenKey(accounts, account) as key:
                        folder, _ = winreg.QueryValueEx(key, "UserFolder")
                        if folder:
                            label = "Microsoft OneDrive Personal" if account.lower() == "personal" else "Microsoft OneDrive 工作或学校版"
                            roots.append((label, folder))
        except OSError:
            pass
        return roots

    @classmethod
    def _installed_programs(cls):
        if cls._installed_cache is not None:
            return cls._installed_cache
        found = []
        locations = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hive, subkey in locations:
            try:
                with winreg.OpenKey(hive, subkey) as root:
                    for i in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, i)) as key:
                                name = winreg.QueryValueEx(key, "DisplayName")[0]
                                try:
                                    location = winreg.QueryValueEx(key, "InstallLocation")[0]
                                except OSError:
                                    location = ""
                                try:
                                    publisher = winreg.QueryValueEx(key, "Publisher")[0]
                                except OSError:
                                    publisher = ""
                                if name and location and os.path.isdir(location):
                                    found.append((os.path.abspath(location), str(name), str(publisher)))
                        except OSError:
                            continue
            except OSError:
                continue
        cls._installed_cache = sorted(found, key=lambda x: len(x[0]), reverse=True)
        return cls._installed_cache

    def _identify_default_app(self, info):
        ext = os.path.splitext(self.file_path)[1]
        if not ext:
            info.default_app = "未识别（文件没有扩展名）"
            return
        executable = self._query_shell_executable(ext)
        if not executable:
            info.default_app = f"未找到 {ext} 的默认打开程序"
            return
        executable = os.path.expandvars(executable)
        exe_name = os.path.basename(executable)
        info.app_path = executable
        info.default_app = self._EXE_NAMES.get(exe_name.lower()) or self._product_name(executable) or exe_name
        info.evidence.append("Windows Shell 默认应用关联")
        info.confidence = max(info.confidence, 0.95)

    @staticmethod
    def _product_name(path):
        """读取可执行文件版本资源中的 ProductName/FileDescription。"""
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
            if not size:
                return ""
            buf = ctypes.create_string_buffer(size)
            if not ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buf):
                return ""
            trans_ptr, trans_len = ctypes.c_void_p(), wintypes.UINT()
            if not ctypes.windll.version.VerQueryValueW(buf, r"\VarFileInfo\Translation", ctypes.byref(trans_ptr), ctypes.byref(trans_len)):
                return ""
            lang, codepage = ctypes.cast(trans_ptr, ctypes.POINTER(ctypes.c_ushort * 2)).contents
            for field in ("ProductName", "FileDescription"):
                value_ptr, value_len = ctypes.c_void_p(), wintypes.UINT()
                query = fr"\StringFileInfo\{lang:04x}{codepage:04x}\{field}"
                if ctypes.windll.version.VerQueryValueW(buf, query, ctypes.byref(value_ptr), ctypes.byref(value_len)) and value_ptr.value:
                    return ctypes.wstring_at(value_ptr.value).strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def _query_shell_executable(extension):
        try:
            query = ctypes.windll.shlwapi.AssocQueryStringW
            query.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR,
                              wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
            size = wintypes.DWORD(0)
            query(0, 2, extension, None, None, ctypes.byref(size))
            if size.value <= 1:
                return ""
            buffer = ctypes.create_unicode_buffer(size.value)
            return buffer.value if query(0, 2, extension, None, buffer, ctypes.byref(size)) == 0 else ""
        except Exception:
            return ""

    def _safe_online_query(self, info):
        """仅生成不含完整路径和用户名的搜索词。"""
        basename = os.path.basename(self.file_path).strip()
        if not basename or re.fullmatch(r"[0-9a-fA-F-]{20,}", basename):
            basename = info.sync_software if info.sync_software != "普通本地文件或文件夹" else ""
        return f"{basename} Windows 属于什么软件".strip() if basename else ""
