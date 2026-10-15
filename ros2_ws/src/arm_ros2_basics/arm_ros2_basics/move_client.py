# 第五週 實作 5：Action Client —— 送目標、看回饋、可取消
# 用法：
#   ros2 run arm_ros2_basics move_client panda_joint1 1.2
#   最後加 --cancel 1.0：1 秒後送出取消
import argparse
import math
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from arm_interfaces.action import MoveJoint


class MoveClient(Node):
    def __init__(self):
        super().__init__('move_client')
        self.client = ActionClient(
            self, MoveJoint, 'move_joint')

    def send(self, joint, target):
        # ① 等伺服器出現（最多 5 秒），再非同步送出目標
        if not self.client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError('5 秒內找不到 /move_joint')
        goal = MoveJoint.Goal(joint_name=joint, target=target)
        return self.client.send_goal_async(
            goal, feedback_callback=self.on_feedback)

    def on_feedback(self, msg):          # ② 每次回饋都印出
        fb = msg.feedback
        self.get_logger().info(
            f'目前 {math.degrees(fb.current):7.1f}°'
            f' | 誤差 {math.degrees(fb.error):7.1f}°')


def parse_args():
    argv = remove_ros_args(sys.argv)[1:]
    p = argparse.ArgumentParser()
    p.add_argument('joint')               # 例：panda_joint1
    p.add_argument('target', type=float)  # rad
    p.add_argument('--cancel', type=float, default=0.0,
                   help='幾秒後取消（0＝不取消）')
    return p.parse_args(argv)


def main():
    args = parse_args()
    rclpy.init()
    node = MoveClient()
    try:
        future = node.send(args.joint, args.target)
        rclpy.spin_until_future_complete(node, future)
        handle = future.result()
        if not handle.accepted:
            node.get_logger().warn('目標被拒絕')
            return
        node.get_logger().info('目標已接受')

        def cancel_once():                    # ③ 正式取消
            timer.cancel()
            node.get_logger().info('送出取消請求')
            handle.cancel_goal_async()

        if args.cancel > 0:                 # 幾秒後取消
            timer = node.create_timer(
                args.cancel, cancel_once)
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(node, result_future)
        r = result_future.result().result     # ④ 取得結果
        node.get_logger().info(
            f'結果：{r.message}'
            f'，最終誤差 {math.degrees(r.final_error):.2f}°')
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
