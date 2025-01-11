#! /bin/bash

# ######################################################
#
#    项目运行状态监控 & 自动重启脚本
#    启动 m3u8ProxyServer.py
#
# ######################################################

# 添加系统级定时任务
#
# crontab -e
# ------------------------------------------------------
# 0,5,10,15,20,25,30,35,40,45,50,55 * * * * /path/to/m3u8-proxy-server/monitor/monitor.sh >/dev/null 2>&1
# ------------------------------------------------------

# 项目部署的路径
project_path=/path/to/m3u8-proxy-server

# 进程检测关键字
process_check_key=m3u8ProxyServer

# PID 全局变量
timer_pid=""

# 获取 PID 函数
get_pid(){
  timer_pid=`ps -ef | grep "${process_check_key}" | grep -v "grep" | awk '{print $2}'`
}

# 检测函数
check_timer(){
  get_pid
  if [ `echo ${timer_pid} | wc -w` -eq 0 ];then
    # /usr/bin/python3 -u  ${project_path}/m3u8ProxyServer.py >> /dev/null 2>&1 &
    # /usr/bin/python3 -u  ${project_path}/m3u8ProxyServer.py >> ${project_path}/run.log 2>&1 &
    cd ${project_path}
    gunicorn --timeout 600 -w 4 -c gunicorn_config.py m3u8ProxyServer:app
    get_pid
    echo "[`date +'%Y-%m-%d %H:%M:%S'`] 进程已停止，重启 ${process_check_key} [`echo ${timer_pid}`]" >> ${project_path}/monitor/monitor.log
  fi
}

# 运行检测函数
check_timer
