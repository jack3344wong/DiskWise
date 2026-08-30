# -*- coding: utf-8 -*-
"""磁盘智理 / DiskWise 主程序入口。"""
import os
import sys
from pathlib import Path

import PyQt5


# Qt 5.15.2 在 Windows 上无法正确解析含中文字符的默认插件路径，
# 必须在导入 QtWidgets 之前显式传入真实的 Unicode 路径。
_qt_plugins = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
if _qt_plugins.is_dir():
    os.environ["QT_PLUGIN_PATH"] = str(_qt_plugins)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(_qt_plugins / "platforms")

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon


def main():
    try:
        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DiskWise.DiskSpaceAdvisor")
            except Exception:
                pass
        app = QApplication(sys.argv)
        app.setApplicationName("磁盘智理")
        app.setApplicationDisplayName("磁盘智理")
        resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        icon_path = resource_root / "assets" / "diskwise.ico"
        if icon_path.is_file():
            app.setWindowIcon(QIcon(str(icon_path)))
        app.setStyle("Fusion")  # 统一跨平台基础样式，QSS 在此基础上叠加

        from main_window import DiskMonitor
        window = DiskMonitor()
        window.show()
        sys.exit(app.exec_())
    except ImportError as e:
        QMessageBox.critical(None, "启动失败", f"缺少依赖模块:\n{e}\n\n请确保所有代码文件在同一目录下。")
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "致命错误", f"程序启动失败:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
