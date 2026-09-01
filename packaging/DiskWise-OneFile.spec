# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# PyInstaller sets SPECPATH to the directory containing this spec file.
project = Path(SPECPATH).resolve().parent
code = project / "src"

# Collect all files for document parsing libraries
datas = [(str(project / "assets"), "assets")]
binaries = []
hiddenimports = [
    "main_window", "file_association", "file_operations",
    "web_search", "recycle_bin_ui", "disk_scanner",
    "quick_search", "fulltext_search", "content_extractor",
    "ui_event_handlers", "file_classifier", "duplicate_detector",
    "large_file_analyzer", "smart_cleaner", "cleanup",
    "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
    "PyQt5.sip",
    "psutil",
]

# Collect document parsing libraries
for pkg in ["pypdf", "docx", "openpyxl", "pptx", "striprtf", "lxml", "PIL", "xlsxwriter"]:
    try:
        datas_pkg, binaries_pkg, hiddenimports_pkg = collect_all(pkg)
        datas += datas_pkg
        binaries += binaries_pkg
        hiddenimports += hiddenimports_pkg
    except Exception as e:
        print(f"Warning: Could not collect {pkg}: {e}")

a = Analysis(
    [str(code / "main.py")],
    pathex=[str(code)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DiskWise",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project / "assets" / "diskwise.ico"),
)
