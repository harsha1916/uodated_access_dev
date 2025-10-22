# 🔘 Push Button Setup & Troubleshooting Guide

Complete guide for setting up push buttons to trigger camera captures.

## 🎯 What You're Building

```
Push Button 1 → Captures Camera 1 (r1/Entry) → Shows animation on webpage
Push Button 2 → Captures Camera 2 (r2/Exit) → Shows animation on webpage
Push Button 3 → Captures Camera 3 (r3/Auxiliary) → Shows animation on webpage
```

---

## 🔌 Push Button Wiring (CRITICAL!)

### Correct Wiring Diagram

```
Push Button for Camera 1:

    ┌─────────────┐
    │   Button    │
    │             │
    │  1      2   │
    └──┬───────┬──┘
       │       │
       │       └─────→ GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
       │
       └─────→ GPIO 18 (Physical Pin 12)


When button is NOT pressed:
    GPIO 18 ──[Pull-up 3.3V]── HIGH (no trigger)
    
When button IS pressed:
    GPIO 18 ──[Button]── GND ── LOW (TRIGGER!)
```

### All 3 Buttons

```
Button 1 (Camera 1/r1/Entry):
    Side 1 → GPIO 18 (Physical Pin 12)
    Side 2 → GND (Physical Pin 6 or any GND)

Button 2 (Camera 2/r2/Exit):
    Side 1 → GPIO 19 (Physical Pin 35)
    Side 2 → GND (Physical Pin 9 or any GND)

Button 3 (Camera 3/r3/Auxiliary):
    Side 1 → GPIO 20 (Physical Pin 38)
    Side 2 → GND (Physical Pin 14 or any GND)
```

### ⚠️ IMPORTANT: Which Pins to Use

**GPIO Pins (BCM Mode):**
- GPIO 18 = **Physical Pin 12** (not pin 18!)
- GPIO 19 = **Physical Pin 35** (not pin 19!)
- GPIO 20 = **Physical Pin 38** (not pin 20!)

**GND Pins (Any of these):**
- Physical Pin 6, 9, 14, 20, 25, 30, 34, or 39

---

## 🧪 Testing Your Setup

### Step 1: Create `.env` File

**CRITICAL:** Create `.env` file with this content:

```bash
# MUST BE TRUE for GPIO to work!
GPIO_ENABLED=true
GPIO_TRIGGER_ENABLED=true

# Pin assignments
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20
GPIO_BOUNCE_TIME=300

# Other required settings
CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203
CAMERA_USERNAME=admin
CAMERA_PASSWORD=admin
CAMERA_1_ENABLED=true
CAMERA_2_ENABLED=true
CAMERA_3_ENABLED=true
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
BIND_IP=192.168.1.33
BIND_PORT=9000
IMAGE_STORAGE_PATH=images
IMAGE_RETENTION_DAYS=120
WEB_AUTH_ENABLED=true
PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G
SECRET_KEY=your-secret-key
```

### Step 2: Test Push Buttons (Hardware Test)

```bash
python test_gpio_pushbutton.py
```

**You'll see:**
```
🔘 GPIO PUSH BUTTON TEST SCRIPT
✓ RPi.GPIO imported successfully
✓ GPIO setup complete!

🟢 MONITORING ACTIVE - Press your buttons!

💚 Waiting for button press...
```

**Now press Button 1 (connected to GPIO 18):**

**Expected:**
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
⚡⚡⚡ BUTTON PRESSED! ⚡⚡⚡
📍 Pin: GPIO 18
📹 Camera: Camera 1 (r1/Entry)
⏰ Time: 14:23:45.123
📊 Total Count: 1
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔

✓ In full system, this would capture an image!
```

**Press it again:** Count should increase to 2

**Press Button 2 and 3:** Should also trigger

**Success!** If you see these messages, your buttons are wired correctly! ✓

---

### Step 3: Run Full System

```bash
python main.py
```

**You should see in logs:**
```
GPIO service initialized successfully
GPIO pin 18 configured for camera_1 (r1/entry)
GPIO pin 19 configured for camera_2 (r2/exit)
GPIO pin 20 configured for camera_3 (r3/auxiliary)
Started monitoring GPIO pin 18 for camera_1
Started monitoring GPIO pin 19 for camera_2
Started monitoring GPIO pin 20 for camera_3
```

**If you see "GPIO not available":** Check .env has `GPIO_ENABLED=true`

### Step 4: Watch Web Interface Animation

1. **Open browser:** `http://your-raspberry-pi-ip:9000`
2. **Login:** Password `admin123`
3. **Stay on Dashboard tab**
4. **Look at "⚡ GPIO Triggers" card** (should show 3 indicators)
5. **Press Button 1** (GPIO 18)

