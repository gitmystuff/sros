# QCar2 Setup Guide — QCar2 #2
## Sinha Data Science Innovation Lab — Summer 2026
*Based on bring-up experience from QCar2 #1*

Follow steps in order. Total time: approximately 2.5 hours (mostly OpenCV compile time).

---

## Prerequisites

- QCar2 powered on and connected to the lab network
- Windows laptop on the same network
- Remote Desktop (mstsc) connected to the QCar2
- Internet access from the QCar2

---

## Step 1 — Verify CSI Cameras Are Detected

```bash
v4l2-ctl --list-devices
```

Expected output — 4 IMX219 cameras at `/dev/video0` through `/dev/video3`:

```
vi-output, imx219 30-0010 (platform:tegra-capture-vi:0):
    /dev/video0
vi-output, imx219 31-0010 (platform:tegra-capture-vi:1):
    /dev/video1
vi-output, imx219 32-0010 (platform:tegra-capture-vi:2):
    /dev/video2
vi-output, imx219 33-0010 (platform:tegra-capture-vi:3):
    /dev/video3
```

Also confirm RealSense is detected at `/dev/video4` through `/dev/video9`.

If cameras are not listed, check the physical ribbon cable connections.

---

## Step 2 — Verify nvargus-daemon Is Running

```bash
sudo systemctl status nvargus-daemon
```

Should show `Active: active (running)`. If not:

```bash
sudo systemctl restart nvargus-daemon
sleep 3
sudo systemctl status nvargus-daemon
```

---

## Step 3 — Find the GDM Xauthority File

```bash
id gdm
```

Note the UID number (e.g., `uid=124`). On QCar2 #1 this was 124 — it may differ on this car.

```bash
ls /run/user/124/gdm/Xauthority
```

Replace `124` with the actual UID shown. **Note this number — you need it throughout.**

---

## Step 4 — Test the GStreamer Pipeline

```bash
sudo DISPLAY=:0 XAUTHORITY=/run/user/124/gdm/Xauthority gst-launch-1.0 \
  nvarguscamerasrc sensor-id=0 num-buffers=10 ! \
  'video/x-raw(memory:NVMM),format=NV12,width=820,height=616,framerate=80/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! \
  filesink location=/home/nvidia/test_csi.jpg
```

Should end with `Got EOS from element "pipeline0"`. View the result:

```bash
eog /home/nvidia/test_csi.jpg
```

If you see a real image, the GStreamer pipeline is working. Proceed to Step 5.

---

## Step 5 — Check OpenCV GStreamer Support

```bash
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer
```

- `GStreamer: YES` — skip to Step 9
- `GStreamer: NO` — continue with Steps 6–8

---

## Step 6 — Install Build Dependencies

```bash
sudo apt-get install -y build-essential cmake git libgtk2.0-dev pkg-config \
  libavcodec-dev libavformat-dev libswscale-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libopenjp2-7-dev
```

---

## Step 7 — Download OpenCV Source

```bash
cd ~ && git clone --branch 4.10.0 --depth 1 https://github.com/opencv/opencv.git
git clone --branch 4.10.0 --depth 1 https://github.com/opencv/opencv_contrib.git
```

---

## Step 8 — Build and Install OpenCV

### 8a — Create symlinks for openjpeg headers

```bash
sudo ln -s /usr/include/openjpeg-2.3/openjpeg.h /usr/include/openjpeg.h
sudo ln -s /usr/include/openjpeg-2.3/opj_stdint.h /usr/include/opj_stdint.h
sudo ln -s /usr/include/openjpeg-2.3/opj_config.h /usr/include/opj_config.h
```

### 8b — Configure the build

```bash
cd ~/opencv && mkdir build && cd build && cmake \
  -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
  -D WITH_GSTREAMER=ON \
  -D WITH_CUDA=ON \
  -D CUDA_ARCH_BIN=7.2 \
  -D WITH_CUDNN=ON \
  -D OPENCV_DNN_CUDA=ON \
  -D BUILD_opencv_python3=ON \
  -D PYTHON3_EXECUTABLE=$(which python3) \
  -D BUILD_EXAMPLES=OFF \
  -D BUILD_TESTS=OFF \
  -D BUILD_PERF_TESTS=OFF ..
```

