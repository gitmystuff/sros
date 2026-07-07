## Suggested Title

**"Demonstrating and Mitigating ROS 2 Network-Layer Vulnerabilities on Physical Autonomous Vehicle Platforms: A Red Team / Blue Team Security Study"**

---

## Problem Statement (frame this in your intro)

ROS 2 is rapidly becoming the standard middleware for autonomous vehicles and robotics research, yet its default configuration provides no authentication, no encryption, and no access control at the network layer. A single unauthorized laptop joining a shared Wi-Fi network gains immediate, unrestricted access to every sensor stream and every actuator command channel on any robot in that environment. This paper demonstrates four classes of network-layer attacks against a physical ROS 2 autonomous vehicle platform, measures their real-world impact, and evaluates SROS2 as a defensive countermeasure.

---

## Paper Sections & Keyword Bullets

---

### Abstract
- ROS 2 default security posture
- Four attack categories demonstrated on Quanser QCar 2
- Red team / blue team methodology
- SROS2 as countermeasure
- Simulated and physical platform results
- Implications for autonomous vehicle security

---

### 1. Introduction
- Autonomous vehicles increasingly rely on ROS 2 middleware
- ROS 2 uses DDS (Data Distribution Service) as transport layer
- Default DDS configuration: no authentication, no encryption, no access control
- Any node on same subnet joins computational graph automatically
- Wi-Fi attack surface: lab networks, campus networks, shared infrastructure
- Gap in literature: most ROS 2 security work is theoretical; few live physical demonstrations
- Contribution: reproducible red team / blue team lab on physical QCar 2 hardware
- Contribution: four attacks implemented as bounded, safe emulators with measured impact
- Contribution: open-source toolkit for ROS 2 security education
- Research questions:
  - How quickly can an unauthorized node gain control of a ROS 2 vehicle?
  - What is the measurable impact of each attack class on vehicle behavior?
  - Does SROS2 effectively block these attacks in practice?
- Scope: network and transport layer attacks (Category 1 & 2); physical safety maintained throughout

---

### 2. Background & Related Work

**ROS 2 and DDS Architecture**
- ROS 2 publish/subscribe model
- DDS middleware: FastDDS, CycloneDDS
- RTPS (Real-Time Publish-Subscribe) wire protocol
- UDP multicast for discovery (SPDP on 239.255.0.1:7400)
- CDR (Common Data Representation) message serialization
- Topic namespace: /cmd_vel, /scan, /imu as common attack surfaces
- QoS (Quality of Service) profiles: RELIABLE vs BEST_EFFORT

**Known ROS 2 Security Vulnerabilities**
- Peer-to-peer zero-trust discovery by default
- No participant authentication in default DDS profile
- Plaintext RTPS payload — no encryption
- No publisher authorization on sensitive topics
- Resource exhaustion via discovery protocol flooding
- Prior work: Dieber et al. (2016) — seminal ROS security paper
- Prior work: White et al. — RTPS vulnerability analysis
- ROS 2 threat model: design.ros2.org

**SROS2 and DDS Security**
- SROS2: Secure ROS 2 using DDS Security specification
- Certificate-based identity (X.509)
- Governance files: domain-wide encryption and authentication policy
- Permissions files: per-node topic publish/subscribe access control
- Keystore structure: CA, identity keys, permissions
- Known limitations: Python node enclave binding complexity
- DDS Security specification: OMG DDS-SECURITY v1.1

**Related Work**
- Network security in autonomous vehicle systems
- V2X (vehicle-to-everything) communication security
- ROS 1 vs ROS 2 security model differences
- Industrial control system (ICS) security parallels
- Federated learning for anomaly detection in robotics (SecureVLA-Car stretch goal)

---

### 3. Platform and Experimental Setup

**Hardware**
- Quanser QCar 2: Jetson-based autonomous vehicle platform
- Ubuntu 20.04 (Focal) on QCar 2 Jetson
- Onboard sensors: IMU, RPLidar A2, Intel RealSense, 4x CSI cameras
- Red machine: Ubuntu 22.04, x86_64 (attacker)
- Blue machine: Ubuntu 22.04, x86_64 (simulated victim)
- Isolated lab router: 192.168.2.0/24, no internet uplink

**Software Stack**
- ROS 2 Humble Hawksbill on all machines
- FastDDS as default RMW (ROS Middleware)
- Quanser PAL (Hardware Abstraction Library) on QCar 2
- Custom ROS 2 bridge: qcar2_ros2_bridge.py (pal → ROS 2 topics)
- Python 3.10 attack scripts with built-in safety limits
- SROS2 keystore with X.509 certificates

