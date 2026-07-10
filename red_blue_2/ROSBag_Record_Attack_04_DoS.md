## Rosbag Recording — Attack 4: Command Flood / DoS

**What you need open:**
- Blue machine: 3 terminals
- Red machine: 1 terminal

---

### Blue Machine — Terminal 1
Start the victim node if not already running:
```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```
Leave this running the entire time.

---

### Blue Machine — Terminal 2
Start recording:
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
You should see all 6 topics subscribed. Leave this running.

---

### Blue Machine — Terminal 3
Start monitoring the topic rate — this is how you see the attack happening in real time:
```bash
ros2 topic hz /qcar2/cmd_vel
```
Note the baseline rate before the attack starts. It should show nothing or very low since no one is publishing to cmd_vel yet.

---

### Wait 10 seconds
Let the recording capture 10 seconds of normal behavior before the attack starts.

---

### Red Machine — Terminal 1
Start a legitimate operator stream first to establish a baseline:
```bash
ros2 topic pub /qcar2/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}, angular: {z: 0.0}}' --rate 10
```
Leave this running. Blue machine Terminal 3 should now show:
```
average rate: 10.0
```

---

### Wait 5 seconds
Let the legitimate 10 Hz rate establish in the recording.

---

### Red Machine — open a second terminal
Launch the flood alongside the legitimate stream:
```bash
python3 ~/Documents/sros/cmd_flood.py --rate 1000 --duration 10
```

You will see:
```
  Attack 4: Command Flood / Denial of Service
  Topic    : /qcar2/cmd_vel
  Rate     : 1000 Hz
  Duration : 10s
  Throttle : 0.00  (0.0 = DoS only, no motion)

  Flooding...
  [  1.0s]  sent=  1000  actual rate=1000 Hz
  [  2.0s]  sent=  2000  actual rate=1000 Hz
  ...
  [10.0s]  sent= 10000  actual rate=1000 Hz

  Flood complete.
  Stop command sent.
```

---

### Watch Blue Machine Terminal 3
The topic rate monitor should spike dramatically during the flood:
```
# Before flood
average rate: 10.0

# During flood
average rate: 1023.412

# After flood stops
average rate: 10.0
```

This shows the legitimate 10 Hz operator stream getting completely buried.

---

### Watch Blue Machine Terminal 1
During the flood you should see CMD_VEL RECEIVED warnings coming in much faster than normal:
```
[WARN] CMD_VEL RECEIVED  throttle=+0.000  steering=+0.000  total_received=10100
[WARN] CMD_VEL RECEIVED  throttle=+0.000  steering=+0.000  total_received=10101
...
```

---

### Wait another 10 seconds
After the flood stops let the recording continue for 10 more seconds to capture the recovery period and confirm the legitimate 10 Hz rate resumes.

---

### Red Machine — Terminal 1
Stop the legitimate operator stream:
```
Ctrl+C
```

---

### Blue Machine — Terminal 2
Stop the recording:
```
Ctrl+C
```

---

### Blue Machine — Terminal 2
Verify the recording:
```bash
ros2 bag info ~/bags/attack_flood_001
```

The `/qcar2/cmd_vel` message count should be very high — around 10,000+ messages from the flood versus the ~100 you would expect from a normal 30-second session at 10 Hz.

---

### Blue Machine — Terminal 2
Create the metadata label:
```bash
cat > ~/bags/attack_flood_001/metadata.json << 'EOF'
{
  "label": "command_flooding",
  "description": "cmd_vel flooded at 1000 Hz for 10 seconds alongside legitimate 10 Hz operator stream",
  "duration_seconds": 35,
  "attack_start_offset_seconds": 15,
  "attack_duration_seconds": 10,
  "flood_rate_hz": 1000,
  "legitimate_rate_hz": 10,
  "flood_throttle": 0.0,
  "packets_sent": 10000,
  "machine": "blue_victim_simulated",
  "ros_domain_id": 0,
  "date": "2026-07-08",
  "attack_scripts": [
    "ros2 topic pub /qcar2/cmd_vel --rate 10 (legitimate)",
    "cmd_flood.py --rate 1000 --duration 10 (flood)"
  ]
}
EOF
```

---

### Blue Machine — check all bags are complete
```bash
ls ~/bags/
du -sh ~/bags/*/
```

You should see all four sessions:
```
normal_run_001/
attack_rogue_001/
attack_sniffer_001/
attack_ghost_001/
attack_flood_001/
```
