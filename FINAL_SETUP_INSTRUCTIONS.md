# 🚀 FINAL SETUP INSTRUCTIONS - Push Button GPIO System

## ⚠️ CRITICAL INFORMATION

**You're currently on Windows!** Your path shows: `D:\nmr_plate\uodated_access_dev`

**GPIO ONLY works on Raspberry Pi!** You need to:
1. Transfer these files to your Raspberry Pi
2. Run the system on Raspberry Pi (not Windows)
3. Then GPIO push buttons will work

---

## 📦 What You Need

### Hardware
- ✅ Raspberry Pi (any model with GPIO)
- ✅ 3 Push Buttons (for 3 cameras)
- ✅ Jumper wires (6 wires minimum)
- ✅ 3 RTSP cameras

### Software
- ✅ Raspberry Pi OS
- ✅ Python 3.7+
- ✅ All files from this project

---

## 🎯 Complete Setup (Step by Step)

### Step 1: Transfer Files to Raspberry Pi

**From Windows to Raspberry Pi:**

```bash
# Option A: Use WinSCP or FileZilla (GUI)
# Copy entire folder to: /home/pi/camera_system

# Option B: Use command line
scp -r D:\nmr_plate\uodated_access_dev pi@192.168.1.33:/home/pi/camera_system
```

### Step 2: SSH to Raspberry Pi

```bash
ssh pi@192.168.1.33
```

### Step 3: Navigate to Project

```bash
cd /home/pi/camera_system
```

### Step 4: Create `.env` File

```bash
nano .env
```

**Paste this content:**

```bash
GPIO_ENABLED=true
GPIO_TRIGGER_ENABLED=true
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20
GPIO_BOUNCE_TIME=300

CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203
CAMERA_USERNAME=admin
CAMERA_PASSWORD=admin
CAMERA_1_RTSP=
CAMERA_2_RTSP=
CAMERA_3_RTSP=
CAMERA_1_ENABLED=true
CAMERA_2_ENABLED=true
CAMERA_3_ENABLED=true

S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
UPLOAD_QUEUE_SIZE=100
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60

MAX_RETRIES=5
RETRY_DELAY=5
BIND_IP=192.168.1.33
BIND_PORT=9000

IMAGE_STORAGE_PATH=images
IMAGE_RETENTION_DAYS=120
CLEANUP_INTERVAL_HOURS=24

WEB_AUTH_ENABLED=true
PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G
SECRET_KEY=your-secret-key-change-this
```

**Save:** Ctrl+X, then Y, then Enter

**Important:** Change `CAMERA_X_IP` and `BIND_IP` to match your network!

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
pip install RPi.GPIO
```

### Step 6: Wire Push Buttons

**Button 1 (Camera 1 - Entry):**
```
Button Terminal 1 → Raspberry Pi Physical Pin 12 (GPIO 18)
Button Terminal 2 → Raspberry Pi Physical Pin 6 (GND)
```

**Button 2 (Camera 2 - Exit):**
```
Button Terminal 1 → Raspberry Pi Physical Pin 35 (GPIO 19)
Button Terminal 2 → Raspberry Pi Physical Pin 9 (GND)
```

**Button 3 (Camera 3 - Auxiliary):**
```
Button Terminal 1 → Raspberry Pi Physical Pin 38 (GPIO 20)
Button Terminal 2 → Raspberry Pi Physical Pin 14 (GND)
```

**Visual Diagram:**
```
Push Button:
    [O]───→ GPIO Pin (12, 35, or 38)
     |
    [O]───→ GND Pin (6, 9, or 14)
    
When pressed: GPIO → GND → TRIGGER!
```

### Step 7: Test Push Buttons

```bash
python test_gpio_pushbutton.py
```

**Press each button one by one**

**Expected output for each press:**
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
⚡⚡⚡ BUTTON PRESSED! ⚡⚡⚡
📍 Pin: GPIO 18
📹 Camera: Camera 1 (r1/Entry)
📊 Total Count: 1
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
```

**If you see this:** ✅ Hardware is working!

**If not:** See troubleshooting section below