**Network Configuration**
- ROS_DOMAIN_ID=0 on all machines
- FASTDDS_BUILTIN_TRANSPORTS=UDPv4 (forced real UDP, no shared memory)
- Isolated Wi-Fi — no UNT campus network
- DDS SPDP multicast confirmed via ros2 multicast send/receive test

**Simulated vs Physical Platform**
- blue_victim.py: pure ROS 2 node simulating QCar 2 sensor topics
- Publishes identical topic names, types, and rates to physical QCar 2
- Enables safe student practice without physical hardware risk
- Physical QCar 2 used for final live demonstration with safety protocol

**Safety Protocol**
- All attack scripts bounded: max throttle 0.15, max duration 30s
- Stop command sent automatically on script exit
- Physical QCar 2 tested with wheels lifted before floor testing
- One student runs attack scripts at a time
- Battery voltage monitored throughout (stop below 10.5V)

---

### 4. Attack Methodology

**Attack 1 — Rogue Node Injection**
- Threat model: unauthorized laptop joins lab Wi-Fi
- Method: rclpy publisher node on /qcar2/cmd_vel, 10 Hz, no authentication
- ROS 2 discovery: automatic, zero credentials required
- Measurement: time from network join to first injected command
- Measurement: publisher count visible via ros2 topic info --verbose
- Result indicator: CMD_VEL RECEIVED on victim node, two publishers visible
- Script: rogue_node.py (safety limit: throttle ≤ 0.15, duration ≤ 30s)

**Attack 2 — Plaintext Packet Sniffing**
- Threat model: passive attacker on same subnet, never joins ROS 2 graph
- Method: Scapy raw socket capture, RTPS magic byte detection, CDR decoding
- No ROS 2 installation required on attacker machine
- Measurement: packets captured, cmd_vel decoded, IMU decoded, battery decoded
- Detectability: zero — completely passive, no packets sent
- Script: sniffer.py (no writes to network)

**Attack 3 — DDS Discovery Poisoning**
- Threat model: attacker sends forged SPDP announcements via raw UDP
- Method: craft minimal RTPS SPDP DATA submessage with random GUID prefix
- Target: 239.255.0.1:7400 (DDS SPDP multicast group)
- Measurement: CPU usage on victim before, during, after injection
- Measurement: ROS 2 daemon recovery time
- Observable effect: incompatible QoS warnings on victim node
- Script: dds_ghost.py (safety limit: max 100 participants, min 0.05s interval)

**Attack 4 — Command Flood / DoS**
- Threat model: attacker publishes at rate far exceeding operator
- Method: rclpy publisher with BEST_EFFORT QoS, configurable rate up to 5000 Hz
- Measurement: legitimate command delivery rate via ros2 topic hz
- Measurement: ratio of attacker packets to legitimate packets
- Observable effect: victim CMD_VEL counter increases at flood rate
- Script: cmd_flood.py (safety limit: throttle=0.0, max 30s, max 5000 Hz)

---

### 5. Results

**Attack 1 — Rogue Node Injection**
- Time from network join to first injected command: seconds (just ros2 topic list + script)
- Publisher count: increased from 1 to 2 during attack, visible to any observer
- Victim response: CMD_VEL RECEIVED logged for every injected packet
- 99 packets injected over 10 seconds at 10 Hz
- Blue machine had no mechanism to distinguish legitimate from rogue commands
- rqt_graph showed attacker_node as indistinguishable from operator node

**Attack 2 — Plaintext Packet Sniffing**
- 100 RTPS packets captured in 30-second session
- 40 cmd_vel messages successfully decoded from raw UDP
- Throttle and steering values reconstructed from plaintext CDR payload
- Victim completely unaware — zero indicators of passive capture
- Wireshark confirmed raw RTPS packet structure visible at network level
- No ROS 2 installation required on attacker machine

**Attack 3 — DDS Discovery Poisoning**
- 30 ghost SPDP announcements injected in 3 seconds
- Victim DDS stack detected incompatible QoS on ghost participants
- CPU spike observed on victim during injection burst
- ROS 2 daemon recovery required after high-count injection
- Warning visible in victim logs: "New publisher discovered on /qcar2/cmd_vel, offering incompatible QoS"

**Attack 4 — Command Flood / DoS**
- Legitimate baseline rate: ~10 Hz
- Flood rate achieved: 1000+ Hz (100x legitimate rate)
- ros2 topic hz confirmed rate spike during flood
- Victim CMD_VEL counter incremented at flood rate, burying legitimate commands
- Recovery: legitimate rate restored within seconds of flood stopping
- BEST_EFFORT QoS maximized throughput with no retransmit overhead

