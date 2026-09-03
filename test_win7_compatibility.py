# -*- coding: utf-8 -*-
"""发布配置的 Windows 7 SP1 x64 兼容性静态门禁。"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    source_files = sorted((ROOT / "src").glob("*.py"))
    for path in source_files:
        source = path.read_text(encoding="utf-8-sig")
        ast.parse(source, filename=str(path), feature_version=(3, 8))

    requirements = (ROOT / "requirements-win7.txt").read_text(encoding="utf-8")
    required_pins = {
        "PyQt5==5.15.10",
        "PyQt5-Qt5==5.15.2",
        "psutil==5.9.8",
        "Pillow==9.5.0",
        "lxml==4.9.3",
        "pyinstaller==5.13.2",
    }
    assert required_pins.issubset(set(requirements.splitlines()))

    installer = (ROOT / "packaging" / "FileCare.iss").read_text(
        encoding="utf-8-sig")
    assert "MinVersion=6.1sp1" in installer
    assert "ArchitecturesAllowed=x64compatible" in installer
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in installer
    assert 'Name: "desktopicon"' in installer
    assert 'Name: "startmenuicon"' in installer
    assert 'Filename: "{uninstallexe}"' in installer
    assert 'Tasks: startmenuicon' in installer

    for spec_name in ("FileCare.spec", "FileCare-OneFile.spec"):
        spec = (ROOT / "packaging" / spec_name).read_text(encoding="utf-8-sig")
        assert "sys.version_info[:2] != (3, 8)" in spec
        assert 'struct.calcsize("P") != 8' in spec
        assert '"PyQt5-Qt5": "5.15.2"' in spec
        assert '"pyinstaller": "5.13.2"' in spec

    print(f"Win7 compatibility gate: {len(source_files)} source files PASS")


if __name__ == "__main__":
    main()