### Step 8: Run Full System

```bash
python main.py
```

**Expected output:**
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

**If you see "GPIO not available":**
- Check `.env` has `GPIO_ENABLED=true`
- Try: `sudo python main.py`

### Step 9: Test in Web Interface

**On Raspberry Pi or your computer:**

1. **Open browser:** `http://192.168.1.33:9000` (use your Raspberry Pi IP)
2. **Login:** Password is `admin123`
3. **Stay on Dashboard tab**
4. **Look at "⚡ GPIO Triggers" card**

**Press Button 1 on Raspberry Pi**

**Within 1 second, you should see:**
- ● Light turns **GREEN** and **PULSES**
- Background turns **BLUE**
- Count changes to **1**

**Press again:**
- Animation repeats
- Count increases to **2**

**Check Images tab:**
- New images should appear: `r1_1234567890.jpg`

---

## 🔧 Troubleshooting Guide

### ❌ Problem: "RPi.GPIO not available"

**You're on Windows or GPIO not installed**

**Solution:**
```bash
# On Raspberry Pi (not Windows!):
sudo pip install RPi.GPIO

# Verify:
python3 -c "import RPi.GPIO; print('GPIO OK')"
```

### ❌ Problem: Test script works but main.py shows "GPIO not available"

**`.env` file issue**

**Solution:**
```bash
# Check .env
cat .env | grep GPIO_ENABLED

# Should show: GPIO_ENABLED=true

# If not, add it:
echo "GPIO_ENABLED=true" >> .env

# Restart:
python main.py
```

### ❌ Problem: Button press not detected

**Wiring issue**

**Check:**
1. **Correct pins?**
   - GPIO 18 = Physical Pin **12** (not 18!)
   - Use a pinout diagram

2. **GND is actually GND?**
   - Test with multimeter (should be 0V)

3. **Button works?**
   - Test continuity with multimeter
   - When pressed, should have continuity

4. **Solid connections?**
   - Wires might be loose
   - Try re-seating connections

**Debug:**
```bash
# Run test and watch logs
python test_gpio_pushbutton.py

# Try connecting GPIO 18 directly to GND with jumper wire
# (bypass button to test GPIO itself)
```

### ❌ Problem: No animation in web interface

**Browser/Network issue**

**Check:**
1. **Browser open during button press?**
2. **On Dashboard tab?**
3. **Internet connection good?**
4. **JavaScript errors?** Press F12, check Console

**Force refresh:**
- Refresh browser (F5)
- Check if count increased in ⚡ GPIO Triggers card

### ❌ Problem: Trigger detected but no image captured

**Camera issue**

**Check:**
1. **Camera Health card** → Should be 🟢 ONLINE
2. **Try manual capture** → Click "Capture r1" button
3. **Check RTSP URL** → Configuration tab
4. **Test with VLC** → Open RTSP URL in VLC player

---

## 📊 Verification Checklist

Before expecting everything to work:

- [ ] **Files on Raspberry Pi** (not Windows!)
- [ ] **`.env` file created** with `GPIO_ENABLED=true`
- [ ] **RPi.GPIO installed:** `pip list | grep RPi.GPIO`
- [ ] **Push buttons wired correctly:**
  - Button 1: Pin 12 + GND
  - Button 2: Pin 35 + GND  
  - Button 3: Pin 38 + GND
- [ ] **Test script works:** `python test_gpio_pushbutton.py` shows triggers
- [ ] **Cameras online:** Web interface shows 🟢 ONLINE
- [ ] **System running:** `python main.py` shows "GPIO service initialized"
- [ ] **Web interface open:** `http://raspberry-pi-ip:9000`
- [ ] **On Dashboard tab**
- [ ] **Can see ⚡ GPIO Triggers card**

**If ALL checked:** Press button → Should work!

---

## 🎬 What You'll See (Complete Workflow)

### 1. Press Button on Raspberry Pi

```
[Physical button pressed]
    ↓
GPIO 18 connects to GND
```

### 2. Raspberry Pi Terminal (Instant)

