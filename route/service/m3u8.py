# M3U8 代理服务

import re
import requests

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from route.beans import M3U8Object
from route.consts.param_name import ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_PROXY, URI_NAME_M3U8, URI_NAME_VIDEO, URI_NAME_KEY
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
LINE_TYPE_NORMAL = 0  # 普通行
LINE_TYPE_EXTINF = 1  # #EXTINF
LINE_TYPE_STREAM_INF = 2  # #EXT-X-STREAM-INF

# URI 类型
URI_TYPE_KEY = 0  # KEY
URI_TYPE_M3U8 = 1  # M3U8 文件
URI_TYPE_VIDEO = 2  # 视频文件

# 检查 URI 的类型
CHECK_URI_TYPE_ABSOLUTE = 0  # 绝对路径
CHECK_URI_TYPE_RELATIVE = 1  # 相对路径
CHECK_URI_TYPE_RELATIVE_HOST = 2  # 相对主机路径
CHECK_URI_TYPE_OTHER = 3  # 其他协议


def _do_request_m3u8_file(url: str, enable_proxy: bool) -> M3U8Object:
    """
    请求 M3U8 文件
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
                return M3U8Object(to_request_url, response)
            else:
                # Content-Type 不合法
                response.close()
                raise NotSupportContentTypeError
        elif 300 <= status_code < 400:
            # 处理重定向
            location = response.headers["Location"]
            if location.startswith("http"):
                # 绝对路径
                to_request_url = location
            elif location.startswith("/"):
                # 相对主机路径
                parsed_url = urlparse(to_request_url)
                to_request_url = f'{parsed_url.scheme}://{parsed_url.netloc}{location}'
            else:
                # 相对路径
                find_root_url = to_request_url.split('?')[0]  # 截取 ? 前的部分
                last_slash_index = find_root_url.rfind("/")
                relative_uri = to_request_url[:last_slash_index + 1]
                to_request_url = f'{relative_uri}{location}'
        else:
            # 不正常的请求，抛出异常
            raise RequestM3u8FileError(url=to_request_url, status_code=status_code, text=response.text)

    # 抛出异常：请求次数超过设置的最大重定向次数
    raise RequestM3u8FileError(message="请求次数超过设置的最大重定向次数", url=url)


def _get_uri(line_str: str) -> str | None:
    """
    获取 URI
    :param line_str: 一行字符串
    :return 提取出来的 URI
    """
    pattern = r'URI="([^"]+)"'

    # 使用 re.search 查找匹配项
    match = re.search(pattern, line_str)

    if match:
        uri = match.group(1)
        return uri
    else:
        return None


def _merge_query_params(url: str, query_string: str):
    """
    合并 URL 参数到 url 中
    :param url: URL
    :param query_string: 要合并的查询参数字符串 (a=1&b=2)
    """
    add_leading_slash = not url.startswith("/")  # 记录原始状态

    # 确保 `urlparse` 解析正确（临时加 `/`）
    if add_leading_slash:
        url = "/" + url

    # 解析 URL
    parsed_url = urlparse(url)
    original_params = parse_qs(parsed_url.query)  # 解析查询参数

    # 解析新查询参数
    new_params = parse_qs(query_string)

    # 仅添加原 URL 中不存在的参数
    for key, values in new_params.items():
        if key not in original_params:
            original_params[key] = values

    # 重新拼接查询字符串
    new_query_string = urlencode(original_params, doseq=True)

    # 重新组合 URL
    updated_url = urlunparse((
        parsed_url.scheme,  # 为空
        parsed_url.netloc,  # 为空
        parsed_url.path,
        parsed_url.params,
        new_query_string,
        parsed_url.fragment
    ))

    # 如果原始 `final_uri` 没有 `/`，则去掉 `/`
    if add_leading_slash:
        updated_url = updated_url.lstrip("/")

    return updated_url


def _process_uri(uri: str,
                 server_name: str,
                 enable_proxy: bool,
                 m3u8_object: M3U8Object,
                 uri_type: int) -> str:
    """
    处理 URI
    :param uri: 原始 URI
    :param server_name: 服务器名称
    :param enable_proxy: 是否使用外部代理请求文件
    :param m3u8_object: 需要处理的 M3U8 对象
    :param uri_type: URI 类型
    :return 处理后的 URI
    """
    # 参数准备
    # enable_proxy_direct_url: 是否强制代理直连 URL
    url_prefix = server_util.get_server_url(server_name) + f'/{URI_NAME_PROXY}/'

    if uri_type == URI_TYPE_KEY:
        url_prefix = url_prefix + f'{URI_NAME_KEY}/'
        enable_proxy_direct_url = service_util.get_enable_proxy_key_direct_url(uri)
    elif uri_type == URI_TYPE_M3U8:
        url_prefix = url_prefix + f'{URI_NAME_M3U8}/'
        enable_proxy_direct_url = service_util.get_enable_proxy_m3u8_direct_url(uri)
    elif uri_type == URI_TYPE_VIDEO:
        url_prefix = url_prefix + f'{URI_NAME_VIDEO}/'
        enable_proxy_direct_url = service_util.get_enable_proxy_video_direct_url(uri)
    else:
        raise Exception("参数 [uri_type] 不正确")

    # 检查 URI 类型
    if uri.startswith("http"):
        # 绝对路径
        check_uri_type = CHECK_URI_TYPE_ABSOLUTE

        # 检查是否强制代理绝对路径 URL
        if enable_proxy_direct_url is not True:
            # 如果不强制代理，原样返回
            return uri
    elif uri.startswith("/"):
        # 相对主机路径
        check_uri_type = CHECK_URI_TYPE_RELATIVE_HOST
    else:
        protocol_pos = uri.find("://")
        slash_pos = uri.find("/")

        if protocol_pos != -1 and slash_pos > protocol_pos:
            # 如果 "/" 出现在 "://" 中间或之后
            # 其他协议
            check_uri_type = CHECK_URI_TYPE_OTHER
        else:
            # 相对路径
            check_uri_type = CHECK_URI_TYPE_RELATIVE

    if check_uri_type == CHECK_URI_TYPE_OTHER:
        # 其他协议
        final_uri = uri
    else:
        # 拼接 Query 参数
        full_url = uri

        # 对同名参数进行处理
        if m3u8_object.query_param_string is not None:
            full_url = _merge_query_params(full_url, m3u8_object.query_param_string)

        if check_uri_type == CHECK_URI_TYPE_ABSOLUTE:
            # 绝对路径
            uri = url_prefix + encrypt_util.encrypt_string(f'{full_url}')
        elif check_uri_type == CHECK_URI_TYPE_RELATIVE:
            # 相对路径
            uri = url_prefix + encrypt_util.encrypt_string(
                f'{m3u8_object.get_uri_relative()}{full_url}')
        elif check_uri_type == CHECK_URI_TYPE_RELATIVE_HOST:
            # 相对主机路径
            uri = url_prefix + encrypt_util.encrypt_string(
                f'{m3u8_object.get_uri_host()}{full_url}')
        else:
            raise Exception("参数 [check_uri_type] 不正确")

        # 准备附加额外参数
        query_params = {}

        # 是否开启代理
        if enable_proxy is True:
            query_params[ENABLE_PROXY] = "true"

        # 拼接查询参数
        final_uri = request_util.append_query_params_to_url(uri, query_params)

    # 返回结果
    return final_uri


def _check_and_process_if_final_m3u8_file(
        m3u8_object: M3U8Object,
        enable_proxy: bool,
        server_name: str,
        need_process: bool) -> bool:
    """
    判断是否是最后要返回的 M3U8 文件，并对文件进行处理
    :param m3u8_object: 要处理/检查的 M3U8 对象
    :param enable_proxy: 是否使用外部代理请求文件
    :param server_name: 服务器名称
    :param need_process: 是否需要处理; True/False: 会/不会对 M3U8 文件进行深层次处理
    """
    body = m3u8_object.body  # M3U8 文件内容
    m3u8_stream_count = 0  # 轨道数
    latest_m3u8_stream_uri = None  # 最新的 stream uri
    new_body = ""  # 新的 M3U8 文件内容

    # 设置当前行类型
    line_type = LINE_TYPE_NORMAL

    # 按行遍历处理
    for line_str in body.split("\n"):
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
                elif line_str.startswith("#EXT-X-MEDIA"):
                    # 当前行是媒体信息
                    line_type = LINE_TYPE_NORMAL
                    if need_process is True:
                        # 需要处理
                        uri = _get_uri(line_str)
                        if uri is not None:
                            # 记录轨道
                            m3u8_stream_count += 1
                            if service_util.enable_proxy_m3u8:
                                # 代理 M3U8
                                process_uri = _process_uri(uri, server_name, enable_proxy, m3u8_object, URI_TYPE_M3U8)
                                # 将代理的 URI 放入到原来的位置
                                line_str = line_str.replace(uri, process_uri)
                elif line_str.startswith("#EXT-X-KEY"):
                    # 当前行是 M3U8 KEY
                    line_type = LINE_TYPE_NORMAL
                    if need_process is True:
                        # 需要处理
                        uri = _get_uri(line_str)
                        if uri is not None:
                            if service_util.enable_proxy_key:
                                # 代理 M3U8 KEY
                                process_uri = _process_uri(uri, server_name, enable_proxy, m3u8_object, URI_TYPE_KEY)
                                # 将代理的 KEY URI 放入到原来的位置
                                line_str = line_str.replace(uri, process_uri)
                elif line_str.startswith("#EXT-X-PREFETCH"):
                    # 当前行是视频分片 PREFETCH
                    line_type = LINE_TYPE_NORMAL
                    if need_process is True:
                        # 需要处理
                        video_url = line_str.split(":", 1)[1]
                        video_url = _process_uri(video_url, server_name, enable_proxy, m3u8_object, URI_TYPE_VIDEO)
                        line_str = f"#EXT-X-PREFETCH:{video_url}"
        elif line_type == LINE_TYPE_STREAM_INF:
            # 可变视频流(多轨道)
            line_type = LINE_TYPE_NORMAL

            # 记录轨道
            m3u8_stream_count += 1
            latest_m3u8_stream_uri = line_str

            if need_process is True and service_util.enable_proxy_m3u8:
                # 代理 M3U8
                line_str = _process_uri(line_str, server_name, enable_proxy, m3u8_object, URI_TYPE_M3U8)
        elif line_type == LINE_TYPE_EXTINF:
            # 视频分片
            line_type = LINE_TYPE_NORMAL
            if need_process is True and service_util.enable_proxy_video:
                # 代理视频流
                line_str = _process_uri(line_str, server_name, enable_proxy, m3u8_object, URI_TYPE_VIDEO)

        # 这一行处理完成，附加当前这一行
        new_body += line_str + "\n"

    if m3u8_stream_count == 1:
        # 单轨道
        # 检查 latest_m3u8_stream_uri 的类型
        if latest_m3u8_stream_uri.startswith("http"):
            # 绝对路径
            m3u8_object.next_level_url = latest_m3u8_stream_uri
        elif latest_m3u8_stream_uri.startswith("/"):
            # 相对主机路径
            m3u8_object.next_level_url = f'{m3u8_object.get_uri_host()}{latest_m3u8_stream_uri}'
        else:
            protocol_pos = latest_m3u8_stream_uri.find("://")
            slash_pos = latest_m3u8_stream_uri.find("/")

            if protocol_pos != -1 and slash_pos > protocol_pos:
                # 如果 "/" 出现在 "://" 中间或之后
                # 其他协议
                # 保持原样，并返回：这是最后一个文件
                m3u8_object.body = new_body
                return True
            else:
                # 相对路径
                m3u8_object.next_level_url = f'{m3u8_object.get_uri_relative()}{latest_m3u8_stream_uri}'

        # 返回结果：这不是最后一个 M3U8 文件
        return False
    else:
        # 这是最后一个 M3U8 文件
        # 处理完成，更新 M3U8 文件
        m3u8_object.body = new_body
        return True


def get_m3u8_file(url: str,
                  enable_proxy: bool,
                  server_name: str,
                  need_process: bool = True) -> M3U8Object:
    """
    请求 M3U8 文件
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param server_name: 服务器名称
    :param need_process: 是否需要处理; True/False: 会/不会对 M3U8 文件进行深层次处理
    :return:
    """
    # 递归查找最终含 ts 流的 M3U8 文件（指定层级）
    for i in range(m3u8_util.get_max_deep(url) + 1):
        # 请求并获取 M3U8 Object
        m3u8_object = _do_request_m3u8_file(url, enable_proxy)

        # 判断是否是最后要返回的 M3U8 文件，并对文件进行处理
        is_final_m3u8_file = _check_and_process_if_final_m3u8_file(
            m3u8_object,
            enable_proxy,
            server_name,
            need_process
        )

        if is_final_m3u8_file:
            return m3u8_object
        else:
            url = m3u8_object.next_level_url

    raise RequestM3u8FileError(f"请求超过最大层级: [{url}]")


def proxy_video(url, enable_proxy) -> requests.Response:
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


def proxy_key(url, enable_proxy) -> requests.Response:
    """
    代理请求 M3U8 KEY 文件
    :param url: 原始非加密的视频 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param user_agent: 请求 User-Agent
    :return:
    """
    response = requests.get(url,
                            timeout=request_timeout,
                            headers={
                                'User-Agent': request_util.get_user_agent(url),
                            },
                            proxies=proxy_util.get_proxies(url, enable_proxy),
                            stream=True)

    # 不校验 KEY 文件 Content-Type 类型
    return response


def proxy_stream(url, enable_proxy) -> requests.Response:
    """
    代理请求流式传输文件
    :param url: 原始非加密的流式传输文件 URL
    :param enable_proxy: 是否启用代理访问流式传输文件
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
