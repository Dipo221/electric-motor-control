# 第四週 實作 3：第一個 ROS 2 節點（每秒印一行訊息）
import rclpy
from rclpy.node import Node


# ---- 第 41 頁：節點類別 ----
class HelloNode(Node):
    def __init__(self):
        super().__init__('hello_node')          # 節點名稱
        self.count = 0
        self.create_timer(1.0, self.on_timer)   # 每秒呼叫一次
        self.get_logger().info('hello_node 啟動')

    def on_timer(self):
        self.count += 1
        text = f'第 {self.count} 次：Hello ROS 2'
        self.get_logger().info(text)


# ---- 第 42 頁：main() 四步驟 ----
def main():
    rclpy.init()                  # ① 初始化 ROS 2
    node = HelloNode()            # ② 建立節點
    try:
        rclpy.spin(node)          # ③ 等待並執行回呼函式
    except KeyboardInterrupt:     # Ctrl+C 離開
        pass
    finally:
        node.destroy_node()       # ④ 收尾
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
