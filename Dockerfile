# ==================================================
#  電動機控制理論與實作｜第三週
#  ROS 2 Humble + MoveIt 2 + CUDA 12.1 + cuDNN 8
#  建置：bash build.sh    啟動：bash run.sh
# ==================================================

# ① 基底：CUDA 12.1.1（nvcc）+ cuDNN 8 + Ubuntu 22.04
#    驅動在主機，映像裡不裝驅動
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# ② 建置參數：由 build.sh 傳入
ARG USER_UID=1000
ARG USER_GID=1000
ARG ROS_APT_SOURCE_VERSION
ARG DEBIAN_FRONTEND=noninteractive

# ③ NVIDIA：開放全部 GPU 功能；指定 CUDA 位置
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV CUDA_HOME=/usr/local/cuda

# ④ apt 來源：Ubuntu 套件走淡江鏡像站
ARG MIRROR=http://ftp.tku.edu.tw/ubuntu/
ARG PARTS="main restricted universe multiverse"
RUN printf "deb ${MIRROR} %s ${PARTS}\n" \
        jammy jammy-updates jammy-security \
        > /etc/apt/sources.list

# ⑤ 時區：Asia/Taipei
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone

# ⑥ 基本工具：sudo、git、nano、python3、pip ...
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        sudo git nano \
        python3 python3-pip python3-venv \
        build-essential curl ca-certificates \
        locales tzdata bash-completion \
        mesa-utils libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/*

# ⑦ 語系：ROS 2 需要 UTF-8
RUN locale-gen en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ⑧ ROS 2 Humble：官方 ros2-apt-source 設定套件庫
ENV ROS_DISTRO=humble
ARG ROS_APT_REPO=ros-infrastructure/ros-apt-source
RUN V="${ROS_APT_SOURCE_VERSION:?請用 build.sh 建置}" \
    && GH=https://github.com/${ROS_APT_REPO} \
    && DEB=ros2-apt-source_${V}.jammy_all.deb \
    && curl -fsSL --retry 3 -o /tmp/${DEB} \
        ${GH}/releases/download/${V}/${DEB} \
    && dpkg -i /tmp/${DEB} && rm /tmp/${DEB} \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-humble-desktop ros-dev-tools \
    && rosdep init \
    && rm -rf /var/lib/apt/lists/*

# ⑨ MoveIt 2 + ros2_control + Panda 範例手臂
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-humble-moveit \
        ros-humble-moveit-resources-panda-moveit-config \
        ros-humble-ros2-control \
        ros-humble-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# ⑩ 建立 student（UID/GID 與主機相同），sudo 免密碼
RUN (getent group ${USER_GID} \
        || groupadd --gid ${USER_GID} student) \
    && useradd --uid ${USER_UID} --gid ${USER_GID} \
        -m -s /bin/bash student \
    && echo "student ALL=(ALL) NOPASSWD:ALL" \
        > /etc/sudoers.d/student \
    && chmod 0440 /etc/sudoers.d/student

# ⑪ 啟動腳本、驗收腳本與使用者環境
COPY ros_env.sh /etc/ros_env.sh
COPY entrypoint.sh /entrypoint.sh
COPY check.sh /usr/local/bin/week03-check
RUN chmod 0755 /entrypoint.sh /usr/local/bin/week03-check
USER student
RUN rosdep update \
    && mkdir -p ~/ros2_ws/src \
    && echo 'source /etc/ros_env.sh' >> ~/.bashrc
WORKDIR /home/student/ros2_ws
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
