# 代理服务

import re
import requests
from flask import Response

from route.consts.param_name import ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_PROXY, URI_NAME_URL, URI_NAME_VIDEO
from route.consts.url_type import (accept_content_type_regex_list_m3u8,
                                   accept_content_type_regex_list_video,
                                   accept_content_type_regex_list_stream)
from route.exception import RequestM3u8FileError, NotSupportContentTypeError
from util import encrypt as encrypt_util
from util import m3u8 as m3u8_util
from util import proxy as proxy_util
from util import request as request_util
from util import server as server_util
from util import service as service_util
from util.request import request_timeout

# match = re.fullmatch("正则表达式", "测试字符串")

# 行类型
LINE_TYPE_NORMAL = '0'  # 普通行
LINE_TYPE_EXTINF = '1'  # #EXTINF
LINE_TYPE_STREAM_INF = '2'  # #EXT-X-STREAM-INF


class JudgeFinalM3u8FileResult:
    """
    判断 M3U8 是否是最后一个文件的结果
    """

    def __init__(self):
        self.is_final_m3u8_file = True
        self.m3u8_url = ""
        self.body = ""

    def append_body_line(self, line_string: str):
        """
        附加一行到 body，自动引入换行符
        :param line_string: 要附加的字符串
        """
        if self.body is not None:
            self.body += line_string + "\n"

    def append_body_empty_line(self):
        """
        附加空行
        """
        self.body += "\n"


class M3u8Response:
    """获取代理 M3U8 文件的响应"""

    def __init__(self):
        self.response_object = None
        self.body = ""
        self.real_url = ""

    def get_body_length(self):
        """获取 body 的长度"""
        return len(self.body)

    def get_relative_m3u8_file_url_root(self):
        """
        获取相对路径的 M3U8 文件的真正的根 URL
        """
        if self.real_url is None or len(self.real_url) == 0:
            return ''

        # 查找最后一个斜杠的索引
        last_slash_index = self.real_url.rfind("/")

        # 截取字符串
        substring = self.real_url[:last_slash_index + 1]

        # 返回结果
        return substring


def get_m3u8_response(url: str,
                      enable_proxy: bool,
                      server_name: str,
                      check_mode: bool = False) -> M3u8Response:
    """
    请求 M3U8 文件
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param server_name: 服务器名称
    :param check_mode: 是否是检查模式，在检查模式下，不会对 M3U8 文件进行深层次处理
    :return:
    """
    m3u8_response = None

    # 递归查找最终含 ts 流的 M3U8 文件（指定层级）
    for i in range(m3u8_util.get_max_deep(url) + 1):
        m3u8_response = do_request_m3u8_file(url, enable_proxy)
        judge_result = judge_final_m3u8_file(m3u8_response, enable_proxy, server_name, check_mode=check_mode)
        if judge_result.is_final_m3u8_file:
            # 是最后一级，赋值
            m3u8_response.body = judge_result.body
            break
        else:
            # 不是最后一级，转换 URL
            url = judge_result.m3u8_url

    # 返回查询结果
    return m3u8_response


def do_request_m3u8_file(url: str, enable_proxy: bool) -> M3u8Response:
    """
    请求 m3u8 文件
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :return:
    """
    # 请求，请求次数限制在设置的最大重定向次数
    to_request_url = url
    max_redirect_times = request_util.get_max_redirect_times(url)
    for i in range(max_redirect_times + 1):
        response = requests.get(to_request_url,
                                timeout=request_timeout,
                                headers={
                                    'User-Agent': request_util.get_user_agent(url),
                                },
                                allow_redirects=False,
                                proxies=proxy_util.get_proxies(url, enable_proxy))

        # 获取请求结果 code，根据请求结果 code 进行判断
        status_code = response.status_code
        if status_code == 200:
            # 正常请求，返回结果
            is_m3u8_file = False

            # 判断是否是 M3U8 文件
            if response.text.splitlines()[0] == "#EXTM3U":
                # 响应里以 "#EXTM3U" 开头
                is_m3u8_file = True
            else:
                # 判断 Content-Type 是否是合法的
                content_type = response.headers.get('Content-Type') or response.headers.get('content-type')
                for regex in accept_content_type_regex_list_m3u8:
                    if re.fullmatch(regex, content_type):
                        # Content-Type 合法
                        is_m3u8_file = True

            if is_m3u8_file:
                # 如果是 M3U8 文件
                proxy_m3u8_response = M3u8Response()
                proxy_m3u8_response.response_object = response
                proxy_m3u8_response.real_url = to_request_url
                proxy_m3u8_response.body = response.text
                return proxy_m3u8_response
            else:
                # Content-Type 不合法
                response.close()
                raise NotSupportContentTypeError
        elif 300 <= status_code < 400:
            # 处理重定向
            to_request_url = response.headers["Location"]
        else:
            # 不正常的请求，抛出异常
            raise RequestM3u8FileError(url=to_request_url, status_code=status_code, text=response.text)

    # 抛出异常：请求次数超过设置的最大重定向次数
    raise RequestM3u8FileError(message="请求次数超过设置的最大重定向次数", url=url)


