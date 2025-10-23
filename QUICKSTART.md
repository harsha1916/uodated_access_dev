# 🚀 CamCap - Quick Start Guide

Get your push button camera system running in 10 minutes!

## 📝 Step-by-Step Setup

### Step 1: Create `.env` File (2 minutes)

Create a file named `.env` with this content:

```bash
# GPIO Pins
BTN1_GPIO=18
BTN2_GPIO=19

# Camera Enable/Disable
CAM1_ENABLED=true
CAM2_ENABLED=true

# RTSP URLs - CHANGE THESE!
CAM1_RTSP=rtsp://admin:admin@192.168.1.201:554/avstream/channel=1/stream=0.sdp
CAM2_RTSP=rtsp://admin:admin@192.168.1.202:554/avstream/channel=1/stream=0.sdp

# Camera Credentials
CAM_USERNAME=admin
CAM_PASSWORD=admin
CAM1_IP=192.168.1.201
CAM2_IP=192.168.1.202

# Storage
MEDIA_DIR=/home/maxpark
RETENTION_DAYS=120

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
FLASK_DEBUG=0

# Authentication (Password: admin123)
WEB_AUTH_ENABLED=true
WEB_PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G
SECRET_KEY=change-this-secret-key-in-production

# Upload
UPLOAD_MODE=POST
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_AUTH_BEARER=
UPLOAD_FIELD_NAME=file
UPLOAD_ENABLED=true

# Offline retry settings
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60
```

**⚠️ IMPORTANT:** Change `CAM1_RTSP` and `CAM2_RTSP` to your camera URLs!

### Step 2: Install Dependencies (3 minutes)

```bash
# Install system packages
sudo apt update
sudo apt install -y ffmpeg python3-pip

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Wire Push Buttons (3 minutes)

```
Button 1 (Camera 1 - Entry):
  [Button] Pin 1 ──→ Raspberry Pi Physical Pin 12 (GPIO 18)
  [Button] Pin 2 ──→ Raspberry Pi Physical Pin 6 (GND)

Button 2 (Camera 2 - Exit):
  [Button] Pin 1 ──→ Raspberry Pi Physical Pin 35 (GPIO 19)
  [Button] Pin 2 ──→ Raspberry Pi Physical Pin 9 (GND)
```

### Step 4: Run System (1 minute)

```bash
python app.py
```

You should see:
```
[APP] Starting CamCap on 0.0.0.0:8080
[APP] Authentication: ENABLED
[APP] Upload: ENABLED
[APP] Cameras: r1=ENABLED, r2=ENABLED
[GPIO] ✓ Buttons configured: GPIO 18 (r1), GPIO 19 (r2)
[UPLOADER] Background upload thread started
```

### Step 5: Access Web Interface (1 minute)

**Open browser:** `http://your-raspberry-pi-ip:8080`

**Login:** Password is `admin123`

**You should see:**
- 📹 Camera Health (showing online/offline)
- 🌡️ System Monitor (RPi temperature)
- ☁️ Upload Status
- ⚡ GPIO Triggers
- 🖼️ Recent Images

### Step 6: Test Push Buttons!

**Press Button 1:**
- Terminal should show: `[GPIO] 🔔 BUTTON 1 PRESSED - Capturing r1...`
- Dashboard GPIO Triggers count should increase
- New image appears in recent images

**Press Button 2:**
- Terminal should show: `[GPIO] 🔔 BUTTON 2 PRESSED - Capturing r2...`
- Dashboard updates
- New image appears

## ✅ Success Checklist

Your system is working if:

- [ ] Web interface loads at `http://pi-ip:8080`
- [ ] Can login with password `admin123`
- [ ] Dashboard shows camera health status
- [ ] RPi temperature displayed (or N/A)
- [ ] Press Button 1 → Terminal shows "BUTTON 1 PRESSED"
- [ ] GPIO Triggers count increases
- [ ] Image appears in Recent Images section
- [ ] Configuration tab allows changing settings
- [ ] Can save configuration from web

## 🔧 Troubleshooting

### Web interface not loading

```bash
# Check if running
ps aux | grep app.py

# Check port
sudo netstat -tlnp | grep 8080

# Try accessing locally first
curl http://localhost:8080
```

### GPIO buttons not working

```bash
# Verify wiring:
# - Button pin 1 to Physical Pin 12 (GPIO 18)
# - Button pin 2 to GND (Pin 6)

# Run with sudo
sudo python app.py
```

### Camera shows offline

```bash
# Test RTSP URL
ffplay "rtsp://admin:admin@192.168.1.201:554/stream"

# Or with VLC
vlc "rtsp://admin:admin@192.168.1.201:554/stream"

# Check if reachable
ping 192.168.1.201
```

### Upload not working

- Dashboard → Check upload status (should be 🟢 ONLINE)
- If offline, system will retry when internet returns
- Check pending count - shows queued uploads

## 🎯 Common Tasks

### Change Camera RTSP URL

**Option 1: Web Interface (Recommended)**
1. Open dashboard → Configuration tab
2. Edit RTSP URL for camera
3. Click "💾 Save Configuration"
4. Done! No restart needed!

**Option 2: Edit .env**
1. Edit `.env` file
2. Change `CAM1_RTSP` or `CAM2_RTSP`
3. Changes apply on next capture (dynamic reload!)

### Disable a Camera

1. Configuration tab
2. Uncheck camera checkbox
3. Save Configuration
4. Camera disabled immediately!

### View Images for Specific Date

1. Click "📅 Images" tab
2. Select date from date picker
3. (Optional) Filter by camera
4. Click "Load"
5. Browse paginated results

## 🎊 What You Have Now

✅ Push button triggers (GPIO 18 & 19)
✅ 2 cameras (r1 Entry, r2 Exit)
✅ Instant image capture with ffmpeg
✅ Background S3 upload
✅ Offline operation (auto-retry when online)
✅ Web dashboard with 4 tabs
✅ Camera health monitoring
✅ RPi temperature display
✅ Configuration management (change URLs from web!)
✅ Enable/disable cameras from web
✅ Storage analysis
✅ Date-wise image viewing with pagination
✅ Password protected (admin123)
✅ 120-day automatic cleanup
✅ Terminal shows button press messages

## 🎓 Pro Tips

1. **Monitor terminal** - See button presses in real-time
2. **Use Configuration tab** - Much easier than editing .env
3. **Check camera health** - Before wondering why no images
4. **Works offline** - Don't worry about internet outages
5. **Filter by date** - Find images from specific day easily

## 📞 Need Help?

**Check logs:**
```bash
# Terminal output
python app.py

# Or if running as service
sudo journalctl -u camcap -f
```

**Look for:**
- `[GPIO] 🔔 BUTTON X PRESSED` - Button triggers working
- `[SNAP] ✓ r1 -> path` - Image captured successfully
- `[UPLOADER] ✓ Uploaded:` - Upload succeeded
- `[UPLOADER] Offline` - System in offline mode

---

**You're all set! Press your buttons and watch images appear!** 🎉

**Default login:** `http://your-pi-ip:8080` with password `admin123`

