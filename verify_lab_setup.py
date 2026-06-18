#!/usr/bin/env python3
"""
verify_lab_setup.py
===================
QCar ROS 2 Security Lab — Environment Verification Script

Run this on every machine before the first lab session:
  - Ubuntu 22.04 attacker laptop (native)
  - Windows student laptops (inside Docker/WSL2 container)

Usage:
    python3 verify_lab_setup.py
    python3 verify_lab_setup.py --ros-ip 192.168.1.10   # also ping QCar
    python3 verify_lab_setup.py --full                   # run all checks inc. DDS multicast

Prints a PASS / FAIL / WARN for every requirement with fix instructions.
"""

import argparse
import importlib
import os
import platform
import shutil
import socket
import struct
import subprocess
import sys
import time

# ── Colour helpers ────────────────────────────────────────────────────────────
# Detect if the terminal supports colour (disabled on Windows CMD)
USE_COLOR = sys.stdout.isatty() and platform.system() != "Windows"

def green(s):  return f"\033[92m{s}\033[0m" if USE_COLOR else s
def red(s):    return f"\033[91m{s}\033[0m" if USE_COLOR else s
def yellow(s): return f"\033[93m{s}\033[0m" if USE_COLOR else s
def bold(s):   return f"\033[1m{s}\033[0m"  if USE_COLOR else s
def cyan(s):   return f"\033[96m{s}\033[0m" if USE_COLOR else s
def dim(s):    return f"\033[2m{s}\033[0m"  if USE_COLOR else s

PASS  = green("  ✔  PASS")
FAIL  = red("  ✗  FAIL")
WARN  = yellow("  ⚠  WARN")
SKIP  = dim("  –  SKIP")

results = []   # list of (label, status, fix_hint)

def record(label, status, fix=None):
    results.append((label, status, fix))
    tag = {True: PASS, False: FAIL, "warn": WARN, "skip": SKIP}.get(status, SKIP)
    print(f"{tag}  {label}")
    if fix and status is not True:
        for line in fix.splitlines():
            print(f"       {dim(line)}")

def section(title):
    print()
    print(bold(cyan(f"── {title} {'─' * max(0, 55 - len(title))}")))


# ── 1. Platform ───────────────────────────────────────────────────────────────
section("Platform")

os_name    = platform.system()
os_release = platform.release()
py_version = sys.version_info

record("Python ≥ 3.10",
       py_version >= (3, 10),
       f"Current: {sys.version.split()[0]}\n"
       "Install Python 3.10+: sudo apt install python3.10")

is_linux = os_name == "Linux"
record("Running on Linux",
       is_linux,
       f"Detected: {os_name} {os_release}\n"
       "This script is designed for Ubuntu 22.04 (native or WSL2/Docker).")

if is_linux:
    try:
        with open("/etc/os-release") as f:
            lines = dict(l.strip().split("=", 1) for l in f if "=" in l)
        distro  = lines.get("NAME", "").strip('"')
        version = lines.get("VERSION_ID", "").strip('"')
        is_jammy = ("Ubuntu" in distro and version == "22.04")
        record('Ubuntu 22.04 "Jammy Jellyfish"',
               is_jammy,
               f"Detected: {distro} {version}\n"
               "ROS 2 Humble targets Ubuntu 22.04. Other versions may work but are unsupported.")
    except Exception:
        record("OS version readable", "warn", "Could not read /etc/os-release.")

# Architecture
arch = platform.machine()
record(f"Architecture detected: {arch}", True)


# ── 2. ROS 2 Installation ─────────────────────────────────────────────────────
section("ROS 2 Humble")

ros_distro = os.environ.get("ROS_DISTRO", "")
record("ROS_DISTRO=humble in environment",
       ros_distro == "humble",
       "Run: source /opt/ros/humble/setup.bash\n"
       "Or add it to ~/.bashrc so it loads automatically.")

ros2_bin = shutil.which("ros2")
record("ros2 binary on PATH",
       ros2_bin is not None,
       "Install ROS 2 Humble:\n"
       "  sudo apt install ros-humble-desktop\n"
       "Then: source /opt/ros/humble/setup.bash")

