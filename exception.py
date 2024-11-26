# 异常类
from http.client import HTTPException


class RouteError(HTTPException):
    def __init__(self, message='接口异常', http_code=500, code=-1, data=None):
        self.message = message
        self.http_code = http_code
        self.code = code
        self.data = data

    def __str__(self):
        return self.message


class ParamsError(RouteError):
    """参数不正确"""

    def __init__(self, message='参数不正确', data=None):
        super().__init__(message=message, http_code=200, data=data)


class TokenParamsError(ParamsError):
    """Token 参数不正确"""

    def __init__(self):
        super().__init__(message='Token 不正确')


class DecryptError(ParamsError):
    """解密不正确"""

    def __init__(self, message='解密不正确'):
        super().__init__(message=message)


class UrlDecryptError(DecryptError):
    """URL 解密不正确"""

    def __init__(self):
        super().__init__(message='URL 不正确')


class ServerUrlTypeError(ParamsError):
    """Server URL 类型不正确"""

    def __init__(self):
        super().__init__(message='Server URL 类型不正确')


class TimestampParamsError(ParamsError):
    """时间戳参数不正确"""

    def __init__(self):
        super().__init__()