**You should see:**
- Light turns **GREEN** and **PULSES**
- Card **highlights in BLUE**
- Count changes from 0 to 1
- Animation lasts 2 seconds
- Then returns to normal

**In browser console (F12), you should see:**
```
Updating GPIO triggers...
Trigger active for camera_1
```

---

## 🔍 Troubleshooting Checklist

### ✅ Pre-Flight Checklist

- [ ] Running on **Raspberry Pi** (not Windows!)
- [ ] RPi.GPIO installed: `pip install RPi.GPIO`
- [ ] `.env` file created in project directory
- [ ] `.env` has `GPIO_ENABLED=true`
- [ ] `.env` has `GPIO_TRIGGER_ENABLED=true`
- [ ] Push button wired correctly (GPIO pin to one side, GND to other)
- [ ] Using **BCM GPIO numbers** (18, 19, 20) not physical pin numbers
- [ ] System started: `python main.py`

### Problem: Test script says "RPi.GPIO not available"

**Cause:** Not on Raspberry Pi or module not installed

**Solutions:**
```bash
# Install RPi.GPIO
sudo pip install RPi.GPIO

# Or
sudo apt-get install python3-rpi.gpio

# Verify installation
python3 -c "import RPi.GPIO; print('OK')"
```

### Problem: Button press not detected in test script

**Check:**

1. **Wiring:**
   - One side of button to GPIO pin (e.g., Pin 12 for GPIO 18)
   - Other side to GND (e.g., Pin 6)
   - NOT to 3.3V or 5V!

2. **Button works:**
   - Test button with multimeter
   - Should have continuity when pressed

3. **Pin numbers:**
   - GPIO 18 = Physical Pin 12
   - NOT Physical Pin 18!

4. **Run with sudo:**
   ```bash
   sudo python test_gpio_pushbutton.py
   ```

### Problem: Test script works but full system doesn't capture

**Check:**

1. **Cameras enabled:**
   ```bash
   cat .env | grep CAMERA_1_ENABLED
   # Should be: CAMERA_1_ENABLED=true
   ```

2. **Cameras online:**
   - Check web interface → Camera Health
   - Should show 🟢 ONLINE

3. **Watch logs:**
   ```bash
   tail -f camera_system.log | grep -E "TRIGGER|captured"
   ```

4. **RTSP URLs correct:**
   - Test with VLC player
   - Or click manual capture button in web interface

### Problem: No animation in web interface

**Check:**

1. **Web interface open during button press?**
   - Must have browser open to see animation

2. **On Dashboard tab?**
   - Animation only shows on Dashboard tab
   - Look for "⚡ GPIO Triggers" card

3. **Browser console errors:**
   - Press F12 in browser
   - Look at Console tab for errors
   - Should see: "Updating GPIO triggers..."

4. **Auto-refresh working:**
   - Triggers update every 1 second
   - Page should auto-update

**Force Refresh:**
- Refresh browser (F5)
- Check if trigger count increased

---

## 🎬 Complete Workflow

### What Should Happen When You Press Button

**1. Hardware (Instant):**
```
Button Pressed → GPIO Pin goes LOW → Trigger Event
```

**2. System (< 1 second):**
```
GPIO Service detects trigger
    ↓
Logs: "🔔 GPIO TRIGGER: camera_1 (pin 18)"
    ↓
Captures image from camera
    ↓
Logs: "camera_1 (r1): Image captured -> r1_1234567890.jpg"
    ↓
Queues for S3 upload
```

**3. Web Interface (1-2 seconds):**
```
Next auto-refresh (every 1 second)
    ↓
Fetches /api/gpio/status
    ↓
Sees trigger event active=true
    ↓
Shows animation:
  - Light turns green
  - Light pulses
  - Card highlights blue
  - Count increases
```

**4. Result:**
```
- Image saved in images/ folder
- Visible in web interface Images tab
- Upload queued for S3
```

---

## 🧪 Step-by-Step Testing Process

### Test 1: Verify RPi.GPIO Works

```bash
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

**Expected:** `GPIO OK`

**If fails:** Not on Raspberry Pi or not installed

### Test 2: Test Button Hardware

```bash
python test_gpio_pushbutton.py
```

**Press each button**

**Expected:** See trigger messages with 🔔 bells

**Count should increase:** 1, 2, 3, ...

### Test 3: Run Full System

```bash
python main.py
```

**Watch logs:**
```bash
# In another terminal
tail -f camera_system.log | grep TRIGGER
```

**Press Button 1**

**Expected:**
```
🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
camera_1 (r1): Image captured -> r1_1234567890.jpg
```

### Test 4: Check Web Interface Animation

**Open browser:** `http://your-pi-ip:9000`

