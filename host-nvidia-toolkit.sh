#!/usr/bin/env bash
# ==================================================
#  第三週：在「主機」安裝 NVIDIA Container Toolkit
#  每台電腦只要一次；不可寫進 Dockerfile
#  前提：NVIDIA 驅動已安裝，nvidia-smi 正常
# ==================================================
set -euo pipefail
URL=https://nvidia.github.io/libnvidia-container
SRC=$URL/stable/deb/nvidia-container-toolkit.list
KEY=/usr/share/keyrings/nvidia-container-toolkit.gpg
LIST=/etc/apt/sources.list.d/nvidia-container-toolkit.list
BASE=nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# ① 先確認主機驅動正常（失敗就停止）
nvidia-smi

# ② 加入 NVIDIA 套件庫與簽章金鑰
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL "$URL/gpgkey" \
    | sudo gpg --dearmor --yes -o "$KEY"
curl -fsSL "$SRC" \
    | sed "s#^deb #deb [signed-by=$KEY] #" \
    | sudo tee "$LIST" > /dev/null

# ③ 安裝 Toolkit，設定 Docker 的 nvidia runtime
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
echo '重新啟動 Docker（執行中的容器會被中斷）'
sudo systemctl restart docker

# ④ 測試：ubuntu 映像裡沒有驅動，也能執行 nvidia-smi
docker run --rm --gpus all ubuntu:22.04 nvidia-smi

echo '完成。建議接著下載基底映像（約 4.9 GB）：'
echo "  docker pull $BASE"
