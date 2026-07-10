## Rosbag Recording — Attack 1: Rogue Node Injection

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
  -o ~/bags/attack_rogue_001 \
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

### Red Machine — Terminal 1
Launch the rogue node:
```bash
python3 ~/Documents/sros/rogue_node.py
```

You will see:
```
ROGUE NODE ACTIVE -- Attack 1: Node Injection
  Topic    : /qcar2/cmd_vel
  Throttle : +0.10
  Steering : +0.30
  Duration : 10s
```

The script runs for **10 seconds automatically** then stops and sends a stop command.

---

### Watch Blue Machine Terminal 1
While the attack runs you should see:
```
[WARN] CMD_VEL RECEIVED  throttle=+0.100  steering=+0.300  total_received=1
[WARN] CMD_VEL RECEIVED  throttle=+0.100  steering=+0.300  total_received=2
...
```
This confirms injected commands are reaching the victim.

---

### Wait another 10 seconds
After the rogue node stops let the recording continue for 10 more seconds to capture the recovery period.

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
ros2 bag info ~/bags/attack_rogue_001
```

You should now see `/qcar2/cmd_vel` in the topic list with approximately 100 messages — those are the injected commands captured in the bag.

Here's the metadata label for the rogue attack. Run this on the **blue machine**:

```bash
cat > ~/bags/attack_rogue_001/metadata.json << 'EOF'
{
  "label": "cmd_vel_spoofing",
  "description": "Rogue node injecting throttle=0.1 steering=0.3 at 10 Hz for 10 seconds",
  "duration_seconds": 30,
  "attack_start_offset_seconds": 10,
  "attack_duration_seconds": 10,
  "packets_injected": 99,
  "throttle": 0.1,
  "steering": 0.3,
  "rate_hz": 10,
  "machine": "blue_victim_simulated",
  "ros_domain_id": 0,
  "date": "2026-07-08",
  "attack_scripts": ["rogue_node.py --throttle 0.1 --steering 0.3 --duration 10"]
}
EOF
```

Verify it saved correctly:
```bash
cat ~/bags/attack_rogue_001/metadata.json
```

Then check your bags directory has everything so far:
```bash
ls ~/bags/
```

You should see:
```
normal_run_001/
attack_rogue_001/
attack_sniffer_001/
```
