"""
gunicorn 配置
"""
import logging

import server_config

# 默认监听端口
bind = f'{server_config.HOST}:{server_config.PORT}'

daemon = True
pidfile = 'log/gunicorn.pid'  # PID 文件
#accesslog = 'log/access.log'  # 访问日志
errorlog = 'log/gunicorn.log'  # gunicorn 日志

logger = logging.getLogger(__name__)


def on_exit(server):
    """gunicorn 退出函数"""
    logger.debug('[系统退出前回调函数] - 执行开始')

    logger.info('[系统退出前回调函数] - 执行结束')
