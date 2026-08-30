import os
import hashlib
from pathlib import Path
from collections import defaultdict
import shutil
import unittest

class DuplicateDetector:
    """
    基于哈希的重复文件检测器。
    采用两阶段检测策略：先基于文件大小分组，再对大小相同的组进行哈希验证，以优化性能。
    """

    def __init__(self):
        # 存储扫描到的文件信息: {size: [path1, path2, ...]}
        self._size_groups = defaultdict(list)
        # 存储检测到的重复文件组: list of dicts [{'hash': str, 'files': [str], 'size': int}, ...]
        self._duplicate_groups = []
        # 当前扫描的总文件数
        self._total_scanned = 0

    def scan_directory(self, root_path: str, min_size: int = 0):
        """
        两阶段检测第一阶段：遍历目录并按大小对文件进行分组。
        
        Args:
            root_path (str): 开始扫描的目录
            min_size (int): 忽略小于此大小的文件 (bytes)
        """
        self._size_groups.clear()
        self._duplicate_groups.clear()
        self._total_scanned = 0
        
        root = Path(root_path)
        if not root.is_dir():
            raise ValueError(f"路径不是目录: {root_path}")

        for file_path in root.rglob('*'):
            try:
                if file_path.is_file() and not file_path.is_symlink():
                    size = file_path.stat().st_size
                    if size >= min_size:
                        self._size_groups[size].append(str(file_path))
                        self._total_scanned += 1
            except (PermissionError, OSError):
                # 跳过无法访问的文件
                continue

    def _calculate_hash(self, filepath: str, chunk_size: int = 65536) -> str:
        """
        计算文件的MD5哈希。
        """
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                # 循环读取，避免大文件占用过多内存
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (PermissionError, OSError):
            return ""

    def find_duplicates(self) -> list:
        """
        两阶段检测第二阶段：对大小相同的组进行哈希比对。
        
        Returns:
            list[dict]: 重复文件组列表，格式为 [{'hash': str, 'files': [str], 'size': int}, ...]
        """
        self._duplicate_groups = []
        
        # 只处理可能有重复的文件组（大小相同的组，且文件数 > 1）
        possible_duplicates = {
            size: paths for size, paths in self._size_groups.items() 
            if len(paths) > 1
        }

        for size, paths in possible_duplicates.items():
            hash_groups = defaultdict(list)
            for path in paths:
                file_hash = self._calculate_hash(path)
                if file_hash:
                    hash_groups[file_hash].append(path)
            
            # 筛选出真正的重复项 (同一个hash下面有多个文件)
            for file_hash, dup_paths in hash_groups.items():
                if len(dup_paths) > 1:
                    self._duplicate_groups.append({
                        'hash': file_hash,
                        'files': dup_paths,
                        'size': size
                    })
        
        return self._duplicate_groups

    def get_wasted_space(self) -> int:
        """
        计算重复文件浪费的总空间 (bytes)。
        """
        total_wasted = 0
        for group in self._duplicate_groups:
            # 假设每组中保留一个，其余的都是浪费的
            count = len(group['files'])
            total_wasted += group['size'] * (count - 1)
        return total_wasted

if __name__ == "__main__":
    class TestDuplicateDetector(unittest.TestCase):
        def setUp(self):
            self.detector = DuplicateDetector()
            self.test_dir_name = "test_temp_dir_duplicate_detector"
            self.test_path = Path(self.test_dir_name)
            if self.test_path.exists():
                shutil.rmtree(self.test_path)
            self.test_path.mkdir(parents=True)

        def tearDown(self):
            if self.test_path.exists():
                shutil.rmtree(self.test_path)

        def create_file(self, name, content):
            p = self.test_path / name
            p.write_text(content, encoding='utf-8')
            return str(p)

        def test_basic_duplicate_detection(self):
            """测试基础重复检测逻辑"""
            self.create_file("file1.txt", "hello world")
            self.create_file("file2.txt", "hello world")
            self.create_file("file3.txt", "hello world")
            self.create_file("unique.txt", "different content")
            
            self.detector.scan_directory(self.test_dir_name)
            duplicates = self.detector.find_duplicates()
            
            self.assertEqual(len(duplicates), 1)
            self.assertEqual(len(duplicates[0]['files']), 3)
            self.assertEqual(duplicates[0]['size'], len("hello world".encode('utf-8')))

        def test_different_sizes(self):
            """测试大小不同的文件不应被视为重复"""
            self.create_file("f1.txt", "content1")
            self.create_file("f2.txt", "content1_longer")
            
            self.detector.scan_directory(self.test_dir_name)
            duplicates = self.detector.find_duplicates()
            self.assertEqual(len(duplicates), 0)

        def test_wasted_space(self):
            """测试浪费空间计算"""
            self.create_file("f1.txt", "same")      # 4 bytes
            self.create_file("f2.txt", "same")      # 4 bytes
            self.create_file("f3.txt", "same")      # 4 bytes -> 2 * 4 = 8 wasted
            
            self.detector.scan_directory(self.test_dir_name)
            self.detector.find_duplicates()
            self.assertEqual(self.detector.get_wasted_space(), 8)

    unittest.main()
