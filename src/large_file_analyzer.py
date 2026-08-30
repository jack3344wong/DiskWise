from pathlib import Path
import os
from typing import List, Dict, Any
import unittest

class LargeFileAnalyzer:
    """
    用于查找和分析系统中大文件的工具类。
    """

    def __init__(self, threshold_mb: float = 100.0):
        """
        初始化 LargeFileAnalyzer。

        Args:
            threshold_mb (float): 大文件的阈值（MB）。
        """
        self.threshold_bytes = int(threshold_mb * 1024 * 1024)

    def find_large_files(self, root_path: str) -> List[Dict[str, Any]]:
        """
        查找超过阈值的大文件。

        Args:
            root_path (str): 开始扫描的目录路径。

        Returns:
            List[Dict[str, Any]]: 包含文件路径和大小的字典列表。
        """
        large_files = []
        root = Path(root_path)
        
        if not root.is_dir():
            raise ValueError(f"路径不是目录: {root_path}")

        for file_path in root.rglob('*'):
            try:
                if file_path.is_file() and not file_path.is_symlink():
                    size = file_path.stat().st_size
                    if size >= self.threshold_bytes:
                        large_files.append({
                            'path': str(file_path),
                            'size': size
                        })
            except (PermissionError, OSError):
                # 跳过无法访问的文件
                continue
                
        return large_files

    def get_top_largest(self, root_path: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        获取最大的 N 个文件。

        Args:
            root_path (str): 开始扫描的目录路径。
            top_n (int): 返回前 N 个最大的文件。

        Returns:
            List[Dict[str, Any]]: 排序后的文件列表。
        """
        all_files = []
        root = Path(root_path)
        
        if not root.is_dir():
            raise ValueError(f"路径不是目录: {root_path}")

        for file_path in root.rglob('*'):
            try:
                if file_path.is_file() and not file_path.is_symlink():
                    size = file_path.stat().st_size
                    all_files.append({
                        'path': str(file_path),
                        'size': size
                    })
            except (PermissionError, OSError):
                continue

        # 按大小降序排序
        all_files.sort(key=lambda x: x['size'], reverse=True)
        
        return all_files[:top_n]

if __name__ == "__main__":
    import shutil
    import os

    class TestLargeFileAnalyzer(unittest.TestCase):
        def setUp(self):
            self.analyzer = LargeFileAnalyzer(threshold_mb=1.0) # 1MB threshold
            self.test_dir = Path("test_temp_dir_large_analyzer")
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            self.test_dir.mkdir(parents=True)

        def tearDown(self):
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)

        def create_file(self, name, size_kb):
            p = self.test_dir / name
            with open(p, "wb") as f:
                f.write(b"\0" * (size_kb * 1024))
            return p

        def test_find_large_files(self):
            """测试阈值过滤"""
            # 创建一个 2MB 的文件 (大于 1MB 阈值)
            self.create_file("large.bin", 2048)
            # 创建一个 500KB 的文件 (小于 1MB 阈值)
            self.create_file("small.bin", 512)
            
            large_files = self.analyzer.find_large_files(str(self.test_dir))
            self.assertEqual(len(large_files), 1)
            self.assertIn("large.bin", large_files[0]['path'])

        def test_get_top_largest(self):
            """测试排序逻辑"""
            self.create_file("small.bin", 100)
            self.create_file("huge.bin", 5000)
            self.create_file("medium.bin", 1000)
            
            top_files = self.analyzer.get_top_largest(str(self.test_dir), top_n=2)
            self.assertEqual(len(top_files), 2)
            # Note: Path order might vary, but top 2 are huge and medium
            self.assertTrue(any("huge.bin" in f['path'] for f in top_files))
            self.assertTrue(any("medium.bin" in f['path'] for f in top_files))

    unittest.main()
