# Route: 异常处理

from flask import Flask, Response

import server_config
from exception import RouteError
from route.util import response_json, response_json_error

# 服务器隐身，不抛出任何异常，只有参数正确时才返回数据
hide_server = server_config.get_config(["security", "hideServer"], False)


def register(app: Flask):
    """外部调用注册 handler 到 flask 上"""
    app.register_error_handler(400, bad_request_error)
    app.register_error_handler(401, unauthorized)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, not_found)
    app.register_error_handler(500, internal_server_error)
    app.register_error_handler(RouteError, route_error)
    app.register_error_handler(Exception, exception_error)


def route_error(e: RouteError):
    return response_json(
        code=e.code,
        message=e.message,
        data=e.data
    ), e.http_code


def bad_request_error(e):
    return response_json(
        status=400,
        code=-1,
        message='Bad Request'
        # data=f'[{type(e).__name__}: {e}]'
    )


def unauthorized(e):
    if hide_server:
        return no_response_handler(e)
    else:
        return response_json(
            status=401,
            code=-1,
            message='Forbidden'
        )


def forbidden(e):
    if hide_server:
        return no_response_handler(e)
    else:
        return response_json(
            status=403,
            code=-1,
            message='Forbidden'
        )


def not_found(e):
    if hide_server:
        return no_response_handler(e)
    else:
        return response_json(
            status=404,
            code=-1,
            message='数据不存在'
        )


def internal_server_error(e):
    if hide_server:
        return no_response_handler(e)
    else:
        return response_json_error(
            message='str(e)',
            data=f'{type(e).__name__}: {e}'
        )


def exception_error(e):
    return response_json_error(
        message='Internal Server Error',
        data=f'{type(e).__name__}: {e}'
    )


# 不返回任何数据
def no_response_handler(e):
    return Response(status=404)
