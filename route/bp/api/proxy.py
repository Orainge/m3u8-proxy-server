# Route: API-代理
from flask import Blueprint, request

from exception import ParamsError
from route import service
from route.consts.param_name import URL, SERVER_NAME, HIDE_SERVER_NAME, ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_URL
from route.util import response_json_ok

# 创建蓝图，以 /api 为前缀
api_proxy_bp = Blueprint("api_proxy", __name__, url_prefix='/proxy')


@api_proxy_bp.route('/getUrl', methods=['POST'])
def api_proxy_get_url():
    """
    获取代理 URL
    """

    # 获取参数
    try:
        body = request.get_json()
        url = body[URL]
        server_name = body[SERVER_NAME] if SERVER_NAME in body else None
        hide_server_name = body[HIDE_SERVER_NAME] if HIDE_SERVER_NAME in body else False
        enable_proxy = body[ENABLE_PROXY] if ENABLE_PROXY in body else False
    except Exception:
        raise ParamsError()

    # 对 URL 进行处理
    # 如果包含 $，应该分割 URL，最后再拼接上去
    url_str_list = url.rsplit("$", 1) if "$" in url else [url]

    # 获取代理后的 URL
    proxy_url = service.generate_proxy_url(url_str_list[0], URI_NAME_URL, server_name, hide_server_name, enable_proxy)

    # 如果包含 $，就拼接上去
    if len(url_str_list) > 1:
        proxy_url += "$"
        proxy_url += url_str_list[1]

    # 返回结果
    return response_json_ok(data=proxy_url)
