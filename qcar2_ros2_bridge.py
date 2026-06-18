#!/usr/bin/env python3
# qcar2_ros2_bridge.py
# Run on the QCar. Bridges pal library <-> ROS 2 topics.
# Usage: python3 qcar2_ros2_bridge.py

import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import Float32
import numpy as np

from pal.products.qcar import QCar, QCarLidar


class QCar2Bridge(Node):

    def __init__(self):
        super().__init__('qcar2_bridge')

        # QCar hardware
        self.car   = QCar(readMode=1, frequency=100)
        self.lidar = QCarLidar(numMeasurements=1000)

        # Publishers
        self.pub_imu     = self.create_publisher(Imu,      '/qcar2/imu',     10)
        self.pub_scan    = self.create_publisher(LaserScan, '/qcar2/scan',    10)
        self.pub_battery = self.create_publisher(Float32,   '/qcar2/battery', 10)

        # Subscriber
        self.sub_cmd = self.create_subscription(
            Twist, '/qcar2/cmd_vel', self.cmd_callback, 10)

        self._throttle = 0.0
        self._steering = 0.0
        self._lock = threading.Lock()

        # Timers
        self.create_timer(0.01, self.write_drive)
        self.create_timer(0.02, self.publish_sensors)

        self.get_logger().info('QCar2 ROS 2 bridge started')
        self.get_logger().info('Subscribing to /qcar2/cmd_vel')
        self.get_logger().info('Publishing /qcar2/imu  /qcar2/scan  /qcar2/battery')

    def cmd_callback(self, msg):
        with self._lock:
            self._throttle = float(msg.linear.x)
            self._steering = float(msg.angular.z)

    def write_drive(self):
        with self._lock:
            t = self._throttle
            s = self._steering
        leds = np.array([0, 0, 0, 0, 0, 0, 1, 1], dtype=float)
        if s >  0.15:
            leds[0] = 1
            leds[2] = 1
        elif s < -0.15:
            leds[1] = 1
            leds[3] = 1
        if t < 0:
            leds[5] = 1
        self.car.write(throttle=t, steering=s, LEDs=leds)
        self.car.read()

    def publish_sensors(self):
        now = self.get_clock().now().to_msg()

        # IMU
        imu = Imu()
        imu.header.stamp = now
        imu.header.frame_id = 'imu_link'
        imu.linear_acceleration.x = float(self.car.accelerometer[0])
        imu.linear_acceleration.y = float(self.car.accelerometer[1])
        imu.linear_acceleration.z = float(self.car.accelerometer[2])
        imu.angular_velocity.x    = float(self.car.gyroscope[0])
        imu.angular_velocity.y    = float(self.car.gyroscope[1])
        imu.angular_velocity.z    = float(self.car.gyroscope[2])
        self.pub_imu.publish(imu)

        # Battery
        batt = Float32()
        batt.data = float(self.car.batteryVoltage)
        self.pub_battery.publish(batt)

        # LiDAR
        try:
            self.lidar.read()
            scan = LaserScan()
            scan.header.stamp    = now
            scan.header.frame_id = 'lidar_link'
            scan.angle_min       = float(self.lidar.angles[0])
            scan.angle_max       = float(self.lidar.angles[-1])
            scan.angle_increment = float(
                (self.lidar.angles[-1] - self.lidar.angles[0])
                / max(len(self.lidar.angles) - 1, 1)
            )
            scan.range_min = 0.05
            scan.range_max = 12.0
            scan.ranges    = self.lidar.distances.tolist()
            self.pub_scan.publish(scan)
        except Exception as e:
            self.get_logger().warn('LiDAR read error: ' + str(e))


def main():
    rclpy.init()
    node = QCar2Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.car.write(throttle=0.0, steering=0.0,
                           LEDs=np.zeros(8, dtype=float))
            node.car.terminate()
        except Exception:
            pass
        try:
            node.lidar.terminate()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
