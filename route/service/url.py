# URL 服务
import base64
import json
import re
import requests

from route import service
from route.consts.uri_param_name import URI_NAME_M3U8, URI_NAME_MPD, URI_NAME_VIDEO, URI_NAME_STREAM
from route.consts.url_type import URL_TYPE_M3U8, URL_TYPE_MPD, URL_TYPE_VIDEO, URL_TYPE_STREAM
from route.consts.url_type import accept_content_type_regex_list_m3u8, accept_content_type_regex_list_mpd, \
    accept_content_type_regex_list_video, accept_content_type_regex_list_stream
from route.exception import NotSupportContentTypeError, RequestUrlError, RequestM3u8FileError
from route.service import m3u8 as m3u8_proxy_service
from util import proxy as proxy_util
from util import request as request_util
from util.request import request_timeout
from util.mpd import XMLFile
from urllib.parse import parse_qs, urlparse


def get_redirect_url(url, enable_proxy, server_name, request_cookies: dict, m3u8_max_stream: bool):
    """
    获取跳转链接
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param server_name: 服务器名称
    :param request_cookies: 请求时 URL 时携带的 Cookie
    :param m3u8_max_stream: M3U8 文件中，是否只保留最清晰的视频流
    """
    # 先请求 URL，看看是什么类型的链接
    request_success = False  # 请求是否成功
    response = None
    to_request_url = url

    # 转换请求 Cookie
    cookies = request_cookies

    for i in range(request_util.get_max_redirect_times(url) + 1):
        response = requests.get(to_request_url,
                                timeout=request_timeout,
                                headers={
                                    'User-Agent': request_util.get_user_agent(to_request_url)
                                },
                                allow_redirects=False,
                                proxies=proxy_util.get_proxies(to_request_url, enable_proxy),
                                cookies=cookies,
                                stream=True)

        # 获取请求结果 code，根据请求结果 code 进行判断
        status_code = response.status_code

        # 获取 cookie 字典
        new_cookies = response.cookies.get_dict()
        if new_cookies is not None and len(new_cookies) > 0:
            cookies.update(new_cookies)

        if status_code == 200:
            # 正常请求
            request_success = True

            # 退出循环
            break
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
            raise RequestUrlError(url=to_request_url, status_code=status_code, text=response.text)

    # 变量赋值
    url_type = None
    response_text = ""
    content_type = response.headers.get('Content-Type') or response.headers.get('content-type')
    final_url = to_request_url  # 拿到最后 URL（包括重定向后的 URL）

    # 先检查是否是流式传输的 Content-Type
    for regex in accept_content_type_regex_list_stream:
        if re.search(regex, content_type):
            url_type = URL_TYPE_STREAM
            break

    if url_type is None:
        # 如果是流式传输会卡住不动，所以要先判断再获取
        response_text = response.text

    # 关闭流
    response.close()

    if request_success is not True:
        # 抛出异常：请求次数超过设置的最大重定向次数
        raise RequestUrlError(message="请求次数超过设置的最大重定向次数", url=url)

    # 检查 User-Agent: 是否是 M3U8
    if url_type is None:
        for regex in accept_content_type_regex_list_m3u8:
            if re.search(regex, content_type):
                url_type = URL_TYPE_M3U8
                break

    # 检查 User-Agent: 是否是 MPD
    if url_type is None:
        for regex in accept_content_type_regex_list_mpd:
            if re.search(regex, content_type):
                url_type = URL_TYPE_MPD
                break

    # 检查 User-Agent: 是否是 Video
    if url_type is None:
        for regex in accept_content_type_regex_list_video:
            if re.search(regex, content_type):
                url_type = URL_TYPE_VIDEO
                break

    # 检查文件内容：是否是 M3U8
    if url_type is None:
        try:
            if response_text.splitlines()[0] == "#EXTM3U":
                url_type = URL_TYPE_M3U8
        except Exception:
            # 解析失败
            pass

    # 检查文件内容：是否是 MPD 文件
    if url_type is None:
        try:
            xml_file = XMLFile(response_text)
            if xml_file.is_mpd_file():
                url_type = URL_TYPE_MPD
        except Exception:
            # XML 解析失败
            pass

    if url_type is None:
        # URL 不合法
        raise NotSupportContentTypeError

    # 生成代理链接
    if url_type is URL_TYPE_M3U8:
        # 寻找真正的 M3U8 链接
        m3u8_object = m3u8_proxy_service.get_m3u8_file(
            final_url,
            enable_proxy,
            server_name,
            request_cookies=cookies,
            m3u8_max_stream=m3u8_max_stream,
            need_process=False
        )

        if m3u8_object is None:
            raise RequestM3u8FileError(url=url, message="无法请求指定文件")

        # 根据最后的 M3U8 URL，生成代理 URL
        proxy_url = service.generate_proxy_url(m3u8_object.url,
                                               URI_NAME_M3U8,
                                               server_name=server_name,
                                               request_cookies=cookies,
                                               m3u8_max_stream=m3u8_max_stream,
                                               enable_proxy=enable_proxy)
    elif url_type is URL_TYPE_MPD:
        proxy_url = service.generate_proxy_url(final_url,
                                               URI_NAME_MPD,
                                               server_name=server_name,
                                               hide_server_name=True,
                                               enable_proxy=enable_proxy,
                                               request_cookies=cookies,
                                               query_params=parse_qs(urlparse(final_url).query))
    elif url_type is URL_TYPE_VIDEO:
        proxy_url = service.generate_proxy_url(final_url,
                                               URI_NAME_VIDEO,
                                               server_name=server_name,
                                               hide_server_name=True,
                                               request_cookies=cookies,
                                               enable_proxy=enable_proxy)
    elif url_type is URL_TYPE_STREAM:
        proxy_url = service.generate_proxy_url(final_url,
                                               URI_NAME_STREAM,
                                               server_name=server_name,
                                               hide_server_name=True,
                                               request_cookies=cookies,
                                               enable_proxy=enable_proxy)
    else:
        raise NotSupportContentTypeError

    # 返回最终的链接
    return proxy_url
