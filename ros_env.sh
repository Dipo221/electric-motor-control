# 載入 ROS 2 與已編譯的工作區
# （entrypoint.sh 與 ~/.bashrc 共用）
source "/opt/ros/${ROS_DISTRO:-humble}/setup.bash"
if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
    source "$HOME/ros2_ws/install/setup.bash"
fi
