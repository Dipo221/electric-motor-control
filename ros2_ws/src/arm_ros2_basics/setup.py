from glob import glob

from setuptools import find_packages, setup

package_name = 'arm_ros2_basics'
share = 'share/' + package_name

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (share, ['package.xml']),
        # 第5週：launch、YAML、RViz 要安裝到 share/ 才找得到
        (share + '/launch', glob('launch/*.launch.py')),
        (share + '/config', glob('config/*.yaml')),
        (share + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'hello_node = arm_ros2_basics.hello_node:main',
            'joint_wave = arm_ros2_basics.joint_wave:main',
            'joint_monitor = arm_ros2_basics.joint_monitor:main',
            # 第5週 實作 5：Action Server／Client
            'joint_mover = arm_ros2_basics.joint_mover:main',
            'move_client = arm_ros2_basics.move_client:main',
        ],
    },
)
