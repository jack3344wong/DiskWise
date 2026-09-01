# -*- coding: utf-8 -*-
"""文件删除和回收站管理 - 安全的文件移动/恢复/搜索 (File Operations & Recycle Bin)"""
import json
import os
import shutil
import fnmatch
import time


class FileOperations:
    """文件操作类：移入回收站、恢复、搜索"""

    def __init__(self, recycle_bin_path):
        self.recycle_bin_path = recycle_bin_path
        try:
            os.makedirs(self.recycle_bin_path, exist_ok=True)
        except OSError as e:
            print(f"[FileOperations] 创建回收站目录失败: {e}")

    def _write_meta(self, recycle_file_path, origin_path):
        """在回收站条目旁写入元数据（原路径、删除时间）。"""
        try:
            meta = {
                "origin_path": origin_path,
                "deleted_at": time.time(),
                "deleted_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
            with open(recycle_file_path + ".meta.json", "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False)
        except OSError:
            pass

    def move_to_recycle_bin(self, file_path):
        """
        将文件移动到自定义回收站目录。
        返回 (bool, message) 元组。
        """
        try:
            if not os.path.exists(file_path):
                return False, "源文件不存在"

            file_name = os.path.basename(file_path)
            new_path = os.path.join(self.recycle_bin_path, file_name)

            # 避免文件名冲突
            counter = 1
            base, ext = os.path.splitext(file_name)
            while os.path.exists(new_path):
                new_path = os.path.join(self.recycle_bin_path, f"{base}_{counter}{ext}")
                counter += 1

            shutil.move(file_path, new_path)
            self._write_meta(new_path, os.path.abspath(file_path))
            return True, f"已将 '{file_name}' 移入回收站"

        except PermissionError:
            return False, "没有权限移动该文件（可能需要管理员权限）"
        except shutil.Error as e:
            return False, f"移动失败: {e}"
        except Exception as e:
            return False, f"未知错误: {e}"

    def restore_from_recycle_bin(self, recycle_path, target_path):
        """
        从回收站恢复文件到指定路径。
        返回 (bool, message) 元组。
        """
        try:
            if not os.path.exists(recycle_path):
                return False, "回收站中找不到该文件"

            # 确保目标目录存在
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            shutil.move(recycle_path, target_path)
            try:
                os.remove(recycle_path + ".meta.json")
            except OSError:
                pass
            return True, f"已恢复到: {target_path}"

        except PermissionError:
            return False, "没有权限恢复文件"
        except shutil.Error as e:
            return False, f"恢复失败: {e}"
        except Exception as e:
            return False, f"未知错误: {e}"

    def search_in_recycle_bin(self, search_pattern):
        """
        在回收站中搜索文件（支持通配符 * 和 ?）。
        返回 (bool, list_of_filenames) 元组。
        """
        try:
            if not os.path.exists(self.recycle_bin_path):
                return True, []

            found = []
            for name in os.listdir(self.recycle_bin_path):
                if fnmatch.fnmatch(name.lower(), search_pattern.lower()):
                    found.append(name)
            return True, sorted(found)

        except PermissionError:
            return False, ["无权限读取回收站"]
        except Exception as e:
            return False, [f"搜索出错: {e}"]

    def empty_recycle_bin(self):
        """清空回收站目录中的所有文件"""
        try:
            if not os.path.exists(self.recycle_bin_path):
                return True, "回收站已为空"

            count = 0
            for name in os.listdir(self.recycle_bin_path):
                if name.endswith(".meta.json"):
                    # 元数据文件随主文件一起清理，不单独计数
                    try:
                        os.remove(os.path.join(self.recycle_bin_path, name))
                    except OSError:
                        pass
                    continue
                full = os.path.join(self.recycle_bin_path, name)
                try:
                    if os.path.isfile(full):
                        os.remove(full)
                        count += 1
                    elif os.path.isdir(full):
                        shutil.rmtree(full)
                        count += 1
                    try:
                        os.remove(full + ".meta.json")
                    except OSError:
                        pass
                except Exception:
                    continue

            return True, f"已清除 {count} 个项目"

        except Exception as e:
            return False, f"清空失败: {e}"
