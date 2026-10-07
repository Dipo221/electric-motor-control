#!/usr/bin/env bash
# 容器啟動時：先載入 ROS 2，再執行指定的指令
set -e
source /etc/ros_env.sh
exec "$@"
