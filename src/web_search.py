# -*- coding: utf-8 -*-
"""联网搜索功能 - 使用必应搜索引擎 (Web Search via Bing)"""
import webbrowser
import urllib.parse


class WebSearch:
    """通过系统默认浏览器在必应搜索"""

    def __init__(self, engine="bing"):
        """
        初始化搜索引擎。
        :param engine: 保留参数，始终使用必应
        """
        self.engine = "bing"

    def search_online(self, query):
        """
        在浏览器中打开必应搜索结果页面。
        :param query: 搜索关键词
        :return: bool 是否成功打开
        """
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded}"
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"[WebSearch] 打开浏览器失败: {e}")
            return False

    def set_engine(self, engine):
        """切换搜索引擎（保留接口，实际无效）"""
        return True

    def get_available_engines(self):
        """返回可用搜索引擎列表"""
        return ["bing"]