def judge_final_m3u8_file(proxy_m3u8_result: M3u8Response,
                          enable_proxy: bool,
                          server_name: str,
                          check_mode: bool = False) -> JudgeFinalM3u8FileResult:
    """
    判断是否是最后一级 M3U8 文件
    :param proxy_m3u8_result: 获取代理 M3U8 文件的响应
    :param enable_proxy: 是否使用外部代理请求文件
    :param server_name: 服务器名称
    :param check_mode: 是否是检查模式，在检查模式下，不会对 M3U8 文件进行深层次处理
    """
    judge_result = JudgeFinalM3u8FileResult()
    body = proxy_m3u8_result.body
    url_prefix = server_util.get_server_url(server_name) + f'/{URI_NAME_PROXY}/'
    m3u8_url_prefix = url_prefix + f'{URI_NAME_URL}/'
    video_url_prefix = url_prefix + f'{URI_NAME_VIDEO}/'

    # 轨道数
    stream_count = 0
    latest_stream_line_str = None

    # 设置当前行类型
    line_type = LINE_TYPE_NORMAL

    for line_str in body.split("\n"):
        # 去除多余的换行符（如果有）
        line_str = line_str.replace('\r', '')  # 这个大坑，气死我了

        if line_type == LINE_TYPE_NORMAL:
            # 普通行
            if line_str.startswith("#"):
                # 可能是标签行/注释
                if line_str.startswith("#EXT-X-STREAM-INF"):
                    # 下一行是可变视频流(多轨道)
                    line_type = LINE_TYPE_STREAM_INF
                elif line_str.startswith("#EXTINF"):
                    # 下一行是视频分片
                    line_type = LINE_TYPE_EXTINF
                elif line_str.startswith("#EXT-X-PREFETCH"):
                    line_type = LINE_TYPE_NORMAL

                    if check_mode is False:
                        video_url = line_str.split(":", 1)[1]
                        video_url = _process_video_url(proxy_m3u8_result, enable_proxy, video_url, video_url_prefix)
                        line_str = f"#EXT-X-PREFETCH:{video_url}"
        elif line_type == LINE_TYPE_STREAM_INF:
            # 可变视频流(多轨道)
            line_type = LINE_TYPE_NORMAL

            # 记录轨道
            stream_count += 1
            latest_stream_line_str = line_str

            if check_mode is False and service_util.enable_proxy_m3u8:
                # 代理 M3U8
                line_str = _process_m3u8_url(proxy_m3u8_result, enable_proxy, line_str, m3u8_url_prefix)
        elif line_type == LINE_TYPE_EXTINF:
            # 视频分片
            line_type = LINE_TYPE_NORMAL
            if check_mode is False and service_util.enable_proxy_video:
                # 代理视频流
                line_str = _process_video_url(proxy_m3u8_result, enable_proxy, line_str, video_url_prefix)

        # 这一行处理完成，附加当前这一行
        judge_result.append_body_line(line_str)

    if stream_count == 1:
        # 单轨道，还需要继续请求
        judge_result.is_final_m3u8_file = False

        # 判断子 M3U8 文件 URL 情况
        if latest_stream_line_str.startswith("http"):
            # 如果文件 URL 开始于 http / https
            judge_result.m3u8_url = latest_stream_line_str
        else:
            # 相对路径
            if latest_stream_line_str.startswith("/"):
                # 如果开始于 "/" ，需要去掉这个斜杠
                line_str = latest_stream_line_str[1:]
            judge_result.m3u8_url = f'{proxy_m3u8_result.get_relative_m3u8_file_url_root()}{latest_stream_line_str}'

    # 返回结果
    return judge_result


