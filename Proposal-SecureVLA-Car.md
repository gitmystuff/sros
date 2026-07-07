# **Summary**

SecureVLA-Car is a two-month undergraduate research project centered on **ROS 2 cybersecurity** for physical autonomous driving platforms. The project gives students a tangible robotics experience while producing reusable research data for future **Vision-Language-Action (VLA)** and optional **Federated Learning (FL)** work. The core deliverable is a complete physical-car security demo on QCar2: students collect normal and attack-emulation rosbags, evaluate SROS2/DDS-Security protections, build a lightweight runtime security monitor, and use LLMs as red-team assistants and incident analysts.

The attack-related experiments are assigned to QCar2 because the project security module depends on ROS 2, SROS2, DDS-Security, and ROS 2 topic-level instrumentation. The RobiX cars are treated as ROS 1 platforms under the current local configuration, so they remain valuable for physical mapping, normal data collection, and long-term VLA data acquisition, but they are not the primary platform for ROS 2/SROS2 attack-emulation experiments. This separation keeps the project technically consistent and avoids mixing ROS 1 security assumptions with ROS 2 security mechanisms.

The summer output will include a GitHub repository, documented safety protocol, SROS2 configuration materials, controlled attack-emulation scripts, runtime monitor, LLM incident reports, normal and attack-labeled rosbags, and VLA-ready records that link vision, spatial state, language instructions, actions, and security labels. FL is designed as a detachable stretch module: if students progress quickly, they can train a small federated security-event classifier; if time is limited, removing FL will not harm the core project.

| Priority | Module | Role in Project |
| :---- | :---- | :---- |
| Must Have | QCar2 physical security demo; ROS 2/SROS2 security; LLM-assisted attack emulation and incident analysis; normal and attack-labeled rosbags. | Required for a complete summer project. |
| Should Have | VLA-ready dataset export: camera/LiDAR/odom/action/language/security-label records. | Preserves long-term VLA research value without requiring VLA model training during the summer. |
| Could Have | Federated Learning module using Flower or PySyft to train a small security-event classifier across cars, runs, or data partitions. | Stretch module; removable without harming the main project. |

 

# **Project Goals**

* **Primary goal**: build and demonstrate a ROS 2 cybersecurity workflow on physical QCar2 vehicles, with RobiX used for compatible data collection and future VLA bridge activities.  
* **Security goal**: use SROS2 and runtime monitoring to study unauthorized and compromised-node behaviors under controlled, safe attack-emulation scenarios on QCar2.  
* **LLM goal**: use LLMs to support threat modeling, generate bounded attack-emulation plans, classify structured security event windows, and produce human-readable incident reports.  
* **VLA goal**: export multimodal rosbags into VLA-ready records containing vision, spatial state, language instruction, action, and security labels.  
* **FL stretch goal**: if time and student progress allow, train a small federated security classifier across QCar2/RobiX datasets, QCar2 runs, or simulated clients.

# **Platform Scope and Rationale**

The project uses both vehicle families, but their roles are separated to keep the technical design coherent.

| Platform | Primary Role | Reasoning |
| :---- | :---- | :---- |
| QCar2 | Primary platform for ROS 2 security, SROS2 experiments, controlled attack emulation, runtime monitoring, and security-labeled attack rosbags. | QCar2 is the correct target for the security module because it supports a ROS 2-centered workflow and can use DDS-Security/SROS2 mechanisms. Attack-emulation scenarios such as rogue /cmd\_vel publication, /scan injection, and ROS 2 permission testing should be performed here. |
| RobiX | Secondary platform for physical mapping, normal rosbag collection, VLA-ready data capture, and possible future cross-platform dataset comparison. | Under the current local configuration, RobiX cars are treated as ROS 1 platforms. Since ROS 1 does not use the ROS 2 DDS-Security/SROS2 model, RobiX should not be the primary target for ROS 2/SROS2 attack experiments. If a ROS 2 bridge or upgraded stack is later validated, selected monitoring-only or data-collection activities may be added. |

 

# 

# **Security Scope and Threat Model**