```bash
# In terminal running python main.py:
🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
camera_1 (r1): Attempting to connect to camera...
camera_1 (r1): Image captured -> r1_1698765432.jpg
```

### 3. Web Interface (Within 1 second)

```
⚡ GPIO Triggers card:

● Camera 1 (r1/Entry)  ← GREEN PULSING!
  Pin 18 - Count: 1     ← Number changed!
  [Highlighted blue]    ← Background blue!
```

### 4. Images Tab (Immediate)

```
Click "Images" tab:

New image appears:
[r1_1698765432.jpg]
Size: 234 KB
Age: 0 days
```

### 5. Logs (Continuous)

```bash
# tail -f camera_system.log
Background upload successful: images/r1_1698765432.jpg
```

**All 5 happening = Perfect system!** 🎉

---

## 🎯 Quick Start Commands

### On Raspberry Pi:

```bash
# Test buttons
python test_gpio_pushbutton.py

# Run system
python main.py

# Watch logs
tail -f camera_system.log | grep TRIGGER

# List images
ls -lt images/r*.jpg | head -5
```

### On Your Computer:

```bash
# Open web interface
http://192.168.1.33:9000

# Login: admin123
# Watch ⚡ GPIO Triggers card on Dashboard
```

---

## 🎊 Files Created for GPIO Testing

| File | Purpose | When to Use |
|------|---------|-------------|
| `test_gpio_pushbutton.py` | ⭐ Test push buttons | First time testing |
| `test_gpio_simple.py` | Test GPIO hardware | Quick GPIO check |
| `test_gpio_triggers.py` | Test with config | Advanced testing |
| `PUSH_BUTTON_SETUP.md` | Complete guide | When stuck |
| `GPIO_TESTING_GUIDE.md` | All test methods | Reference |
| `GPIO_TROUBLESHOOTING.md` | Fix issues | When not working |

---

## 🎁 Bonus: Quick Diagnostic

**Run this on Raspberry Pi:**

```bash
# Create quick_test.sh
cat > quick_test.sh << 'EOF'
#!/bin/bash
echo "=== Quick GPIO Diagnostic ==="
echo ""
echo "1. System:"
cat /proc/device-tree/model 2>/dev/null || echo "Not a Raspberry Pi!"
echo ""
echo "2. Python:"
python3 --version
echo ""
echo "3. RPi.GPIO:"
python3 -c "import RPi.GPIO; print('OK')" 2>&1
echo ""
echo "4. .env exists:"
ls -la .env 2>/dev/null || echo "NOT FOUND!"
echo ""
echo "5. GPIO_ENABLED:"
grep GPIO_ENABLED .env 2>/dev/null || echo "NOT SET!"
echo ""
echo "=== End Diagnostic ==="
EOF

chmod +x quick_test.sh
./quick_test.sh
```

**This shows:** System info, Python version, GPIO availability, .env status

---

## 🔥 Most Common Issue: Running on Windows

**Your current directory shows Windows:**
```
D:\nmr_plate\uodated_access_dev
```

**GPIO will NOT work on Windows!**

**Solution:** Transfer files to Raspberry Pi and run there!

---

## ✅ Success Path

**Windows (Current):**
```
1. Verify all files present
2. Check code looks correct
3. Transfer to Raspberry Pi
```

**Raspberry Pi (Next):**
```
1. Receive files
2. Create .env with GPIO_ENABLED=true
3. Install dependencies
4. Wire push buttons
5. Test: python test_gpio_pushbutton.py
6. Run: python main.py
7. Open browser and watch animations!
```

---

## 📞 Need Help?

**First, run diagnostic:**
```bash
# On Raspberry Pi:
python test_gpio_pushbutton.py
```

**Press button**

**If you see trigger message:** Hardware works! ✓

**If not:** Read PUSH_BUTTON_SETUP.md section on troubleshooting

**Still stuck?** Check camera_system.log for errors

---

**Your system is complete and ready - just needs to run on Raspberry Pi for GPIO to work!** 🚀

**Start here:** Transfer files to Raspberry Pi, then run `python test_gpio_pushbutton.py`

