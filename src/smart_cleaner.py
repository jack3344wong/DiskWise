from PyQt5.QtCore import QThread, pyqtSignal
from typing import List, Dict, Any
import os
from pathlib import Path

# Attempting to import from the same directory
try:
    from .large_file_analyzer import LargeFileAnalyzer
    from .duplicate_detector import DuplicateDetector
    from .file_classifier import FileClassifier
except (ImportError, ValueError):
    try:
        from large_file_analyzer import LargeFileAnalyzer
        from duplicate_detector import DuplicateDetector
        from file_classifier import FileClassifier
    except ImportError:
        # Fallbacks for when the module is not in the current python path
        import sys
        os_path = os.path.dirname(os.path.abspath(__file__))
        if os_path not in sys.path:
            sys.path.append(os_path)
        from large_file_analyzer import LargeFileAnalyzer
        from duplicate_detector import DuplicateDetector
        from file_classifier import FileClassifier

class SmartCleaningAdvisor:
    """
    Smart Cleaning Engine that integrates multiple analysis tools.
    Analyzes a directory to find large files, duplicates, and suggested cleanup items.
    """
    def __init__(self, threshold_mb: float = 100.0):
        self.analyzer = LargeFileAnalyzer(threshold_mb)
        self.duplicate_detector = DuplicateDetector()
        self.classifier = FileClassifier()

    def analyze(self, root_path: str, progress_hook=None) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the directory.
        
        Args:
            root_path (str): The directory to scan.
            progress_hook (callable, optional): A function called with (current_count, total_count).
        
        Returns:
            dict: A dictionary containing analysis results.
        """
        results = {
            'large_files': [],
            'duplicate_groups': [],
            'wasted_space': 0,
            'risk_suggestions': {
                'high': [],      # e.g. Temporary, Cache
                'medium': [],    # e.g. Logs, Backups
                'low': []        # e.g. Old downloads
            },
            'inactive_files': [],
            'total_count': 0
        }

        root = Path(root_path)
        if not root.is_dir():
            raise ValueError(f"Invalid directory: {root_path}")

        # Phase 1: Counting files for progress bar
        # This avoids requiring two full scans if possible, but for a true progress bar,
        # we need a total count.
        total_files = 0
        for _ in root.rglob('*'):
            total_files += 1
        
        results['total_count'] = total_files
        if total_files == 0:
            return results

        # Phase 2: Large File Analysis (Fast)
        if progress_hook:
            progress_hook(1, total_files)
        results['large_files'] = self.analyzer.find_large_files(root_path)

        # Phase 3: Duplicate Detection (Medium)
        if progress_hook:
            progress_hook(int(total_files * 0.2), total_files)
        self.duplicate_detector.scan_directory(root_path)
        results['duplicate_groups'] = self.duplicate_detector.find_duplicates()
        results['wasted_space'] = self.duplicate_detector.get_wasted_space()

        # Phase 4: Risk and Inactivity Classification (More Intensive)
        if progress_hook:
            progress_hook(int(total_files * 0.5), total_files)
        
        processed = 0
        # We iterate through the directory again for classification. 
        # This is the most expensive part due to file metadata access.
        for file_path in root.rglob('*'):
            if progress_hook:
                processed += 1
                # Only update UI every 50 files to reduce overhead
                if processed % 50 == 0 or processed == total_files:
                    progress_hook(processed, total_files)

            try:
                if file_path.is_file() and not file_path.is_symlink():
                    f_path = str(file_path)
                    
                    # 1. Risk Classification
                    risk = self.classifier.classify_by_risk(f_path)
                    if risk in results['risk_suggestions']:
                        if len(results['risk_suggestions'][risk]) < 1000:
                            results['risk_suggestions'][risk].append(f_path)
                    
                    # 2. Inactivity Classification
                    access = self.classifier.classify_by_access(f_path)
                    if access == 'inactive':
                        if len(results['inactive_files']) < 1000:
                            results['inactive_files'].append(f_path)
                            
            except (PermissionError, OSError):
                continue
            except Exception:
                continue

        return results

class SmartCleanerThread(QThread):
    """
    Background thread for running the SmartCleaningAdvisor to keep the UI responsive.
    """
    progress_signal = pyqtSignal(int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, root_path: str, threshold_mb: float = 100.0):
        super().__init__()
        self.root_path = root_path
        self.threshold_mb = threshold_mb
        self._is_aborted = False
        self.advisor = SmartCleaningAdvisor(threshold_mb)

    def run(self):
        try:
            self.status_signal.emit("Starting multidimensional analysis...")
            
            def on_progress(cur, total):
                if self._is_aborted:
                    raise InterruptedError()
                self.progress_signal.emit(cur, total)

            results = self.advisor.analyze(self.root_path, on_progress)
            
            if not self._is_aborted:
                self.finished_signal.emit(results)
            else:
                self.finished_signal.emit({'aborted': True})
        
        except InterruptedError:
            # Silent exit on abort
            pass
        except Exception as e:
            self.error_signal.emit(str(e))

    def abort(self):
        """Request the thread to stop processing."""
        self._is_aborted = True
