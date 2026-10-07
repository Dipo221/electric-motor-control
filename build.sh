#!/usr/bin/env bash
# ==================================================
#  第三週：建置映像檔 motor-control:week03
#  用法：bash build.sh 2>&1 | tee build.log
#  （不要加 sudo）
# ==================================================
set -euo pipefail
lab_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
IMAGE=motor-control:week03

# ① 不可用 sudo / root：UID 會變成 0
if [ "$(id -u)" = 0 ]; then
    echo '請用一般使用者執行：bash build.sh' >&2
    exit 1
fi

# ② ROS 套件庫設定檔的版本，依序取自：
#    環境變數 → ros-apt-source.version → GitHub 最新版
ver_file="$lab_dir/ros-apt-source.version"
V="${ROS_APT_SOURCE_VERSION:-}"
if [ -z "$V" ] && [ -s "$ver_file" ]; then
    V="$(tr -d '[:space:]' < "$ver_file")"
fi
if [ -z "$V" ]; then
    repo=ros-infrastructure/ros-apt-source
    api="https://api.github.com/repos/$repo"
    api="$api/releases/latest"
    py='import json,sys'
    py="$py; print(json.load(sys.stdin)['tag_name'])"
    V="$(curl -fsSL --retry 3 "$api" | python3 -c "$py")"
fi
if [[ ! "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ROS_APT_SOURCE_VERSION 格式錯誤：$V" >&2
    exit 1
fi
printf '%s\n' "$V" > "$ver_file"

# ③ 建置：傳入主機的 UID/GID 與 ROS 版本
docker build --progress=plain \
    --build-arg USER_UID="$(id -u)" \
    --build-arg USER_GID="$(id -g)" \
    --build-arg ROS_APT_SOURCE_VERSION="$V" \
    -t "$IMAGE" -f "$lab_dir/Dockerfile" "$lab_dir"

echo "[build.sh] 完成：$IMAGE（ROS 來源 $V）"
