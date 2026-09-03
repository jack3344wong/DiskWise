# -*- coding: utf-8 -*-
"""全文索引的一致性与过滤规则回归测试。"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# 数据库一致性测试不需要启动界面或线程；允许在精简的 CI Python 中运行。
try:
    from PyQt5.QtCore import QThread, pyqtSignal  # noqa: F401
except ImportError:
    qt_core = types.ModuleType("PyQt5.QtCore")
    qt_core.QThread = type("QThread", (), {})
    qt_core.pyqtSignal = lambda *args, **kwargs: None
    pyqt = types.ModuleType("PyQt5")
    pyqt.QtCore = qt_core
    sys.modules["PyQt5"] = pyqt
    sys.modules["PyQt5.QtCore"] = qt_core

from fulltext_search import FullTextIndexDB  # noqa: E402


def add(db: FullTextIndexDB, path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    stat = path.stat()
    db.upsert_document(
        str(path), path.name, path.suffix.lower(), stat.st_size,
        stat.st_mtime, content,
    )
    db.commit()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="filecare-fts-") as temp_dir:
        root = Path(temp_dir)
        db_path = root / "fulltext-test.db"
        db = FullTextIndexDB(str(db_path))
        try:
            folder_a = root / "A"
            folder_ab = root / "AB"
            text_file = folder_a / "alpha.txt"
            pdf_file = folder_a / "guide.pdf"
            sibling = folder_ab / "sibling.txt"

            add(db, text_file, "hello old content")
            assert len(db.search("hello")) == 1

            percent_file = folder_a / "percent.txt"
            add(db, percent_file, "中文 100%_完成")
            assert {item["path"] for item in db.search("100%_完成")} == {
                str(percent_file)}, "% 和 _ 在回退搜索中必须按字面量匹配"

            add(db, text_file, "fresh replacement phrase")
            assert db.search("old") == [], "更新后不应残留旧的 FTS 内容"
            assert len(db.search("replacement")) == 1
            assert db.get_document_content(str(text_file)) == "fresh replacement phrase"

            add(db, pdf_file, "portable document marker")
            add(db, sibling, "sibling marker")
            multi_ext = db.search("marker", ext_filter=".txt,.pdf")
            assert {item["path"] for item in multi_ext} == {str(pdf_file), str(sibling)}

            scoped = db.search("marker", path_filter=str(folder_a))
            assert {item["path"] for item in scoped} == {str(pdf_file)}, (
                "A 的路径过滤不能误匹配 AB")

            db.delete_document(str(pdf_file))
            assert db.search("portable") == []

            outside = root / "outside.txt"
            add(db, outside, "outside retained")
            db.prune_missing([str(folder_a)], set())
            assert db.search("replacement") == []
            assert len(db.search("outside")) == 1, "清理只能影响指定扫描范围"
        finally:
            db.close()

        # Windows 上连接正确关闭后，临时数据库应可正常移除。
        assert os.path.exists(db_path)

    print("fulltext search consistency: PASS")


if __name__ == "__main__":
    main()
