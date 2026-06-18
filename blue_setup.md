# Blue Setup

Since it's Ubuntu 22.04 (same as the red machine based on what we saw earlier), the setup is straightforward:

**Step 1 — ROS 2 Humble (same as red machine)**
```bash
# Add ROS 2 apt repo
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu jammy main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update && sudo apt install -y ros-humble-desktop

# Add to ~/.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
echo "export FASTDDS_BUILTIN_TRANSPORTS=UDPv4" >> ~/.bashrc
source ~/.bashrc

# Fix library paths (same fix as red machine)
echo "/opt/ros/humble/lib" | sudo tee /etc/ld.so.conf.d/ros-humble.conf
echo "/opt/ros/humble/lib/x86_64-linux-gnu" | sudo tee -a /etc/ld.so.conf.d/ros-humble.conf
sudo ldconfig
```

**Step 2 — Victim simulator node**

The blue machine doesn't have a QCar or `pal` library, so instead of the bridge script we run a pure ROS 2 simulator that publishes fake but realistic sensor data on the same topics the attack scripts expect:**On the blue machine, that's all you need:**

```bash
# 1 — Install ROS 2 Humble (same steps as red machine)
# 2 — Run the verify script to confirm setup
python3 verify_lab_setup.py

# 3 — Start the victim node
python3 blue_victim.py
```

**On the red machine, attacks work identically:**

```bash
ros2 topic list
# /qcar2/battery
# /qcar2/cmd_vel
# /qcar2/imu
# /qcar2/scan
# /qcar2/motor

python3 rogue_node.py   # blue machine logs every injected command
python3 sniffer.py      # captures blue machine's plaintext sensor data
python3 cmd_flood.py    # floods blue machine's cmd_vel queue
sudo python3 dds_ghost.py  # exhausts blue machine's DDS discovery
```

**The key advantage** — when `rogue_node.py` injects commands, the blue machine logs every single received packet with a `CMD_VEL RECEIVED` warning. Students on the blue machine watch the attack happen in real time from the victim's perspective, which is a much richer teaching moment than just watching the red machine send packets.

**Your full lab architecture now looks like this:**

| Machine | Role | Runs |
|---|---|---|
| Red machine | Attacker | All 4 attack scripts |
| Blue machine | Victim (software) | `blue_victim.py` |
| QCar 2 | Victim (hardware) | `qcar2_ros2_bridge.py` |
| Lab router | Network | Isolated `192.168.2.0` |

Practice on blue machine daily, QCar comes out for the live demo that makes everyone realize this is real.