if ros2_bin:
    try:
        out = subprocess.check_output(["ros2", "--version"],
                                      stderr=subprocess.STDOUT, text=True, timeout=5)
        version_line = out.strip().splitlines()[0]
        record(f"ros2 version: {version_line}", True)
    except Exception as e:
        record("ros2 --version", "warn", str(e))

# Check key ROS 2 Python packages are importable
for pkg in ("rclpy", "geometry_msgs", "sensor_msgs", "std_msgs"):
    try:
        importlib.import_module(pkg)
        record(f"import {pkg}", True)
    except ImportError:
        record(f"import {pkg}", False,
               f"{pkg} not importable. Make sure you have sourced ROS 2:\n"
               "  source /opt/ros/humble/setup.bash\n"
               f"And that ros-humble-desktop is installed (includes {pkg}).")


# ── 3. Environment Variables ──────────────────────────────────────────────────
section("ROS 2 Environment Variables")

domain_id = os.environ.get("ROS_DOMAIN_ID", "")
record("ROS_DOMAIN_ID is set",
       domain_id != "",
       "Add to ~/.bashrc:\n"
       "  export ROS_DOMAIN_ID=0\n"
       "All machines in the lab must use the same value.")

if domain_id:
    try:
        did = int(domain_id)
        record(f"ROS_DOMAIN_ID value is valid integer ({did})",
               0 <= did <= 232,
               "Valid range is 0–232.")
    except ValueError:
        record("ROS_DOMAIN_ID is a valid integer", False,
               f"Current value '{domain_id}' is not an integer.")

fastdds_transport = os.environ.get("FASTDDS_BUILTIN_TRANSPORTS", "")
record("FASTDDS_BUILTIN_TRANSPORTS=UDPv4",
       fastdds_transport == "UDPv4",
       "Add to ~/.bashrc:\n"
       "  export FASTDDS_BUILTIN_TRANSPORTS=UDPv4\n"
       "Prevents Fast-DDS shared-memory mode which breaks Docker/WSL2 setups.")


# ── 4. Python Attack Libraries ────────────────────────────────────────────────
section("Python Attack Libraries")

pip_packages = {
    "scapy":          ("scapy",          "pip install scapy",           True),
    "cyclonedds":     ("cyclonedds",     "pip install cyclonedds-python", False),
    "psutil":         ("psutil",         "pip install psutil",           False),
    "numpy":          ("numpy",          "pip install numpy",            False),
    "matplotlib":     ("matplotlib",     "pip install matplotlib",       False),
}

for display_name, (import_name, install_cmd, needs_root) in pip_packages.items():
    try:
        mod = importlib.import_module(import_name)
        ver = getattr(mod, "__version__", "unknown")
        record(f"import {display_name}  (v{ver})", True)
    except ImportError:
        hint = f"{install_cmd}"
        if needs_root:
            hint += "\n(Scapy also needs root or cap_net_raw for raw sockets)"
        record(f"import {display_name}", False, hint)

# rclpy should NOT be installed via pip
try:
    result = subprocess.check_output(
        [sys.executable, "-m", "pip", "show", "rclpy"],
        stderr=subprocess.DEVNULL, text=True, timeout=5)
    if result.strip():
        record("rclpy NOT installed via pip (correct)",
               "warn",
               "rclpy appears to be pip-installed. This can conflict with the\n"
               "system ROS 2 rclpy. Remove it:\n"
               "  pip uninstall rclpy\n"
               "rclpy is provided by ros-humble-desktop via apt.")
    else:
        record("rclpy NOT installed via pip (correct)", True)
except Exception:
    record("rclpy NOT installed via pip (correct)", True)


# ── 5. Network Tools ──────────────────────────────────────────────────────────
section("Network Tools")

for tool, install in [
    ("wireshark",  "sudo apt install wireshark"),
    ("tshark",     "sudo apt install tshark"),
    ("tcpdump",    "sudo apt install tcpdump"),
    ("ip",         "sudo apt install iproute2"),
    ("ping",       "sudo apt install iputils-ping"),
]:
    found = shutil.which(tool)
    record(f"{tool} on PATH",
           found is not None,
           f"Install: {install}")

