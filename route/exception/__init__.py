# 异常类
import logging

from exception import RouteError

logger = logging.getLogger(__name__)


class NotSupportContentTypeError(RouteError):
    """不支持的内容类型"""

    def __init__(self):
        super().__init__(
            code=500,
            message='请求错误：不支持的内容类型'
        )


class RequestM3u8FileError(RouteError):
    """请求 M3U8 文件出错"""

    def __init__(self, message=None, url=None, status_code=None, text=None):
        """
        :param message: 错误信息
        :param url: 请求的 URL
        :param status_code: 响应 http code
        :param text: 响应 text
        """
        data = {}

        if url is not None:
            data["url"] = url

        if status_code is not None:
            data["statusCode"] = status_code

        if status_code is not None:
            data["text"] = text

        super().__init__(
            code=500,
            message='请求错误' if message is None else f'请求错误：{message}',
            data=data
        )
