# 第三週實作：ROS 2 Humble + MoveIt 2 + CUDA/cuDNN 開發容器（v3）

適用：原生 Ubuntu 22.04 x86_64、Docker Engine、Bash。GUI 建議使用「Ubuntu on Xorg」登入。
VirtualBox 或沒有 NVIDIA 顯卡的電腦會自動走 CPU 模式（軟體繪圖，可用但較慢）。
本資料夾的腳本不適用於 Windows PowerShell、WSLg 或 Jetson。

## 檔案

| 檔案 | 用途 | 在哪裡執行 |
|---|---|---|
| `Dockerfile` | 映像檔建置說明書（11 個區塊） | 由 build.sh 使用 |
| `build.sh` | 建置 `motor-control:week03` | 主機 |
| `run.sh` | 啟動容器 `motor-week03`（自動偵測 GPU / 螢幕） | 主機 |
| `entrypoint.sh` | 容器啟動時先載入 ROS 2，再執行指令 | 容器（自動） |
| `ros_env.sh` | 載入 ROS 2 與已編譯的工作區（entrypoint 與 `~/.bashrc` 共用） | 容器（自動） |
| `check.sh` | 驗收腳本，映像內指令為 `week03-check` | 容器 |
| `host-nvidia-toolkit.sh` | 安裝 NVIDIA Container Toolkit | 主機（一次） |
| `ros-apt-source.version` | 固定 ROS 套件庫設定檔版本（目前 1.2.0） | 由 build.sh 讀取 |
| `ros2_ws/src/` | 工作區，掛載到容器 `/home/student/ros2_ws` | run.sh 自動建立 |

## 課前（每台電腦一次）

1. `docker run --rm hello-world` 可以不加 sudo 執行（第一週「設定 Docker 權限」）。
2. 主機需有 curl、python3、xauth。
3. NVIDIA 顯卡：主機先裝好驅動並重開機，確認 `nvidia-smi` 正常，再執行
   `bash host-nvidia-toolkit.sh`（會設定 Docker runtime 並重新啟動 Docker）。
4. 預先下載基底映像（壓縮後約 4.9 GB）：
   `docker pull nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04`

主機驅動與 Toolkit 只能裝在主機，不可寫進 Dockerfile。

## 建置

```bash
cd ~/week03_lab
bash build.sh 2>&1 | tee build.log     # 不要加 sudo
docker image ls motor-control:week03
```

- build.sh 會拒絕以 root 執行，並把主機的 UID/GID 傳入，容器使用者 `student` 的 UID 與主機相同。
- ROS 套件庫改用官方 `ros2-apt-source` 套件。版本依序取自：環境變數 `ROS_APT_SOURCE_VERSION` →
  `ros-apt-source.version` → GitHub 最新版。全班共用同一個版本檔，避免 GitHub API 次數限制。
- Ubuntu 的 jammy、jammy-updates、jammy-security 全部走 `http://ftp.tku.edu.tw/ubuntu/`（Dockerfile 的 `ARG MIRROR`）；
  ROS 與 NVIDIA CUDA 套件仍用官方站。校外連不到 TKU 時，把 `ARG MIRROR` 改成 `http://tw.archive.ubuntu.com/ubuntu/`。
- `NVIDIA_DRIVER_CAPABILITIES=all`：基底映像預設只開 compute,utility，改成 all 才包含 OpenGL 繪圖（RViz）。

## 執行

```bash
bash run.sh                    # 自動：有 NVIDIA 且 Toolkit 已設定 → GPU；有 DISPLAY → 開 GUI
GPU=0 bash run.sh              # 強制 CPU 模式（GPU=1 強制 GPU）
GUI=0 bash run.sh              # 只用終端機
bash run.sh ros2 pkg list      # 執行一個指令後離開
docker exec -it motor-week03 bash   # 第二個終端
```

- ROS 2 預設 `ROS_LOCALHOST_ONLY=1`、`ROS_DOMAIN_ID=30`：只在本機通訊，教室裡互不干擾。
  之後要跨機器（例如接實體手臂）：`ROS_LOCALHOST_ONLY=0 ROS_DOMAIN_ID=<座號> bash run.sh`。
- GUI 只把本機 X11 的授權 cookie 交給容器（唯讀掛載），不使用 `xhost +` 開放整台機器。
- CPU 模式會設定 `LIBGL_ALWAYS_SOFTWARE=1` 與 `NVIDIA_VISIBLE_DEVICES=void`。
- `docker exec` 不會重新執行 entrypoint；互動 bash 由 `~/.bashrc` 執行 `source /etc/ros_env.sh` 載入 ROS 2。
- run.sh 分成 ①～⑨ 九段（偵測 GPU 的 `has_gpu`、準備 X11 授權的 `setup_x11` 兩個函式），每段都不超過 10 行，方便對照講義。

## 驗收

```bash
week03-check                                   # 容器內：系統、工具、CUDA/cuDNN、ROS 2/MoveIt
ros2 run demo_nodes_cpp talker                 # 終端 A
ros2 run demo_nodes_py listener                # 終端 B：持續收到訊息才算通過
ros2 run turtlesim turtlesim_node              # GUI
ros2 run turtlesim turtle_teleop_key
ros2 launch moveit_resources_panda_moveit_config demo.launch.py   # MoveIt Panda Demo
nvidia-smi && glxinfo -B | grep renderer       # GPU 模式；CPU 模式為 llvmpipe
```

掛載測試：容器內 `echo week03 > ~/ros2_ws/proof.txt`，主機 `ls -l ~/week03_lab/ros2_ws/proof.txt`，
擁有者應是主機帳號而不是 root。程式放在 ros2_ws 才會保留；容器內臨時 apt install 的東西離開後就消失。

## 內容範圍

- 保留：CUDA 12.1.1（nvcc）、cuDNN 8.9、Python3、pip、venv、git、nano、sudo、build-essential、
  ROS 2 Humble Desktop、ros-dev-tools（colcon、rosdep）、MoveIt 2、ros2_control、Panda 範例。
- 移除原實驗室 Dockerfile 的 PyTorch、PyTorch3D、Kaolin、nvdiffrast、RealSense、Azure Kinect、
  UR driver 原始碼建置與自訂 config，待對應週次再加。
- 主機驅動需支援 CUDA 12.1 以上（例如 535 版）；較新的 GPU 架構需改用支援該硬體的 CUDA 映像。
- sudo 免密碼只用於隔離的教學開發環境。

## 授課者備援

- 課前在教室網路與目標硬體完整建置一次，並驗收 GUI / GPU。
- 備援：`docker save -o motor-week03.tar motor-control:week03`，學生 `docker load -i motor-week03.tar`。
  映像內 student 的 UID/GID 需與學生主機相同（多數為 1000），不同時請各自重建。
- 本資料夾的腳本已做語法與邏輯測試，但製作環境無法連線 Docker Hub，尚未實際 build 與 GPU 執行。

## 官方參考

- https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- https://github.com/ros-infrastructure/ros-apt-source
- https://moveit.ai/install-moveit2/binary/
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
- https://hub.docker.com/r/nvidia/cuda
- https://docs.docker.com/reference/dockerfile/
