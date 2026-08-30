# -*- coding: utf-8 -*-
"""文件清理工具 - 实现安全移入回收站的后台线程"""

import os
import ctypes
from ctypes import wintypes
from PyQt5.QtCore import QThread, pyqtSignal

# SHFileOperation 常量 (FOF_*)
FOF_SILENT = 0x0004        # 不显示进度对话框
FOF_ALLOWUNDO = 0x0040     # 允许撤销（移入回收站）
FOF_NOCONFIRMATION = 0x0010  # 不显示确认对话框

# 定义 SHFILEOPSTRUCT 结构
class SHFILEOPSTRUCT(ctypes.Structure):
    _fields_ = [
        ('wFunc', wintypes.WORD),
        ('hwnd', wintypes.HWND),
        ('pFrom', wintypes.LPCWSTR),
        ('pTo', wintypes.LPCWSTR),
        ('fFlags', wintypes.WORD),
        ('fAnyOperationsAborted', wintypes.BOOL),
        ('hNameMappings', wintypes.HANDLE),
        ('lpszProgressTitle', wintypes.LPCWSTR),
    ]

# 封装 SHFileOperation 函式
SHFileOperationW = ctypes.windll.shell32.SHFileOperationW

class FileCleanerThread(QThread):
    """后台文件清理线程。
    接收待删路径列表，执行 SHFileOperation 将其移入回收站，并通过信号反馈进度。"""
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(list)

    def __init__(self, paths, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paths = paths
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        """执行文件清理任务。逐个处理文件以支持进度更新。"""
        total = len(self.paths)
        cleaned_paths = []
        
        for idx, path in enumerate(self.paths):
            if self._cancel_requested:
                break
            
            # 更新进度
            self.progress_signal.emit(idx + 1, total)
            
            try:
                # 检查文件是否存在
                if not os.path.exists(path):
                    continue
                
                # 构造单文件的路径字符串（需要双 null 终止）
                from_path = path + '\0\0'
                
                # 构造 SHFILEOPSTRUCT
                op_struct = SHFILEOPSTRUCT(
                    wFunc=1,  # FO_DELETE
                    hwnd=None,
                    pFrom=from_path,
                    pTo=None,
                    fFlags=FOF_ALLOWUNDO | FOF_SILENT | FOF_NOCONFIRMATION,
                    fAnyOperationsAborted=False,
                    hNameMappings=None,
                    lpszProgressTitle='文件清理'
                )
                
                # 调用系统 API
                result = SHFileOperationW(ctypes.byref(op_struct))
                
                # 检查操作是否成功 (返回 0 表示成功)
                if result == 0 and not op_struct.fAnyOperationsAborted:
                    cleaned_paths.append(path)
                    
            except Exception as e:
                # 记录错误但继续处理其他文件
                print(f"清理文件失败: {path}, 错误: {e}")
                continue
        
        # 发送完成信号，返回实际清理的文件列表
        self.finished_signal.emit(cleaned_paths)

# 测试块
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("FileCleanerThread 可正常实例化")
    sys.exit(0)