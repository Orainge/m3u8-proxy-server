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


def get_filter_max_bandwidth_stream_m3u8_content(m3u8_content: str) -> str:
    """
    获取一个 M3U8 文件内容，它只保留最高画质的视频流
    :param m3u8_content: m3u8 文件内容
    :return 过滤后的 m3u8 文件内容
    """
    # 按行分割文件内容
    lines = m3u8_content.split("\n")

    others = []
    stream_dict = {}
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXT-X-STREAM-INF"):
            # 提取 BANDWIDTH 的值
            bandwidth_part = [part for part in line.split(',') if "BANDWIDTH=" in part]
            if bandwidth_part:
                try:
                    bandwidth = int(bandwidth_part[0].split('=')[1])
                    uri_line = lines[i + 1].strip() if (i + 1) < len(lines) else ""
                    stream_dict[bandwidth] = [line, uri_line]
                    i += 2  # 跳过 URI 行
                    continue
                except ValueError:
                    pass  # 如果格式不对就跳过
        else:
            others.append(line)
            i += 1

    # 如果没找到任何 bandwidth 信息，直接原样输出
    if not stream_dict:
        return m3u8_content

    # 找出最大 bandwidth 的那一组
    max_bw = max(stream_dict.keys())
    max_stream_lines = stream_dict[max_bw]

    # 合并输出为字符串
    final_lines = others + max_stream_lines
    return '\n'.join([line.strip() for line in final_lines if line.strip()]) + '\n'
