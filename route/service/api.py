# API 服务
from util import server as server_util
from util import encrypt as encrypt_util
from util import request as request_util
from route.consts.param_name import SERVER_NAME, ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_PROXY, URI_NAME_M3U8


def generate_m3u8_proxy_url(url, enable_proxy, server_name):
    """
    生成 M3U8 代理链接
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问视频文件
    :param server_name: 服务器名称
    """

    # 将 url 进行加密
    encrypt_url = encrypt_util.encrypt_string(url)

    # 拼接url
    server_url = server_util.get_server_url(server_name)
    proxy_url = f"{server_url}/{URI_NAME_PROXY}/{URI_NAME_M3U8}/{encrypt_url}"

    # 准备额外参数
    query_params = {}

    # 是否开启代理
    if enable_proxy is True:
        query_params[ENABLE_PROXY] = "true"

    # 是否附加 URL 类型
    if server_name is not None:
        query_params[SERVER_NAME] = server_name

    # 拼接查询参数
    proxy_url = request_util.append_query_params_to_url(proxy_url, query_params)

    # 返回结果
    return proxy_url