**Stay on Dashboard tab**

**Look at "⚡ GPIO Triggers" card**

**Press Button 1**

**Within 1 second, you should see:**
- ● Green pulsing light (instead of ○ gray circle)
- Blue background on that row
- Count increases from 0 to 1

**Press Ctrl+Shift+I** (browser console) and look for:
```
Updating GPIO triggers...
```

---

## 🔧 Hardware Debugging

### Test Button with Multimeter

**Set multimeter to continuity mode:**

1. Put probes on both button pins
2. Not pressed: No continuity (beep)
3. Pressed: Continuity (beep) ✓

**If no continuity when pressed:** Button is broken

### Test GPIO Connection

**With test script running:**

1. Don't use button first
2. Use jumper wire directly
3. Connect GPIO 18 to GND
4. Should trigger immediately

**If this works but button doesn't:**
- Button might be faulty
- Wiring might be loose
- Try different button

### Verify GND Pin

**With multimeter:**
- Set to DC voltage mode
- Black probe to any GND pin
- Red probe to 3.3V pin
- Should read ~3.3V

**Or:**
- Black to GND
- Red to 5V pin
- Should read ~5V

**If not:** Check your GND pin is actually GND

---

## 📊 Understanding the Animation

### Web Interface Behavior

**Normal State (No Trigger):**
```
⚡ GPIO Triggers

○ Camera 1 (r1/Entry)      ← Gray circle
  Pin 18 - Count: 0
  [Normal gray background]
```

**Triggered State (Button Pressed):**
```
⚡ GPIO Triggers

● Camera 1 (r1/Entry)      ← GREEN PULSING circle
  Pin 18 - Count: 1         ← Count increased
  [Blue highlighted background]
```

**Animation Details:**
- **Duration:** 2 seconds
- **Light:** Green with glow effect
- **Pulse:** Scales from 1.0x to 1.1x
- **Background:** Blue highlight
- **Update rate:** Every 1 second (checks for new triggers)

### Why 1-Second Delay?

The web interface polls GPIO status every 1 second:

```
Press Button → GPIO triggers instantly → System logs it
                                              ↓
                                     (Wait up to 1 second)
                                              ↓
                             Web polls status → Sees trigger
                                              ↓
                                     Shows animation!
```

**So:** Maximum 1 second delay from button press to seeing animation

---

## 🔥 Common Problems & Solutions

### Problem: GPIO triggering not working at all

**Solution Checklist:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```
   
   **If not found:** Create it! (See START_HERE.md)

2. **Check GPIO_ENABLED:**
   ```bash
   cat .env | grep GPIO_ENABLED
   ```
   
   **Must show:** `GPIO_ENABLED=true`
   
   **If false or missing:**
   ```bash
   echo "GPIO_ENABLED=true" >> .env
   ```

3. **Check you're on Raspberry Pi:**
   ```bash
   cat /proc/device-tree/model
   ```
   
   **Should show:** "Raspberry Pi..."
   
   **If not:** GPIO won't work on Windows/Linux PC!

4. **Check RPi.GPIO installed:**
   ```bash
   python3 -c "import RPi.GPIO; print('OK')"
   ```
   
   **If error:** `pip install RPi.GPIO`

5. **Run test script:**
   ```bash
   python test_gpio_pushbutton.py
   ```
   
   **Press button** → Should see trigger message

### Problem: Test script works but main.py doesn't

**Check:**

1. **System logs show GPIO initialized:**
   ```bash
   python main.py 2>&1 | grep GPIO
   ```
   
   **Should see:**
   ```
   GPIO service initialized successfully
   Started monitoring GPIO pin 18
   ```

2. **Cameras are enabled and online:**
   - Open web interface
   - Check Camera Health card
   - All should be 🟢 ONLINE

3. **Camera URLs correct:**
   - Configuration tab
   - Check IP addresses
   - Try manual capture button

### Problem: Animation doesn't show in web interface

**Check:**

1. **Browser open during button press?**
   - Animation only shows if browser is open

2. **On Dashboard tab?**
   - Animation only on Dashboard
   - Not on other tabs

3. **Auto-refresh enabled:**
   - Page should show "Last Updated: XX:XX:XX"
   - Should update every 10 seconds

4. **JavaScript errors:**
   - Press F12 in browser
   - Check Console tab
   - Should see "Updating GPIO triggers..." every second

5. **Force manual check:**
   - Open browser console (F12)
   - Type: `updateGPIOTriggers()`
   - Press Enter
   - Should manually update triggers

---

## 📋 Complete Test Procedure

### Full System Test (15 Minutes)

**1. Hardware Setup** (5 min)
```bash
# Wire Button 1:
# - Pin 1 to Physical Pin 12 (GPIO 18)
# - Pin 2 to Physical Pin 6 (GND)

