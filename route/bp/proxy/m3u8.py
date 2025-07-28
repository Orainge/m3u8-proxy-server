# Route: 代理 M3U8

from flask import Blueprint, request, Response

from util import encrypt as encrypt_util
from util import request as request_util
from exception import DecryptError, UrlDecryptError
from route import util as route_util
from route.consts.param_name import ENABLE_PROXY, SERVER_NAME, REQUEST_COOKIES
from route.consts.uri_param_name import URI_NAME_M3U8
from route.service import m3u8 as m3u8_proxy_service
from route.exception import RequestM3u8FileError

# 创建蓝图
proxy_m3u8_bp = Blueprint("proxy_m3u8", __name__, url_prefix=f'/{URI_NAME_M3U8}')


# 代理接口：获取 M3U8 文件
@proxy_m3u8_bp.route('/<encrypt_url>', methods=['GET'])
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
    request_cookies_param = request.args.get(REQUEST_COOKIES)  # 请求 URL 时携带的 Cookie

    # 生成反代 M3U8 的链接
    m3u8_object = m3u8_proxy_service.get_m3u8_file(
        url,
        enable_proxy,
        server_name,
        request_cookies=request_util.get_cookies_dict_from_params(request_cookies_param)
    )

    # 没有内容，抛出异常
    if m3u8_object is None:
        raise RequestM3u8FileError(url=url, message="无法请求指定文件")

    # 设置响应头
    headers = {
        'Content-Type': 'application/x-mpegURL',
        'Content-Length': m3u8_object.get_body_length()
    }

    # 返回结果（M3U8 文件内容，不是 JSON）
    return Response(m3u8_object.body, status=200, headers=headers)
