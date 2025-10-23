# 📷 CamCap - Push Button Camera Capture System

Press-to-capture system for 2 RTSP cameras using GPIO push buttons on Raspberry Pi.  
Features web dashboard with health monitoring, offline operation, and automatic S3 upload.

## ✨ Features

- **🔘 Push Button Triggers** - GPIO buttons (pins 18 & 19) capture images instantly
- **📹 2 Cameras** - r1 (Entry) and r2 (Exit) with independent RTSP streams
- **☁️ Background S3 Upload** - Automatic upload in background thread
- **📡 Offline Operation** - Works without internet, auto-uploads when connection returns
- **🌐 Web Dashboard** - Modern UI with 4 tabs
- **📊 Health Monitoring** - Camera online/offline status & RPi temperature
- **⚙️ Web Configuration** - Change RTSP URLs and settings without restart
- **💾 Storage Analysis** - View stats by camera and date
- **📅 Date-wise Viewing** - Browse images by specific date with pagination
- **🔒 Password Protected** - Secure login (default: admin123)
- **🗑️ Auto Cleanup** - Automatically deletes images older than 120 days

## 🎯 How It Works

```
Push Button 1 (GPIO 18) → Captures from Camera 1 → Saves as r1_{timestamp}.jpg
Push Button 2 (GPIO 19) → Captures from Camera 2 → Saves as r2_{timestamp}.jpg
                                    ↓
                          Background thread uploads to S3
                                    ↓
                          (Works offline, retries when online)
```

## 📋 Requirements

- **Hardware:** Raspberry Pi (any model with GPIO)
- **OS:** Raspberry Pi OS
- **Software:** Python 3.7+, ffmpeg
- **Cameras:** 2 RTSP cameras

## 🚀 Quick Setup

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
```

### 2. Clone/Copy Files

```bash
mkdir -p ~/camcap && cd ~/camcap
# Copy all project files here
```

### 3. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 4. Configure

```bash
cp config.example.env .env
nano .env
```

**Update these settings:**
```bash
# Your camera RTSP URLs
CAM1_RTSP=rtsp://admin:admin@192.168.1.201:554/stream
CAM2_RTSP=rtsp://admin:admin@192.168.1.202:554/stream

# Or use IP-based auto-generation
CAM1_IP=192.168.1.201
CAM2_IP=192.168.1.202
CAM_USERNAME=admin
CAM_PASSWORD=admin

# S3 upload endpoint
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
```

### 5. Wire Push Buttons

```
Button 1 (Entry):
  Terminal 1 → GPIO 18 (Physical Pin 12)
  Terminal 2 → GND (Physical Pin 6)

Button 2 (Exit):
  Terminal 1 → GPIO 19 (Physical Pin 35)
  Terminal 2 → GND (Physical Pin 9)
```

### 6. Run

```bash
# Test mode (non-sudo)
python app.py

# Or with GPIO permissions
sudo -E env "PATH=$PATH" ./.venv/bin/python app.py
```

### 7. Access Web Interface

**Browser:** `http://your-raspberry-pi-ip:8080`  
**Password:** `admin123`

## 🎨 Web Dashboard (4 Tabs)

### 1. 🏠 Dashboard
- **Camera Health:** Shows 🟢 ONLINE or 🔴 OFFLINE for each camera
- **System Monitor:** Displays Raspberry Pi CPU temperature
- **Upload Status:** Shows online/offline, uploaded count, pending count
- **GPIO Triggers:** Visual indicators with trigger counts
- **Recent Images:** Last 10 captured images with thumbnails

### 2. ⚙️ Configuration
- **Enable/Disable Cameras:** Toggle checkboxes
- **Change RTSP URLs:** Edit URLs for each camera
- **Camera IPs:** Set camera IP addresses
- **S3 Upload Settings:** Enable/disable upload, change endpoint
- **💾 Save Button:** Applies changes immediately (no restart!)

### 3. 💾 Storage
- **Total Images:** Count of all stored images
- **Uploaded vs Pending:** Track upload progress
- **Breakdown by Camera:** See image count per camera (r1/r2)

### 4. 📅 Images
- **Date Picker:** Select any date to view
- **Camera Filter:** Filter by r1 or r2
- **Pagination:** Browse 50 images per page
- **Image Grid:** Click to view full size

## 📡 Offline Operation

**Works without internet!**

- Images always saved locally first
- Upload queue stored in SQLite database
- When offline: Images queued for upload
- When online returns: Auto-uploads all pending images
- Dashboard shows 🟢 ONLINE or 🔴 OFFLINE status

**Example:**
```
Day 1: Internet down → 100 images captured → All saved locally
Day 2: Internet restored → Background thread uploads all 100 images automatically
```

## 🔌 GPIO Wiring Reference

| Camera | GPIO (BCM) | Physical Pin | Button Wiring |
|--------|------------|--------------|---------------|
| r1 (Entry) | 18 | Pin 12 | One side to Pin 12, other to GND |
| r2 (Exit) | 19 | Pin 35 | One side to Pin 35, other to GND |

**GND Pins:** Physical pins 6, 9, 14, 20, 25, 30, 34, 39

## ⚙️ Configuration Options

All settings in `.env` file:

```bash
# GPIO Pins (BCM numbering)
BTN1_GPIO=18
BTN2_GPIO=19

# Enable/Disable cameras
CAM1_ENABLED=true
CAM2_ENABLED=true

# RTSP URLs (or use IP-based auto-generation)
CAM1_RTSP=rtsp://admin:admin@ip:port/stream
CAM2_RTSP=rtsp://admin:admin@ip:port/stream

# Storage
MEDIA_DIR=/home/maxpark
RETENTION_DAYS=120

# Web Server
FLASK_HOST=0.0.0.0
FLASK_PORT=8080

# Authentication
WEB_AUTH_ENABLED=true
WEB_PASSWORD_HASH=<bcrypt_hash>  # Password: admin123

# Upload
UPLOAD_ENABLED=true
UPLOAD_ENDPOINT=https://your-api.com/upload
```

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard (requires login) |
| `/login` | GET/POST | Login page |
| `/logout` | GET | Logout |
| `/images/<filename>` | GET | Serve image file |
| `/api/status` | GET | System status (cameras, storage, upload) |
| `/api/health` | GET | Camera health & system temperature |
| `/api/config` | GET | Get current configuration |
| `/api/config` | POST | Update configuration |
| `/api/images/recent` | GET | Recent images with pagination |
| `/api/images/by-date` | GET | Images for specific date |
| `/api/dates` | GET | List of dates with images |

## 🔐 Security

**Default Password:** `admin123`

**Change Password:**
```bash
# Generate new hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword', bcrypt.gensalt()).decode())"

# Add to .env
WEB_PASSWORD_HASH=<new_hash>
```

**Disable Authentication:**
```bash
WEB_AUTH_ENABLED=false
```

## 🎯 Usage Examples

### Push Button Capture
- Press Button 1 → Captures from Camera 1 → Saves as `r1_1698765432.jpg`
- Press Button 2 → Captures from Camera 2 → Saves as `r2_1698765432.jpg`
- Terminal shows: `[GPIO] 🔔 BUTTON 1 PRESSED - Capturing r1...`

### Web Interface
- View camera online/offline status
- See RPi temperature
- Check upload queue status
- Browse all captured images
- Filter by date or camera

### Change Camera Settings
1. Open web dashboard
2. Click "⚙️ Configuration" tab
3. Edit RTSP URL or IP
4. Click "💾 Save Configuration"
5. Changes applied immediately!

## 🛠️ Troubleshooting

### Push Buttons Not Working

**Check:**
```bash
# Verify GPIO library
python3 -c "import gpiozero; print('OK')"

# Check button wiring
# - One side to GPIO pin (12 or 35)
# - Other side to GND (pin 6 or 9)

# Check .env
cat .env | grep BTN
# Should show: BTN1_GPIO=18, BTN2_GPIO=19
```

### Camera Offline

**Check:**
1. Test RTSP URL with VLC or ffplay
2. Verify camera IP is reachable: `ping 192.168.1.201`
3. Check credentials in .env
4. Dashboard shows camera health status

### Upload Not Working

**Check:**
1. Dashboard shows upload status (online/offline)
2. Verify `UPLOAD_ENDPOINT` in .env
3. Check `UPLOAD_ENABLED=true`
4. Look for pending count in dashboard

### Web Interface Won't Load

**Check:**
1. System running: `ps aux | grep app.py`
2. Port not blocked: `sudo netstat -tlnp | grep 8080`
3. Access from network: `http://raspberry-pi-ip:8080`

## 🚀 Running as Service

```bash
# Install service
sudo cp camcap.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camcap
sudo systemctl start camcap

# Check status
sudo systemctl status camcap

# View logs
sudo journalctl -u camcap -f
```

## 📊 System Architecture

```
Push Buttons (GPIO 18, 19)
    ↓
gpiozero.Button (event detection)
    ↓
grab_jpeg() - ffmpeg RTSP capture
    ↓
Save to MEDIA_DIR/{source}_{epoch}.jpg
    ↓
Add to SQLite database
    ↓
Background upload thread
    ↓
(Checks internet → Uploads to S3)
    ↓
Mark as uploaded in database
```

## 📁 Project Structure

```
~/camcap/
├── app.py                  # Main Flask application
├── rtsp_capture.py         # ffmpeg RTSP frame grabber
├── storage.py              # SQLite database management
├── uploader.py             # Background S3 uploader
├── health_monitor.py       # Camera & system health monitoring
├── requirements.txt        # Python dependencies
├── config.example.env      # Configuration template
├── .env                    # Your configuration (create this!)
├── camcap.service         # Systemd service file
└── images/                 # Captured images (auto-created)
    ├── r1_*.jpg
    └── r2_*.jpg
```

## 🎓 Tips

1. **Test cameras first:** Open RTSP URLs in VLC before configuring
2. **Use Configuration tab:** Easier than editing .env manually
3. **Monitor health:** Dashboard shows if cameras are reachable
4. **Check logs:** Terminal output shows button presses and captures
5. **Offline mode:** System works fine without internet, uploads later

## 📚 Additional Documentation

- `config.example.env` - All configuration options explained
- `camcap.service` - Systemd service configuration

## 🤝 Support

**Check logs for errors:**
```bash
# Real-time
sudo journalctl -u camcap -f

# Or if running manually
python app.py  # Watch terminal output
```

**Common issues:**
- GPIO permissions → Run with sudo
- ffmpeg not found → `sudo apt install ffmpeg`
- Module not found → `pip install -r requirements.txt`

## 📄 License

This project is provided as-is for your use.

---

**Quick Start:** Create `.env`, install deps, wire buttons, run `python app.py`, open `http://pi-ip:8080` 🚀
