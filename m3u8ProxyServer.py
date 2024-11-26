# 主函数

import logging
from flask import Flask

import gunicorn_config
import server_config
from route import bp
from route.handler import error as error_handler

# 配置日志输出格式和日志级别
logging.basicConfig(
    level=server_config.LOGGING_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 时间格式
)
logging.getLogger('charset_normalizer').setLevel(logging.CRITICAL)


class LocalFlask(Flask):
    def process_response(self, response):
        super().process_response(response)
        # 可以自定义处理请求头
        return response


def create_app():
    new_app = LocalFlask(__name__)

    # 注册蓝图
    bp.register(new_app)

    # 注册错误处理函数
    error_handler.register(new_app)

    # 其它初始化操作
    return new_app


app = create_app()


def exit_hook(signalNumber=None, frame=None):
    gunicorn_config.on_exit(None)


if __name__ == '__main__':
    # 添加线程池退出函数
    # 注册 atexit 钩子以确保程序正常退出时执行清理操作
    # atexit.register(exit_hook)
    # signal.signal(signal.SIGINT, exit_hook)
    # signal.signal(signal.SIGTERM, exit_hook)
    try:
        app.run(server_config.HOST, server_config.PORT)
    finally:
        exit_hook()
