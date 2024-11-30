# URL 服务

import re
import requests

from route import service
from route.consts.uri_param_name import URI_NAME_M3U8, URI_NAME_VIDEO
from route.consts.url_type import URL_TYPE_M3U8, URL_TYPE_VIDEO
from route.consts.url_type import accept_content_type_regex_list_m3u8, accept_content_type_regex_list_video
from route.exception import NotSupportContentTypeError, RequestM3u8FileError
from route.service import proxy as proxy_service
from util import proxy as proxy_util
from util import request as request_util
from util.request import request_timeout


def get_redirect_url(url, enable_proxy, server_name):
    """
    获取跳转链接
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问视频文件
    :param server_name: 服务器名称
    """
    # 先请求 URL，看看是什么类型的链接
    response = requests.get(url,
                            timeout=request_timeout,
                            headers={
                                'User-Agent': request_util.get_user_agent(url),
                            },
                            proxies=proxy_util.get_proxies(url, enable_proxy),
                            stream=True)
    # 关闭流
    response.close()

    # 拿到最后 URL（包括重定向后的 URL）
    final_url = response.url

    # 判断  URL 类型
    url_type = None
    content_type = response.headers.get('Content-Type')

    for regex in accept_content_type_regex_list_m3u8:
        if re.fullmatch(regex, content_type):
            url_type = URL_TYPE_M3U8
            break

    if url_type is None:
        for regex in accept_content_type_regex_list_video:
            if re.fullmatch(regex, content_type):
                url_type = URL_TYPE_VIDEO
                break

    if url_type is None:
        # Content-Type 不合法
        raise NotSupportContentTypeError

    # 生成代理链接
    if url_type is URL_TYPE_M3U8:
        # 寻找真正的 M3U8 链接
        m3u8_response = proxy_service.get_m3u8_response(final_url, enable_proxy, server_name)

        if m3u8_response is None:
            raise RequestM3u8FileError(url=url, message="无法请求指定文件")

        # 真实链接：m3u8_response.real_url
        # 根据最后的 M3U8 URL，生成代理 URL
        proxy_url = service.generate_proxy_url(m3u8_response.real_url,
                                               URI_NAME_M3U8,
                                               server_name=server_name,
                                               enable_proxy=enable_proxy)
    elif url_type is URL_TYPE_VIDEO:
        proxy_url = service.generate_proxy_url(final_url,
                                               URI_NAME_VIDEO,
                                               server_name=server_name,
                                               hide_server_name=True,
                                               enable_proxy=enable_proxy)
    else:
        raise NotSupportContentTypeError

    # 返回最终的链接
    return proxy_url