# Check Scapy raw socket capability
if is_linux:
    try:
        import scapy  # noqa
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        test_sock.close()
        record("Raw socket access (needed for Scapy attacks 2 & 3)", True)
    except PermissionError:
        record("Raw socket access (needed for Scapy attacks 2 & 3)", False,
               "Run this script with sudo, OR grant capability permanently:\n"
               "  sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)\n"
               "The second option is safer for a shared lab machine.")
    except ImportError:
        record("Raw socket access", "skip", "Scapy not installed yet.")


# ── 6. Network Connectivity ───────────────────────────────────────────────────
section("Network Interfaces")

try:
    import psutil
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    found_up = []
    for iface, addr_list in addrs.items():
        if iface == "lo":
            continue
        if stats.get(iface) and stats[iface].isup:
            ipv4 = [a.address for a in addr_list if a.family == socket.AF_INET]
            if ipv4:
                found_up.append(f"{iface}: {ipv4[0]}")
    if found_up:
        record(f"Active network interfaces: {', '.join(found_up)}", True)
    else:
        record("Active network interfaces", "warn",
               "No active interfaces with IPv4 found. Is networking up?")
except ImportError:
    record("Network interface check", "skip", "Install psutil: pip install psutil")


# ── 7. DDS Multicast (optional, requires --full flag) ────────────────────────
def check_dds_multicast():
    """
    Send a UDP packet to the DDS SPDP multicast group (239.255.0.1:7400)
    and confirm the socket binds successfully. This does NOT verify that
    other nodes receive it — for that, run ros2 multicast send/receive
    on two separate machines.
    """
    MCAST_GRP  = "239.255.0.1"
    MCAST_PORT = 7400
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(1.0)
        # Minimal RTPS header (magic bytes only) — won't be parsed by real nodes
        test_payload = b"RTPS\x02\x01\x01\x0f" + b"\x00" * 12
        sock.sendto(test_payload, (MCAST_GRP, MCAST_PORT))
        sock.close()
        return True, None
    except OSError as e:
        return False, str(e)

section("DDS Multicast (cross-machine check)")
ok, err = check_dds_multicast()
record(f"UDP multicast socket to {239}.{255}.{0}.{1}:{7400} (SPDP group)",
       ok,
       err or "Check firewall:\n"
              "  sudo ufw allow 7400:7500/udp\n"
              "And verify the network interface supports multicast:\n"
              "  ip link show   # look for MULTICAST flag")

# Check firewall status
if is_linux and shutil.which("ufw"):
    try:
        out = subprocess.check_output(["sudo", "ufw", "status"],
                                      stderr=subprocess.DEVNULL, text=True, timeout=5)
        if "inactive" in out.lower():
            record("ufw firewall status", True,
                   )
        elif "7400" in out:
            record("ufw: DDS port 7400-7500/udp open", True)
        else:
            record("ufw: DDS port 7400-7500/udp open",
                   "warn",
                   "ufw is active but DDS ports may not be open. Run:\n"
                   "  sudo ufw allow 7400:7500/udp\n"
                   "  sudo ufw allow 7400:7500/tcp")
    except Exception:
        record("ufw firewall check", "warn",
               "Could not read ufw status (needs sudo). Run manually:\n"
               "  sudo ufw status")


# ── 8. Optional: ping the QCar ────────────────────────────────────────────────
def ping_host(ip, count=3):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "1", ip],
            capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)


# ── 9. ROS 2 daemon & topic check ─────────────────────────────────────────────
section("ROS 2 Runtime")

