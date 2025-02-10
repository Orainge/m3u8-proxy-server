# URL 类型

URL_TYPE_M3U8 = 'm3u8'  # M3U8 文件
URL_TYPE_MPD = 'mpd'  # mpd 文件
URL_TYPE_VIDEO = 'video'  # 视频文件
URL_TYPE_STREAM = 'stream'  # 流式传输

# 允许的 M3U8 文件 Content-Type 类型
# 'application/vnd.apple.mpegurl', 'application/x-mpegURL', 'audio/mpegurl', 'audio/x-mpegurl',
accept_content_type_regex_list_m3u8 = [
    '^(audio|application)\\/(vnd\\.apple\\.|x-)*(m|M)(p|P)(e|E)(g|G)(u|U)(r|R)(l|L)$']

# 允许的 MPD 文件 Content-Type 类型
accept_content_type_regex_list_mpd = ['application/dash']

# 允许的视频 Content-Type 类型
accept_content_type_regex_list_video = ['^video\\/.*$']

# 允许的流式传输 Content-Type 类型
accept_content_type_regex_list_stream = ['application\\/octet-stream']
