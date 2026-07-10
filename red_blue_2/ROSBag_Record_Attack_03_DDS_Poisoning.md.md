## Rosbag Recording — Attack 3: DDS Discovery Poisoning

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
  -o ~/bags/attack_ghost_001 \
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
Launch the ghost injection — needs sudo for raw sockets:

Note: sudo may not be needed

```bash
sudo python3 ~/Documents/sros/dds_ghost.py --count 30 --interval 0.1 
```

You will see:
```
  Attack 3: DDS Discovery Protocol Poisoning
  Target    : 239.255.0.1:7400 (SPDP multicast)
  Ghosts    : 30 fake participants
  Interval  : 0.10s between packets
  Duration  : ~3.0s
```

Then each ghost participant prints as it's injected:
```
  [001/030] GUID: a3f2c1...
  [002/030] GUID: 7b91e4...
  ...
  [030/030] GUID: 2d45f8...
  Done. Sent 30 ghost SPDP announcements in 3.0s
```

The script finishes in about **3 seconds** automatically.

---

### Watch Blue Machine Terminal 1
During the injection you should see warnings appearing:
```
[WARN] New publisher discovered on topic '/qcar2/cmd_vel',
offering incompatible QoS. No messages will be received from it.
Last incompatible policy: RELIABILITY
```
This confirms the blue machine's DDS stack is processing the ghost announcements.

---

### Wait another 20 seconds
After the ghost injection finishes let the recording continue for 20 more seconds to capture the recovery period. The recovery is important — it shows how long the victim takes to return to normal after the attack.

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
ros2 bag info ~/bags/attack_ghost_001
```

The key thing to look for is the `/rosout` message count — it should be higher than in the normal run because the DDS ghost warnings were logged there during the attack.

---

### Blue Machine — Terminal 2
Create the metadata label:
```bash
cat > ~/bags/attack_ghost_001/metadata.json << 'EOF'
{
  "label": "dds_discovery_poisoning",
  "description": "30 ghost SPDP participants injected at 0.1s intervals via raw UDP multicast",
  "duration_seconds": 33,
  "attack_start_offset_seconds": 10,
  "attack_duration_seconds": 3,
  "ghost_count": 30,
  "ghost_interval_seconds": 0.1,
  "target_multicast": "239.255.0.1:7400",
  "machine": "blue_victim_simulated",
  "ros_domain_id": 0,
  "date": "2026-07-08",
  "attack_scripts": ["dds_ghost.py --count 30 --interval 0.1"]
}
EOF
```
