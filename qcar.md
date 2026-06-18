# The QCar

## 1. Multi-Sensor Orchestration & Data Collection

The QCar2 acts as a synchronized data collection hub, natively outputting data into NumPy arrays for direct integration with machine learning libraries like PyTorch:

* **CSI Camera Streaming**: Integrates **4x IMX219 CSI cameras** (covering front, rear, left, and right fields of view). Utilizing a customized GStreamer pipeline, it bypasses default limitations to process raw 10-bit Bayer data through a sequential burst capture strategy to maintain daemon stability.


* **RGB-D Vision**: Drives an **Intel RealSense D435 camera** to simultaneously capture standard RGB video streams ($480 \times 640 \times 3$) and float32 raw spatial depth maps measured in meters.


* **LiDAR Spatial Mapping**: Operates an **RPLidar system** that samples environmental distance and angle points (up to 384 points per scan over a 6-meter range) to compile instant Bird’s Eye View (BEV) arrays.


* **Synchronized Logging**: Natively packages high-speed, sub-millisecond timestamped streams across all sensors concurrently, generating automated session folders, metadata JSON files, and environmental descriptions at up to 106 FPS.



## 2. On-Device AI & Federated Learning Infrastructure

The platform is fully capable of running end-to-end computer vision and training cycles completely at the edge, ensuring raw data never leaves the vehicle:

* **Real-Time Object Detection**: Runs **YOLOv8** architectures locally to track objects, extract feature geometries, and perform immediate baseline inference.


* **Automated Pseudo-Labeling**: Uses pretrained models to automatically flag objects with high-confidence thresholds, completely eliminating the need for manual data annotation.


* **Edge Fine-Tuning**: Performs local backpropagation and training loops directly on the Jetson Xavier GPU. It utilizes Automatic Mixed Precision (AMP FP16) to optimize memory overhead, executing complete environment adaptation cycles using under 0.7 GB of VRAM.


* **Federation Weight Exporting**: Compiles local optimization passes into highly condensed, federation-ready weight matrices (6.5 MB files) designed to interface with **Flower (`flwr`)** federation servers for distributed global model aggregation.



## 3. "Second Care" Vision & Behavioral Analytics

Though an autonomous vehicle platform, the QCar2 has been successfully configured with a specialized, real-world perception stack tailored for healthcare monitoring, predictive analytics, and humanoid-intent modeling:

* **Edge Face Recognition**: Implements a lightweight `InsightFace` ONNX model that maintains a persistent local database across power cycles, enabling the system to naturally prompt and enroll unknown individuals.


* **Sliding-Window Emotion Detection**: Leverages `HSEmotion` networks to read 8 core facial expressions in real-time (Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise) utilizing a 15-frame smoothing window to mitigate single-frame environmental anomalies.


* **Advanced Body Pose Tracking**: Deploys `YOLOv8-pose` to evaluate skeletal keypoints for high-stakes clinical event reporting:


* *Slump Detection*: Triggers when facial/nose keypoints drop significantly below the shoulder midpoint line.


* *Arm Raised Alerts*: Recognizes distress calls when left, right, or both wrist keypoints clear shoulder heights.


* *Dangerous Lean Diagnostics*: Measures structural stability by raising events if the directional shoulder height differential crosses a 60-pixel threshold.


* *Inactivity Protocols*: Evaluates a smoothed coordinate buffer to deploy structural alerts if minimal physical movement ($<8\text{px}$) is recorded over sustained periods (e.g., 8+ seconds).
