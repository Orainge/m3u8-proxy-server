# 代理参数

from server_config import get_config

# 代理服务使用的 URI：代理
URI_NAME_PROXY = get_config(["security", "uri", "proxy"], 'proxy')

# 代理服务使用的 URI：URL
URI_NAME_URL = get_config(["security", "uri", "url"], 'url')

# 代理服务使用的 URI：M3U8 文件
URI_NAME_M3U8 = get_config(["security", "uri", "m3u8"], 'm3u8')

# 代理服务使用的 URI：M3U8 KEY 文件
URI_NAME_KEY = get_config(["security", "uri", "key"], 'key')

# 代理服务使用的 URI：M3U8 文件
URI_NAME_MPD = get_config(["security", "uri", "mpd"], 'mpd')

# 使用代理服务的 URI：视频文件
URI_NAME_VIDEO = get_config(["security", "uri", "video"], 'video')

# 使用代理服务的 URI：流式传输
URI_NAME_STREAM = get_config(["security", "uri", "stream"], 'stream')