The project focuses on attacks and defenses on a single autonomous vehicle rather than vehicle-to-vehicle or V2X communication. The assumed adversary has already gained the ability to launch a user-level ROS 2 node or script on the QCar2 due to a prior network or firewall compromise. The initial compromise mechanism is out of scope. The project studies whether ROS 2 security controls, runtime monitoring, and LLM-assisted log analysis can detect or mitigate suspicious post-compromise behavior.

*  **In scope**: unauthorized publisher/listener attempts, command spoofing, command flooding, scan/noise injection, rosbag replay, node impersonation, compromised-but-authorized node behavior, and runtime anomaly detection on QCar2.  
* **Out of scope**: real malware deployment, credential theft, privilege escalation, persistence, worm-like behavior, external network scanning, and uncontrolled Wi-Fi exploitation.  
* **Safety principle**: all attack scenarios are implemented as bounded attack emulators or fault-injection scripts under lab supervision, with speed limits, emergency-stop procedures, and wheels-lifted testing before floor testing.  
* **RobiX security boundary**: RobiX is not used for ROS 2/SROS2 attack-emulation unless its ROS 2 stack is later verified. It can still contribute normal mapping data and VLA-style records.

# 

# **System Architecture**

| Component | Function |
| :---- | :---- |
| Physical Platforms | QCar2 runs ROS 2 security experiments, teleoperation, mapping, controlled attack emulation, and runtime monitoring. RobiX supports physical mapping and normal data collection under its local ROS 1 configuration. |
| Rosbag Recorder | Records camera, LiDAR/scan, odometry, command topics, /rosout or equivalent logs, and metadata from normal and attack-emulation runs. |
| Controlled Attack Emulator | Runs safe post-compromise test scripts on QCar2, such as rogue /cmd\_vel publisher, scan noise injection, command flooding, or replayed commands. |
| SROS2 Security Layer | Uses keystores, certificates, governance, and permissions files to authenticate and restrict ROS 2 communication on QCar2. |
| Runtime Security Monitor | Collects topic rates, publisher counts, node changes, command ranges, /rosout messages, CPU/network statistics, and produces structured event windows. |
| LLM Security Analyst | Reads structured event windows and produces attack labels, evidence, confidence, limitations, and recommended response. |
| VLA Dataset Exporter | Converts rosbag segments into vision-spatial-language-action-security records for future VLA research. |
| Optional FL Module | Trains a small security classifier across vehicles, runs, or data partitions using a federated framework if time allows. |

 

# 

# **LLM Role in the Project**

The LLM component should be useful but not safety-critical. Real-time safety decisions remain rule-based. The LLM is used as a red-team assistant and post-event analyst.

| LLM Function | Description |
| :---- | :---- |
| Threat Modeling | Analyze ROS 2 topic maps and identify high-risk QCar2 topics such as /cmd\_vel, /scan, /odom, camera, emergency stop, and map topics. |
| Attack-Emulation Planning | Suggest bounded attack scenarios and required evidence to collect. Students and mentors approve scripts before running them. |
| Incident Classification | Classify structured 5-10 second event windows as normal, command spoofing, command flooding, scan injection, unknown publisher, resource anomaly, or uncertain. |
| Incident Reporting | Generate concise reports containing summary, evidence, physical risk, response taken, and recommended follow-up. |
| Safety Boundary | The LLM does not directly control the vehicle or decide emergency-stop actions. |

 

# **Controlled Attack-Emulation Scenarios on QCar2**

All attack-related experiments are performed on QCar2 because the experiments depend on ROS 2 topics, SROS2 permissions, DDS-Security, and ROS 2 runtime observability. The scripts are controlled emulators, not real malware.

| Scenario | Description | Expected Security Lesson |
| :---- | :---- | :---- |
| Rogue /cmd\_vel publisher | An unauthorized ROS 2 node attempts to publish velocity commands. | SROS2 blocks unauthorized publishers; monitor flags unexpected publisher count if behavior is allowed. |
| Command flooding | A node publishes repeated commands at an abnormal frequency. | Monitor detects rate spike, CPU/network load, and unstable command stream. |
| Unsafe command injection | A node sends speed or steering values above lab-defined thresholds. | Rule-based guard stops/warns; LLM classifies event and cites value/range evidence. |
| Scan/noise injection | A node publishes altered /scan values or replays inconsistent sensor data. | Monitor flags mapping inconsistency or topic-source anomaly; mapping quality is compared. |
| Rosbag replay attack | Old command or sensor messages are replayed during a live run. | Monitor detects stale timestamps, repeated patterns, or conflict with current state. |
| Compromised authorized node | An authorized node behaves abnormally after passing SROS2 authentication. | Shows why SROS2 must be complemented by runtime monitoring. |

 

