## observer.py
#
# Windows observer for QCar2 sensor streams.
# Displays all sensor feeds from the QCar2:
#   - 4x CSI cameras (Front, Rear, Left, Right)
#   - RealSense RGB
#   - RealSense Depth
#   - LiDAR bird's eye view
#
# RUN ON WINDOWS LAPTOP before starting any QCar2 sensor script.
#
# HOW TO RUN:
#   python3 observer.py

import sys
sys.path.insert(0, 'C:/Users/cliff/Documents/Quanser/libraries/python')

from pal.utilities.probe import Observer

observer = Observer()

# ── CSI Cameras (820x616) ─────────────────────────────────────────────────────
observer.add_display(imageSize=[616, 820, 3], scalingFactor=2, name='Front Camera')
observer.add_display(imageSize=[616, 820, 3], scalingFactor=2, name='Rear Camera')
observer.add_display(imageSize=[616, 820, 3], scalingFactor=2, name='Left Camera')
observer.add_display(imageSize=[616, 820, 3], scalingFactor=2, name='Right Camera')

# ── RealSense (640x480) ───────────────────────────────────────────────────────
observer.add_display(imageSize=[480, 640, 3], scalingFactor=2, name='RGB')
observer.add_display(imageSize=[480, 640, 3], scalingFactor=2, name='Depth')

# ── LiDAR bird's eye view (512x512) ──────────────────────────────────────────
observer.add_display(imageSize=[512, 512, 3], scalingFactor=1, name='LiDAR')

observer.launch()
