## Step 1 — Connect both machines to the lab network

Both machines must be on `192.168.2.0` — not UNT wifi.

Confirm on each machine:
```bash
ip addr show
# Should show 192.168.2.X
```

---

## Step 2 — Open terminals

* **Blue machine — open 3 terminals**
* **Red machine — open 1 terminal**

---

## Step 3 — Source ROS 2 on both machines if needed

Run this in **every terminal** on both machines:
```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
```

---

## Step 4 — Start the victim node on blue machine (Terminal 1)

```bash
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```

Leave this running. You should see:
```
[INFO] Blue Machine -- Simulated QCar2 Victim
[INFO] Publishing: /qcar2/imu  /qcar2/scan  /qcar2/battery  /qcar2/motor
[INFO] Listening:  /qcar2/cmd_vel
```

---

## Step 5 — Confirm red machine sees blue's topics

On the **red machine**:
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

**Stop if you only see `/parameter_events` and `/rosout`**

---

## Step 6 — Start rosbag recording on blue machine (Terminal 2)

```bash
mkdir -p ~/bags
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

---

## Step 7 — Wait 30 seconds, then stop

**Do nothing on either machine.** Just let it record.

After 30 seconds press **Ctrl+C** in Terminal 2 on the blue machine.

---

## Step 8 — Verify the recording

```bash
ros2 bag info ~/bags/normal_run_001
```
