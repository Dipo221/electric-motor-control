# 第五週 實作 2：一次啟動 Panda 顯示＋自己的節點
# 用法：ros2 launch arm_ros2_basics arm.launch.py
#   wave:=false  不啟動 joint_wave（bag 重播、實作 5 Action 用）
#   rviz:=false  不開 RViz（沒有畫面時）
#   use_sim_time:=true  跟著 ros2 bag play --clock 的時間走
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

PKG = 'arm_ros2_basics'


def load_panda_urdf():
    # Panda 的 URDF：MoveIt 範例套件內附（與第四週相同）
    share = get_package_share_directory(
        'moveit_resources_panda_description')
    urdf = Path(share, 'urdf', 'panda.urdf')
    if urdf.is_file():
        return urdf.read_text()
    import xacro                        # 備援：由 xacro 產生
    cfg = get_package_share_directory(
        'moveit_resources_panda_moveit_config')
    xa = Path(cfg, 'config', 'panda.urdf.xacro')
    return xacro.process_file(str(xa)).toxml()


def generate_launch_description():
    # ① 啟動參數：指令列用「名稱:=值」覆寫
    args = [
        DeclareLaunchArgument('wave', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('use_sim_time',   # bag 重播用
                              default_value='false'),
    ]
    wave_on = IfCondition(LaunchConfiguration('wave'))
    rviz_on = IfCondition(LaunchConfiguration('rviz'))
    sim = {'use_sim_time': LaunchConfiguration('use_sim_time')}
    share = Path(get_package_share_directory(PKG))
    rviz_cfg = str(share / 'rviz' / 'panda.rviz')
    wave_yaml = str(share / 'config' / 'wave.yaml')
    urdf = load_panda_urdf()
    return LaunchDescription(args + [
        # ② rsp：URDF → /tf　③ RViz2：設定檔隨套件安裝
        Node(package='robot_state_publisher',
             executable='robot_state_publisher',
             parameters=[{'robot_description': urdf}, sim]),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', rviz_cfg], condition=rviz_on,
             parameters=[sim]),
        # ④ 自己的節點：joint_wave 的參數來自 YAML
        Node(package=PKG, executable='joint_wave',
             parameters=[wave_yaml], condition=wave_on,
             output='screen'),
        Node(package=PKG, executable='joint_monitor',
             parameters=[sim], output='screen'),
    ])