def _process_m3u8_url(proxy_m3u8_result: M3u8Response,
                      enable_proxy: bool,
                      m3u8_url: str,
                      m3u8_url_prefix: str) -> str:
    """
    处理 M3U8 URL
    :param proxy_m3u8_result: 获取代理 M3U8 文件的响应
    :param enable_proxy: 是否使用外部代理请求文件
    :param m3u8_url: M3U8 URL
    :param m3u8_url_prefix: URL 前缀
    """
    if m3u8_url.startswith("http"):
        # 绝对路径
        is_direct_url = True

        # 检查是否强制代理 M3U8 里面的 M3U8 轨道
        if service_util.get_enable_proxy_m3u8_direct_url(m3u8_url) is not True:
            # 如果不强制代理，原样返回
            return m3u8_url
    else:
        # 相对路径
        is_direct_url = False

        # 如果开始于 "/" ，需要去掉这个斜杠
        if m3u8_url.startswith("/"):
            m3u8_url = m3u8_url[1:]

    # 拼接成代理 URL
    if is_direct_url:
        # 如果是绝对路径 URL
        m3u8_url = m3u8_url_prefix + encrypt_util.encrypt_string(f'{m3u8_url}')
    else:
        # 如果是相对路径 URL
        m3u8_url = m3u8_url_prefix + encrypt_util.encrypt_string(
            f'{proxy_m3u8_result.get_relative_m3u8_file_url_root()}{m3u8_url}')

    # 准备附加额外参数
    query_params = {}

    # 是否开启代理
    if enable_proxy is True:
        query_params[ENABLE_PROXY] = "true"

    # 拼接查询参数
    return request_util.append_query_params_to_url(m3u8_url, query_params)


def _process_video_url(proxy_m3u8_result: M3u8Response,
                       enable_proxy: bool,
                       video_url: str,
                       video_url_prefix: str) -> str:
    """
    处理 Video URL
    :param proxy_m3u8_result: 获取代理 M3U8 文件的响应
    :param enable_proxy: 是否使用外部代理请求文件
    :param video_url: Video URL
    :param video_url_prefix: URL 前缀
    """
    if video_url.startswith("http"):
        # 绝对路径
        is_direct_url = True

        # 检查是否强制代理 M3U8 里面的 Video
        if service_util.get_enable_proxy_video_direct_url(video_url) is not True:
            # 如果不强制代理，原样返回
            return video_url
    else:
        # 相对路径
        is_direct_url = False

        # 如果开始于 "/" ，需要去掉这个斜杠
        if video_url.startswith("/"):
            video_url = video_url[1:]

    # 拼接成代理 URL
    if is_direct_url:
        # 如果是绝对路径 URL
        video_url = video_url_prefix + encrypt_util.encrypt_string(f'{video_url}')
    else:
        # 如果是相对路径 URL
        video_url = video_url_prefix + encrypt_util.encrypt_string(
            f'{proxy_m3u8_result.get_relative_m3u8_file_url_root()}{video_url}')

    # 准备附加额外参数
    query_params = {}

    # 是否开启代理
    if enable_proxy is True:
        query_params[ENABLE_PROXY] = "true"

    # 拼接查询参数
    return request_util.append_query_params_to_url(video_url, query_params)


def proxy_video(url, enable_proxy) -> Response:
    """
    代理请求视频文件
    :param url: 原始非加密的视频 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param user_agent: 请求 User-Agent
    :return:
    """
    # 执行请求并返回结果
    # 这里允许直接跳转，因为播放是流式传输
    response = requests.get(url,
                            timeout=request_timeout,
                            headers={
                                'User-Agent': request_util.get_user_agent(url),
                            },
                            proxies=proxy_util.get_proxies(url, enable_proxy),
                            stream=True)

    # 判断 Content-Type 是否是合法的
    content_type = response.headers.get('Content-Type') or response.headers.get('content-type')
    for regex in accept_content_type_regex_list_video:
        if re.fullmatch(regex, content_type):
            # Content-Type 合法，返回结果
            return response

    # Content-Type 不合法
    response.close()
    raise NotSupportContentTypeError


def proxy_stream(url, enable_proxy) -> Response:
    """
    代理请求流式传输文件
    :param url: 原始非加密的流式传输文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param user_agent: 请求 User-Agent
    :return:
    """
    # 执行请求并返回结果
    # 这里允许直接跳转，因为播放是流式传输
    response = requests.get(url,
                            timeout=request_timeout,
                            headers={
                                'User-Agent': request_util.get_user_agent(url),
                            },
                            proxies=proxy_util.get_proxies(url, enable_proxy),
                            stream=True)

    # 判断 Content-Type 是否是合法的
    content_type = response.headers.get('Content-Type') or response.headers.get('content-type')
    for regex in accept_content_type_regex_list_stream:
        if re.fullmatch(regex, content_type):
            # Content-Type 合法，返回结果
            return response

    # Content-Type 不合法
    response.close()
    raise NotSupportContentTypeError