# **Eight-Week Work Plan**

The timeline keeps the two-phase structure, but the physical car appears early and the attack-emulation work is explicitly assigned to QCar2. RobiX remains useful for compatible normal data capture and VLA bridge activities.

| Week | Theme | Main Tasks | Deliverables |
| :---- | :---- | :---- | :---- |
| Week 1 | Physical Onboarding, ROS 2 Topics, and Rosbag Basics | Set up ROS 2; introduce ros2 bag record/play; power on QCar2 and RobiX; list nodes/topics; identify motion/sensor/security-critical topics; collect first short physical-car rosbag when hardware access allows. | car\_topic\_map.md; rosbag\_recording\_script.py; topic criticality table; first\_real\_car\_rosbag. |
| Week 2 | Baseline Mapping and Normal Data Collection | Use Gazebo/Quanser digital twin as training support, but collect physical normal driving/mapping data when possible; record /scan, /odom, /cmd\_vel, camera, /rosout or equivalent logs; compute normal topic statistics. | normal\_run rosbags; baseline\_stats.csv/json; optional .yaml/.pgm map. |
| Week 3 | SROS2 Fundamentals \+ LLM Threat Modeling | Create SROS2 keystore, certificates, governance, and permissions; secure talker/listener; use LLM to analyze the QCar2 topic map and propose safe attack-emulation scenarios. | sros2\_demo; threat\_model.md; approved\_attack\_scenarios.md. |
| Week 4 | Secure Mapping Simulation and Attack-Emulation Prototype | Combine simulated mapping with SROS2; test rogue publisher/listener attempts on QCar2-compatible ROS 2 topics; implement first safe attack emulators; compare no-SROS2 vs SROS2 behavior. | Milestone 1 demo; blocked/allowed behavior table; attack\_emulators\_v1. |
| Week 5 | QCar2 Physical Deployment and Sensor Bridging | Deploy/configure secure ROS 2 workspace on QCar2; validate physical LiDAR/camera/odom streaming; teleoperate QCar2 while recording authenticated topics; collect compatible RobiX normal data if available. | physical\_secure\_streaming\_demo; deployment notes; physical rosbag samples. |
| Week 6 | QCar2 Physical Security Data Campaign | Run QCar2 normal and controlled attack-emulation campaigns; record high-fidelity rosbags; label each run; follow safety checklist. RobiX may contribute normal mapping/VLA runs only. | normal/attack rosbags; security\_labels.json; demo video draft. |
| Week 7 | Security Evaluation, LLM Incident Analysis, and Optional FL | Build runtime monitor; extract structured event windows; use LLM/tiny model to classify and explain incidents; benchmark SROS2 overhead; optionally train a federated security classifier. | security\_monitor.py; incident\_reports; evaluation table; optional FL benchmark. |
| Week 8 | Final Demo, Dataset Handoff, and Documentation | Polish QCar2 physical security demo; export VLA-ready security-labeled records; clean GitHub repo; prepare final presentation and dataset index. | final demo video; GitHub repo; VLA-security JSONL; rosbag index; final report/slides. |

 

# **Month 1: Foundations, Simulation, and Security Prototyping**

The first month introduces ROS 2, rosbags, simulation, basic SLAM, SROS2, and LLM-assisted security thinking. Simulation is used as a safety and learning environment, but the physical car is introduced early to maintain student motivation and project identity.

* Week 1 emphasizes ROS 2 topic discovery and rosbag recording, including a first short physical-car recording when hardware access allows.  
* Week 2 establishes normal driving/mapping baselines and creates structured metadata for each run.  
* Week 3 introduces SROS2 and uses an LLM to help produce a safe, mentor-approved threat model for QCar2.  
* Week 4 integrates secure simulation, first QCar2-compatible attack-emulation scripts, and an initial no-SROS2 vs SROS2 comparison.

