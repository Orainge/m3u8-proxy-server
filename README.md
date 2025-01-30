# M3U8 代理服务

该项目可代理多种流媒体格式，包括：

- M3U8 文件（支持多级 M3U8 文件，但不支持多轨道 M3U8 文件）
- 流式传输的视频（video/x-flv）
- MPD 文件 (application/dash)

使用场景：

- 某些客户端没有 IPV6 地址，可以将本项目部署到有 IPV6 地址的主机进行反代。

- 某些需要特定网络环境才能访问的 M3U8 文件，可以统一在一台主机管理。

## 1 接口文档

见文档：`docs/接口文档.md`

## 2 安装依赖

`pip install -r requirements.txt`

## 3 启动命令

1. gunicorn启动

   > 注意：需要设置超时时间，否则在代理流式传输的视频时，会播放一段时间就自动停止。
   >
   > 设置`--timeout 600` 参数表示 10*60 秒内自动关闭连接

   ```sh
   # gunicorn --timeout 600 -w 线程数 -c gunicorn_config.py m3u8ProxyServer:app
   # 例如
   gunicorn --timeout 600 -w 4 -c gunicorn_config.py m3u8ProxyServer:app
   ```

2. 直接启动（单线程）

   ```sh
   # 无输出日志
   # python3 -u m3u8ProxyServer.py >> /dev/null 2>&1 &
   
   # 输出日志
   /usr/bin/python3 -u m3u8ProxyServer.py >> run.log 2>&1 &
   ```

3. 使用 `monitor/monitor.sh` 脚本启动。

   - 该脚本可以用于 crontab 监控运行检查服务运行是否正常。
   - 使用前需要修改脚本里的文件夹路径。

## 4 配置文件说明

见文档：`docs/配置文件说明.md`

注意：MPD代理会使用默认服务器地址，不支持其它自定义地址，务必填写正确。
