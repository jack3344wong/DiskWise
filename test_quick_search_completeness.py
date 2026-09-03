# -*- coding: utf-8 -*-
"""快速搜索完整性回归测试。"""
import os
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from PyQt5.QtCore import QCoreApplication  # noqa: E402
except ImportError:
    class _Signal:
        def __init__(self):
            self.callbacks = []

        def connect(self, callback):
            self.callbacks.append(callback)

        def emit(self, *args):
            for callback in list(self.callbacks):
                callback(*args)

    class _SignalDescriptor:
        def __set_name__(self, owner, name):
            self.name = "_signal_" + name

        def __get__(self, instance, owner):
            if instance is None:
                return self
            if not hasattr(instance, self.name):
                setattr(instance, self.name, _Signal())
            return getattr(instance, self.name)

    class _QThread:
        def start(self):
            self.run()

        def isRunning(self):
            return False

        def wait(self, *args):
            return True

    class _QCoreApplication:
        _instance = None

        def __init__(self, _args):
            type(self)._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

    qt_core = types.ModuleType("PyQt5.QtCore")
    qt_core.QThread = _QThread
    qt_core.pyqtSignal = lambda *args, **kwargs: _SignalDescriptor()
    qt_core.QCoreApplication = _QCoreApplication
    pyqt = types.ModuleType("PyQt5")
    pyqt.QtCore = qt_core
    sys.modules["PyQt5"] = pyqt
    sys.modules["PyQt5.QtCore"] = qt_core
    QCoreApplication = _QCoreApplication
from quick_search import (  # noqa: E402
    FileIndexDB, IndexBuildThread, build_name_index_sync,
)


app = QCoreApplication.instance() or QCoreApplication([])


def scan(root: Path, db: FileIndexDB, cancel=False):
    thread = IndexBuildThread(drives=[], db_path=db.db_path)
    thread.db.close()
    thread.db = db
    thread._cancel = cancel
    thread._scan_drive(str(root))


with tempfile.TemporaryDirectory(prefix="quick_search_", dir=".") as tmp:
    root = Path(tmp).resolve()
    (root / "Windows" / "WinSxS").mkdir(parents=True)
    (root / "Windows" / "WinSxS" / "rare-system-file.dll").write_text("x")
    (root / "$Recycle.Bin").mkdir()
    (root / "$Recycle.Bin" / "recoverable-note.txt").write_text("x")
    (root / ".hidden-folder").mkdir()
    (root / ".hidden-folder" / ".hidden-file.txt").write_text("x")
    (root / "100%_done.txt").write_text("x")
    (root / "ordinary.docx").write_text("x")

    link_created = False
    try:
        os.symlink(root / "Windows", root / "windows-link", target_is_directory=True)
        link_created = True
    except OSError:
        pass

    db = FileIndexDB(str(root / "index-test.db"))
    scan(root, db)

    assert db.search("rare-system-file"), "WinSxS 不应被排除"
    assert db.search("recoverable-note"), "回收站目录不应被排除"
    assert db.search(".hidden-file"), "隐藏文件不应丢失"
    folder_results = db.search("hidden-folder", is_dir_filter=True)
    assert folder_results and all(item["is_dir"] for item in folder_results), "文件夹筛选必须只返回目录"
    assert db.search("100%_done"), "% 和 _ 在普通查询中应按字面量匹配"
    assert db.search("*.docx"), "显式通配符应可用"
    if link_created:
        assert db.search("windows-link"), "链接目录本身应进入索引"

    # 成功刷新要删除失效记录并收录新文件。
    (root / "ordinary.docx").unlink()
    (root / "new-file.pdf").write_text("new")
    scan(root, db)
    assert not db.search("ordinary.docx"), "已删除文件不应残留"
    assert db.search("new-file.pdf"), "新文件应进入索引"

    # 取消不得清空或截断已有索引。
    before_cancel = db.get_total_count()
    scan(root, db, cancel=True)
    assert db.get_total_count() == before_cancel

    total = db.count_search_results("*")
    assert total == db.get_total_count(), (total, db.get_total_count())
    first_page = db.search("*", max_results=3)
    second_page = db.search("*", max_results=3, offset=3)
    assert len(first_page) == len(second_page) == 3
    assert {item["path"] for item in first_page}.isdisjoint(
        {item["path"] for item in second_page})
    print("已索引目录项:", total)
    db.close()

    # 安装器使用的无界面入口也必须生成可搜索数据库。
    cli_db = str(root / "installer-index.db")
    cli_total, _, cli_errors = build_name_index_sync(
        drives=[str(root)], db_path=cli_db)
    assert cli_total > 0 and not cli_errors
    cli_index = FileIndexDB(cli_db)
    assert cli_index.search("new-file.pdf")
    cli_index.close()
    print("ALL PASS")
