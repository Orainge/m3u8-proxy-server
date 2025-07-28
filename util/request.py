# 请求工具类
import base64
import json
import re
import urllib.parse

from urllib.parse import urlencode, urljoin

import server_config
from exception import CookieParamsError

# 默认 User-Agent
default_user_agent = server_config.get_config(["request", "userAgent", "default"],
                                              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                              "like Gecko) Chrome/109.0.5410.0 Safari/537.36")
user_agent_rules_dict = server_config.get_config(["request", "userAgent", "rules"], {})  # User-Agent 规则
request_timeout = server_config.get_config(["request", "timeout"], 10)  # 请求超时时间

# 请求 URL 时，最大的重定向次数
default_max_redirect_times = server_config.get_config(["request", "url", "maxRedirectTimes", "default"], 5)
max_redirect_times_rules_dict = server_config.get_config(
    ["request", "url", "maxRedirectTimes", "rules"], {})


def get_user_agent(url: str) -> str | None:
    """
    获取 User-Agent
    :param url: 待访问的 URL
    :return: 命中的第一个规则对应的 User-Agent，如果没有匹配到则返回默认 User-Agent
    """
    # 根据正则表达式寻找对应的代理服务器 URL
    for regex, value in user_agent_rules_dict.items():
        if re.search(regex, url):
            return value

    # 返回默认 User-Agent
    return default_user_agent


# 拼接查询参数到 URL 中
def append_query_params_to_url(url, query_params):
    # 如果没有参数，直接返回原 URL
    if query_params is None or len(query_params) == 0:
        return url

    # 使用 urlencode() 函数将查询参数编码为 URL 编码格式
    encoded_query_params = urlencode(query_params, doseq=True)

    # 使用 urljoin() 函数拼接 URL 和查询参数
    final_url = urljoin(url, '?' + encoded_query_params)

    # 返回结果
    return final_url


def get_max_redirect_times(url: str) -> int:
    """
    获取请求 URL 时，最大的重定向次数
    :param url: 待访问的 URL
    :return: 最大重定向次数
    """
    # 根据正则表达式寻找 URL 最大重定向次数
    for regex, value in max_redirect_times_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            return value

    # 返回默认值
    return default_max_redirect_times


def get_cookies_query_param_from_dict(cookie_dict: dict) -> str | None:
    """
    将 Cookie Dict 转换为 URL 中的请求参数
    """
    # if cookie_dict is None or len(cookie_dict) == 0:
    #     # 没有 Dict，无需转换
    #     return None

    json_str = json.dumps(cookie_dict, ensure_ascii=False)
    b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    cookie_query_param = urllib.parse.quote(b64_str)
    return cookie_query_param


def get_cookies_dict_from_params(cookie_query_param: str) -> dict | None:
    """
    将 URL 中的请求参数的 Cookie 转换为 Dict
    """
    if cookie_query_param is None or len(cookie_query_param) == 0:
        # 没有传入参数，无需转换
        return None

    json_str = base64.b64decode(cookie_query_param).decode('utf-8')

    try:
        cookie_dict = json.loads(json_str)
        return cookie_dict
    except Exception:
        raise CookieParamsError()
