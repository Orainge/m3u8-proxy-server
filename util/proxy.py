# 代理工具类

import re

import server_config

# 预载代理服务器信息
enable_proxy = server_config.get_config(["proxy", "enable"], False)  # 是否启用代理
default_proxy_server_url = server_config.get_config(["proxy", "server", "default"], None)  # 默认代理服务器 URL
proxy_server_rules_dict = server_config.get_config(["proxy", "server", "rules"], {})  # 代理服务器规则


def get_proxy_server_url(url: str) -> str | None:
    """
    获取代理服务器 URL
    :param url: 待访问的 URL
    :return: None: 不开启代理; str: 命中的第一个规则对应的服务器 URL，如果没有匹配到则返回默认服务器 URL
    """
    if not enable_proxy:
        return None

    # 根据正则表达式寻找对应的代理服务器 URL
    for regex, value in proxy_server_rules_dict.items():
        if re.search(regex, url):
            return value

    # 返回默认服务器 URL
    return default_proxy_server_url


def get_proxies(url: str) -> dict | None:
    """
    获取代理服务器 URL dict
    :param url: 待访问的 URL
    :return: None: 不开启代理; dict: 用于请求 proxies 的配置 dict
    """
    proxies = None
    proxy_server_url = get_proxy_server_url(url)
    if proxy_server_url is not None:
        proxies = {
            'http': proxy_server_url,
            'https': proxy_server_url
        }
    return proxies
