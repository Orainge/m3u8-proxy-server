# Route: 代理 URL

from flask import Blueprint, request, Response

from util import encrypt as encrypt_util
from exception import DecryptError, UrlDecryptError
from route import util as route_util
from route.consts.param_name import ENABLE_PROXY, SERVER_NAME
from route.consts.uri_param_name import URI_NAME_URL
from route.service import url as url_service
from route.exception import NotSupportContentTypeError

# 创建蓝图
proxy_url_bp = Blueprint("proxy_url", __name__, url_prefix=f'/{URI_NAME_URL}')


# 代理接口：获取 M3U8 文件
@proxy_url_bp.route('/<encrypt_url>', methods=['GET'])
def proxy_m3u8_file(encrypt_url):
    # 解密 URL
    try:
        url = encrypt_util.decrypt_string(encrypt_url)
    except Exception:
        raise DecryptError()

    if not url.startswith("http"):
        raise UrlDecryptError()

    # 获取参数（可以为空）
    enable_proxy = route_util.judge_if_true(request.args.get(ENABLE_PROXY))
    server_name = request.args.get(SERVER_NAME)

    # 获取跳转的 URL
    redirect_url = url_service.get_redirect_url(url, enable_proxy, server_name)

    # 没有跳转的 URL，抛出异常
    if redirect_url is None:
        raise NotSupportContentTypeError()

    # 返回 302 跳转
    return Response("", headers={"Location": redirect_url}, status=302)
