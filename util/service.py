# 服务工具类

import re

import server_config

# 是否启用 MPD 代理服务
enable_proxy_mpd = server_config.get_config(["service", "proxy", "mpd", "enable"], True)

# 是否开启对直链 URL 的代理服务
default_proxy_mpd_direct_url = server_config.get_config(["service", "proxy", "mpd", "directUrl", "enable"], False)
proxy_mpd_direct_url_rules_dict = server_config.get_config(["service", "proxy", "mpd", "directUrl", "rules"], {})

# 是否启用 m3u8 文件中多轨道 URL 的代理服务
enable_proxy_m3u8 = server_config.get_config(["service", "proxy", "m3u8", "enable"], True)

# 是否开启对直链 URL 的代理服务
default_proxy_m3u8_direct_url = server_config.get_config(["service", "proxy", "m3u8", "directUrl", "enable"], False)
proxy_m3u8_direct_url_rules_dict = server_config.get_config(["service", "proxy", "m3u8", "directUrl", "rules"], {})

# 是否启用视频流代理服务
enable_proxy_video = server_config.get_config(["service", "proxy", "video", "enable"], True)

# 是否开启对直链 URL 的代理服务
default_proxy_video_direct_url = server_config.get_config(["service", "proxy", "video", "directUrl", "enable"], False)
proxy_video_direct_url_rules_dict = server_config.get_config(["service", "proxy", "video", "directUrl", "rules"], {})


def get_enable_proxy_mpd_direct_url(url: str) -> int:
    """
    检查待访问的 ** MPD URL ** 是否强制代理
    :param url: 待访问的 ** MPD URL **
    :return: M3U8 最深层级
    """
    # 根据正则表达式寻找 M3U8 最深层级
    for regex, value in proxy_mpd_direct_url_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            return value

    # 返回默认值
    return default_proxy_mpd_direct_url


def get_enable_proxy_m3u8_direct_url(url: str) -> int:
    """
    检查待访问的 ** M3U8 URL ** 是否强制代理
    :param url: 待访问的 ** M3U8 URL **
    :return: M3U8 最深层级
    """
    # 根据正则表达式寻找 M3U8 最深层级
    for regex, value in proxy_m3u8_direct_url_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            return value

    # 返回默认值
    return default_proxy_video_direct_url


def get_enable_proxy_video_direct_url(url: str) -> int:
    """
    检查待访问的 ** Video URL ** 是否强制代理
    :param url: 待访问的 ** Video URL **
    :return: M3U8 最深层级
    """
    # 根据正则表达式寻找 M3U8 最深层级
    for regex, value in proxy_video_direct_url_rules_dict.items():
        if re.search(regex, url):
            # 找到匹配规则
            return value

    # 返回默认值
    return default_proxy_video_direct_url
