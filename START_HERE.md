# 🚀 START HERE - Quick Setup Guide

## ⚡ IMPORTANT: Create Your `.env` File First!

### Step 1: Create `.env` File

Create a new file called `.env` in this directory with the following content:

```bash
# ===========================
# Camera Configuration
# ===========================
CAMERA_USERNAME=admin
CAMERA_PASSWORD=admin

CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203

CAMERA_1_RTSP=
CAMERA_2_RTSP=
CAMERA_3_RTSP=

CAMERA_1_ENABLED=true
CAMERA_2_ENABLED=true
CAMERA_3_ENABLED=true

# ===========================
# S3 Upload Configuration
# ===========================
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
UPLOAD_QUEUE_SIZE=100
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60

# ===========================
# GPIO Configuration - IMPORTANT!
# ===========================
# Set to true to enable GPIO on Raspberry Pi
GPIO_ENABLED=true
GPIO_TRIGGER_ENABLED=true

GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20

GPIO_BOUNCE_TIME=300

# ===========================
# Network Configuration
# ===========================
MAX_RETRIES=5
RETRY_DELAY=5

# Change this to your Raspberry Pi IP!
BIND_IP=192.168.1.33
BIND_PORT=9000

# ===========================
# Storage Configuration
# ===========================
IMAGE_STORAGE_PATH=images
IMAGE_RETENTION_DAYS=120
CLEANUP_INTERVAL_HOURS=24

# ===========================
# Web Authentication
# ===========================
WEB_AUTH_ENABLED=true

# Password: admin123
PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G

# Change this to a random string!
SECRET_KEY=change-this-to-random-string-in-production
```

### Step 2: Customize Settings

**MUST CHANGE:**
- `BIND_IP` → Your Raspberry Pi's IP address
- `CAMERA_X_IP` → Your camera IP addresses  
- `GPIO_ENABLED` → **MUST be `true` for GPIO to work!**

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install RPi.GPIO
```

### Step 4: Run the System

```bash
python main.py
```

You should see:
```
GPIO service initialized successfully
GPIO pin 18 configured for camera_1 (r1/entry)
GPIO pin 19 configured for camera_2 (r2/exit)
GPIO pin 20 configured for camera_3 (r3/auxiliary)
Started monitoring GPIO pin 18 for camera_1
Started monitoring GPIO pin 19 for camera_2
Started monitoring GPIO pin 20 for camera_3
Web interface available at http://192.168.1.33:9000
```

### Step 5: Access Web Interface

**Open browser:** `http://192.168.1.33:9000`

**Login:** Password is `admin123`

## 🔌 GPIO Wiring

Connect pins to GND to trigger capture:

```
GPIO 18 (Pin 12) + GND → Captures Camera 1 (r1/Entry)
GPIO 19 (Pin 35) + GND → Captures Camera 2 (r2/Exit)
GPIO 20 (Pin 38) + GND → Captures Camera 3 (r3/Auxiliary)
```

## ✅ Verify GPIO is Working

### Check Dashboard

1. Open http://192.168.1.33:9000
2. Look at **⚡ GPIO Triggers** card
3. Connect Pin 18 to GND
4. **You should see:**
   - Light turns GREEN and pulses
   - Count increases to 1
   - Card highlights in blue

### Check Logs

```bash
tail -f camera_system.log | grep TRIGGER
```

When you connect Pin 18 to GND, you should see:
```
🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
camera_1 (r1): Image captured -> r1_1234567890.jpg
```

## ⚙️ Using Configuration Tab

### Change Camera Settings (No Restart!)

1. Click **⚙️ Configuration** tab
2. Modify settings:
   - Check/uncheck to enable/disable cameras
   - Change IP addresses
   - Change RTSP URLs
3. Click **💾 Save Configuration**
4. Done! Changes apply immediately!

## 🎯 Quick Troubleshooting

### GPIO Not Working?

**Check this:**
```bash
# 1. Verify .env file exists
ls -la .env

# 2. Check GPIO_ENABLED is true
cat .env | grep GPIO_ENABLED

# Should show:
# GPIO_ENABLED=true    ← MUST be true!
```

**If GPIO_ENABLED=false:**
1. Edit .env file
2. Change to: `GPIO_ENABLED=true`
3. **Restart system:** `python main.py`

### Still Not Working?

**Run test mode:**
```bash
python main.py --test-gpio
```

**Should show:**
```
✓ GPIO service initialized successfully
camera_1 pin state: False
camera_2 pin state: False
camera_3 pin state: False
```

**If shows error:**
- Not on Raspberry Pi
- RPi.GPIO not installed
- Permission denied (try `sudo python main.py`)

## 📊 New UI Overview

### 5 Tabs:

1. **🏠 Dashboard**
   - Camera Health (online/offline)
   - System Monitor (temperature)
   - Capture Statistics
   - Upload Statistics
   - Storage Statistics
   - GPIO Status
   - **⚡ GPIO Triggers** (with animations!)
   - Manual Capture buttons

2. **⚙️ Configuration** (NEW!)
   - Enable/disable cameras
   - Change RTSP URLs
   - Change camera IPs
   - Change camera credentials
   - Enable/disable GPIO triggering
   - Enable/disable S3 uploads
   - Change S3 API URL
   - **💾 Save Configuration button**

3. **🖼️ Images**
   - Browse all recent images
   - Filter by camera
   - Pagination
   - Click to view full-size

4. **💾 Storage**
   - Total images and size
   - Bar charts by camera
   - Bar charts by date (last 30 days)

5. **📅 By Date**
   - Date picker
   - View images for specific date
   - Filter by camera
   - Pagination

## 🎉 What's Different Now?

### Before
- Had to edit .env file manually
- Had to restart system for changes
- No visual GPIO trigger indicators
- Images mixed with other tabs

### After  
- ✅ Web-based configuration editor
- ✅ No restart needed (for most settings)
- ✅ GPIO triggers show pulsing green lights
- ✅ Separate tabs for better organization
- ✅ Real-time trigger animations (updates every 1 second!)

## 🔥 Hot Tips

1. **Test GPIO**: Connect pin to GND and watch trigger light turn green!

2. **Use Configuration Tab**: Much easier than editing .env

3. **Monitor Triggers**: Dashboard shows trigger count and last trigger time

4. **Camera Health**: See which cameras are online before triggering

5. **Temperature**: Keep RPi cool (< 60°C is good)

## 🚨 Critical Settings for GPIO

```bash
# In .env file - MUST be true!
GPIO_ENABLED=true           ← Without this, GPIO won't work!
GPIO_TRIGGER_ENABLED=true   ← Can disable triggering without restart
```

**Remember:** Only `GPIO_TRIGGER_ENABLED` can be changed from Configuration tab. `GPIO_ENABLED` requires restart!

---

**Ready to start? Create your `.env` file and run `python main.py`!** 🚀

