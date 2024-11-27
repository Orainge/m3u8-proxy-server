# 代理服务

import requests

from server_config import M3U8_FILE_MAX_DEEP, M3U8_FILE_MAX_REDIRECT_TIMES
from route.consts.param_name import ENABLE_PROXY
from route.consts.uri_param_name import URI_NAME_PROXY, URI_NAME_VIDEO
from route.exception import RequestM3u8FileError
from util import encrypt as encrypt_util
from util import proxy as proxy_util
from util import request as request_util
from util import server as server_util
from util.request import request_timeout


class JudgeFinalM3u8FileResult:
    """
    判断 M3U8 是否是最后一个文件的结果
    """

    def __init__(self):
        self.is_final_m3u8_file = True
        self.m3u8_url = ""
        self.body = ""

    def append_body_line(self, line_string: str):
        """
        附加一行到 body，自动引入换行符
        :param line_string: 要附加的字符串
        """
        if self.body is not None:
            self.body += line_string + "\n"

    def append_body_empty_line(self):
        """
        附加空行
        """
        self.body += "\n"


class ProxyM3u8Response:
    """获取代理 M3U8 文件的响应"""

    def __init__(self):
        self.response_object = None
        self.body = ""
        self.real_url = ""

    def get_body_length(self):
        return len(self.body)

    def get_real_url_root(self):
        """
        获取真实 URL 的根 URI
        """
        if self.real_url is None or len(self.real_url) == 0:
            return ''

        # 查找最后一个斜杠的索引
        last_slash_index = self.real_url.rfind("/")

        # 截取字符串
        substring = self.real_url[:last_slash_index + 1]

        # 返回结果
        return substring


def get_proxy_m3u8_response(url, enable_proxy, server_name) -> ProxyM3u8Response:
    """
    代理请求 M3U8 文件
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问视频文件
    :param server_name: 服务器名称
    :return:
    """
    proxy_m3u8_response = None

    # 递归查找最终含 ts 流的 M3U8 文件（指定层级）
    for i in range(M3U8_FILE_MAX_DEEP):
        proxy_m3u8_response = do_request_m3u8_file(url, enable_proxy)
        judge_result = judge_final_m3u8_file(proxy_m3u8_response, enable_proxy, server_name)
        if judge_result.is_final_m3u8_file:
            # 是最后一级，赋值
            proxy_m3u8_response.body = judge_result.body
            break
        else:
            # 不是最后一级，转换 URL
            url = judge_result.m3u8_url

    # 返回查询结果
    return proxy_m3u8_response


def do_request_m3u8_file(url, enable_proxy) -> ProxyM3u8Response:
    """
    请求 m3u8 文件
    :param url: 原始非加密的 M3U8 文件 URL
    :param enable_proxy: 是否启用代理访问视频文件
    :return:
    """
    # 请求，请求次数限制在设置的最大重定向次数
    to_request_url = url
    for i in range(M3U8_FILE_MAX_REDIRECT_TIMES):
        response = requests.get(to_request_url,
                                timeout=request_timeout,
                                headers={
                                    'User-Agent': request_util.get_user_agent(url),
                                },
                                allow_redirects=False,
                                proxies=proxy_util.get_proxies(url, enable_proxy))

        # 获取请求结果 code，根据请求结果 code 进行判断
        status_code = response.status_code
        if status_code == 200:
            # 正常请求，返回结果
            proxy_m3u8_response = ProxyM3u8Response()
            proxy_m3u8_response.response_object = response
            proxy_m3u8_response.real_url = to_request_url
            proxy_m3u8_response.body = response.text
            return proxy_m3u8_response
        elif 300 <= status_code < 400:
            # 处理重定向
            to_request_url = response.headers["Location"]
        else:
            # 不正常的请求，抛出异常
            raise RequestM3u8FileError(url=to_request_url, status_code=status_code, text=response.text)

    # 抛出异常：请求次数超过设置的最大重定向次数
    raise RequestM3u8FileError(message="请求次数超过设置的最大重定向次数", url=url)


# 判断是否是最后一级 M3U8 文件
def judge_final_m3u8_file(proxy_m3u8_result: ProxyM3u8Response, enable_proxy, server_name):
    judge_result = JudgeFinalM3u8FileResult()
    body = proxy_m3u8_result.body
    url_prefix = server_util.get_server_url(server_name) + f'/{URI_NAME_PROXY}/{URI_NAME_VIDEO}/'

    for line_str in body.split("\n"):
        if len(line_str) == 0:
            # 空行
            judge_result.append_body_empty_line()
        elif line_str.startswith("#"):
            # "#" 开头的行 / 非 URL 行
            judge_result.append_body_line(line_str)
        elif ".m3u" in line_str:
            # 包含子 M3U8 文件，需要继续请求，退出循环
            judge_result.is_final_m3u8_file = False

            # 判断子 M3U8 文件 URL 情况
            if line_str.startswith("http"):
                # 如果文件 URL 开始于 http / https
                judge_result.m3u8_url = line_str
            else:
                # 相对路径
                if line_str.startswith("/"):
                    # 如果开始于 "/" ，需要去掉这个斜杠
                    line_str = line_str[1:]
                judge_result.m3u8_url = f'{proxy_m3u8_result.get_real_url_root()}{line_str}'

            # 退出循环
            break
        else:
            # 普通 TS 流文本行
            # 判断文件 URL 情况
            if line_str.startswith("http"):
                # 如果文件 URL 开始于 http / https，直接使用
                pass
            else:
                # 相对路径
                if line_str.startswith("/"):
                    # 如果开始于 "/" ，需要去掉这个斜杠
                    line_str = line_str[1:]

                # 对原始 URI 进行处理
                line_str = line_str.replace('\r', '')  # 这个大坑，气死我了

                # 拼接成代理 URL
                line_str = url_prefix + encrypt_util.encrypt_string(
                    f'{proxy_m3u8_result.get_real_url_root()}{line_str}')

                # 准备附加额外参数
                query_params = {}

                # 是否开启代理
                if enable_proxy is True:
                    query_params[ENABLE_PROXY] = "true"

                # 拼接查询参数
                line_str = request_util.append_query_params_to_url(line_str, query_params)

            # 附加行
            judge_result.append_body_line(line_str)

    # 返回结果
    return judge_result


def proxy_video(url, enable_proxy):
    """
    代理请求视频文件
    :param url: 原始非加密的视频 URL
    :param enable_proxy: 是否启用代理访问视频文件
    :param user_agent: 请求 User-Agent
    :return:
    """
    # 执行请求并返回结果
    return requests.get(url,
                        timeout=request_timeout,
                        headers={
                            'User-Agent': request_util.get_user_agent(url),
                        },
                        proxies=proxy_util.get_proxies(url, enable_proxy),
                        stream=True)
