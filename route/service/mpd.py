# MPD 代理服务

import requests
from flask import Response

from urllib.parse import urlparse

from route.consts.uri_param_name import URI_NAME_PROXY, URI_NAME_MPD
from route.exception import RequestMPDFileError, NotSupportContentTypeError
from util import encrypt as encrypt_util
from util import proxy as proxy_util
from util import request as request_util
from util import server as server_util
from util import service as service_util
from util.request import request_timeout
from util.mpd import XMLFile


# match = re.fullmatch("正则表达式", "测试字符串")

def get_mpd_response(url: str,
                     enable_proxy: bool,
                     request_params: dict = None,
                     request_cookies: dict = None) -> XMLFile:
    """
    请求 MPD 文件
    :param url: 原始非加密的 MPD 文件 URL
    :param enable_proxy: 是否启用代理访问 M3U8 文件
    :param request_params: 额外请求的参数（附带到实际请求中）
    :param request_cookies: 请求时 URL 时携带的 Cookie
    :return: XMLFile 对象
    """
    xml_files = do_request_mpd_file(url, enable_proxy,
                                    request_params=request_params,
                                    request_cookies=request_cookies)

    # 检查是否存在 BaseURL
    base_url_path = 'Period/BaseURL'
    base_url = xml_files.get_element_text(base_url_path)
    if base_url is not None:
        # 检查是否是绝对路径
        if base_url.startswith("http"):
            # 绝对路径，检查是否强制代理
            if service_util.get_enable_proxy_mpd_direct_url(base_url):
                # 启用强制代理
                if not base_url.endswith("/"):
                    base_url += '/'

                # 对 URL 进行加密
                url_prefix = server_util.get_server_url() + f'/{URI_NAME_PROXY}/{URI_NAME_MPD}/'
                encrypt_url = encrypt_util.encrypt_string(base_url)
                new_base_url = url_prefix + encrypt_url

                # 放入新的 BaseURL
                xml_files.insert_or_update_value(base_url_path, new_base_url)

    # 返回 MPD 文件对象
    return xml_files


def do_request_mpd_file(url: str,
                        enable_proxy: bool,
                        request_params: dict = None,
                        request_cookies: dict = None) -> XMLFile:
    """
    请求 MPD 文件
    :param url: 原始非加密的 MPD 文件 URL
    :param enable_proxy: 是否启用代理访问 MPD 文件
    :param request_params: 额外请求的参数（附带到实际请求中）
    :param request_cookies: 请求时 URL 时携带的 Cookie
    :return: MPD 文件内容字符串
    """
    # 请求，请求次数限制在设置的最大重定向次数
    to_request_url = url
    max_redirect_times = request_util.get_max_redirect_times(url)
    for i in range(max_redirect_times + 1):
        response = requests.get(to_request_url,
                                params=request_params,
                                timeout=request_timeout,
                                headers={
                                    'User-Agent': request_util.get_user_agent(url),
                                },
                                allow_redirects=False,
                                cookies=request_cookies,
                                proxies=proxy_util.get_proxies(url, enable_proxy))

        # 获取请求结果 code，根据请求结果 code 进行判断
        status_code = response.status_code
        if status_code == 200:
            # 判断文件结构是否合法
            try:
                content_type = response.headers.get('Content-Type') or response.headers.get('content-type')
                xml_file = XMLFile(response.text, content_type=content_type)
                if xml_file.is_mpd_file():
                    # 返回结果
                    return xml_file
            except Exception:
                # 如果 XML 解析失败，返回 False
                pass

            # 文件不合法
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
            raise RequestMPDFileError(url=to_request_url, status_code=status_code, text=response.text)

    # 抛出异常：请求次数超过设置的最大重定向次数
    raise RequestMPDFileError(message="请求次数超过设置的最大重定向次数", url=url)


def proxy_mpd_media_files(url: str, request_params: dict = None, request_cookies: dict = None) -> Response:
    """
    代理请求视频文件
    :param url: 原始的媒体文件 URL
    :param request_params: 额外请求的参数
    :param request_cookies: 请求时 URL 时携带的 Cookie
    :return:
    """
    # 执行请求并返回结果
    # 这里允许直接跳转，因为播放是流示传输
    response = requests.get(url,
                            timeout=request_timeout,
                            params=request_params,
                            headers={
                                'User-Agent': request_util.get_user_agent(url),
                            },
                            cookies=request_cookies,
                            proxies=proxy_util.get_proxies(url),
                            stream=True)

    # 这里不做 Content-Type 判断，直接返回
    return response
