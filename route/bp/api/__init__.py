# Route: API

import time
import server_config
from flask import Blueprint, request

from .m3u8_proxy_url import api_m3u8_proxy_url_bp

from exception import ParamsError, TokenParamsError, TimestampParamsError
from route.consts.param_name import TOKEN, TIMESTAMP

# 创建蓝图，以 /api 为前缀
api_bp = Blueprint("api", __name__, url_prefix='/api')

# 注册蓝图
api_bp.register_blueprint(api_m3u8_proxy_url_bp)

# 是否启用 API
enable_api = server_config.get_config(["security", "api", "enable"], False)
api_token = server_config.api_token

# 允许的请求时间戳和当前时间间隔（秒）
timestamp_interval = 300


@api_bp.before_request
def api_before_request():
    """
    请求接口前钩子
    """

    # 检查是否启用 API 访问
    if not enable_api:
        return

    # 检查有没有 body
    try:
        body = request.get_json()
    except Exception:
        raise ParamsError()

    if body is None:
        # 没有 body
        raise ParamsError()

    try:
        # 检查时间戳是否正确
        timestamp = body[TIMESTAMP]

        # 将传入的时间戳转换为浮点型
        provided_timestamp = float(timestamp)

        # 如果时间戳是以毫秒为单位的，将其转换为秒
        if provided_timestamp > 1e10:  # 假设大于 1e10 的是毫秒
            provided_timestamp /= 1000

        # 获取当前的时间戳
        current_timestamp = time.time()

        # 计算时间差（单位：秒）
        difference_in_seconds = current_timestamp - provided_timestamp
        if difference_in_seconds > timestamp_interval:
            # 如果时间间隔大于 timestamp_interval，就返回错误
            raise TimestampParamsError()
    except TimestampParamsError as te:
        raise te
    except Exception as e:
        raise ParamsError()

    # 验证 Token
    if body[TOKEN] != api_token:
        raise TokenParamsError()
