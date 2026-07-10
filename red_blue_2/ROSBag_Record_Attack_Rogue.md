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
