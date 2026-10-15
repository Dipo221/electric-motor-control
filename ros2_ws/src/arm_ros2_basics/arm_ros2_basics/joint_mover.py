# 第五週 實作 5：Action Server —— P 控制把關節移到目標角度
#   目標 Goal：joint_name、target（rad）
#   回饋 Feedback：current、error
#   結果 Result：success、final_error、message
# 這個節點自己發布 /joint_states（模擬 7 顆馬達），
# 執行前要先停掉 joint_wave，避免兩個來源搶同一個 Topic。
# 注意：馬達模型是理想的速度控制（θ ← θ + v·Δt），沒有讀真實編碼器，
#       沒有慣量與扭矩限制，不能直接拿來控制實體手臂。
import time

import rclpy
from rcl_interfaces.msg import FloatingPointRange, ParameterDescriptor
from rclpy.action import (ActionServer, CancelResponse,
                          GoalResponse)
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState

from arm_interfaces.action import MoveJoint
from arm_ros2_basics.joint_monitor import LIMITS

JOINTS = [f'panda_joint{i}' for i in range(1, 8)]
FINGERS = ['panda_finger_joint1', 'panda_finger_joint2']
HOME = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]


def rng(lo, hi):   # 允許範圍：超出就自動拒絕
    return ParameterDescriptor(floating_point_range=[
        FloatingPointRange(from_value=lo, to_value=hi)])


RATE = 20.0          # 控制迴圈頻率（Hz）
DT = 1.0 / RATE      # 取樣時間 0.05 s
TOL = 0.005          # 到位誤差（rad）≈ 0.3°
TIMEOUT = 10.0       # 逾時（s）：超過就中止


class JointMover(Node):
    def __init__(self):
        super().__init__('joint_mover')
        self.declare_parameter('kp', 2.0, rng(0.1, 10.0))
        self.declare_parameter('max_vel', 1.0, rng(0.05, 2.175))
        self.q = dict(zip(JOINTS, HOME))     # 目前角度
        self.v = dict.fromkeys(JOINTS, 0.0)  # 目前角速度
        self.busy = False                    # 一次一個目標

        group = ReentrantCallbackGroup()     # 回呼可同時執行
        self.pub = self.create_publisher(
            JointState, 'joint_states', 10)
        self.create_timer(DT, self.publish_state,
                          callback_group=group)
        self.server = ActionServer(
            self, MoveJoint, 'move_joint',
            goal_callback=self.on_goal,        # ① 收到目標
            cancel_callback=self.on_cancel,    # ② 收到取消
            execute_callback=self.execute,     # ③ 執行
            callback_group=group)
        self.get_logger().info('等待 /move_joint 的目標')

    def on_goal(self, goal):
        # ① 收到目標：檢查後決定接受或拒絕
        if self.busy or goal.joint_name not in LIMITS:
            return GoalResponse.REJECT
        low, high = LIMITS[goal.joint_name]
        if not low <= goal.target <= high:
            self.get_logger().warn('目標超出關節極限，拒絕')
            return GoalResponse.REJECT
        self.busy = True
        return GoalResponse.ACCEPT

    def on_cancel(self, goal_handle):
        # ② 收到取消請求：這裡一律同意
        self.get_logger().info('收到取消請求')
        return CancelResponse.ACCEPT

    def execute(self, goal_handle):   # ③ P 控制迴圈
        name = goal_handle.request.joint_name
        target = goal_handle.request.target
        kp = self.get_parameter('kp').value
        vmax = self.get_parameter('max_vel').value
        fb, result = MoveJoint.Feedback(), MoveJoint.Result()
        t_end = time.monotonic() + TIMEOUT    # 逾時時間
        while not goal_handle.is_cancel_requested:
            error = target - self.q[name]
            if abs(error) < TOL or time.monotonic() > t_end:
                break                            # 到位或逾時
            v = max(-vmax, min(vmax, kp * error))  # P＋飽和
            self.v[name] = v
            self.q[name] += v * DT               # 馬達轉動
            fb.current, fb.error = self.q[name], error
            goal_handle.publish_feedback(fb)
            time.sleep(DT)
        self.v[name] = 0.0
        self.busy = False
        result.final_error = target - self.q[name]
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()   # 狀態：已取消
            result.message = '已取消'
        elif abs(result.final_error) < TOL:
            goal_handle.succeed()    # 狀態：成功
            result.success, result.message = True, '到位'
        else:
            goal_handle.abort()      # 狀態：中止（逾時）
            result.message = '逾時中止'
        return result

    def publish_state(self):
        # ④ 不論有沒有目標，持續發布 7 顆馬達的狀態
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINTS + FINGERS
        q = [self.q[j] for j in JOINTS]
        v = [self.v[j] for j in JOINTS]
        msg.position = q + [0.04, 0.04]     # 手指全開
        msg.velocity = v + [0.0, 0.0]
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = JointMover()
    executor = MultiThreadedExecutor()  # 邊控制邊發布
    try:
        rclpy.spin(node, executor=executor)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
