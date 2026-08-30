# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

# PyInstaller sets SPECPATH to the directory containing this spec file.
project = Path(SPECPATH).resolve().parent
code = project / "src"

a = Analysis(
    [str(code / "main.py")],
    pathex=[str(code)],
    binaries=[],
    datas=[(str(project / "assets"), "assets")],
    hiddenimports=[
        "main_window", "file_association", "file_operations",
        "web_search", "recycle_bin_ui", "disk_scanner",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="DiskWise", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False,
    icon=str(project / "assets" / "diskwise.ico"),
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, upx_exclude=[], name="DiskWise",
)
