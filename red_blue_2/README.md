
## Playing Back the Bags

Playback allows re-publishing all the recorded messages on the same ROS 2 topics, at the same timing, as if the attack were happening live again — but without needing the red machine to run any attack scripts.

**Why it's useful:**

- **Runtime monitor development** — you can develop and test your security monitor against the recorded attack without needing both machines running live
- **Replay attack demo** — playing back the rogue attack bag is itself Attack 5 from the SecureVLA project (replay attack)
- **LLM analysis** — play back a bag and feed the topic data to the LLM security analyst in real time
- **Repeatable results** — same attack, same timing, same data every time you play it back

**Example:**
```bash
# Terminal 1 — play back the rogue attack recording
ros2 bag play ~/bags/attack_rogue_001

# Terminal 2 — watch the injected commands replay exactly as they were recorded
ros2 topic echo /qcar2/cmd_vel

# Terminal 3 — check the rate
ros2 topic hz /qcar2/cmd_vel
```

The blue machine will receive the replayed commands just as if the red machine were running rogue_node.py right now.

---

## Building the Session Index

The session index is a single JSON file that acts as a **table of contents** for your entire dataset. It lists every bag, its label, duration, and path in one place.

**Why it's useful:**

- Makes the dataset self-documenting for GitHub
- The LLM analyst and runtime monitor can read it to know which bags to process
- Anyone cloning your repo knows exactly what's in the dataset without opening each bag individually
- Required for the SecureVLA-Car final deliverable (dataset package)

```json
{
  "project": "SecureVLA-Car",
  "platform": "blue_victim_simulated",
  "ros_version": "humble",
  "date": "2026-07-08",
  "total_sessions": 5,
  "sessions": [
    {
      "id": "normal_run_001",
      "label": "normal",
      "duration_s": 53,
      "path": "bags/normal_run_001"
    },
    {
      "id": "attack_rogue_001",
      "label": "cmd_vel_spoofing",
      "duration_s": 30,
      "attack_offset_s": 10,
      "path": "bags/attack_rogue_001"
    },
    {
      "id": "attack_sniffer_001",
      "label": "plaintext_sniffing",
      "duration_s": 50,
      "attack_offset_s": 10,
      "path": "bags/attack_sniffer_001"
    },
    {
      "id": "attack_ghost_001",
      "label": "dds_discovery_poisoning",
      "duration_s": 33,
      "attack_offset_s": 10,
      "path": "bags/attack_ghost_001"
    },
    {
      "id": "attack_flood_001",
      "label": "command_flooding",
      "duration_s": 35,
      "attack_offset_s": 15,
      "path": "bags/attack_flood_001"
    }
  ]
}
```
