# ROS 2 Rosbag Recording Guide
## SecureVLA-Car Security Lab — Labeled Dataset Collection

> **Purpose:** Record normal and attack-labeled rosbag sessions from the simulated  
> red/blue machine setup or the physical QCar2. These bags form the foundation  
> of the SecureVLA security dataset.

---

## Table of Contents

1. [What Is a Rosbag?](#1-what-is-a-rosbag)
2. [Before You Start](#2-before-you-start)
3. [Session A — Normal Run](#3-session-a--normal-run)
4. [Session B — Rogue Node Injection](#4-session-b--rogue-node-injection)
5. [Session C — Command Flood / DoS](#5-session-c--command-flood--dos)
6. [Session D — DDS Discovery Poisoning](#6-session-d--dds-discovery-poisoning)
7. [Inspecting Your Bags](#7-inspecting-your-bags)
8. [Playing Back a Recording](#8-playing-back-a-recording)
9. [Replay Attack Demo](#9-replay-attack-demo)
10. [Dataset Index](#10-dataset-index)
11. [On the Physical QCar2](#11-on-the-physical-qcar2)
12. [Quick Reference](#12-quick-reference)

---

## 1. What Is a Rosbag?

A rosbag is a file that records every ROS 2 message published on specified topics,
with timestamps, and lets you play it back later as if the robot were live.

```
Blue machine running   →   ros2 bag record   →   .db3 file on disk
                                                        ↓
Analysis laptop        ←   ros2 bag play     ←   same .db3 file
```

**Why it matters for this project:**
- Capture normal driving behavior as a baseline
- Capture attacks in progress as labeled evidence
- Play back attacks later without needing live hardware
- Feed structured windows to the LLM security analyst
- Export VLA-ready records for the SecureVLA dataset

---

## 2. Before You Start

### 2.1 Check Available Disk Space

```bash
# On whichever machine will store the bags (blue machine or QCar)
df -h ~
```

You need at least **500 MB free** for a 30-second multi-topic session.
If space is low, choose a different storage location:

```bash
# Store bags on an external drive or different partition
ros2 bag record -o /media/usb/bags/session_001 ...
```

### 2.2 Create a Bags Directory

```bash
mkdir -p ~/bags
ls ~/bags   # should be empty to start
```

### 2.3 Confirm Topics Are Live

On the **blue machine**, start the victim node if not already running:

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

On the **red machine**, confirm topics are visible:

```bash
ros2 topic list
```

Expected:
```
/qcar2/battery
/qcar2/cmd_vel
/qcar2/imu
/qcar2/motor
/qcar2/scan
/rosout
```

> **If topics are missing:** blue_victim.py is not running. Start it first.

### 2.4 Topics We Record

| Topic | Type | Rate | Why |
|-------|------|------|-----|
| `/qcar2/cmd_vel` | geometry_msgs/Twist | 10 Hz | Drive commands — primary attack target |
| `/qcar2/imu` | sensor_msgs/Imu | 50 Hz | Accelerometer + gyroscope |
| `/qcar2/scan` | sensor_msgs/LaserScan | 10 Hz | LiDAR — environment map |
| `/qcar2/battery` | std_msgs/Float32 | 1 Hz | Power state |
| `/qcar2/motor` | std_msgs/String | 10 Hz | Encoder, tach, current |
| `/rosout` | rcl_interfaces/Log | variable | ROS 2 system logs — security events |

---

## 3. Session A — Normal Run

Records the robot publishing sensor data with **no attack active**.
This is your baseline — the "healthy" state to compare against.

### Blue Machine — Terminal 1 (victim node)

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

Leave this running throughout the session.

### Blue Machine — Terminal 2 (recorder)

```bash
ros2 bag record \
  -o ~/bags/normal_run_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /qcar2/motor \
  /rosout
```

You should see:
```
[INFO] Listening for topics...
[INFO] Subscribed to topic '/qcar2/cmd_vel'
[INFO] Subscribed to topic '/qcar2/imu'
[INFO] Subscribed to topic '/qcar2/scan'
[INFO] Subscribed to topic '/qcar2/battery'
[INFO] Subscribed to topic '/qcar2/motor'
[INFO] Subscribed to topic '/rosout'
```

### Red Machine — do nothing

No attacks. Let the session run for **30 seconds**.

### Stop Recording

Press **Ctrl+C** in Terminal 2 on the blue machine.

```
[INFO] Writing remaining messages...
[INFO] Bag closed.
```

### Label This Session

```bash
# Create a metadata file alongside the bag
cat > ~/bags/normal_run_001/metadata.json << 'EOF'
{
  "label": "normal",
  "description": "Normal operation, no attack active",
  "duration_seconds": 30,
  "machine": "blue_victim",
  "ros_domain_id": 0,
  "date": "2026-07-02",
  "attack_scripts": []
}
EOF
```

---

## 4. Session B — Rogue Node Injection

Records the robot while an **unauthorized node injects drive commands**.

### Blue Machine — Terminal 1 (victim node)

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

### Blue Machine — Terminal 2 (recorder)

```bash
ros2 bag record \
  -o ~/bags/attack_rogue_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /qcar2/motor \
  /rosout
```

### Red Machine — start the attack (10 seconds after recording starts)

```bash
python3 ~/Documents/sros/rogue_node.py
```

Wait for the rogue node to finish its 10-second run. Then let the
recording continue for another 10 seconds to capture the recovery period.

**Total session: ~30 seconds**
- 0-10s: normal (before attack)
- 10-20s: rogue node injecting commands
- 20-30s: recovery (after attack)

### Stop Recording

Press **Ctrl+C** in Terminal 2 on the blue machine.

### Label This Session

```bash
cat > ~/bags/attack_rogue_001/metadata.json << 'EOF'
{
  "label": "cmd_vel_spoofing",
  "description": "Rogue node injecting throttle=0.1 steering=0.3 at 10 Hz",
  "duration_seconds": 30,
  "attack_start_offset_seconds": 10,
  "attack_duration_seconds": 10,
  "machine": "blue_victim",
  "ros_domain_id": 0,
  "date": "2026-07-02",
  "attack_scripts": ["rogue_node.py --throttle 0.1 --steering 0.3"]
}
EOF
```

---

## 5. Session C — Command Flood / DoS

Records the robot while the **command channel is flooded** at 1000 Hz.

### Blue Machine — Terminal 1 (victim node)

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

### Blue Machine — Terminal 2 (recorder)

```bash
ros2 bag record \
  -o ~/bags/attack_flood_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /qcar2/motor \
  /rosout
```

### Blue Machine — Terminal 3 (monitor topic rate during attack)

```bash
ros2 topic hz /qcar2/cmd_vel
```

Watch this number spike from ~10 Hz to 1000+ Hz during the attack.

### Red Machine — start the flood (10 seconds after recording starts)

```bash
python3 ~/Documents/sros/cmd_flood.py --rate 1000 --duration 10
```

### Stop Recording

Press **Ctrl+C** in Terminal 2 after about 30 seconds total.

### Label This Session

```bash
cat > ~/bags/attack_flood_001/metadata.json << 'EOF'
{
  "label": "command_flooding",
  "description": "cmd_vel flooded at 1000 Hz for 10 seconds, throttle=0.0",
  "duration_seconds": 30,
  "attack_start_offset_seconds": 10,
  "attack_duration_seconds": 10,
  "flood_rate_hz": 1000,
  "machine": "blue_victim",
  "ros_domain_id": 0,
  "date": "2026-07-02",
  "attack_scripts": ["cmd_flood.py --rate 1000 --duration 10"]
}
EOF
```

---

## 6. Session D — DDS Discovery Poisoning

Records the robot while **ghost DDS participants** are injected.

### Blue Machine — Terminal 1 (victim node)

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

### Blue Machine — Terminal 2 (recorder)

```bash
ros2 bag record \
  -o ~/bags/attack_ghost_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /qcar2/motor \
  /rosout
```

### Red Machine — start ghost injection (10 seconds after recording starts)

```bash
sudo python3 ~/Documents/sros/dds_ghost.py --count 30 --interval 0.1
```

### Stop Recording

Press **Ctrl+C** in Terminal 2 after about 30 seconds total.

### Label This Session

```bash
cat > ~/bags/attack_ghost_001/metadata.json << 'EOF'
{
  "label": "dds_discovery_poisoning",
  "description": "30 ghost SPDP participants injected at 0.1s intervals",
  "duration_seconds": 30,
  "attack_start_offset_seconds": 10,
  "ghost_count": 30,
  "machine": "blue_victim",
  "ros_domain_id": 0,
  "date": "2026-07-02",
  "attack_scripts": ["dds_ghost.py --count 30 --interval 0.1"]
}
EOF
```

---

## 7. Inspecting Your Bags

After recording, inspect each bag to confirm it captured data correctly.

```bash
# Check all bags at once
for bag in ~/bags/*/; do
  echo "=== $bag ==="
  ros2 bag info "$bag"
  echo ""
done
```

Or inspect a single bag:

```bash
ros2 bag info ~/bags/normal_run_001
```

Expected output:
```
Files:             normal_run_001_0.db3
Bag size:          2.4 MiB
Duration:          30.005s
Start:             Jul  2 2026 13:45:12
End:               Jul  2 2026 13:45:42
Messages:          1823
Topic information:
  Topic: /qcar2/cmd_vel  | Type: geometry_msgs/msg/Twist   | Count: 300
  Topic: /qcar2/imu      | Type: sensor_msgs/msg/Imu       | Count: 1500
  Topic: /qcar2/scan     | Type: sensor_msgs/msg/LaserScan | Count: 300
  Topic: /qcar2/battery  | Type: std_msgs/msg/Float32      | Count: 30
  Topic: /qcar2/motor    | Type: std_msgs/msg/String       | Count: 300
  Topic: /rosout         | Type: rcl_interfaces/msg/Log    | Count: 12
```

**What to check:**
- Duration matches your intended session length
- All 6 topics appear in the topic list
- Message counts look reasonable (imu should be ~5x cmd_vel rate)
- Bag size is non-zero

---

## 8. Playing Back a Recording

Playback re-publishes all messages on the same topics at the original timing.
Use this to replay attacks without needing live hardware.

### Basic Playback

```bash
# Terminal 1 — play the bag
ros2 bag play ~/bags/attack_rogue_001

# Terminal 2 — watch the topics replay in real time
ros2 topic echo /qcar2/cmd_vel

# Terminal 3 — check the replay rate
ros2 topic hz /qcar2/cmd_vel
```

### Play at Different Speeds

```bash
# Play at half speed (useful for analysis)
ros2 bag play ~/bags/attack_flood_001 --rate 0.5

# Play at double speed (useful for long sessions)
ros2 bag play ~/bags/normal_run_001 --rate 2.0
```

### Play Only Specific Topics

```bash
# Only replay the command channel
ros2 bag play ~/bags/attack_rogue_001 --topics /qcar2/cmd_vel
```

### Loop Playback

```bash
# Keep replaying for continuous testing
ros2 bag play ~/bags/attack_rogue_001 --loop
```

---

## 9. Replay Attack Demo

This demonstrates **Attack 5 from the SecureVLA project** — replaying old
legitimate commands as a new attack during a live session.

### Step 1 — Record a legitimate session first

```bash
ros2 bag record -o ~/bags/legitimate_session /qcar2/cmd_vel
# Let it run for 15 seconds, then Ctrl+C
```

### Step 2 — Start a new live session on blue machine

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

### Step 3 — Replay the old session as an attack

```bash
# On red machine — inject the old legitimate commands into the live session
ros2 bag play ~/bags/legitimate_session --topics /qcar2/cmd_vel --loop
```

### What Makes This an Attack

The blue machine receives commands but their timestamps are from the past.
A properly configured security monitor should detect:
- Message timestamps that don't match current system time
- Commands arriving from an unexpected publisher (the bag player node)
- Repeated identical command sequences

### Stop the Replay Attack

```bash
# Ctrl+C on the ros2 bag play terminal
```

---

## 10. Dataset Index

After recording multiple sessions, maintain an index for easy reference.

```bash
# Generate a session index
cat > ~/bags/session_index.json << 'EOF'
{
  "project": "SecureVLA-Car",
  "platform": "blue_victim_simulated",
  "ros_version": "humble",
  "sessions": [
    {
      "id": "normal_run_001",
      "label": "normal",
      "duration_s": 30,
      "path": "~/bags/normal_run_001"
    },
    {
      "id": "attack_rogue_001",
      "label": "cmd_vel_spoofing",
      "duration_s": 30,
      "attack_offset_s": 10,
      "path": "~/bags/attack_rogue_001"
    },
    {
      "id": "attack_flood_001",
      "label": "command_flooding",
      "duration_s": 30,
      "attack_offset_s": 10,
      "path": "~/bags/attack_flood_001"
    },
    {
      "id": "attack_ghost_001",
      "label": "dds_discovery_poisoning",
      "duration_s": 30,
      "attack_offset_s": 10,
      "path": "~/bags/attack_ghost_001"
    }
  ]
}
EOF
```

List all bags and their sizes:

```bash
du -sh ~/bags/*/
```

---

## 11. On the Physical QCar2

The process is identical on the QCar, with two differences:

### Difference 1 — Start the bridge first

```bash
# QCar Terminal 1 — bridge must be running before recording
python3 ~/Documents/Quanser/summer_2026/sros/qcar2_ros2_bridge.py

# QCar Terminal 2 — then record
ros2 bag record \
  -o ~/bags/qcar2_normal_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /rosout
```

### Difference 2 — Check disk space on the Jetson first

```bash
df -h ~
# Jetson has limited storage — keep sessions short (30s) or use USB drive
```

### Difference 3 — Copy bags off the QCar when done

```bash
# From your laptop — copy bags from QCar to local machine
scp -r nvidia@<qcar-ip>:~/bags/ ~/qcar_bags/
```

---

## 12. Quick Reference

### Record Commands

```bash
# Record all topics
ros2 bag record -a -o ~/bags/session_name

# Record specific topics
ros2 bag record -o ~/bags/session_name \
  /qcar2/cmd_vel /qcar2/imu /qcar2/scan /qcar2/battery /qcar2/motor /rosout

# Stop recording
Ctrl+C
```

### Inspect Commands

```bash
# Bag info
ros2 bag info ~/bags/session_name

# List all bags
ls ~/bags/

# Check sizes
du -sh ~/bags/*/
```

### Playback Commands

```bash
# Basic playback
ros2 bag play ~/bags/session_name

# Half speed
ros2 bag play ~/bags/session_name --rate 0.5

# Specific topics only
ros2 bag play ~/bags/session_name --topics /qcar2/cmd_vel

# Loop
ros2 bag play ~/bags/session_name --loop
```

### Session Checklist

Before each recording session:
- [ ] blue_victim.py running (or QCar bridge running)
- [ ] `ros2 topic list` shows all 6 topics
- [ ] Disk space checked (`df -h ~`)
- [ ] Bags directory exists (`mkdir -p ~/bags`)
- [ ] Both machines on `192.168.2.0` isolated network
- [ ] `ROS_DOMAIN_ID=0` on both machines

After each recording session:
- [ ] `ros2 bag info` confirms all topics captured
- [ ] `metadata.json` created with label and description
- [ ] `session_index.json` updated
- [ ] Bag size non-zero

### Label Reference (from SecureVLA project)

| Label | Attack Script | Description |
|-------|--------------|-------------|
| `normal` | none | Baseline healthy operation |
| `cmd_vel_spoofing` | rogue_node.py | Unauthorized drive commands injected |
| `command_flooding` | cmd_flood.py | cmd_vel flooded at 1000+ Hz |
| `dds_discovery_poisoning` | dds_ghost.py | Ghost DDS participants injected |
| `replay_attack` | ros2 bag play | Old commands replayed as new attack |
| `scan_injection` | TBD | Altered LiDAR data published |

---

*SecureVLA-Car Project — UNT Summer 2026*  
*Rosbag Recording Guide v1.0*