# Verify with multimeter:
# - Continuity test button
# - Test GND pin voltage
```

**2. Software Check** (5 min)
```bash
# Create .env (if not exists)
nano .env
# Add GPIO_ENABLED=true

# Install dependencies
pip install RPi.GPIO

# Test button
python test_gpio_pushbutton.py

# Press button → Should see trigger message
# Ctrl+C to stop
```

**3. System Test** (5 min)
```bash
# Run full system
python main.py

# In another terminal, watch logs
tail -f camera_system.log | grep TRIGGER

# Press button
# Should see: "🔔 GPIO TRIGGER: camera_1 (pin 18)"

# Check images folder
ls -lt images/r1_*.jpg | head -3

# Should see new image!
```

**4. Web Interface Test** (2 min)
```bash
# Open browser: http://your-pi-ip:9000
# Login: admin123
# Dashboard → ⚡ GPIO Triggers card
# Press button
# Should see: Green pulsing light within 1 second!
```

---

## 🎯 What Success Looks Like

### Test Script Success:
```
🔔🔔🔔 ⚡⚡⚡ BUTTON PRESSED! ⚡⚡⚡
📍 Pin: GPIO 18
📊 Total Count: 1
```

### Full System Success:
```bash
# Logs show:
🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
camera_1 (r1): Image captured -> r1_1234567890.jpg

# Images folder shows:
-rw-r--r-- 1 pi pi 234567 Oct 22 14:23 r1_1234567890.jpg
```

### Web Interface Success:
```
⚡ GPIO Triggers

● Camera 1 (r1/Entry)  ← Green pulsing light!
  Pin 18 - Count: 1     ← Counter increased!
  [Blue background]     ← Card highlighted!
```

**All three = Perfect!** 🎉

---

## 🚨 If Still Not Working

### Last Resort Debugging

**1. Check GPIO service status in logs:**
```bash
grep "GPIO" camera_system.log
```

**Should show:**
```
GPIO service initialized successfully
GPIO pin 18 configured for camera_1
Started monitoring GPIO pin 18
```

**If shows:**
```
GPIO functionality is disabled in configuration
```
→ `.env` has `GPIO_ENABLED=false` - Change to `true`!

**2. Enable debug logging:**

Edit `main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    ...
)
```

Run again:
```bash
python main.py 2>&1 | tee debug.log
```

Press button, check `debug.log`

**3. Check permissions:**
```bash
# Try with sudo
sudo python main.py
```

**4. Verify GPIO pins not in use:**
```bash
# Check if something else using GPIO
sudo lsof | grep gpio
```

**5. Test minimal GPIO:**
```python
# Create test.py
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(f"Pin 18 state: {GPIO.input(18)}")
GPIO.cleanup()
```

Run:
```bash
sudo python test.py
```

Should show: `Pin 18 state: 1` (HIGH)

---

## 📞 Getting Help

**Include this info when asking for help:**

1. **System info:**
   ```bash
   cat /proc/device-tree/model
   python3 --version
   pip list | grep RPi.GPIO
   ```

2. **Config:**
   ```bash
   cat .env | grep GPIO
   ```

3. **Test script output:**
   ```bash
   python test_gpio_pushbutton.py > test_output.txt 2>&1
   ```

4. **System logs:**
   ```bash
   tail -50 camera_system.log > system_logs.txt
   ```

5. **What happens when you press button:**
   - Any message in terminal?
   - Any log entry?
   - Web interface shows anything?

---

## 🎓 Summary

**For Push Button Triggers:**

1. **Wire each button:**
   - One side → GPIO Pin (12, 35, or 38)
   - Other side → GND

2. **Create `.env` with:**
   ```bash
   GPIO_ENABLED=true
   ```

3. **Test buttons:**
   ```bash
   python test_gpio_pushbutton.py
   ```

4. **Run system:**
   ```bash
   python main.py
   ```

5. **Watch animations:**
   - Browser: http://your-pi-ip:9000
   - Dashboard → ⚡ GPIO Triggers
   - Press button → Green pulsing light!

**That's it!** Your push buttons will trigger image captures with visual feedback! 🚀

---

**Start testing:** `python test_gpio_pushbutton.py` and press your buttons! 🔘⚡

