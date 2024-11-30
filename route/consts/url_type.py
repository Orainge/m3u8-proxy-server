# URL 类型

URL_TYPE_M3U8 = 'm3u8'  # M3U8 文件
URL_TYPE_VIDEO = 'video'  # 视频文件

# 允许的 M3U8 文件 Content-Type 类型
accept_content_type_regex_list_m3u8 = ['application/vnd.apple.mpegurl', 'application/x-mpegURL', 'audio/mpegurl']

# 允许的视频 Content-Type 类型
accept_content_type_regex_list_video = ['^video\\/.*$']
