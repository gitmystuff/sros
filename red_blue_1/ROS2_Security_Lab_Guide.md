# QCar ROS 2 Security Lab
## Category 1 & 2: Network, Transport & Standard Protocols
### Step-by-Step Lab Guide

> **Summer Security Project — First Semester College Students**  
> University of North Texas  
> Red Team / Blue Team Hands-On Security Lab

---

## Table of Contents

1. [Lab Overview](#1-lab-overview)
2. [Lab Architecture](#2-lab-architecture)
3. [Background: Why ROS 2 Is Vulnerable](#3-background-why-ros-2-is-vulnerable)
4. [Pre-Lab Checklist](#4-pre-lab-checklist)
5. [Attack 1 — Rogue Node Injection](#5-attack-1--rogue-node-injection)
6. [Attack 2 — Plaintext Packet Sniffing](#6-attack-2--plaintext-packet-sniffing)
7. [Attack 3 — DDS Discovery Poisoning](#7-attack-3--dds-discovery-poisoning)
8. [Attack 4 — Command Flood / DoS](#8-attack-4--command-flood--dos)
9. [Defense — SROS2 Hardening](#9-defense--sros2-hardening)
10. [Student Deliverables](#10-student-deliverables)
11. [Quick Reference](#11-quick-reference)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Lab Overview

This lab demonstrates four real-world attacks against a ROS 2 robotic system using two machines on an isolated network:

- **Red Machine** — the attacker. Runs all four attack scripts.
- **Blue Machine** — the victim. Simulates a ROS 2 robot (or replaced by a physical QCar when available).

By the end of the lab, students will have:
- Injected unauthorized drive commands into a robot
- Captured plaintext sensor data from the air
- Exhausted a robot's DDS discovery resources
- Flooded and denied legitimate operator control
- Configured SROS2 to defend against all four attacks

> **Legal & Ethical Notice:** All activities must be performed exclusively on the isolated lab network using equipment you own or have written permission to test. Never perform these attacks on public networks or production systems.

---

## 2. Lab Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   RED MACHINE       │         │   BLUE MACHINE       │
│   (Attacker)        │◄───────►│   (Victim)           │
│                     │         │                      │
│  rogue_node.py      │         │  blue_victim.py      │
│  sniffer.py         │  Wi-Fi  │                      │
│  dds_ghost.py       │ 192.168 │  Publishes:          │
│  cmd_flood.py       │  .2.0   │  /qcar2/cmd_vel      │
│                     │         │  /qcar2/imu          │
│  Ubuntu 22.04       │         │  /qcar2/scan         │
│  ROS 2 Humble       │         │  /qcar2/battery      │
│  x86_64             │         │  /qcar2/motor        │
└─────────────────────┘         └─────────────────────┘
          │                               │
          └───────────────────────────────┘
                  Isolated Lab Router
                  192.168.2.0/24
                  No internet uplink
```

### Key Rules
- Both machines **must** be on the **same isolated router** — not UNT wifi
- Both machines **must** have `ROS_DOMAIN_ID=0`
- Both machines **must** have `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`
- Only **one student runs attack scripts at a time** during shared QCar demos

---

## 3. Background: Why ROS 2 Is Vulnerable

ROS 2 uses **DDS (Data Distribution Service)** as its transport layer. By default:

| Layer | Protocol | Default Security |
|-------|----------|-----------------|
| Wi-Fi | 802.11 | Often open in labs |
| Network | UDP multicast | No authentication |
| Transport | RTPS | Plaintext, no integrity |
| ROS 2 Middleware | FastDDS / CycloneDDS | No SROS2 by default |
| Messages | geometry_msgs, sensor_msgs | No encryption |

**The core problem:** Any machine on the same subnet can:
- Discover all nodes and topics with `ros2 topic list`
- Subscribe to any sensor stream
- Publish commands to any actuator topic
- Impersonate any node

No credentials. No handshake. No authentication.

---

## 4. Pre-Lab Checklist

Run this on **both machines** before starting any attacks.

### 4.1 Verify Both Machines Are Ready

```bash
# Run on both red and blue machines
python3 verify_lab_setup.py
```

Expected on **red machine** (attacker): 29+ passed, 0 failed  
Expected on **blue machine** (victim): 24+ passed, 0 real failures  
(scapy/wireshark failures on blue are expected — blue is the victim, not attacker)

### 4.2 Connect to Isolated Lab Network

Both machines must be on `192.168.2.0/24` — **not UNT wifi**.

```bash
# Confirm your IP is on the lab network
ip addr show
# Should show something like: 192.168.2.X
```

### 4.3 Start the Blue Victim Node

On the **blue machine**:

```bash
python3 blue_victim.py
```

You should see:
```
[INFO] Blue Machine -- Simulated QCar2 Victim
[INFO] Publishing: /qcar2/imu  /qcar2/scan  /qcar2/battery  /qcar2/motor
[INFO] Listening:  /qcar2/cmd_vel
```

### 4.4 Confirm Red Machine Sees Blue's Topics

On the **red machine**:

```bash
ros2 topic list
```

Expected output:
```
/parameter_events
/qcar2/battery
/qcar2/cmd_vel
/qcar2/imu
/qcar2/motor
/qcar2/scan
/rosout
```

> **If you only see `/parameter_events` and `/rosout`:** the machines aren't seeing each other. Check they're on the same network and `ROS_DOMAIN_ID=0` on both.

### 4.5 Confirm DDS Multicast Works

```bash
# Terminal 1 — blue machine
ros2 multicast receive

# Terminal 2 — red machine
ros2 multicast send
```

Blue machine should print: `Received from ...: 'Hello World: X'`

---

## 5. Attack 1 — Rogue Node Injection

### What Is It?
An unauthorized laptop joins the network and publishes drive commands directly to `/qcar2/cmd_vel`. No credentials required — DDS accepts any publisher on the same subnet.

### The ROS Command This Demonstrates
```bash
# What the attacker is effectively doing:
rostopic pub /qcar2/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}, angular: {z: 0.3}}'
```

### Step-by-Step

**Step 1** — On the **blue machine**, watch for incoming commands:
```bash
ros2 topic echo /qcar2/cmd_vel
```
Leave this running. You will see injected commands appear here.

**Step 2** — On the **red machine**, check how many publishers currently exist:
```bash
ros2 topic info /qcar2/cmd_vel --verbose
```

**Step 3** — On the **red machine**, launch the rogue node:
```bash
python3 rogue_node.py
```

Default behavior: publishes throttle=0.1, steering=0.3 for 10 seconds.

**Step 4** — Back on the **blue machine**, observe:
- `ros2 topic echo /qcar2/cmd_vel` shows injected commands arriving
- The blue machine logs: `CMD_VEL RECEIVED throttle=+0.100 steering=+0.300`
- Running `ros2 topic info /qcar2/cmd_vel --verbose` now shows **2 publishers**

### What Students Should Record
- How long did it take from joining the network to injecting a command?
- What does `rqt_graph` show? (run `rqt_graph` on either machine)
- Could you tell the difference between legitimate and rogue commands from the victim side?

### Safety Limits Built Into the Script
- Max throttle: **0.15** (enforced in code, cannot be overridden)
- Max duration: **30 seconds**
- Sends a zero stop command automatically on exit

### Custom Options
```bash
python3 rogue_node.py --throttle 0.05 --steering 0.0 --duration 5
```

---

## 6. Attack 2 — Plaintext Packet Sniffing

### What Is It?
A passive attacker captures raw UDP packets from the air and decodes ROS 2 RTPS messages without ever joining the ROS 2 graph. The victim has no way to detect this.

### The ROS Command This Demonstrates
```bash
# What this reveals — live from the network:
rostopic echo /qcar2/imu
rostopic echo /qcar2/cmd_vel
```
...except the attacker doesn't need ROS 2 installed at all.

### Step-by-Step

**Step 1** — On the **blue machine**, start driving (simulating an operator):
```bash
# Publish continuous drive commands to simulate operator activity
ros2 topic pub /qcar2/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}, angular: {z: 0.2}}' --rate 10
```

**Step 2** — On the **red machine**, start the passive sniffer:
```bash
python3 sniffer.py --verbose
```

**Step 3** — Watch decoded cmd_vel packets appear on red machine:
```
[14:23:01] CMD_VEL CAPTURED  throttle=+0.100  steering=+0.200  src=7412
[14:23:01] IMU CAPTURED  accel=[+0.20,+0.10,+9.81]  gyro=[+0.001,-0.002,+0.040]
[14:23:02] BATTERY CAPTURED  12.43 V
```

**Step 4** — Stop the sniffer with `Ctrl+C`. Review the summary:
```
  RESULT: Drive commands successfully captured in plaintext.
  An attacker can reconstruct operator intent from passive capture.
```

**Step 5** — Advanced: run Wireshark alongside the sniffer for visual packet inspection:
```bash
# In a second terminal on red machine
sudo wireshark &
# Filter: udp portrange 7400-7600
```

### What Students Should Record
- What information could an attacker reconstruct from passively watching cmd_vel?
- How many packets per second does the sniffer see?
- Is the victim (blue machine) aware it's being sniffed? Why or why not?

### Key Teaching Point
This attack requires **zero** interaction with the victim. It's completely passive — no injected packets, no connections, nothing that could be logged or detected.

---

## 7. Attack 3 — DDS Discovery Poisoning

### What Is It?
Fake DDS participant announcements are injected into the multicast discovery channel. Each fake participant causes every real DDS node to allocate memory, attempt handshakes, and log events — exhausting CPU and memory over time.

### The ROS Command This Demonstrates
```bash
# Normal DDS discovery (what the attacker is abusing):
ros2 multicast send   # sends one legitimate announcement
# Ghost attack sends hundreds of fake ones
```

### Step-by-Step

**Step 1** — On the **blue machine**, monitor CPU and node list before the attack:
```bash
# Terminal 1 — watch CPU
top

# Terminal 2 — watch node list
watch -n 1 'ros2 node list'
```

**Step 2** — On the **red machine**, run the ghost injection (needs sudo for raw sockets):
```bash
sudo python3 dds_ghost.py --count 30 --interval 0.1
```

**Step 3** — On the **blue machine**, observe:
- CPU usage spikes during the injection burst
- `ros2 node list` may show unexpected entries
- ROS 2 daemon logs show discovery attempts for unknown GUIDs

**Step 4** — After the script finishes, measure recovery time on blue:
```bash
ros2 daemon stop && ros2 daemon start
ros2 topic list   # should return to normal
```

### What Students Should Record
- CPU % on blue machine before, during, and after the attack
- How long does recovery take after ghost injection stops?
- At what `--count` value does the blue machine become visibly sluggish?

### Safety Limits Built Into the Script
- Max ghost participants: **100** per run
- Min interval: **0.05 seconds** between packets
- Warning printed at startup about duration limits

### Custom Options
```bash
sudo python3 dds_ghost.py --count 50 --interval 0.05
```

> **Warning:** Keep burst duration under 10 seconds. Extended flooding can crash the ROS 2 daemon and require a full restart.

---

## 8. Attack 4 — Command Flood / DoS

### What Is It?
The attacker publishes to `/qcar2/cmd_vel` at a rate thousands of times faster than the legitimate operator. The DDS receive queue fills up and legitimate commands are dropped — denying the operator control of the robot.

### The ROS Command This Demonstrates
```bash
# Legitimate operator rate: ~10 Hz
ros2 topic pub /qcar2/cmd_vel ... --rate 10

# Flood rate: 1000+ Hz — buries the legitimate stream
```

### Step-by-Step

**Step 1** — On the **blue machine**, start a legitimate operator stream:
```bash
ros2 topic pub /qcar2/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}, angular: {z: 0.0}}' --rate 10
```

**Step 2** — On the **red machine**, monitor the topic rate to establish a baseline:
```bash
ros2 topic hz /qcar2/cmd_vel
# Should show ~10 Hz
```

**Step 3** — On the **red machine**, open a second terminal and launch the flood:
```bash
python3 cmd_flood.py --rate 1000 --duration 10
```

**Step 4** — Watch `ros2 topic hz` on the red machine spike dramatically:
```
average rate: 1023.412
```

**Step 5** — On the **blue machine**, observe the CMD_VEL RECEIVED log — legitimate operator commands are now buried in flood packets and the robot would respond erratically or not at all.

**Step 6** — Stop the flood (it auto-stops after `--duration` seconds). Measure how long it takes for the legitimate 10 Hz stream to re-establish itself cleanly on `ros2 topic hz`.

### What Students Should Record
- Minimum flood rate (Hz) at which legitimate control is completely lost
- How long does recovery take after flooding stops?
- What's the difference between BEST_EFFORT and RELIABLE QoS for this attack? (try `--rate 500` and note if the actual rate matches)

### Safety Limits Built Into the Script
- Throttle locked at **0.0** by default (queue saturation only, no physical movement)
- Max duration: **30 seconds**
- Max rate: **5000 Hz**
- Sends stop command on both normal exit and Ctrl+C

### Custom Options
```bash
python3 cmd_flood.py --rate 2000 --duration 5
```

---

## 9. Defense — SROS2 Hardening

After observing all four attacks, students configure SROS2 to defend against them. Run these steps on both machines.

### 9.1 Generate a Keystore

On both **red** and **blue** machines:

```bash
export ROS_SECURITY_KEYSTORE=~/sros2_keystore
ros2 security create_keystore $ROS_SECURITY_KEYSTORE
```

### 9.2 Create Keys for Each Node

```bash
# Create keys for the legitimate nodes
ros2 security create_key $ROS_SECURITY_KEYSTORE /blue_qcar2_node
ros2 security create_key $ROS_SECURITY_KEYSTORE /operator_node
```

### 9.3 Create Permission Policy

Save this as `policy.xml`:

```xml
<policy version="0.2.0">
  <enclaves>
    <enclave path="/operator_node">
      <profiles>
        <profile ns="/" node="operator_node">
          <topics publish="ALLOW" subscribe="DENY">
            <topic>qcar2/cmd_vel</topic>
          </topics>
        </profile>
      </profiles>
    </enclave>
  </enclaves>
</policy>
```

Apply it:
```bash
ros2 security create_permission \
  $ROS_SECURITY_KEYSTORE /operator_node policy.xml
```

### 9.4 Launch With Security Enabled

```bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=~/sros2_keystore

# Start blue victim with security
python3 blue_victim.py --name blue_qcar2_node
```

### 9.5 Verify Rogue Node Is Rejected

On the **red machine**, re-run the rogue node:
```bash
python3 rogue_node.py
```

Expected result:
```
[ERROR] Security: Discovered participant with no matching GUID in keystore.
```

The rogue node is silently rejected. `/qcar2/cmd_vel` receives no injected commands.

### 9.6 Verify Each Attack Is Now Blocked

| Attack | With SROS2 | Why |
|--------|-----------|-----|
| Rogue Node Injection | ✔ Blocked | Node rejected — no keystore entry |
| Packet Sniffing | ✔ Blocked | RTPS payload encrypted |
| DDS Discovery Poisoning | ✔ Blocked | Ghost GUIDs rejected by auth |
| Command Flood | ⚠ Partial | Rate limiting needed in addition |

---

## 10. Student Deliverables

Each student or pair submits the following after completing all four attack labs:

| # | Deliverable | Format |
|---|------------|--------|
| 1 | Wireshark capture showing decoded cmd_vel packets | `.pcapng` + 1-page write-up |
| 2 | Annotated `rogue_node.py` explaining each ROS 2 API call | Python file + inline comments |
| 3 | CPU plot from DDS ghost attack (before, during, after) | Screenshot + data |
| 4 | Graph of legitimate command delivery rate vs flood rate | Plot or table |
| 5 | SROS2 hardening report: keystore setup, policy XML, before/after test | 2-page report |
| 6 | Threat model diagram for the lab network | Hand-drawn or digital |

### Discussion Questions

1. How long did it take from joining the network to injecting a command in Attack 1?
2. Why is Attack 2 (sniffing) the most dangerous from a privacy perspective?
3. What is the difference between a DoS attack (Attack 4) and a takeover (Attack 1)?
4. Why does SROS2 only partially mitigate Attack 4?
5. What would TLS/DTLS add to this model that SROS2 alone doesn't provide?

---

## 11. Quick Reference

### Files on Red Machine (`~/Documents/sros/`)

| File | Purpose |
|------|---------|
| `verify_lab_setup.py` | Pre-lab environment check |
| `rogue_node.py` | Attack 1 — node injection |
| `sniffer.py` | Attack 2 — packet sniffing |
| `dds_ghost.py` | Attack 3 — DDS poisoning |
| `cmd_flood.py` | Attack 4 — command flood |

### Files on Blue Machine

| File | Purpose |
|------|---------|
| `verify_lab_setup.py` | Pre-lab environment check |
| `blue_victim.py` | Simulated QCar2 victim node |

### Files on QCar (when available)

| File | Purpose |
|------|---------|
| `verify_lab_setup.py` | Pre-lab environment check |
| `qcar2_ros2_bridge.py` | Bridges pal hardware to ROS 2 topics |

### Attack Commands Cheat Sheet

```bash
# Recon (always first)
ros2 topic list
ros2 topic info /qcar2/cmd_vel --verbose
ros2 node list

# Attack 1 — Rogue Node
python3 rogue_node.py

# Attack 2 — Sniff (passive)
python3 sniffer.py --verbose

# Attack 3 — DDS Poison (needs sudo)
sudo python3 dds_ghost.py --count 30

# Attack 4 — Flood
python3 cmd_flood.py --rate 1000 --duration 10

# Monitor topic rate (useful during Attack 4)
ros2 topic hz /qcar2/cmd_vel

# Read live sensor data (useful during Attack 2)
ros2 topic echo /qcar2/imu
ros2 topic echo /qcar2/battery
```

### Environment Variables (must match on all machines)

```bash
export ROS_DOMAIN_ID=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
source /opt/ros/humble/setup.bash
```

---

## 12. Troubleshooting

### `ros2 topic list` only shows `/parameter_events` and `/rosout`

Both machines aren't seeing each other. Check in order:
```bash
# 1. Are you on the same network?
ip addr show   # both should be 192.168.2.X

# 2. Do you have the same domain ID?
echo $ROS_DOMAIN_ID   # must be 0 on both

# 3. Is FASTDDS set?
echo $FASTDDS_BUILTIN_TRANSPORTS   # must be UDPv4 on both

# 4. Multicast test
ros2 multicast receive   # blue machine
ros2 multicast send      # red machine
```

### `import rclpy` fails with `librcl_action.so` error

```bash
# Fix library paths
echo "/opt/ros/humble/lib" | sudo tee /etc/ld.so.conf.d/ros-humble.conf
echo "/opt/ros/humble/lib/x86_64-linux-gnu" | sudo tee -a /etc/ld.so.conf.d/ros-humble.conf
sudo ldconfig
python3 -c "import rclpy; print('rclpy OK')"
```

### Scapy raw socket permission denied

```bash
# Find the real python3 binary (not the symlink)
readlink -f $(which python3)
# Apply capability to the real binary path
sudo setcap cap_net_raw,cap_net_admin+eip /usr/bin/python3.10
# Verify
getcap /usr/bin/python3.10
```

### `sudo apt install ros-humble-desktop` fails with GPG error

```bash
# curl missing? Install it first
sudo apt install -y curl gnupg2

# Re-download the key with proper dearmor conversion
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | \
  sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

sudo apt update
sudo apt install -y ros-humble-desktop
```

### apt is locked / stuck after unexpected shutdown

```bash
# Check if apt is actually still running
ps aux | grep apt

# If nothing is running, remove stale locks
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock

# Repair any half-configured packages
sudo dpkg --configure -a
sudo apt update
sudo apt upgrade -y
```

### Blue victim node not logging received commands

```bash
# Confirm blue_victim.py is actually running
ps aux | grep blue_victim

# Confirm red machine is on same ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID   # must be 0

# Check topic is visible from red machine
ros2 topic list | grep qcar2
```

### `ros2 --version` warning in verify script

This is a known quirk in some ROS 2 Humble installs on Ubuntu 20.04/22.04. It returns exit code 2 even though everything works. If `ros2 topic list`, `rclpy`, and the daemon all pass — this warning is harmless and can be ignored.

---

## Appendix: Machine Setup Summary

### What Each Machine Needed (for reference)

**Red Machine (OptiPlex-9020, Ubuntu 22.04)**
- ROS 2 Humble via apt
- `ldconfig` fix for library paths
- `setcap` on `/usr/bin/python3.10` for Scapy raw sockets (not the symlink)
- `cyclonedds` via `pip install cyclonedds --extra-index-url https://pypi.org/simple/`
- Wireshark with non-root capture enabled
- `ROS_DOMAIN_ID=0` and `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` in `~/.bashrc`

**Blue Machine (Aspire-XC-704G, Ubuntu 22.04)**
- `curl` installed first (was missing — caused silent GPG key failure)
- ROS 2 Humble via apt (had to be reinstalled after upgrade removed it)
- GPG key downloaded with `gpg --dearmor` (not raw curl pipe)
- `ldconfig` fix for library paths
- `ROS_DOMAIN_ID=0` and `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` in `~/.bashrc`
- Does **not** need scapy/wireshark/cyclonedds (victim only)

**QCar (Jetson, Ubuntu 20.04, user: nvidia)**
- ROS 2 Humble already installed by Quanser
- `ldconfig` fix using `aarch64-linux-gnu` path (not x86_64)
- `ROS_DOMAIN_ID=0` and `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` in `~/.bashrc`
- Run `qcar2_ros2_bridge.py` in tmux before lab sessions
- Does **not** need scapy/wireshark (victim only)
- `numpy` pinned at `1.23` by Quanser — do not upgrade

---

*Generated for UNT Summer Security Project 2026*  
*QCar ROS 2 Security Lab — Category 1 & 2*