**SROS2 Defense**
- Keystore successfully created with X.509 certificates
- Permissions files generated for /blue_qcar2_node
- Python node enclave binding: known bug in ROS 2 Humble requires --ros-args --enclave at rclpy.init()
- Governance and permissions structure validated
- Full defense demo pending blue_victim.py fix deployment

---

### 6. Discussion

**Ease of Attack**
- All four attacks required only standard Python libraries and ROS 2
- Attack 1 required zero specialized knowledge — just ros2 topic list and a publisher
- Attack 2 required only Scapy — no ROS 2 install on attacker machine
- Time to first successful attack from network join: under 60 seconds
- No credentials, no brute force, no exploits — by design of default DDS

**Real-World Implications**
- Campus Wi-Fi shared with students poses genuine risk to lab robots
- UNT network demonstrated: DDS multicast blocked between clients (partial protection)
- Isolated lab router required for attacks to work — also required for legitimate operation
- Physical autonomous vehicles in shared spaces face same exposure
- Attack 3 (DDS poisoning) most dangerous on resource-constrained platforms (Jetson)

**SROS2 Effectiveness**
- Certificate-based identity prevents rogue node injection when enforced
- DDS encryption prevents packet sniffing when configured
- Governance file controls domain-wide security policy
- Practical deployment complexity: significant — keystore, certificates, permissions, enclave binding
- Python node enclave limitation: known issue, workaround documented
- SROS2 does not fully mitigate Attack 4 (flooding) — rate limiting needed separately
- Conclusion: SROS2 is necessary but not sufficient — runtime monitoring required

**Simulated vs Physical Platform**
- blue_victim.py accurately replicated QCar 2 topic structure
- All four attacks demonstrated identically on both platforms
- ROS 2 bridge (qcar2_ros2_bridge.py) enabled physical QCar 2 topic exposure
- Physical platform added real sensor noise and timing variation to rosbag dataset
- Simulated platform enabled safe student practice without hardware risk

**Rosbag Dataset Value**
- Attack-labeled bags enable offline security monitor development
- Replay attack demonstrates fifth attack class without live attacker
- Structured event windows from bags feed LLM incident analysis pipeline
- Dataset labels align with SecureVLA-Car JSONL format for VLA research

**Limitations**
- Simulated sensor data lacks physical noise characteristics of real Jetson hardware
- CDR offset decoding in sniffer.py showed throttle parsing error — steering decoded correctly
- SROS2 Python enclave binding required source code modification
- Single isolated network — multi-hop or internet-facing scenarios not tested
- Attack scripts bounded by safety limits — real adversary would have no such limits

---

### 7. Conclusion

- Demonstrated all four Category 1 & 2 network attacks against ROS 2 autonomous vehicle
- Default ROS 2/DDS configuration provides zero network-layer security
- Any laptop on the same subnet can inject commands, capture sensors, exhaust resources, or deny control
- SROS2 provides strong theoretical defense but has practical deployment complexity
- Open-source toolkit produced: verify_lab_setup.py, four attack scripts, blue_victim.py, qcar2_ros2_bridge.py, rosbag guide
- Red team / blue team methodology effective for security education at introductory level
- Rosbag dataset provides foundation for runtime security monitor and LLM incident analysis
- Future work: runtime security monitor (Week 7 SecureVLA), LLM incident classification, federated learning module
- Future work: Category 3 & 4 attacks (application layer, authentication bypass)
- Recommendation: SROS2 should be default-on in all ROS 2 robot deployments

---

### References (key ones to look up)

- Dieber et al. — "Security for the Robot Operating System" (2016)
- White et al. — "ROSRTPS Security Analysis"
- ROS 2 DDS Security design: design.ros2.org/articles/ros2_dds_security.html
- ROS 2 threat model: design.ros2.org/articles/ros2_threat_model.html
- SROS2 documentation: docs.ros.org/en/rolling/Tutorials/Advanced/Security
- OMG DDS Security specification v1.1
- Quanser QCar 2 technical documentation
- RT-2 VLA paper: arxiv.org/abs/2307.15818 (for SecureVLA context)
- Flower federated learning: flower.ai/docs

---

**One writing tip:** Your results section will be strongest if you include the actual numbers from rosbag recording session — 99 packets injected, 40 cmd_vel decoded, 1000 Hz flood rate, 30 ghost participants. Those specific measurements are what make the paper concrete rather than theoretical.
