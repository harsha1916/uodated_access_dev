# Raspberry Pi Zero 2W Setup Guide

## ✅ **Pi Zero 2W Compatibility - EXCELLENT CHOICE!**

The Raspberry Pi Zero 2W is **perfect** for this project:
- ✅ **Quad-core ARM Cortex-A53** (1GHz) - sufficient for image capture
- ✅ **512MB RAM** - adequate for Flask app + image processing
- ✅ **GPIO pins** - native GPIO support
- ✅ **WiFi** - for web dashboard access
- ✅ **Low power** - ideal for 24/7 operation
- ✅ **Small form factor** - compact installation

## 📦 **Required Libraries Installation**

### **1. Update System**
```bash
sudo apt update && sudo apt upgrade -y
```

### **2. Install System Dependencies**
```bash
# Essential packages
sudo apt install -y python3 python3-pip python3-venv git

# Image processing and camera support
sudo apt install -y ffmpeg v4l-utils

# GPIO and hardware support
sudo apt install -y python3-gpiozero python3-rpi.gpio

# Database support
sudo apt install -y sqlite3

# Network tools
sudo apt install -y curl wget
```

### **3. Install Python Dependencies**
```bash
# Create virtual environment (recommended)
python3 -m venv camcap_env
source camcap_env/bin/activate

# Install required packages
pip install Flask==3.0.3
pip install gpiozero==2.0.1
pip install RPi.GPIO==0.7.1
pip install python-dotenv==1.0.1
pip install requests==2.32.3
pip install opencv-python-headless==4.8.1.78
pip install Pillow==10.0.1
```

### **4. Verify GPIO Access**
```bash
# Test GPIO access
python3 -c "from gpiozero import Button; print('GPIO access: OK')"
```

## 🔧 **Hardware Setup for Pi Zero 2W**

### **GPIO Pin Layout:**
```
Pi Zero 2W GPIO Pins:
┌─────────────────┐
│ 1: 3.3V   2: 5V │
│ 3: GPIO2  4: 5V │
│ 5: GPIO3  6: GND │
│ 7: GPIO4  8: GPIO14│
│ 9: GND   10: GPIO15│
│11: GPIO17 12: GPIO18│ ← Button 1 (r1)
│13: GPIO27 14: GND │
│15: GPIO22 16: GPIO23│
│17: 3.3V  18: GPIO24│
│19: GPIO10 20: GND │
│21: GPIO9 22: GPIO25│
│23: GPIO11 24: GPIO8 │
│25: GND   26: GPIO7 │
│27: GPIO0 28: GPIO1 │
│29: GPIO5 30: GND   │
│31: GPIO6 32: GPIO12│
│33: GPIO13 34: GND │
│35: GPIO19 36: GPIO16│ ← Button 2 (r2)
│37: GPIO26 38: GPIO20│
│39: GND   40: GPIO21│
└─────────────────┘
```

### **Button Wiring:**
```
Button 1 (r1): GPIO 18 → Button → GND
Button 2 (r2): GPIO 19 → Button → GND
```

## ⚙️ **Configuration for Pi Zero 2W**

### **1. Environment Variables (.env)**
```bash
# GPIO Configuration
BTN1_GPIO=18
BTN2_GPIO=19

# Camera Configuration
CAM1_RTSP=rtsp://username:password@192.168.1.100:554/stream1
CAM2_RTSP=rtsp://username:password@192.168.1.101:554/stream1
CAM1_ENABLED=true
CAM2_ENABLED=true

# Storage
MEDIA_DIR=/home/pi/camcap/images
RETENTION_DAYS=120

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
FLASK_DEBUG=0

# Authentication
WEB_AUTH_ENABLED=true
WEB_PASSWORD_HASH=your_sha256_hash_here
SECRET_KEY=your_secret_key_here

# Upload
UPLOAD_MODE=POST
UPLOAD_ENDPOINT=https://your-s3-endpoint.com/upload
UPLOAD_AUTH_BEARER=your_bearer_token
UPLOAD_FIELD_NAME=singleFile
UPLOAD_ENABLED=true

# Offline mode
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60
```

### **2. Create Directory Structure**
```bash
mkdir -p /home/pi/camcap/images
mkdir -p /home/pi/camcap/logs
chmod 755 /home/pi/camcap/images
```

## 🚀 **Performance Optimization for Pi Zero 2W**

### **1. Memory Optimization**
```bash
# Add to /boot/config.txt
sudo nano /boot/config.txt

# Add these lines:
gpu_mem=128
disable_camera_led=1
```

### **2. CPU Governor**
```bash
# Set CPU governor to performance
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### **3. Swap Configuration**
```bash
# Increase swap for better performance
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🔧 **System Service Setup**

### **1. Create Systemd Service**
```bash
sudo nano /etc/systemd/system/camcap.service
```

```ini
[Unit]
Description=CamCap Image Capture System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/camcap
Environment=PATH=/home/pi/camcap_env/bin
ExecStart=/home/pi/camcap_env/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **2. Enable and Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable camcap.service
sudo systemctl start camcap.service
sudo systemctl status camcap.service
```

## 📊 **Pi Zero 2W Performance Expectations**

### **Resource Usage:**
- **CPU**: ~20-30% during capture
- **RAM**: ~150-200MB total usage
- **Storage**: ~50MB for app + images
- **Network**: Minimal (only during upload)

### **Capabilities:**
- ✅ **GPIO Triggers**: Instant response
- ✅ **Image Capture**: 2-5 seconds per image
- ✅ **Web Dashboard**: Responsive interface
- ✅ **Background Upload**: Non-blocking
- ✅ **24/7 Operation**: Stable and reliable

### **Limitations:**
- ⚠️ **Single-threaded capture**: One camera at a time
- ⚠️ **Limited RAM**: Keep image sizes reasonable
- ⚠️ **Network dependent**: Upload requires stable connection

## 🧪 **Testing on Pi Zero 2W**

### **1. GPIO Test**
```bash
python3 test_gpio_minimal.py
```

### **2. Full System Test**
```bash
python3 app.py
```

### **3. Performance Monitor**
```bash
# Monitor system resources
htop
# Monitor GPIO
gpio readall
```

## ✅ **Pi Zero 2W is PERFECT for this project!**

**Advantages:**
- 🚀 **Sufficient Performance**: Handles image capture + web server
- 🔋 **Low Power**: Ideal for 24/7 operation
- 📱 **Compact**: Small form factor for installation
- 🔌 **GPIO Native**: Direct hardware access
- 🌐 **WiFi Built-in**: No additional hardware needed
- 💰 **Cost Effective**: Affordable solution

**The Pi Zero 2W will handle this project excellently!** 🎯

