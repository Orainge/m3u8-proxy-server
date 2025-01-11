# M3U8 工具类

import re

import server_config

# 请求 M3U8 文件时，M3U8 最深层级
default_max_deep = server_config.get_config(["request", "m3u8", "maxDeep", "default"], 5)
max_deep_rules_dict = server_config.get_config(["request", "m3u8", "maxDeep", "rules"], {})


def get_max_deep(url: str) -> int:
    """
    获取请求 M3U8 文件时，M3U8 最深层级
    :param url: 待访问的 URL
    :return: M3U8 最深层级
    """
    # 根据正则表达式寻找 M3U8 最深层级
    for regex, value in max_deep_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            return value

    # 返回默认值
    return default_max_deep
