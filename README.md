# SecureVLA-Car: ROS 2 Cybersecurity & Multi-Modal VLA Architecture for Connected Autonomous Vehicles

[![ROS 2 Humble](https://img.shields.io/badge/ROS2-Humble-blue?style=flat-square&logo=ros)](https://docs.ros.org/en/humble/index.html)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-green?style=flat-square&logo=python)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/Environment-Pixi-brightgreen?style=flat-square)](https://pixi.sh/)
[![Hardware Platform](https://img.shields.io/badge/Hardware-Quanser%20QCar2%20%7C%20RobifyX-orange?style=flat-square)](https://www.quanser.com/products/qcar-2/)

SecureVLA-Car is a cyber-physical systems (CPS) research initiative focused on auditing, emulating, and securing the data transmission pipelines of heterogeneous autonomous vehicle fleets. By deploying cutting-edge **SROS2 (DDS-Security)** protocols and custom Python runtime anomaly detection monitors, this project establishes a bulletproof framework to capture high-fidelity, verified multi-modal datasets. 

The core output of this project is the compilation of structured **Vision-Language-Action (VLA) data packages** and secure edge updates via an optional **Federated Learning (FL)** framework, mitigating adversarial manipulation from low-level inertial sensors up to high-level conversational Large Language Models.

---

## 🏗️ The 5-Layer Robotics & AI Security Taxonomy

Traditional cybersecurity safeguards (like firewalls or perimeter network encryption) fail to fully protect autonomous vehicles because they leave internal communication loops unmonitored. This project maps all system vulnerabilities and defensive structures across a strict, 5-layer architecture:
