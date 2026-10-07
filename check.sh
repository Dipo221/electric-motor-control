#!/usr/bin/env bash
# =================================================================
#  第三週驗收：在容器內執行 week03-check（映像檔已內建）
#  只檢查安裝與設定；GPU 計算、ROS 通訊與 GUI 請依講義另外測試
# =================================================================
source /etc/ros_env.sh
fail=0
check() {
    local name="$1"; shift
    if "$@" > /dev/null 2>&1; then
        echo "  [OK]   $name"
    else
        echo "  [FAIL] $name"; fail=1
    fi
}

echo "== 系統 =="
check "Ubuntu 22.04"             grep -q 'VERSION_ID="22.04"' /etc/os-release
check "時區 Asia/Taipei"         test "$(cat /etc/timezone)" = Asia/Taipei
check "apt 來源 ftp.tku.edu.tw"  grep -q ftp.tku.edu.tw /etc/apt/sources.list
check "sudo 免密碼"              sudo -n true
echo "== 工具 =="
check "python3 / pip"            python3 -m pip --version
check "git / nano"               bash -c 'git --version && nano --version'
echo "== CUDA / cuDNN =="
check "nvcc（CUDA 12.1）"        bash -c 'nvcc --version | grep -q "release 12.1"'
check "libcudnn8 / libcudnn8-dev" dpkg-query -W libcudnn8 libcudnn8-dev
check "載入 libcudnn.so.8"       python3 -c 'import ctypes; ctypes.CDLL("libcudnn.so.8")'
echo "== ROS 2 / MoveIt =="
for p in rclpy turtlesim rviz2 moveit_ros_move_group moveit_setup_assistant \
         moveit_resources_panda_moveit_config controller_manager; do
    check "$p" ros2 pkg prefix "$p"
done

echo "== 資訊 =="
echo "  使用者：$(id -un)（UID $(id -u)）  時間：$(date '+%F %T %Z')"
echo "  $(nvcc --version | grep release)"
python3 - <<'PY'
import ctypes
lib = ctypes.CDLL('libcudnn.so.8')
lib.cudnnGetVersion.restype = ctypes.c_size_t
print('  cuDNN 版本：', lib.cudnnGetVersion())
PY
if nvidia-smi -L > /dev/null 2>&1; then
    nvidia-smi -L | sed 's/^/  /'
else
    echo "  （CPU 模式：容器內看不到 GPU，屬正常）"
fi
echo "  ROS_DISTRO=$ROS_DISTRO  ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}  ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-0}"

echo
if [ "$fail" = 0 ]; then
    echo "全部通過。GPU 計算、ROS 通訊與 GUI 請依講義另外測試。"
else
    echo "有項目失敗，請對照簡報「常見錯誤與排查」。"
fi
exit "$fail"
