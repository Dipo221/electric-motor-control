#!/usr/bin/env bash
# ==================================================
#  第三週：啟動容器 motor-week03
#  bash run.sh               自動偵測 GPU 與螢幕
#  GPU=0 bash run.sh         強制 CPU（GPU=1 強制 GPU）
#  GUI=0 bash run.sh         只用終端機
#  bash run.sh ros2 pkg list 執行指令後離開
#  第二個終端：docker exec -it motor-week03 bash
# ==================================================
set -euo pipefail
lab_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
IMAGE=motor-control:week03
NAME=motor-week03

# ① 工作區先用一般使用者建立（否則 Docker 會用 root）
mkdir -p "$lab_dir/ros2_ws/src"

# ② 同一時間只跑一個容器
running="$(docker ps --format '{{.Names}}')"
if grep -qx "$NAME" <<< "$running"; then
    echo "$NAME 已在執行，請改用：" >&2
    echo "  docker exec -it $NAME bash" >&2
    exit 1
fi

# ③ 基本參數：網路、共用記憶體、ROS 2、工作區
args=(--rm -it --name "$NAME")
args+=(--network host --ipc host)
args+=(-e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-30}")
args+=(-e "ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-1}")
args+=(-v "$lab_dir/ros2_ws:/home/student/ros2_ws")

# ④ 偵測 GPU：驅動正常，且 Docker 有 nvidia runtime
has_gpu() {
    nvidia-smi > /dev/null 2>&1 || return 1
    local fmt='{{json .Runtimes}}' rt
    rt="$(docker info -f "$fmt" 2> /dev/null || true)"
    [[ "$rt" == *nvidia* ]] && return 0
    echo '[run.sh] Docker 尚未設定 GPU' >&2
    return 1
}

# ⑤ 決定模式：auto 自動偵測；也可手動設 1 或 0
GPU="${GPU:-auto}"
GUI="${GUI:-auto}"
if [ "$GPU" = auto ]; then
    if has_gpu; then GPU=1; else GPU=0; fi
fi
if [ "$GUI" = auto ]; then
    if [ -n "${DISPLAY:-}" ]; then GUI=1; else GUI=0; fi
fi

# ⑥ GPU 模式交出顯卡；CPU 模式改用軟體繪圖
if [ "$GPU" = 1 ]; then
    args+=(--gpus all)
    echo '[run.sh] GPU 模式（--gpus all）'
else
    args+=(-e LIBGL_ALWAYS_SOFTWARE=1)
    args+=(-e NVIDIA_VISIBLE_DEVICES=void)
    echo '[run.sh] CPU 模式（軟體繪圖）'
fi

# ⑦ X11 授權：只交出本機螢幕的 cookie（唯讀）
setup_x11() {
    auth="$(mktemp)"
    trap 'rm -f -- "$auth"' EXIT
    xauth nlist "$DISPLAY" | sed 's/^..../ffff/' \
        | xauth -f "$auth" nmerge - || true
    [ -s "$auth" ] && return 0
    echo '取不到 X11 授權（需 xauth），或改 GUI=0' >&2
    exit 1
}

# ⑧ GUI 模式：掛載螢幕 socket 與授權 cookie
if [ "$GUI" = 1 ]; then
    setup_x11
    args+=(-e "DISPLAY=$DISPLAY" -e QT_X11_NO_MITSHM=1)
    args+=(-e XAUTHORITY=/tmp/course.xauth)
    args+=(-v /tmp/.X11-unix:/tmp/.X11-unix:ro)
    args+=(-v "$auth:/tmp/course.xauth:ro")
fi

# ⑨ 啟動：後面接的參數會成為容器要執行的指令
docker run "${args[@]}" "$IMAGE" "$@"
