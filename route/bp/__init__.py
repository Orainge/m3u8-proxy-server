"""
路由
"""

from flask import Flask, request

from .api import api_bp
from .proxy import proxy_bp
from route.consts.param_name import ENABLE_PROXY


def register(app: Flask):
    # 注册其它蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(proxy_bp)

    # 手动注册全局请求接口前钩子
    app.before_request_funcs.setdefault(None, []).append(all_before_request)


def all_before_request():
    """全局请求接口前钩子"""

    # 转换参数 "是否开启代理"
    # Body 里转换
    try:
        body = request.get_json()
        if ENABLE_PROXY in body:
            enable_proxy = body[ENABLE_PROXY]
            body[ENABLE_PROXY] = enable_proxy is True or enable_proxy == "true"
    except Exception:
        return
