## Rosbag Recording — Attack 2: Plaintext Packet Sniffing

**What you need open:**
- Blue machine: 2 terminals
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
  -o ~/bags/attack_sniffer_001 \
  /qcar2/cmd_vel \
  /qcar2/imu \
  /qcar2/scan \
  /qcar2/battery \
  /qcar2/motor \
  /rosout
```
You should see all 6 topics subscribed. Leave this running.

---

### Wait 10 seconds
Let the recording capture 10 seconds of normal behavior before the attack starts.

---

### Blue Machine — Terminal 1
In a **new tab** on the blue machine, start publishing operator drive commands to give the sniffer something to capture:
```bash
ros2 topic pub /qcar2/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}, angular: {z: 0.2}}' --rate 10
```
Leave this running — it simulates the operator driving the robot.

---

### Red Machine — Terminal 1
Launch the sniffer:
```bash
python3 ~/Documents/sros/sniffer.py --verbose
```

You will see:
```
  Attack 2: Plaintext Packet Sniffing
  Interface : auto
  Duration  : 30s
  Filter    : UDP ports 7400-7600 (DDS/RTPS)
  Have the operator drive the QCar during capture.
```

Then decoded packets start appearing:
```
[14:36:xx] CMD_VEL CAPTURED  throttle=+0.100  steering=+0.200  src=7412
[14:36:xx] IMU CAPTURED  accel=[+0.20,+0.10,+9.81]  gyro=[+0.001,-0.002,+0.040]
[14:36:xx] BATTERY CAPTURED  12.43 V
```

The sniffer runs for **30 seconds automatically** then prints a summary and stops.

---

### Watch the Sniffer Summary
After 30 seconds you will see:
```
  Sniffer Summary
  Duration       : 30.0s
  RTPS packets   : 100
  cmd_vel decoded: 40
  IMU decoded    : 0
  Battery decoded: 0

  RESULT: Drive commands successfully captured in plaintext.
  An attacker can reconstruct operator intent from passive capture.
```

---

### Blue Machine — Terminal 1 (operator stream)
Stop the operator drive commands:
```
Ctrl+C
```

---

### Wait another 10 seconds
Let the recording continue for 10 more seconds after the sniffer stops to capture the recovery period.

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
ros2 bag info ~/bags/attack_sniffer_001
```

This time `/qcar2/cmd_vel` should appear with messages from the operator stream you started. The sniffer itself is passive — it doesn't add messages to the bag — but the bag captures the plaintext traffic that the sniffer was decoding.

---

### Blue Machine — Terminal 2
Create the metadata label:
```bash
cat > ~/bags/attack_sniffer_001/metadata.json << 'EOF'
{
  "label": "plaintext_sniffing",
  "description": "Passive sniffer captured cmd_vel, IMU, battery from raw UDP",
  "duration_seconds": 50,
  "attack_start_offset_seconds": 10,
  "attack_duration_seconds": 30,
  "machine": "blue_victim_simulated",
  "ros_domain_id": 0,
  "date": "2026-07-08",
  "attack_scripts": ["sniffer.py --verbose"],
  "note": "Sniffer is passive — no packets injected. Bag captures what attacker decoded."
}
EOF
```
