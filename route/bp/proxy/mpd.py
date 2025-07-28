# Route: 代理 MPD

from flask import Blueprint, request, Response

import util

from util import encrypt as encrypt_util
from util import request as request_util

from exception import DecryptError, UrlDecryptError
from route import util as route_util
from route.consts.param_name import ENABLE_PROXY, SERVICE_PARAMS_LIST, REQUEST_COOKIES
from route.consts.uri_param_name import URI_NAME_MPD
from route.service import mpd as mpd_service
from route.exception import RequestMPDFileError

# 创建蓝图
proxy_mpd_bp = Blueprint("proxy_mpd", __name__, url_prefix=f'/{URI_NAME_MPD}')

# 默认 MPD 文件 URI
index_name = "index.mpd"


# 代理接口：获取 MPD 文件
@proxy_mpd_bp.route(f'/<encrypt_url>/{index_name}', methods=['GET'])
def proxy_mpd_file(encrypt_url):
    # 解密 URL
    try:
        url = encrypt_util.decrypt_string(encrypt_url)
    except Exception:
        raise DecryptError()

    if not url.startswith("http"):
        raise UrlDecryptError()

    # 获取参数（可以为空）
    enable_proxy = route_util.judge_if_true(request.args.get(ENABLE_PROXY))

    # 获取请求的查询参数
    request_params = request.args.to_dict()  # 转换为普通字典
    request_params = {k: v for k, v in request_params.items() if k not in SERVICE_PARAMS_LIST}
    request_cookies_param = request.args.get(REQUEST_COOKIES)  # 请求 URL 时携带的 Cookie

    # 生成 MPD 文件
    mpd_file = mpd_service.get_mpd_response(
        url, enable_proxy,
        request_params=request_params,
        request_cookies=request_util.get_cookies_dict_from_params(request_cookies_param)
    )

    # 没有内容，抛出异常
    if mpd_file is None:
        raise RequestMPDFileError(url=url, message="无法请求指定文件")

    # 获取文本
    mpd_content = mpd_file.get_xml_content()

    # 设置响应头
    headers = {
        'Content-Type': 'application/dash+xml',
        'Content-Length': len(mpd_content)
    }

    # 返回结果 (MPD 文件内容)
    return Response(mpd_content, status=200, headers=headers)


# 代理接口：请求 MPD 媒体文件
@proxy_mpd_bp.route(f'/<encrypt_url>/<path:sub_path>', methods=['GET'])
def proxy_mpd_media_files(encrypt_url, sub_path):
    # 解密 URL
    try:
        url = encrypt_util.decrypt_string(encrypt_url)
    except Exception:
        raise DecryptError()

    if not url.startswith("http"):
        raise UrlDecryptError()

    # 构建真正请求的媒体文件 URL
    media_file_url = util.get_url_root(url) + sub_path

    # 获取请求的查询参数
    request_params = request.args.to_dict()  # 转换为普通字典
    request_params = {k: v for k, v in request_params.items() if k not in SERVICE_PARAMS_LIST}
    request_cookies_param = request.args.get(REQUEST_COOKIES)  # 请求 URL 时携带的 Cookie

    # 获得视频流响应
    response = mpd_service.proxy_mpd_media_files(
        media_file_url,
        request_params=request_params,
        request_cookies=request_util.get_cookies_dict_from_params(request_cookies_param)
    )

    response_headers = {
        'Content-Type': response.headers.get('Content-Type') or response.headers.get('content-type')
    }

    # 构造结果
    flask_response = Response(response.iter_content(chunk_size=1024),
                              headers=response_headers,
                              status=response.status_code)

    # 更新响应头
    # flask_response.headers.update(response.headers.items())

    # 返回结果
    return flask_response