# **Month 2: Physical Deployment, Security Evaluation, and Data Handoff**

The second month shifts to the physical vehicles. QCar2 is the primary platform for security testing. RobiX can contribute compatible normal mapping and VLA-oriented data, but it is not used for ROS 2/SROS2 attack-emulation unless a ROS 2 stack is verified.

* Week 5 validates secure physical sensor streaming and deployment on QCar2 onboard systems or central workstations.  
* Week 6 collects QCar2 normal and attack-emulation runs under a documented safety protocol.  
* Week 7 performs security evaluation, incident classification, overhead benchmarking, and optional FL experiments.  
* Week 8 produces the final demo, documentation, GitHub repository, and dataset handoff package.

# **Security-Labeled VLA Data Output**

The project should not attempt to train a full VLA model during the summer. Instead, it will produce VLA-ready records from rosbags. Each record should align robot observations, language instruction, action, and security labels. Normal RobiX runs can be included in the VLA dataset when timestamped and documented consistently; attack-labeled records should come from QCar2 unless RobiX later receives a verified ROS 2 security setup.

| Field | Content |
| :---- | :---- |
| vision | Front camera or RealSense frame path, timestamp, optional image embedding placeholder. |
| spatial | LiDAR/scan/point cloud path, odometry, map pose, IMU/wheel odometry when available. |
| language | Run-level instruction such as “Drive slowly down the hallway and avoid obstacles.” |
| action | /cmd\_vel, steering/throttle, or platform-specific vehicle command. |
| security\_label | normal, cmd\_vel\_spoofing, command\_flooding, scan\_injection, replay\_attack, unknown\_publisher, resource\_anomaly, uncertain. |
| security\_evidence | Topic, publisher, rate, value range, timestamp, detector rule, and LLM explanation snippet. |

 

Example JSONL record:

{  
   "image": "frames/run\_04/000812.jpg",  
   "scan": "scan/run\_04/000812.npy",  
   "odom": {"x": 2.71, "y": 0.44, "yaw": 0.21},  
   "action": {"linear\_x": 0.75, "angular\_z": 0.00},  
   "language\_instruction": "Drive slowly down the hallway and avoid obstacles.",  
   "security\_label": "unsafe\_cmd\_vel\_injection",  
   "security\_evidence": {  
 	"topic": "/cmd\_vel",  
 	"reason": "linear\_x exceeded safe threshold",  
 	"publisher": "unknown\_node\_17"  
   }  
 }

# 

# **Optional Federated Learning Module**

Federated Learning is designed as a removable stretch module. The core project remains complete without it. If students complete the QCar2 security monitor and dataset pipeline early, FL can be added by training a small security-event classifier across QCar2 runs, QCar2/RobiX datasets, or simulated clients.

| Design Point | Recommendation |
| :---- | :---- |
| Trigger condition | Only start after the physical QCar2 demo, event-window extraction, labels, and centralized baseline classifier are working. |
| Model | Small classifier such as logistic regression, random forest, tiny MLP, or compact text classifier. Avoid federated fine-tuning of a large VLA or LLM during summer. |
| Clients | QCar2 vs RobiX normal-data partitions, multiple QCar2 runs, multiple cars, or data partitions representing different vehicles/environments. |
| Comparison | Centralized baseline vs federated classifier: accuracy, F1, false positives, communication rounds, and training time. |
| Fallback | If FL is removed, the project still delivers QCar2 ROS 2 security demo, LLM incident analysis, and VLA-ready security dataset. |

 

# **Evaluation Plan**

| Metric Area | Measurements |
| :---- | :---- |
| Security effectiveness | Attack type, SROS2 blocked?, monitor detected?, detection latency, false positives, and evidence quality. |
| Cyber-physical impact | Mapping distortion, unsafe command prevented?, tracking drift, car stopped/warned safely. |
| System overhead | CPU, memory, network load, rosbag size, DDS/SROS2 encryption overhead, message latency. |
| LLM analyst quality | Correct label, grounded evidence, no unsupported claims, useful recommended response, JSON validity. |
| Dataset quality | Completeness of metadata, timestamp alignment, label consistency, replayability, VLA-record export success. |
| Optional FL result | Centralized vs federated classifier performance and communication/training cost. |

 

