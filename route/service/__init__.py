# 通用服务方法
from util import server as server_util
from util import encrypt as encrypt_util
from util import request as request_util
from route.consts.param_name import SERVER_NAME, ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_PROXY


def generate_proxy_url(url: str,
                       uri: str,
                       server_name: str = None,
                       hide_server_name: bool = False,
                       enable_proxy: bool = False):
    """
    生成代理 URL
    :param url: 原始非加密的 URL
    :param uri: 生成 URL 时中间使用的 URI
    :param server_name: 服务器名称
    :param hide_server_name: 是否在生成的 URL 链接中隐藏服务器名称
    :param enable_proxy: 是否启用代理访问视频文件
    """

    # 将 url 进行加密
    encrypt_url = encrypt_util.encrypt_string(url, server_name)

    # 拼接url
    server_url = server_util.get_server_url(server_name)
    proxy_url = f"{server_url}/{URI_NAME_PROXY}/{uri}/{encrypt_url}"

    # 准备额外参数
    query_params = {}

    # 是否开启代理
    if enable_proxy is True:
        query_params[ENABLE_PROXY] = "true"

    # 是否在 URL 中附加服务器名称
    if not hide_server_name and server_name is not None:
        query_params[SERVER_NAME] = server_name

    # 拼接查询参数
    proxy_url = request_util.append_query_params_to_url(proxy_url, query_params)

    # 返回结果
    return proxy_url
