import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class FileClassifier:
    """
    多维度文件分类器，用于识别文件的用途、风险等级及访问频率。
    用于「电脑运行监测工具」第四阶段核心引擎。
    """

    def __init__(self):
        # 定义常见的按用途分类的后缀
        self._purpose_map = {
            'temporary': {'.tmp', '.temp', '.crdownload', '.part', '.swp'},
            'log': {'.log', '.err', '.out'},
            'cache_ext': {'.cache'},
            'backup': {'.bak', '.old', '.chk', '.copy', '.backup'},
            'installer': {'.exe', '.msi', '.dmg', '.deb', '.pkg'},
        }
        
        # 定义常见的缓存目录关键字 (不区分大小写)
        self._cache_dir_keywords = {'cache', 'thumbs'}

    def classify_by_purpose(self, filepath: str) -> str:
        """
        按用途分类文件。
        
        Args:
            filepath (str): 文件路径
            
        Returns:
            str: 'temporary'|'log'|'cache'|'backup'|'installer'|'download'|'normal'
        """
        try:
            path = Path(filepath)
            suffix = path.suffix.lower()
            name = path.name.lower()
            
            # 1. 优先级最高：基于明确后缀的分类
            if suffix in self._purpose_map['temporary']:
                return 'temporary'
            
            if suffix in self._purpose_map['log']:
                return 'log'
            
            if suffix in self._purpose_map['cache_ext']:
                return 'cache'

            if suffix in self._purpose_map['backup']:
                return 'backup'
                
            if suffix in self._purpose_map['installer']:
                return 'installer'

            # 2. 基于文件名的特殊规则
            if name.startswith('~'):
                return 'temporary'
            
            # 特殊处理: .txt 且名称中包含 log
            if suffix == '.txt' and 'log' in name:
                return 'log'

            # 3. 基于路径的分类 (优先级较低，避免误伤)
            path_str = str(path).lower()
            
            # 检查是否在下载目录
            if 'downloads' in path_str or '下载' in path_str:
                return 'download'

            # 检查是否在缓存目录中 (排除掉已经通过后缀明确分类的文件)
            # 只有当后缀不明确时，才考虑路径
            path_parts = [p.lower() for p in path.parts]
            if any(keyword in part for part in path_parts for keyword in self._cache_dir_keywords):
                return 'cache'

            return 'normal'
        except Exception:
            return 'normal'

    def classify_by_risk(self, filepath: str) -> str:
        """
        按风险等级分类文件 (风险等级指清理该文件的后果严重程度)
        - high: 极大概率可以安全删除 (清理风险低，如临时文件、缓存)
        - medium: 可能有时需要，但通常是冗余的 (如日志、备份)
        - low: 可能重要的用户文件 (如文档、安装包)
        
        Args:
            filepath (str): 文件路径
            
        Returns:
            str: 'high'|'medium'|'low'
        """
        purpose = self.classify_by_purpose(filepath)

        if purpose in ['temporary', 'cache']:
            return 'high'
        
        if purpose in ['log', 'backup']:
            return 'medium'
            
        return 'low'

    def classify_by_access(self, filepath: str) -> str:
        """
        按访问频率分类文件。
        - 'inactive': 长期未访问 (>90天)
        - 'occasional': 偶尔访问 (30-90天)
        - 'active': 活跃文件 (<30天)
        
        Args:
            filepath (str): 文件路径
            
        Returns:
            str: 'inactive'|'occasional'|'active'
        """
        try:
            # 获取最后访问时间
            atime = os.path.getatime(filepath)
            last_access_date = datetime.fromtimestamp(atime)
            now = datetime.now()
            diff_days = (now - last_access_date).days
            
            if diff_days > 90:
                return 'inactive'
            elif diff_days > 30:
                return 'occasional'
            else:
                return 'active'
        except Exception:
            # 如果读取属性失败，默认为活跃（防止误删重要文件）
            return 'active'

    def get_full_classification(self, filepath: str) -> dict:
        """
        返回完整分类字典。
        
        Args:
            filepath (str): 文件路径
            
        Returns:
            dict: 包含 purpose, risk, access 的字典
        """
        return {
            'path': filepath,
            'purpose': self.classify_by_purpose(filepath),
            'risk': self.classify_by_risk(filepath),
            'access': self.classify_by_access(filepath)
        }

if __name__ == "__main__":
    # 简单的本地快速测试
    import unittest
    import time

    class TestFileClassifier(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.test_dir = Path("./test_temp_dir_for_unit_test")
            cls.test_dir.mkdir(exist_ok=True)

        @classmethod
        def tearDownClass(cls):
            if cls.test_dir.exists():
                shutil.rmtree(cls.test_dir, ignore_errors=True)

        def setUp(self):
            self.classifier = FileClassifier()

        def test_purpose_classification(self):
            """测试用途分类"""
            files = {
                "test.tmp": "temporary",
                "~test.txt": "temporary",
                "test.swp": "temporary",
                "test.log": "log",
                "my_log.txt": "log",
                "test.cache": "cache",
                "test.bak": "backup",
                "test.backup": "backup",
                "test.exe": "installer",
                "test.docx": "normal"
            }
            for name, expected in files.items():
                p = self.test_dir / name
                p.touch(exist_ok=True)
                self.assertEqual(self.classifier.classify_by_purpose(str(p)), expected, f"Failed for {name}")

        def test_cache_directory_detection(self):
            """测试缓存目录检测"""
            # 创建一个不包含 temp/thumbs 等关键字的目录名来测试路径检测
            cache_dir = self.test_dir / "MyAppCache"
            cache_dir.mkdir(exist_ok=True)
            p = cache_dir / "data.bin"
            p.touch(exist_ok=True)
            self.assertEqual(self.classifier.classify_by_purpose(str(p)), "cache")

        def test_download_directory_detection(self):
            """测试下载目录检测"""
            dl_dir = self.test_dir / "MyDownloads"
            dl_dir.mkdir(exist_ok=True)
            p = dl_dir / "file.zip"
            p.touch(exist_ok=True)
            self.assertEqual(self.classifier.classify_by_purpose(str(p)), "download")

        def test_risk_classification(self):
            """测试风险等级"""
            files = {
                "test.tmp": "high",
                "test.log": "medium",
                "test.docx": "low"
            }
            for name, expected in files.items():
                p = self.test_dir / name
                p.touch(exist_ok=True)
                self.assertEqual(self.classifier.classify_by_risk(str(p)), expected, f"Failed for {name}")

        def test_access_classification(self):
            """测试访问频率 (通过修改时间)"""
            p = self.test_dir / "access_test.txt"
            p.touch(exist_ok=True)
            
            # 测试活跃文件 (<30天)
            self.assertEqual(self.classifier.classify_by_access(str(p)), "active")
            
            # 测试极旧文件 (通过修改 os.utime)
            # 100天前
            old_time = time.time() - (100 * 24 * 3600)
            os.utime(str(p), (old_time, old_time))
            self.assertEqual(self.classifier.classify_by_access(str(p)), "inactive")

            # 45天前
            mid_time = time.time() - (45 * 24 * 3600)
            os.utime(str(p), (mid_time, mid_time))
            self.assertEqual(self.classifier.classify_by_access(str(p)), "occasional")

    if __name__ == "__main__":
        unittest.main()
