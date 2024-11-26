# 服务器配置
import copy
import logging
from typing import List, Any

import util

# 修改 logging 级别
LOGGING_LEVEL = logging.INFO

# 读取 json 配置文件
config_dict = util.get_dict_from_json_file("config", "m3u8-proxy-server.json")

# 服务监听 IP 地址和端口
HOST = config_dict["server"]["host"]
PORT = config_dict["server"]["port"]

# 初始化 API Token
security = config_dict["security"] if "security" in config_dict else None
api = security["api"] if security is not None and "api" in security else None
api_token = api["token"] if api is not None and "token" in api else None


def get_config(keys: List[str], default_value: Any = None) -> Any:
    """
    获取配置项
    :param keys: 配置 json key 数组
    :param default_value: 如果没有对应的值，返回的默认值
    :return:
    """
    item = config_dict
    for key in keys:
        if key in item:
            # 存在该项，赋值
            item = item[key]
        else:
            # 不存在该项，返回默认值
            return default_value

    if isinstance(item, dict) is True or isinstance(item, list) is True:
        # 如果是 dict 或 list，返回深拷贝的对象，避免对配置文件的修改
        return copy.deepcopy(item)
    else:
        # 否则直接返回
        return item


# ========================== 个性化配置获取 ==========================
# 请求 M3U8 文件时，最大的 URL 重定向次数
M3U8_FILE_MAX_REDIRECT_TIMES = get_config(["request", "m3u8File", "maxRedirectTimes"], 5)

# 请求 M3U8 文件时，M3U8 最深层级
M3U8_FILE_MAX_DEEP = get_config(["request", "m3u8File", "maxDeep"], 5)