# **Safety and Ethics Protocol**

* All attack scripts must be reviewed before execution and must be bounded, reversible, and non-persistent.  
* Attack-related experiments run on QCar2 only, unless a RobiX ROS 2 security setup is later verified and approved.  
* Initial tests should run in simulation or with the vehicle wheels lifted before floor testing.  
* Physical tests must use low speed, open space, an emergency-stop operator, and a written test checklist.  
* No code should perform credential theft, privilege escalation, persistence, external scanning, real firewall bypass, or network exploitation outside the lab setup.  
* The LLM may propose scenarios and analyze logs, but it must not directly control the vehicle or autonomously launch scripts.  
* All datasets should include metadata indicating normal/attack-emulation status, safety conditions, platform, sensor set, ROS version, DDS vendor if applicable, and software version.

# **Final Deliverables**

| Deliverable | Description |
| :---- | :---- |
| Physical demo | QCar2 normal run, controlled attack emulator, SROS2 block or monitor detection, safe response, and LLM incident report. RobiX normal data may appear in the dataset demo if available. |
| Code repository | ROS 2 packages, recording scripts, QCar2 attack emulators, SROS2 setup scripts, monitor, LLM analyst, dataset exporter, optional FL code. |
| Dataset package | Normal and attack-emulation rosbags, metadata, labels, rosbag index, VLA-ready JSONL records. |
| Security evaluation | Benchmark table comparing no-SROS2, SROS2, and SROS2 \+ monitor across QCar2 attack scenarios. |
| Documentation | README, setup guide, safety protocol, threat model, final report, slides/poster. |
| Optional FL artifact | Federated training script and FL vs centralized benchmark if stretch module is completed. |

 

# **Risks and Mitigation**

| Risk | Mitigation |
| :---- | :---- |
| ROS 2/SLAM learning curve | Provide starter workspace, topic map template, and rosbag recorder skeleton; keep Nav2 autonomy as stretch. |
| SROS2 configuration complexity | Begin with talker/listener demo before applying to QCar2 vehicle topics; document DDS vendor and ROS distribution choices. |
| QCar2 hardware availability | Use simulation/digital twin for early weeks, but require at least one QCar2 physical security demo path by Week 5\. |
| RobiX ROS 1/ROS 2 mismatch | Use RobiX for normal mapping/VLA data collection under its current ROS 1 configuration; do not depend on RobiX for SROS2 attack experiments. |
| Attack complexity | Use controlled ROS-level emulators instead of Wi-Fi MITM or low-level packet injection as the default. |
| LLM unreliability | Require structured event windows and JSON output; LLM must cite evidence from input; rule-based guard handles safety. |
| FL scope creep | Keep FL optional and limited to a small security classifier; remove without affecting core deliverables. |
| VLA overpromise | Export VLA-ready records; do not promise full VLA training during summer. |

 

# 

# **References and Technical Basis**

* ROS 2 DDS-Security integration design: [https://design.ros2.org/articles/ros2\_dds\_security.html](https://design.ros2.org/articles/ros2_dds_security.html)  
* ROS 2 security and SROS2 documentation: [https://docs.ros.org/en/rolling/Tutorials/Advanced/Security/Introducing-ros2-security.html](https://docs.ros.org/en/rolling/Tutorials/Advanced/Security/Introducing-ros2-security.html)  
* ROS 2 security keystore documentation: [https://docs.ros.org/en/iron/Tutorials/Advanced/Security/The-Keystore.html](https://docs.ros.org/en/iron/Tutorials/Advanced/Security/The-Keystore.html)  
* ROS 2 threat model: [https://design.ros2.org/articles/ros2\_threat\_model.html](https://design.ros2.org/articles/ros2_threat_model.html)  
* ROS 2 rosbag recording and playback documentation: [https://docs.ros.org/en/rolling/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html](https://docs.ros.org/en/rolling/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html)  
* Quanser QCar 2 technical information: [https://www.quanser.com/products/qcar-2/](https://www.quanser.com/products/qcar-2/)  
* RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control: [https://arxiv.org/abs/2307.15818](https://arxiv.org/abs/2307.15818)  
* Flower federated learning documentation: [https://flower.ai/docs/](https://flower.ai/docs/)

