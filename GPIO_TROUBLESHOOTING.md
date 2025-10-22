# 🔧 GPIO Troubleshooting & Setup Guide

## ⚠️ GPIO Not Working? Here's the Fix!

### Problem: Pin 18 to Ground Not Capturing Image

**Root Causes:**
1. GPIO_ENABLED not set to `true` in `.env`
2. System running on Windows (RPi.GPIO won't work)
3. GPIO service not properly initialized
4. Pins not configured correctly

### ✅ Solution Steps

#### Step 1: Update `.env` File

Make sure your `.env` has:

```bash
# MUST be true for GPIO to work!
GPIO_ENABLED=true
GPIO_TRIGGER_ENABLED=true

# Verify pin numbers
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20

GPIO_BOUNCE_TIME=300
```

#### Step 2: Check You're on Raspberry Pi

GPIO **ONLY** works on Raspberry Pi! If you're on Windows:
- Run on Raspberry Pi for GPIO functionality
- Or use web interface manual capture buttons

Check logs:
```bash
tail -f camera_system.log | grep GPIO
```

You should see:
```
GPIO service initialized successfully
GPIO pin 18 configured for camera_1 (r1/entry)
GPIO pin 19 configured for camera_2 (r2/exit)
GPIO pin 20 configured for camera_3 (r3/auxiliary)
Started monitoring GPIO pin 18 for camera_1
```

If you see:
```
RPi.GPIO not available. GPIO functionality disabled.
```
**→ You're not on Raspberry Pi or RPi.GPIO not installed!**

#### Step 3: Install RPi.GPIO (Raspberry Pi Only)

```bash
pip install RPi.GPIO
```

#### Step 4: Run with Sudo (If Needed)

GPIO may need root permissions:

```bash
sudo python main.py
```

#### Step 5: Test GPIO Wiring

**Correct Wiring:**
```
PIN 18 (BCM) → When connected to GND → Captures Camera 1
PIN 19 (BCM) → When connected to GND → Captures Camera 2
PIN 20 (BCM) → When connected to GND → Captures Camera 3
```

**Test:**
1. Start system: `python main.py`
2. Connect Pin 18 to any GND pin
3. Watch logs:
   ```bash
   tail -f camera_system.log
   ```
4. You should see:
   ```
   🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
   camera_1 (r1): Image captured -> r1_1234567890.jpg
   ```

#### Step 6: Check Pin Mapping

BCM Pin numbers (not physical pin numbers!):

| Camera | BCM GPIO | Physical Pin | When to Trigger |
|--------|----------|--------------|----------------|
| Camera 1 (r1) | 18 | Pin 12 | Connect to GND |
| Camera 2 (r2) | 19 | Pin 35 | Connect to GND |
| Camera 3 (r3) | 20 | Pin 38 | Connect to GND |

**GND Pins on Raspberry Pi:**
- Physical Pin 6, 9, 14, 20, 25, 30, 34, 39

## 🎯 Testing GPIO Triggers

### Test Mode

```bash
python main.py --test-gpio
```

Expected output:
```
✓ GPIO service initialized successfully
camera_1 pin state: False
camera_2 pin state: False
camera_3 pin state: False
```

### Live Test

1. Start system normally:
   ```bash
   python main.py
   ```

2. Open web interface in browser:
   ```
   http://192.168.1.33:9000
   ```

3. Look at **⚡ GPIO Triggers** card on dashboard

4. Connect Pin 18 to GND

5. **Visual Feedback:**
   - Trigger light turns GREEN and pulses
   - Counter increments
   - Card highlights in blue
   - Log shows trigger message

### Debugging GPIO

**Enable Debug Logging:**

Edit `main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    ...
)
```

Then check logs:
```bash
python main.py 2>&1 | grep -i gpio
```

## 🎨 New UI Features Explained

### Dashboard Tab (🏠)
- Camera Health (online/offline status)
- System Monitor (RPi temperature)
- Capture Statistics
- Upload Statistics
- Storage Statistics  
- GPIO Status
- **⚡ GPIO Triggers** ← NEW! Shows when pins trigger
- Manual Capture buttons

### Configuration Tab (⚙️) - NEW!
- **Camera Settings:**
  - Enable/Disable each camera
  - Change IP addresses
  - Change RTSP URLs
  - Change camera credentials
  
- **GPIO Settings:**
  - Enable/Disable GPIO
  - Enable/Disable GPIO triggering
  
- **Upload Settings:**
  - Enable/Disable S3 uploads
  - Change S3 API URL

**→ Click "💾 Save Configuration" to apply changes!**

### Images Tab (🖼️)
- Browse all recent images
- Filter by camera
- Pagination
- Click to view full-size

### Storage Tab (💾)
- Total images and size
- Breakdown by camera (bar charts)
- Last 30 days (bar charts)

### By Date Tab (📅)
- Select date from date picker
- Filter by camera
- View images for specific date

## 🚀 Using Configuration Tab

### Change RTSP URL

1. Click **⚙️ Configuration** tab
2. Find camera you want to change
3. Edit **RTSP URL** field
4. Click **💾 Save Configuration**
5. Done! No restart needed!

### Enable/Disable Camera

1. Click **⚙️ Configuration** tab
2. Find camera checkbox
3. Check ✓ to enable, uncheck ☐ to disable
4. Click **💾 Save Configuration**
5. Camera immediately enabled/disabled!

### Change Camera IP

1. Click **⚙️ Configuration** tab
2. Edit **IP Address** field
3. Click **💾 Save Configuration**
4. New IP applied immediately!

## 📊 GPIO Trigger Animations

When a GPIO pin triggers:

1. **Trigger Light** → Turns GREEN and pulses
2. **Card Background** → Highlights in blue
3. **Counter** → Increments
4. **Animation** → Lasts 2 seconds
5. **Log Entry** → Records trigger event

### What You'll See

**Before Trigger:**
```
⚡ GPIO Triggers
○ Camera 1 (r1/Entry)
  Pin 18 - Count: 0
```

**During Trigger (2 seconds):**
```
⚡ GPIO Triggers
● Camera 1 (r1/Entry)  ← Green pulsing light, blue background
  Pin 18 - Count: 1    ← Counter incremented
```

**After Trigger:**
```
⚡ GPIO Triggers
○ Camera 1 (r1/Entry)  ← Back to normal
  Pin 18 - Count: 1    ← Counter stays
```

## 🔍 Common Issues & Solutions

### Issue: "GPIO service not available"

**Solution:**
1. Check you're on Raspberry Pi
2. Install RPi.GPIO: `pip install RPi.GPIO`
3. Set GPIO_ENABLED=true in .env
4. Restart system

### Issue: Trigger doesn't capture image

**Check:**
1. Is camera enabled? (Configuration tab)
2. Is RTSP URL correct?
3. Check logs for capture errors
4. Try manual capture button first

**Debug:**
```bash
# Watch for triggers
tail -f camera_system.log | grep -i trigger

# Should see:
# 🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
```

### Issue: GPIO triggers but no image saved

**Possible causes:**
1. Camera offline
2. RTSP URL wrong
3. Camera credentials wrong

**Check:**
1. Dashboard → Camera Health (should be green)
2. Try Manual Capture button
3. Check RTSP URL in Configuration tab

### Issue: Configuration changes don't save

**Solutions:**
1. Make sure you're logged in
2. Click "💾 Save Configuration" button
3. Check browser console for errors (F12)
4. Check file permissions on .env file

## 📝 Quick Checklist

Before expecting GPIO to work:

- [ ] Running on Raspberry Pi (not Windows)
- [ ] RPi.GPIO installed: `pip list | grep RPi.GPIO`
- [ ] .env has `GPIO_ENABLED=true`
- [ ] .env has `GPIO_TRIGGER_ENABLED=true`
- [ ] System started: `python main.py`
- [ ] Logs show "GPIO service initialized successfully"
- [ ] Cameras are enabled
- [ ] RTSP URLs are correct
- [ ] Using BCM pin numbers (18, 19, 20)
- [ ] Connecting to GND (not 3.3V!)

## 🎓 Complete Workflow Example

### Scenario: Set up Camera 1 GPIO trigger

```bash
# 1. Edit .env
nano .env

# Add/change:
GPIO_ENABLED=true
GPIO_TRIGGER_ENABLED=true
CAMERA_1_ENABLED=true
CAMERA_1_IP=192.168.1.201

# 2. Start system
python main.py

# 3. Open browser
# Go to: http://192.168.1.33:9000
# Login: admin123

# 4. Check Dashboard
# → Camera Health: Camera 1 should be 🟢 ONLINE
# → GPIO Triggers: Should show "Pin 18 - Count: 0"

# 5. Test trigger
# Connect GPIO Pin 18 (Physical Pin 12) to GND

# 6. Observe
# → Trigger light turns GREEN and pulses
# → Counter shows "Count: 1"
# → Image appears in "Images" tab
# → Log shows: "r1_1234567890.jpg"

# SUCCESS! 🎉
```

## 📚 Additional Resources

- **Main Docs**: README.md
- **Setup Guide**: SETUP_ENV.md
- **Config Reload**: DYNAMIC_CONFIG.md
- **New Features**: NEW_FEATURES_SUMMARY.md
- **Authentication**: AUTHENTICATION.md

## ⚡ Pro Tips

1. **Monitor triggers in real-time:**
   ```bash
   tail -f camera_system.log | grep -E "TRIGGER|captured"
   ```

2. **Check GPIO pin states:**
   - Web interface → Dashboard → GPIO Status card
   - Shows current pin states

3. **Test cameras before GPIO:**
   - Use Manual Capture buttons first
   - Verify cameras work before testing GPIO

4. **Use Configuration tab:**
   - Much easier than editing .env manually
   - Changes save instantly
   - No typos!

---

**Need more help?** Check the logs and look for error messages!

```bash
# Full log
tail -f camera_system.log

# Just GPIO
tail -f camera_system.log | grep -i gpio

# Just triggers
tail -f camera_system.log | grep -i trigger

# Just errors
tail -f camera_system.log | grep -i error
```

