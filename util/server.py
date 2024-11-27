# 服务器工具类

import server_config
from exception import ServerNameError

# 外部服务器访问 URL
server_url_dict = server_config.get_config(["server", "url"], {})

# 默认外部服务器访问 URL
default_server_url = server_url_dict["default"] if "default" in server_url_dict \
    else f"http://{server_config.HOST}:{server_config.PORT}"

# 其它外部服务器访问 URL
others_server_url_dict = server_url_dict["others"] if "others" in server_url_dict else {}


def get_server_url(server_name: str = None) -> str:
    """
    获取外部服务器访问 URL
    :param server_name: 服务器名称
    :return: 服务器名称对应的 URL，如果不存在则抛出异常
    """

    if server_name is None:
        # 返回默认 URL
        return default_server_url

    if server_name == "default":
        # 返回默认 URL
        return default_server_url

    if server_name in others_server_url_dict:
        # 如果存在对应的服务名，就返回对应的 URL
        return others_server_url_dict[server_name]
    else:
        # 否则抛出异常
        raise ServerNameError()
