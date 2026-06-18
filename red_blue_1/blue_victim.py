#!/usr/bin/env python3
"""
blue_victim.py
==============
Blue Machine -- Simulated QCar2 Victim Node

Runs on the blue machine to simulate a QCar2 ROS 2 stack without any
physical hardware. Publishes realistic sensor data on the same topics
the attack scripts target.

Topics published:
    /qcar2/imu      -- sensor_msgs/Imu      (50 Hz)
    /qcar2/scan     -- sensor_msgs/LaserScan (10 Hz)
    /qcar2/battery  -- std_msgs/Float32      (1 Hz)
    /qcar2/motor    -- std_msgs/String        (10 Hz)

Topics subscribed:
    /qcar2/cmd_vel  -- geometry_msgs/Twist

When the red machine injects commands via rogue_node.py, this node
receives them and logs them -- demonstrating the attack worked without
needing a physical robot.

Usage:
    python3 blue_victim.py
    python3 blue_victim.py --name blue_qcar2   # custom node name
"""

import argparse
import math
import random
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import Float32, String
import numpy as np


def noise(scale=1.0):
    return (random.random() - 0.5) * 2 * scale


class BlueVictim(Node):

    def __init__(self, node_name: str):
        super().__init__(node_name)

        self._throttle   = 0.0
        self._steering   = 0.0
        self._t0         = time.time()
        self._cmd_count  = 0
        self._lidar_tick = 0.0

        # ── Publishers ────────────────────────────────────────────────────────
        qos_sensor = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.pub_imu     = self.create_publisher(Imu,       '/qcar2/imu',     qos_sensor)
        self.pub_scan    = self.create_publisher(LaserScan,  '/qcar2/scan',    qos_sensor)
        self.pub_battery = self.create_publisher(Float32,    '/qcar2/battery', qos_sensor)
        self.pub_motor   = self.create_publisher(String,     '/qcar2/motor',   qos_sensor)

        # ── Subscriber ────────────────────────────────────────────────────────
        self.sub_cmd = self.create_subscription(
            Twist, '/qcar2/cmd_vel', self.cmd_callback, 10)

        # ── Timers ────────────────────────────────────────────────────────────
        self.create_timer(0.02,  self.publish_imu)      # 50 Hz
        self.create_timer(0.10,  self.publish_scan)     # 10 Hz
        self.create_timer(0.10,  self.publish_motor)    # 10 Hz
        self.create_timer(1.00,  self.publish_battery)  # 1  Hz

        self.get_logger().info('=' * 55)
        self.get_logger().info('Blue Machine -- Simulated QCar2 Victim')
        self.get_logger().info('=' * 55)
        self.get_logger().info(f'Node name : {node_name}')
        self.get_logger().info('Publishing:')
        self.get_logger().info('  /qcar2/imu      50 Hz')
        self.get_logger().info('  /qcar2/scan     10 Hz')
        self.get_logger().info('  /qcar2/battery   1 Hz')
        self.get_logger().info('  /qcar2/motor    10 Hz')
        self.get_logger().info('Listening:')
        self.get_logger().info('  /qcar2/cmd_vel')
        self.get_logger().info('')
        self.get_logger().info('From red machine, run:')
        self.get_logger().info('  ros2 topic list')
        self.get_logger().info('  python3 rogue_node.py')
        self.get_logger().info('  python3 cmd_flood.py')
        self.get_logger().info('=' * 55)

    # ── Command subscriber ─────────────────────────────────────────────────────

    def cmd_callback(self, msg: Twist):
        self._throttle  = msg.linear.x
        self._steering  = msg.angular.z
        self._cmd_count += 1

        # Log every received command so students can see the attack working
        self.get_logger().warn(
            f'CMD_VEL RECEIVED  '
            f'throttle={msg.linear.x:+.3f}  '
            f'steering={msg.angular.z:+.3f}  '
            f'total_received={self._cmd_count}'
        )

    # ── Sensor publishers ──────────────────────────────────────────────────────

    def publish_imu(self):
        now = self.get_clock().now().to_msg()
        msg = Imu()
        msg.header.stamp    = now
        msg.header.frame_id = 'imu_link'

        # Realistic accelerometer -- Z ~9.81 at rest, X responds to throttle
        msg.linear_acceleration.x = self._throttle * 2.0 + noise(0.08)
        msg.linear_acceleration.y = self._steering * 0.5 + noise(0.05)
        msg.linear_acceleration.z = 9.81               + noise(0.04)

        # Realistic gyroscope -- Z responds to steering
        msg.angular_velocity.x = noise(0.015)
        msg.angular_velocity.y = noise(0.012)
        msg.angular_velocity.z = self._steering * 0.2 + noise(0.010)

        # Identity orientation (no AHRS filter running)
        msg.orientation.w = 1.0

        self.pub_imu.publish(msg)

    def publish_scan(self):
        self._lidar_tick += 0.03
        now = self.get_clock().now().to_msg()
        num_pts = 360

        angles    = np.linspace(0, 2 * math.pi, num_pts, endpoint=False)
        distances = (
            0.8
            + 0.4 * np.abs(np.sin(angles * 2.3 + 1.1 + self._lidar_tick))
            + np.random.uniform(-0.05, 0.05, num_pts)
        )
        distances = np.clip(distances, 0.12, 3.5)

        msg = LaserScan()
        msg.header.stamp    = now
        msg.header.frame_id = 'lidar_link'
        msg.angle_min       = 0.0
        msg.angle_max       = 2 * math.pi
        msg.angle_increment = 2 * math.pi / num_pts
        msg.time_increment  = 0.0
        msg.scan_time       = 0.1
        msg.range_min       = 0.12
        msg.range_max       = 3.5
        msg.ranges          = distances.tolist()
        msg.intensities     = []

        self.pub_scan.publish(msg)

    def publish_battery(self):
        msg      = Float32()
        msg.data = 12.4 + noise(0.05)
        self.pub_battery.publish(msg)

    def publish_motor(self):
        elapsed  = time.time() - self._t0
        encoder  = int(self._throttle * 12 * elapsed + noise(1))
        tach     = self._throttle * 8.0 + noise(0.3)
        current  = abs(self._throttle) * 4.2 + noise(0.1)

        msg      = String()
        msg.data = (
            f'encoder={encoder}  '
            f'tach={tach:.2f}  '
            f'current={current:.2f}'
        )
        self.pub_motor.publish(msg)


def main():
    ap = argparse.ArgumentParser(
        description='Blue Machine: Simulated QCar2 victim node')
    ap.add_argument('--name', default='blue_qcar2_node',
                    help='ROS 2 node name (default: blue_qcar2_node)')
    args = ap.parse_args()

    rclpy.init()
    node = BlueVictim(args.name)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        print('\n[INFO] Blue victim node stopped.')


if __name__ == '__main__':
    main()