if ros2_bin and ros_distro == "humble":
    # Check daemon
    try:
        out = subprocess.check_output(
            ["ros2", "daemon", "status"],
            stderr=subprocess.STDOUT, text=True, timeout=8)
        running = "running" in out.lower()
        record("ROS 2 daemon running",
               running,
               "Start it: ros2 daemon start")
    except subprocess.TimeoutExpired:
        record("ROS 2 daemon status", "warn", "Timed out — daemon may be slow to respond.")
    except Exception as e:
        record("ROS 2 daemon status", "warn", str(e))

    # Quick topic list (will be empty if no nodes are running — that's OK)
    try:
        out = subprocess.check_output(
            ["ros2", "topic", "list"],
            stderr=subprocess.STDOUT, text=True, timeout=8)
        topics = [t for t in out.strip().splitlines() if t.startswith("/")]
        if topics:
            record(f"ros2 topic list: {len(topics)} topic(s) visible", True)
            # Check for QCar namespace
            qcar2_topics = [t for t in topics if "qcar2" in t.lower()]
            qcar_topics  = [t for t in topics if "qcar"  in t.lower() and "qcar2" not in t.lower()]
            if qcar2_topics:
                record(f"QCar2 topics found: {', '.join(qcar2_topics[:3])}", True)
            elif qcar_topics:
                record("QCar topics found (namespace is /qcar/ not /qcar2/)",
                       "warn",
                       "Update attack scripts to use /qcar/ instead of /qcar2/\n"
                       "or check your QCar firmware version.")
        else:
            record("ros2 topic list (no topics yet — start a node first)", "warn",
                   "This is normal if no ROS 2 nodes are running.\n"
                   "Start the simulated QCar node or connect the physical QCar\n"
                   "then re-run this script.")
    except subprocess.TimeoutExpired:
        record("ros2 topic list", "warn", "Timed out. Is the ROS 2 daemon running?")
    except Exception as e:
        record("ros2 topic list", "warn", str(e))
else:
    record("ROS 2 runtime checks", "skip",
           "ROS 2 not sourced or not installed — skipping runtime checks.")


# ── Summary ───────────────────────────────────────────────────────────────────
section("Summary")

passed = sum(1 for _, s, _ in results if s is True)
warned = sum(1 for _, s, _ in results if s == "warn")
failed = sum(1 for _, s, _ in results if s is False)
skipped= sum(1 for _, s, _ in results if s == "skip")
total  = len(results)

print()
print(f"  {green(f'{passed} passed')}   "
      f"{red(f'{failed} failed')}   "
      f"{yellow(f'{warned} warnings')}   "
      f"{dim(f'{skipped} skipped')}   "
      f"out of {total} checks")
print()

if failed == 0 and warned == 0:
    print(bold(green("  ✔  All checks passed. This machine is ready for the security lab.")))
elif failed == 0:
    print(bold(yellow("  ⚠  No hard failures, but review the warnings above before lab day.")))
else:
    print(bold(red(f"  ✗  {failed} check(s) failed. Fix the items above before running the lab.")))

print()

# ── Optional: QCar ping ───────────────────────────────────────────────────────
def run_qcar_ping(ip):
    section(f"QCar Connectivity ({ip})")
    ok, output = ping_host(ip)
    record(f"ping {ip}", ok,
           f"Cannot reach QCar at {ip}.\n"
           "Check: same Wi-Fi network? correct IP? QCar powered on?")
    if ok:
        # Try to list QCar-specific topics
        if ros2_bin and ros_distro == "humble":
            try:
                out = subprocess.check_output(
                    ["ros2", "topic", "list"],
                    stderr=subprocess.STDOUT, text=True, timeout=10)
                topics = [t for t in out.strip().splitlines()
                          if "qcar" in t.lower()]
                if topics:
                    print()
                    print(f"  {green('QCar topics visible:')}")
                    for t in topics:
                        print(f"    {cyan(t)}")
                    print()
                    print(dim("  Tip: if topics show /qcar/ instead of /qcar2/,"))
                    print(dim("  update the namespace in all attack scripts."))
                else:
                    print()
                    print(yellow("  QCar is reachable by ping but no ROS topics found yet."))
                    print(dim("  Make sure the QCar's ROS 2 stack is fully booted."))
            except Exception:
                pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="QCar ROS 2 Security Lab — Environment Verification")
    ap.add_argument("--ros-ip", metavar="IP",
                    help="IP address of the physical QCar — runs a ping + topic check")
    args = ap.parse_args()

    print()
    print(bold("QCar ROS 2 Security Lab — Environment Verification"))
    print(dim(f"  {platform.node()}  |  Python {sys.version.split()[0]}  |  {time.strftime('%Y-%m-%d %H:%M')}"))

    if args.ros_ip:
        run_qcar_ping(args.ros_ip)

    sys.exit(0 if failed == 0 else 1)
