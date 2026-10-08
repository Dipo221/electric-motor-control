# 第四週 實作 5：Subscriber —— 監看 /joint_states
# ① 任何關節距離極限 10° 以內就發出警告
# ② 每秒顯示 joint1 的角度、角速度與換算的馬達轉速
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# ---- 第 54 頁：常數 ----
# Panda 關節極限（rad），數值取自 Panda 的 URDF
LIMITS = {
    'panda_joint1': (-2.8973, 2.8973),
    'panda_joint2': (-1.7628, 1.7628),
    'panda_joint3': (-2.8973, 2.8973),
    'panda_joint4': (-3.0718, -0.0698),
    'panda_joint5': (-2.8973, 2.8973),
    'panda_joint6': (-0.0175, 3.7525),
    'panda_joint7': (-2.8973, 2.8973),
}
MARGIN = math.radians(10.0)   # 警告範圍：極限內 10°
GEAR = 100.0                  # 假設的減速比 100:1（教學用）


class JointMonitor(Node):
    # ---- 第 53 頁：訂閱與回呼 ----
    def __init__(self):
        super().__init__('joint_monitor')
        self.create_subscription(
            JointState, 'joint_states', self.on_msg, 10)
        self.get_logger().info('訂閱 /joint_states')

    def on_msg(self, msg):                  # 每收到一則就執行
        pos = dict(zip(msg.name, msg.position))
        vel = dict(zip(msg.name, msg.velocity))
        self.check_limits(pos)
        self.show_joint1(pos, vel)

    # ---- 第 55 頁：檢查極限 ----
    def check_limits(self, pos):
        near = []                           # 接近極限的關節
        for name, (low, high) in LIMITS.items():
            q = pos.get(name)
            if q is None:
                continue
            if q < low + MARGIN or q > high - MARGIN:
                near.append(f'{name}={math.degrees(q):.0f}°')
        if near:
            self.get_logger().warn(
                '接近極限：' + '、'.join(near),
                throttle_duration_sec=1.0)

    # ---- 第 56 頁：馬達轉速 ----
    def show_joint1(self, pos, vel):
        if 'panda_joint1' not in pos:
            return
        q = math.degrees(pos['panda_joint1'])
        w = vel.get('panda_joint1', 0.0)         # rad/s
        rpm = w * GEAR * 60.0 / (2.0 * math.pi)  # 馬達端
        self.get_logger().info(
            f'joint1 {q:6.1f}° | {math.degrees(w):6.1f}°/s'
            f' | 馬達 {rpm:6.0f} rpm',
            throttle_duration_sec=1.0)


# ---- 和 hello_node 相同，只把類別換成 JointMonitor ----
def main():
    rclpy.init()
    node = JointMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
