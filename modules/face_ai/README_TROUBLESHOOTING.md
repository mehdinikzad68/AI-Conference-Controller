# Face AI Module - Troubleshooting Guide

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Dependency Installation](#dependency-installation)
3. [Common Issues & Solutions](#common-issues--solutions)
4. [Environment Setup](#environment-setup)
5. [Performance Optimization](#performance-optimization)
6. [Testing & Validation](#testing--validation)

---

## 🚀 Quick Start

### Minimum Requirements

- **Python**: 3.10+ (3.11+ recommended)
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **RAM**: 4GB minimum, 8GB+ recommended
- **Camera**: USB webcam or built-in camera

### Quick Installation

```bash
# 1. Check dependencies
python modules/face_ai/dependency_checker.py

# 2. Install core dependencies
pip install opencv-python numpy PyQt6

# 3. Install AI packages
pip install deepface fer dlib

# 4. Download dlib shape predictor model
# Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# Extract to: assets/models/shape_predictor_68_face_landmarks.dat
```

---

## 📦 Dependency Installation

### Core Dependencies

| Package | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| OpenCV | >=4.8.0 | Computer vision, camera access | `pip install opencv-python` |
| NumPy | >=1.24.0 | Numerical operations | `pip install numpy` |
| PyQt6 | >=6.6.0 | UI framework | `pip install PyQt6` |
| Matplotlib | >=3.7.0 | Charts and reports | `pip install matplotlib` |

### AI/ML Dependencies

| Package | Version | Purpose | Installation Notes |
|---------|---------|---------|---------------------|
| DeepFace | >=0.0.79 | Face detection, emotion, age, gender | `pip install deepface` |
| FER | >=22.5.0 | Facial emotion recognition (validation) | `pip install fer` |
| dlib | >=19.24.0 | Head pose estimation | See [dlib Installation](#dlib-installation) |

### dlib Installation

**Windows:**
```bash
# Option 1: Pre-built wheel (recommended)
pip install dlib-binary

# Option 2: Using conda (if using conda environment)
conda install -c conda-forge dlib

# Option 3: Build from source (requires Visual Studio Build Tools)
# Download dlib source and build with CMake
```

**Linux:**
```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev

# Then install dlib
pip install dlib
```

**macOS:**
```bash
# Install system dependencies
brew install cmake

# Then install dlib
pip install dlib
```

### Model Files

**Required Model:**
- `shape_predictor_68_face_landmarks.dat` (99.7 MB)
  - Download: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
  - Extract and place in: `assets/models/shape_predictor_68_face_landmarks.dat`

**Automatic Download (Future):**
```python
# The module will automatically download if not found (future feature)
from modules.face_ai.head_pose_estimator import HeadPoseEstimator
estimator = HeadPoseEstimator()  # Will auto-download model if missing
```

---

## 🔧 Common Issues & Solutions

### 1. ImportError: No module named 'deepface'

**Symptoms:**
```
ImportError: No module named 'deepface'
DeepFace not available. Install with: pip install deepface
```

**Solutions:**
```bash
# Verify Python environment
python --version  # Should be 3.10+

# Install deepface
pip install deepface

# If using virtual environment, activate it first
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Verify installation
python -c "from deepface import DeepFace; print('OK')"
```

**Check Interpreter Path:**
```python
import sys
print(sys.executable)  # Should match your IDE interpreter
```

---

### 2. ImportError: No module named 'fer'

**Symptoms:**
```
ImportError: No module named 'fer'
FER not available. Install with: pip install fer
```

**Solutions:**
```bash
pip install fer

# Verify installation
python -c "from fer import FER; print('OK')"
```

---

### 3. dlib Installation Failure

**Symptoms:**
```
ERROR: Failed building wheel for dlib
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solutions (Windows):**
```bash
# Option 1: Use pre-built wheel
pip install dlib-binary

# Option 2: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Install "Desktop development with C++" workload

# Option 3: Use conda
conda install -c conda-forge dlib
```

**Solutions (Linux):**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev

pip install dlib
```

---

### 4. Camera Not Found / Camera Index Out of Range

**Symptoms:**
```
[ERROR] cv::obsensor::getStreamChannelGroup Camera index out of range
Failed to open camera at index 0
```

**Solutions:**
1. **Check available cameras:**
```python
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: Available")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```

2. **Try different camera index:**
   - In Face AI window, select a different camera from the dropdown
   - Common indices: 0 (default), 1, 2

3. **Check camera permissions:**
   - Windows: Settings → Privacy → Camera → Allow apps to access camera
   - Linux: Check `v4l2` devices: `ls /dev/video*`
   - macOS: System Preferences → Security & Privacy → Camera

4. **Close other applications using camera:**
   - Close Zoom, Teams, Skype, etc.
   - Check Windows Camera app is closed

---

### 5. OpenCV GUI Support Error

**Symptoms:**
```
cv2.error: The function is not implemented. 
Rebuild the library with Windows, GTK+ 2.x or Cocoa support.
```

**Explanation:**
- This error occurs when calling `cv2.destroyAllWindows()` or `cv2.imshow()`
- The application uses PyQt for display, not OpenCV windows
- This error is **non-critical** and has been handled in the code

**Solution:**
- No action needed - error is caught and handled gracefully
- If you see this error, it's logged but doesn't affect functionality

---

### 6. Model File Not Found

**Symptoms:**
```
FileNotFoundError: shape_predictor_68_face_landmarks.dat not found
```

**Solutions:**
1. **Download model file:**
   - URL: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
   - Extract the .bz2 file
   - Place in: `assets/models/shape_predictor_68_face_landmarks.dat`

2. **Verify file location:**
```python
from pathlib import Path
model_path = Path("assets/models/shape_predictor_68_face_landmarks.dat")
print(f"Model exists: {model_path.exists()}")
print(f"Full path: {model_path.absolute()}")
```

3. **Alternative locations checked:**
   - `assets/models/shape_predictor_68_face_landmarks.dat`
   - `modules/face_ai/shape_predictor_68_face_landmarks.dat`
   - Absolute path from project root

---

### 7. Slow Performance / Low FPS

**Symptoms:**
- Frame rate drops below 5 FPS
- High CPU usage (>80%)
- UI becomes unresponsive

**Solutions:**

1. **Reduce processing rate:**
   - In Face AI window, set "Process every" to 3-5 frames
   - Reduces analysis frequency

2. **Lower camera resolution:**
```python
# In face_ai_controller.py, modify:
self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Instead of 640
self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Instead of 480
```

3. **Use faster backend:**
   - In Advanced Settings, select "opencv" or "ssd" instead of "retinaface"
   - RetinaFace is most accurate but slowest

4. **Disable FER (if using DeepFace):**
   - FER is used for validation only
   - Can disable in Advanced Settings if DeepFace is sufficient

5. **Check system resources:**
```python
import psutil
print(f"CPU: {psutil.cpu_percent()}%")
print(f"RAM: {psutil.virtual_memory().percent}%")
```

---

### 8. Memory Leak / High RAM Usage

**Symptoms:**
- RAM usage grows continuously
- Application becomes slow after extended use

**Solutions:**
1. **Restart analysis periodically:**
   - Stop and restart Face AI analysis every 30-60 minutes

2. **Clear statistics:**
   - Use "Reset" button to clear accumulated data

3. **Monitor memory:**
```python
import psutil
import os
process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

---

### 9. No Faces Detected

**Symptoms:**
- Camera feed shows but no faces detected
- Statistics show 0 faces

**Solutions:**
1. **Check lighting:**
   - Ensure good lighting in room
   - Avoid backlighting

2. **Check camera focus:**
   - Ensure camera is in focus
   - Faces should be clearly visible

3. **Adjust detection threshold:**
   - In Advanced Settings, lower "Emotion Confidence Threshold"

4. **Try different backend:**
   - Some backends work better in different conditions
   - Try: retinaface, mtcnn, opencv

5. **Check face size:**
   - Faces should be at least 50x50 pixels
   - Move closer to camera if needed

---

### 10. IDE vs Terminal Execution Differences

**Symptoms:**
- Works in terminal but not in IDE (or vice versa)
- Different interpreter paths

**Solutions:**
1. **Verify interpreter:**
```python
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
```

2. **IDE Configuration:**
   - VS Code: Check `.vscode/settings.json` for `python.defaultInterpreterPath`
   - PyCharm: File → Settings → Project → Python Interpreter
   - Ensure same interpreter as terminal

3. **Virtual Environment:**
   - If using venv, activate in IDE:
   - VS Code: Select interpreter from venv
   - PyCharm: Mark venv as project interpreter

---

## 🛠️ Environment Setup

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python modules/face_ai/dependency_checker.py
```

### Conda Environment

```bash
# Create conda environment
conda create -n face_ai python=3.11

# Activate
conda activate face_ai

# Install packages
conda install -c conda-forge opencv numpy matplotlib
pip install deepface fer
conda install -c conda-forge dlib

# Verify
python modules/face_ai/dependency_checker.py
```

---

## ⚡ Performance Optimization

### Recommended Settings for Different Use Cases

**High Accuracy (Best Quality):**
- Backend: RetinaFace
- Model: VGG-Face
- Process every: 1 frame
- FPS: 10-15

**Balanced (Default):**
- Backend: RetinaFace
- Model: VGG-Face
- Process every: 2 frames
- FPS: 15-20

**Fast (Low Latency):**
- Backend: OpenCV or SSD
- Model: VGG-Face
- Process every: 3-5 frames
- FPS: 20-30

**Low Resources:**
- Backend: OpenCV
- Model: VGG-Face
- Process every: 5 frames
- FPS: 10-15
- Disable FER

---

## 🧪 Testing & Validation

### Run Dependency Check

```bash
python modules/face_ai/dependency_checker.py
```

### Test Module Import

```python
python -c "from modules.face_ai import FaceAIController, FaceAIWindow; print('OK')"
```

### Run Test Script

```bash
python modules/face_ai/test_face_ai.py
```

### Manual Test

```python
from modules.face_ai import FaceAIController

controller = FaceAIController()

# Test camera access
if controller.start_analysis(camera_index=0, fps=15):
    print("✓ Analysis started successfully")
    controller.stop_analysis()
else:
    print("✗ Failed to start analysis")
```

---

## 📝 Additional Resources

### Documentation
- [DeepFace Documentation](https://github.com/serengil/deepface)
- [FER Documentation](https://github.com/justinshenk/fer)
- [dlib Documentation](http://dlib.net/)
- [OpenCV Documentation](https://docs.opencv.org/)

### Support
- Check `modules/face_ai/dependency_checker.py` for diagnostics
- Review logs in console output
- Check `modules/face_ai/test_face_ai.py` for examples

---

## ✅ Verification Checklist

Before reporting issues, verify:

- [ ] Python 3.10+ installed
- [ ] All core dependencies installed (`opencv-python`, `numpy`, `PyQt6`)
- [ ] AI packages installed (`deepface`, `fer`, `dlib`)
- [ ] Model file downloaded and placed correctly
- [ ] Camera accessible and working
- [ ] Correct interpreter selected in IDE (if using IDE)
- [ ] Virtual environment activated (if using venv)
- [ ] Ran `dependency_checker.py` and reviewed output

---

**Last Updated:** 2024
**Module Version:** 1.0.0