Verify GStreamer is enabled in cmake output:

```
--   Video I/O:
--     GStreamer:                   YES (1.16.3)
```

### 8c — Build (~2 hours)

```bash
cd ~/opencv/build && make -j6
```

Wait for `[100%]`. Do not interrupt.

### 8d — Install

```bash
cd ~/opencv/build && sudo make install
```

### 8e — Add to Python path

```bash
echo "export PYTHONPATH=/usr/local/lib/python3.8/site-packages:$PYTHONPATH" >> ~/.bashrc
source ~/.bashrc
```

### 8f — Verify

```bash
python3 -c "import cv2; print(cv2.__file__)"
```

Expected: `/usr/local/lib/python3.8/site-packages/cv2/__init__.py`

```bash
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer
```

Expected: `GStreamer: YES (1.16.3)`

---

## Step 9 — Identify Camera Positions

Save an image from each camera:

```bash
for i in 0 1 2 3; do
  sudo DISPLAY=:0 XAUTHORITY=/run/user/124/gdm/Xauthority \
  gst-launch-1.0 nvarguscamerasrc sensor-id=$i num-buffers=10 ! \
  'video/x-raw(memory:NVMM),format=NV12,width=820,height=616,framerate=80/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! \
  filesink location=/home/nvidia/csi_$i.jpg
done
```

Open each image and record which sensor-id maps to which direction:

```bash
eog /home/nvidia/csi_0.jpg
eog /home/nvidia/csi_1.jpg
eog /home/nvidia/csi_2.jpg
eog /home/nvidia/csi_3.jpg
```

**On QCar2 #1 the mapping was:**

| sensor-id | Camera |
|-----------|--------|
| 0 | Front |
| 1 | Rear |
| 2 | Left |
| 3 | Right |

Update `csi_cameras.py` if this car's mapping is different.

---

## Step 10 — Create summer_2026 Folder and Copy Files

```bash
mkdir -p ~/Documents/Quanser/summer_2026/data
```

Copy the following files from QCar2 #1 or from Windows via WinSCP to
`/home/nvidia/Documents/Quanser/summer_2026/`:

| File | Purpose |
|------|---------|
| `csi_cameras.py` | CSI camera interface |
| `realsense_camera.py` | RealSense RGB + depth |
| `lidar_sensor.py` | LiDAR with bird's eye view |
| `LiDAR_RealSense_data_collector.py` | Data collection pipeline |
| `yolo_inference.py` | YOLOv8 baseline inference |
| `yolo_finetune.py` | Pseudo-labeling + fine-tuning |

---

## Step 11 — Update Vehicle ID and IP Address

Update the vehicle ID to QCar2_02 in the data collector and fine-tuning scripts:

```bash
python3 -c "
import os
scripts = [
    'LiDAR_RealSense_data_collector.py',
    'yolo_finetune.py',
]
for s in scripts:
    path = f'/home/nvidia/Documents/Quanser/summer_2026/{s}'
    f = open(path)
    content = f.read()
    f.close()
    content = content.replace(\"VEHICLE_ID = 'QCar2_01'\", \"VEHICLE_ID = 'QCar2_02'\")
    f = open(path, 'w')
    f.write(content)
    f.close()
    print(f'Updated {s}')
"
```

Update the Windows laptop IP in the CSI camera test script:

```bash
python3 -c "
path = '/home/nvidia/Documents/Quanser/summer_2026/csi_cameras.py'
f = open(path)
content = f.read()
f.close()
content = content.replace('192.168.4.69', 'YOUR_LAPTOP_IP_HERE')
f = open(path, 'w')
f.write(content)
f.close()
print('Done')
"
```

---

## Step 12 — Fix Data Folder Permissions

```bash
sudo chown -R nvidia:nvidia ~/Documents/Quanser/summer_2026/data
```

This prevents permission errors when creating session folders.

---

## Step 13 — Test Live Camera Stream (Optional)

Start observer.py on Windows with this configuration:

