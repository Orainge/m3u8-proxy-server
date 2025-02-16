# 代理工具类

import re

import server_config

# 预载代理服务器信息
config_enable_proxy = server_config.get_config(["proxy", "enable"], False)  # 是否启用代理
force_enable_rules = server_config.get_config(["proxy", "server", "forceEnableRules"], False)  # 是否强制开启规则匹配
default_proxy_server_url = server_config.get_config(["proxy", "server", "default"], None)  # 默认代理服务器 URL
proxy_server_rules_dict = server_config.get_config(["proxy", "server", "rules"], {})  # 代理服务器规则

# 默认不代理本地地址
localhost_addr = ['127\\.0\\.0\\.1', 'localhost']
new_proxy_server_rules_dict = {}
for addr in localhost_addr:
    new_proxy_server_rules_dict[addr] = "none"
new_proxy_server_rules_dict.update(proxy_server_rules_dict)
proxy_server_rules_dict = new_proxy_server_rules_dict


def get_proxy_server_url(url: str, enable_proxy: bool = False) -> str | None:
    """
    获取代理服务器 URL
    :param url: 待访问的 URL
    :param enable_proxy: 请求参数中是否要求使用代理
    :return: None: 不开启代理; str: 命中的第一个规则对应的服务器 URL，如果没有匹配到则返回默认服务器 URL
    """
    # 判断总开关是否打开
    if config_enable_proxy is not True:
        return None

    # 在没有开启规则匹配的情况下，也没有要求用代理请求
    if force_enable_rules is not True and enable_proxy is not True:
        return None

    # 根据正则表达式寻找对应的代理服务器 URL
    for regex, value in proxy_server_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            result = value

            # 检查是否等于 "default"，如果是就替换为默认代理服务器
            if value == "default":
                result = default_proxy_server_url

            # 检查是否等于 "none"，如果是就直接返回不代理
            if value == "none":
                return None

            # 返回结果
            return result

    # 上面正则表达式没有找到，根据情况判断
    if enable_proxy is True:
        # 如果参数要求开启代理，返回默认服务器
        return default_proxy_server_url
    else:
        # 否则返回 None
        return None


def get_proxies(url: str, enable_proxy: bool = False) -> dict | None:
    """
    获取代理服务器 URL dict
    :param url: 待访问的 URL
    :param enable_proxy: 请求参数中是否要求使用代理
    :return: None: 不开启代理; dict: 用于请求 proxies 的配置 dict
    """
    proxies = None
    proxy_server_url = get_proxy_server_url(url, enable_proxy)
    if proxy_server_url is not None:
        proxies = {
            'http': proxy_server_url,
            'https': proxy_server_url
        }
    return proxies
