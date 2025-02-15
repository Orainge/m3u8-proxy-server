# Route: 代理

from flask import Blueprint

from route.consts.uri_param_name import URI_NAME_PROXY
from .url import proxy_url_bp
from .key import proxy_key_bp
from .m3u8 import proxy_m3u8_bp
from .video import proxy_video_bp
from .stream import proxy_stream_bp
from .mpd import proxy_mpd_bp

# 创建蓝图，以 PROXY_ROUTE_NAME 为前缀
proxy_bp = Blueprint("proxy", __name__, url_prefix=f'/{URI_NAME_PROXY}')

# 注册蓝图
proxy_bp.register_blueprint(proxy_url_bp)
proxy_bp.register_blueprint(proxy_key_bp)
proxy_bp.register_blueprint(proxy_m3u8_bp)
proxy_bp.register_blueprint(proxy_video_bp)
proxy_bp.register_blueprint(proxy_stream_bp)
proxy_bp.register_blueprint(proxy_mpd_bp)
