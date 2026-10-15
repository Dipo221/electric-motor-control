# 第五週 實作 1：joint_wave v2 —— 常數改成參數（Parameter），不改程式就能調
# 第五週 實作 3：加上 /home 服務（Service），讓 Panda 回到 HOME
# （第四週 實作 4：Publisher —— 發布 /joint_states 讓 Panda 揮手）
import math

import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

from arm_ros2_basics.joint_monitor import LIMITS

# ---- 第 10 頁：檔頭 ----
JOINTS = [f'panda_joint{i}' for i in range(1, 8)]
FINGERS = ['panda_finger_joint1', 'panda_finger_joint2']
# 第四週的常數 → 現在只是參數的「預設值」
HOME = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
AMP = [0.8, 0.0, 0.0, 0.4, 0.0, 0.0, 0.0]   # 擺幅（rad）
FREQ = 0.2    # 擺動頻率（Hz）：5 秒一個來回
RATE = 30.0   # 發布頻率（Hz），維持常數


def reject(why):                     # 拒絕並附上原因
    return SetParametersResult(successful=False, reason=why)


class JointWave(Node):
    # ---- 第 11 頁：宣告 ----
    def __init__(self):
        super().__init__('joint_wave')
        # ① 宣告參數：名稱＋預設值（型別由預設值決定）
        self.declare_parameter('home', HOME)
        self.declare_parameter('amp', AMP)
        self.declare_parameter('freq', FREQ)
        # ② 參數被修改「之前」先檢查，不合理就拒絕
        self.add_on_set_parameters_callback(self.check_params)
        r = self.check_params([])   # YAML 給的初值也檢查
        if not r.successful:
            raise ValueError(r.reason)

        self.pub = self.create_publisher(
            JointState, 'joint_states', 10)  # 型別、名稱、佇列
        self.srv = self.create_service(
            Trigger, 'home', self.on_home)   # 型別、名稱、回呼
        self.phase = 0.0                     # 目前相位（rad）
        self.create_timer(1.0 / RATE, self.on_timer)
        self.get_logger().info('開始發布 /joint_states')

    # ---- 第 12 頁：檢查 ----
    def check_params(self, params):
        cur = {n: self.get_parameter(n).value
               for n in ('home', 'amp', 'freq')}
        cur.update({p.name: p.value for p in params})  # 新值
        home, amp = cur['home'], cur['amp']
        if not 0.0 < cur['freq'] <= 1.0:
            return reject('freq 要在 0～1 Hz')
        if len(home) != 7 or len(amp) != 7:
            return reject('home、amp 要 7 個數')
        for name, h, a in zip(JOINTS, home, amp):
            low, high = LIMITS[name]
            if h - abs(a) < low or h + abs(a) > high:
                return reject(f'{name} 會超出極限')
        return SetParametersResult(successful=True)

    # ---- 第 13 頁：讀取 ----
    def on_timer(self):
        # ③ 每次都讀參數：ros2 param set 之後立刻生效
        home = self.get_parameter('home').value
        amp = self.get_parameter('amp').value
        freq = self.get_parameter('freq').value
        w = 2.0 * math.pi * freq   # 角頻率 rad/s
        self.phase += w / RATE     # 相位累加：改頻率不跳
        s, c = math.sin(self.phase), math.cos(self.phase)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()  # 時間戳記
        msg.name = JOINTS + FINGERS
        pos = [h + a * s for h, a in zip(home, amp)]
        vel = [a * w * c for a in amp]      # 位置對時間微分
        g = 0.02 if any(amp) else 0.0       # 手指擺幅（m）：amp 全 0 就停
        msg.position = pos + [0.02 + g * s] * 2   # 手指 0～0.04 m
        msg.velocity = vel + [g * w * c] * 2
        self.pub.publish(msg)

    # ---- 第 30 頁：/home 服務 ----
    def on_home(self, request, response):
        # ④ 服務：amp 全部歸零 → 停在 HOME
        zero = Parameter('amp', Parameter.Type.DOUBLE_ARRAY,
                         [0.0] * 7)
        result = self.set_parameters([zero])[0]
        self.phase = 0.0
        ok = result.successful
        response.success = ok
        response.message = (
            '已回到 HOME' if ok else result.reason)
        self.get_logger().info('收到 /home 請求')
        return response


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
