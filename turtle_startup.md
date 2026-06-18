# TurtleBot4 Startup Checklist

## Equipment
- TurtleBot4 robot (IP: **192.168.2.144**)
- Ubuntu laptop (IP may vary — check with `ip addr show`)
- Windows Terminal or SSH client

---

## Step 1 — Power On the Turtle
1. Place the turtle on the dock if not already charged
2. Press the **power button** on the Create 3 base to turn it on
3. Wait for the startup chimes
4. Wait for the display to show the IP address: **192.168.2.144**
5. Confirm all LED lights are on (full battery) or at least 3+ lights

---

## Step 2 — Verify Create 3 is Connected to WiFi
1. Open a browser and go to: `http://192.168.2.144:8080`
2. Click the **Application** tab
3. Confirm:
   - ROS 2 Domain ID = `0`
   - RMW_IMPLEMENTATION = `rmw_fastrtps_cpp`
   - Fast DDS discovery server = **disabled**
4. If Create 3 is not connected to WiFi, click **Connect** tab and enter WiFi credentials (2.4 GHz only)
5. Wait for happy chimes confirming WiFi connection

---

## Step 3 — SSH into the Turtle
Open a terminal on the Ubuntu laptop and run:
```bash
ssh ubuntu@192.168.2.144
```

---

## Step 4 — Start the Bringup
In the SSH session to the turtle:
```bash
ros2 launch turtlebot4_bringup standard.launch.py
```
Wait for this message: `[turtlebot4_node-1]: Turtlebot4 standard running.`

Leave this terminal running — do NOT close it.

---

## Step 5 — Disable EStop (if turtle won't move)
Open a **new** SSH session to the turtle:
```bash
ssh ubuntu@192.168.2.144
```
Then run:
```bash
ros2 service call /e_stop irobot_create_msgs/srv/EStop "{e_stop_on: false}"
```
You should see: `Set system E-Stop OFF, enabling motor power`

---

## Step 6 — Undock the Turtle
Physically lift the turtle off the dock.

---

## Step 7 — Control the Turtle from the Ubuntu Laptop
Open a terminal on the Ubuntu laptop (not SSH — a local terminal) and run:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Controls:
| Key | Action |
|-----|--------|
| `i` | Forward |
| `,` | Backward |
| `j` | Rotate left |
| `l` | Rotate right |
| `k` | Stop |
| `q` / `z` | Increase / decrease speed |

Press **Ctrl+C** to quit teleop.

---

## Shutdown Procedure
1. Press **Ctrl+C** to stop teleop on the Ubuntu laptop
2. Press **Ctrl+C** to stop the bringup on the turtle
3. Place the turtle back on the dock
4. In the SSH session to the turtle, run:
```bash
sudo shutdown now
```
5. Once the Raspberry Pi shuts down, hold the **power button** on the Create 3 base to turn it off

---

## Troubleshooting

**Turtle won't move:**
- Check the EStop (Step 5)
- Check battery level (need at least 3 LED lights)
- Make sure the Create 3 is connected to WiFi (Step 2)
- Restart the Create 3 application via the webserver → Application → Restart Application

**Can't SSH into the turtle:**
- Confirm the turtle's IP on the display
- Make sure you're on the same WiFi network

**Bringup errors / dock/undock loop:**
- Restart the Create 3 application via the webserver
- Wait for happy chimes, then restart bringup

**EStop service waiting:**
- Restart the Create 3 application via the webserver
- Wait for happy chimes, then try again

---

## Key Information
| Item | Value |
|------|-------|
| Turtle IP | 192.168.2.144 |
| SSH username | ubuntu |
| Create 3 webserver | http://192.168.2.144:8080 |
| ROS Domain ID | 0 |
| RMW Implementation | rmw_fastrtps_cpp |
