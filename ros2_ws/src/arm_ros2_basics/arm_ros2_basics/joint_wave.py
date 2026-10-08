# 第四週 實作 4：Publisher —— 發布 /joint_states 讓 Panda 揮手
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# ---- 第 48 頁：常數 ----
JOINTS = [f'panda_joint{i}' for i in range(1, 8)]
FINGERS = ['panda_finger_joint1', 'panda_finger_joint2']
# 起始姿勢（rad），與 MoveIt Panda 範例的 ready 姿勢相同
HOME = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
AMP = [0.8, 0.0, 0.0, 0.4, 0.0, 0.0, 0.0]   # 擺幅（rad）
FREQ = 0.2    # 擺動頻率（Hz）：5 秒一個來回
RATE = 30.0   # 發布頻率（Hz）


class JointWave(Node):
    # ---- 第 49 頁：建立發布者 ----
    def __init__(self):
        super().__init__('joint_wave')
        self.pub = self.create_publisher(
            JointState, 'joint_states', 10)  # 型別、名稱、佇列
        self.t0 = self.get_clock().now()
        self.create_timer(1.0 / RATE, self.on_timer)
        self.get_logger().info('開始發布 /joint_states')

    # ---- 第 50 頁：計算並發布 ----
    def on_timer(self):
        now = self.get_clock().now()
        t = (now - self.t0).nanoseconds * 1e-9  # 經過秒數
        w = 2.0 * math.pi * FREQ            # 角頻率 rad/s
        s, c = math.sin(w * t), math.cos(w * t)

        msg = JointState()
        msg.header.stamp = now.to_msg()     # 時間戳記
        msg.name = JOINTS + FINGERS
        pos = [h + a * s for h, a in zip(HOME, AMP)]
        vel = [a * w * c for a in AMP]      # 位置對時間微分
        grip = 0.02 + 0.02 * s              # 手指 0～0.04 m
        msg.position = pos + [grip, grip]
        msg.velocity = vel + [0.02 * w * c] * 2
        self.pub.publish(msg)


# ---- 和 hello_node 相同，只把類別換成 JointWave ----
def main():
    rclpy.init()
    node = JointWave()
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