```python
from pal.utilities.probe import Observer
observer = Observer()
observer.add_display(imageSize=[480, 640, 3], scalingFactor=2, name='RGB')
observer.add_display(imageSize=[480, 640, 3], scalingFactor=2, name='Depth')
observer.launch()
```

Then on the QCar2:

```bash
sudo -E PYTHONPATH=/usr/local/lib/python3.8/site-packages \
  DISPLAY=:0 XAUTHORITY=/run/user/124/gdm/Xauthority \
  python3 ~/Documents/Quanser/summer_2026/realsense_camera.py
```

---

## Step 14 — Test Data Collection

Run the data collector:

```bash
python3 ~/Documents/Quanser/summer_2026/LiDAR_RealSense_data_collector.py
```

Press **Enter** to start, describe the environment, record for 30 seconds, press **Enter** to stop.

Verify the session saved correctly:

```bash
ls ~/Documents/Quanser/summer_2026/data/session_001/
cat ~/Documents/Quanser/summer_2026/data/session_001/session_info.json
```

Expected folders: `realsense_rgb/`, `realsense_depth/`, `lidar/`, plus `timestamps.csv` and `session_info.json`.

---

## Step 15 — Test YOLOv8 Inference

```bash
python3 -c "
f = open('/home/nvidia/Documents/Quanser/summer_2026/yolo_inference.py')
content = f.read()
f.close()
content = content.replace(\"SESSION = 'session_003'\", \"SESSION = 'session_001'\")
f = open('/home/nvidia/Documents/Quanser/summer_2026/yolo_inference.py', 'w')
f.write(content)
f.close()
print('Done')
"
```

```bash
python3 ~/Documents/Quanser/summer_2026/yolo_inference.py
```

Should print a detection summary table.

---

## Step 16 — Test Fine-tuning

```bash
python3 -c "
f = open('/home/nvidia/Documents/Quanser/summer_2026/yolo_finetune.py')
content = f.read()
f.close()
content = content.replace(\"SESSION = 'session_003'\", \"SESSION = 'session_001'\")
f = open('/home/nvidia/Documents/Quanser/summer_2026/yolo_finetune.py', 'w')
f.write(content)
f.close()
print('Done')
"
```

```bash
python3 ~/Documents/Quanser/summer_2026/yolo_finetune.py
```

This runs pseudo-labeling, fine-tunes YOLOv8 locally on the Jetson (~5-10 minutes), and saves federation-ready weights to:

```
~/Documents/Quanser/summer_2026/fl_weights/QCar2_02_weights.pt
```

---

## Running CSI Camera Scripts

All scripts using CSI cameras require:

```bash
sudo -E PYTHONPATH=/usr/local/lib/python3.8/site-packages \
  DISPLAY=:0 XAUTHORITY=/run/user/124/gdm/Xauthority \
  python3 your_script.py
```

LiDAR and RealSense scripts run without sudo:

```bash
python3 your_script.py
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Green screen from CSI cameras | nvarguscamerasrc not used — check GStreamer pipeline |
| `XOpenDisplay failed` | Missing DISPLAY or XAUTHORITY — check GDM UID |
| `GStreamer: NO` in OpenCV | Recompile OpenCV — follow Steps 6–8 |
| Camera not in `/dev/video*` | Check physical ribbon cable connections |
| nvargus-daemon errors | `sudo systemctl restart nvargus-daemon` |
| Wrong camera direction | Update sensor-id mapping in `csi_cameras.py` |
| Permission denied on data folder | `sudo chown -R nvidia:nvidia ~/Documents/Quanser/summer_2026/data` |
| RealSense server status errors | Warnings only — script continues normally |
| YOLOv8 model download fails | Needs internet — check network connection |
| Argus daemon crashes (4 cameras) | Use sequential capture — already implemented in `csi_cameras.py` |

---

## FL Weights Location

After fine-tuning, federation-ready weights are at:

```
~/Documents/Quanser/summer_2026/fl_weights/QCar2_02_weights.pt
```

Upload to H200:

```bash
scp ~/Documents/Quanser/summer_2026/fl_weights/QCar2_02_weights.pt \
  nvidia@H200:/fl_server/weights/
```

---

*Sinha Data Science Innovation Lab — University of North Texas — Summer 2026*
