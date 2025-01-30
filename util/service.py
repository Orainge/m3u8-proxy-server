# 服务工具类

import re

import server_config

# 是否启用视频流代理服务
enable_proxy_video = server_config.get_config(["service", "proxy", "video", "enable"], True)

# 是否强制代理 M3U8 里的绝对 URL
default_proxy_video_direct_url = server_config.get_config(["service", "proxy", "video", "directUrl", "enable"], False)
proxy_video_direct_url_rules_dict = server_config.get_config(["service", "proxy", "video", "directUrl", "rules"], {})

# 是否启用 MPD 代理服务
enable_proxy_mpd = server_config.get_config(["service", "proxy", "mpd", "enable"], True)

# 是否强制代理 MPD 的绝对 URL
default_proxy_mpd_direct_url = server_config.get_config(["service", "proxy", "mpd", "directUrl", "enable"], False)
proxy_mpd_direct_url_rules_dict = server_config.get_config(["service", "proxy", "mpd", "directUrl", "rules"], {})


def get_proxy_video_direct_url(url: str) -> int:
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


def get_proxy_mpd_direct_url(url: str) -> int:
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
