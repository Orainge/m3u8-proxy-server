from urllib.parse import parse_qs, urlencode, urlparse

import requests


class M3U8Object:
    """M3U8 对象"""

    def __init__(self,
                 url: str,
                 response_object: requests.Response):
        """
        初始化
        :param url: 请求的 URL
        :param response_object: 请求结果对象
        """
        self.url = url
        self.next_level_url = None  # 下一级 M3U8 URL
        self.response_object = response_object
        self.body = str(response_object.text)

        # 获取 Query 参数
        parsed_url = urlparse(url)
        query_param = parse_qs(parsed_url.query)
        if len(query_param) == 0:
            self.query_param_string = None
        else:
            self.query_param_string = urlencode(query_param, doseq=True)

    def get_body_length(self):
        """获取 body 的长度"""
        return len(self.body)

    def get_uri_host(self):
        """
        获取 M3U8 URL 的主机
        例如: http://example.com/a/b/c/index.m3u8
        返回: http://example.com
        """
        if self.url is None or len(self.url) == 0:
            return ''

        parsed_url = urlparse(self.url)
        return f'{parsed_url.scheme}://{parsed_url.netloc}'

    def get_uri_relative(self):
        """
        获取相对于 M3U8 文件的根 URI
        例如: http://example.com/a/b/c/index.m3u8
        返回: http://example.com/a/b/c/
        """
        if self.url is None or len(self.url) == 0:
            return ''

        find_root_url = self.url.split('?')[0]  # 截取 ? 前的部分
        last_slash_index = find_root_url.rfind("/")
        relative_uri = self.url[:last_slash_index + 1]
        return relative_uri
