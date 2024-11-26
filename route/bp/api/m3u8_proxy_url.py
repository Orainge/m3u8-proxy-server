# Route: M3u8 代理链接
from flask import Blueprint, request

from exception import ParamsError
from route.consts.param_name import URL, SERVER_NAME, ENABLE_PROXY
from route.util import response_json_ok
from route.service import api as api_service

# 创建蓝图，以 /api 为前缀
api_m3u8_proxy_url_bp = Blueprint("api_m3u8_proxy_url", __name__, url_prefix='/m3u8Proxy')


@api_m3u8_proxy_url_bp.route('/getUrl', methods=['POST'])
def api_m3u8_proxy_url_get():
    """
    获取 M3U8 代理链接
    """

    # 获取参数
    try:
        body = request.get_json()
        url = body[URL]
        server_name = body[SERVER_NAME] if SERVER_NAME in body else None
        enable_proxy = body[ENABLE_PROXY] if ENABLE_PROXY in body else None
    except Exception:
        raise ParamsError()

    # 获取代理后的链接
    m3u8_proxy_url = api_service.generate_m3u8_proxy_url(url, enable_proxy, server_name)

    # 返回结果
    return response_json_ok(data=m3u8_proxy_url)
