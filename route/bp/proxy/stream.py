# Route: 代理流式传输文件

from flask import Blueprint, request, Response

from exception import DecryptError, UrlDecryptError
from route import util as route_util
from route.consts.param_name import ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_STREAM
from route.service import proxy as proxy_service
from util import encrypt as encrypt_util

# 创建蓝图
proxy_stream_bp = Blueprint("proxy_stream", __name__, url_prefix=f'/{URI_NAME_STREAM}')


# 代理接口：请求流式传输文件
@proxy_stream_bp.route('/<encrypt_url>', methods=['GET'])
def proxy_stream_file(encrypt_url):
    # 解密 URL
    try:
        url = encrypt_util.decrypt_string(encrypt_url)
        if not url.startswith("http"):
            raise UrlDecryptError()
    except DecryptError as e:
        raise e
    except Exception:
        raise UrlDecryptError()

    # 获取参数（可以为空）
    enable_proxy = route_util.judge_if_true(request.args.get(ENABLE_PROXY))

    # 获得视频流响应
    response = proxy_service.proxy_stream(url, enable_proxy)

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
