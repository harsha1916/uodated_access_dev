# 🧪 GPIO Testing Guide

Complete guide for testing GPIO trigger functionality.

## 🎯 Three Ways to Test GPIO

### Method 1: Simple Standalone Test (Recommended for Quick Check)

**File:** `test_gpio_simple.py`

**What it does:**
- Tests GPIO pins directly
- No dependencies on config or other services
- Shows real-time trigger messages
- Perfect for diagnosing GPIO issues

**Usage:**
```bash
python test_gpio_simple.py
```

**What you'll see:**
```
============================================================
Simple GPIO Test Script
============================================================

✓ RPi.GPIO imported successfully

Pin Configuration:
  Pin 18 (GPIO 18, Physical Pin 12) - Camera 1 (r1/Entry)
  Pin 19 (GPIO 19, Physical Pin 35) - Camera 2 (r2/Exit)
  Pin 20 (GPIO 20, Physical Pin 38) - Camera 3 (r3/Auxiliary)

Setting up GPIO...
✓ GPIO pins configured

Initial Pin States:
----------------------------------------
Pin 18: HIGH (Normal)
Pin 19: HIGH (Normal)
Pin 20: HIGH (Normal)
----------------------------------------

============================================================
🎯 GPIO MONITORING ACTIVE
============================================================

Waiting for GPIO triggers...

📍 How to Trigger:
   Camera 1: Connect GPIO 18 (Physical Pin 12) to GND
   Camera 2: Connect GPIO 19 (Physical Pin 35) to GND
   Camera 3: Connect GPIO 20 (Physical Pin 38) to GND

   GND Pins: Physical pins 6, 9, 14, 20, 25, 30, 34, 39

Press Ctrl+C to stop
============================================================

💚 Monitoring... (Triggers: Pin 18=0, Pin 19=0, Pin 20=0)
```

**When you connect Pin 18 to GND:**
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
⚡ TRIGGER DETECTED! Pin 18 → CAMERA_1
⏰ Time: 14:23:45.123
📊 Count: 1
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
```

**When to use:** First time testing GPIO, or when GPIO not working

---

### Method 2: Full System Test

**File:** `test_gpio_triggers.py`

**What it does:**
- Uses your config.py settings
- Tests with actual system configuration
- Shows trigger messages
- Good for testing before running full system

**Usage:**
```bash
python test_gpio_triggers.py
```

**What you'll see:**
```
============================================================
GPIO Trigger Test Script
============================================================

GPIO_ENABLED: True
GPIO_TRIGGER_ENABLED: True
GPIO_BOUNCE_TIME: 300ms

Setting up GPIO...

Configuring GPIO pins:
✓ GPIO 18 (Pin 12) - Camera 1 (r1/Entry)
✓ GPIO 19 (Pin 35) - Camera 2 (r2/Exit)
✓ GPIO 20 (Pin 38) - Camera 3 (r3/Auxiliary)

✓ GPIO initialized successfully!

============================================================
Starting GPIO Trigger Monitoring
============================================================

Current Pin States:
----------------------------------------
○ Pin 18 (camera_1): HIGH (Normal)
○ Pin 19 (camera_2): HIGH (Normal)
○ Pin 20 (camera_3): HIGH (Normal)
----------------------------------------

✓ Monitoring started - waiting for triggers...

⏰ Still monitoring... (Triggers: Camera1=0, Camera2=0, Camera3=0)
```

**When you connect Pin 18 to GND:**
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
⚡ TRIGGER DETECTED! Pin 18 → CAMERA_1
⏰ Time: 14:23:45.123
📊 Count: 1
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
```

**When to use:** Testing with your actual configuration

---

### Method 3: Built-in System Test

**Command:** `python main.py --test-gpio`

**What it does:**
- Checks if GPIO can initialize
- Shows pin states
- Quick verification

**Usage:**
```bash
python main.py --test-gpio
```

**What you'll see:**
```
Running GPIO test mode...
✓ GPIO service initialized successfully
camera_1 pin state: False
camera_2 pin state: False
camera_3 pin state: False
```

**When to use:** Quick check that GPIO is available

---

## 🔌 GPIO Wiring Reference

### Pin Layout

```
Raspberry Pi GPIO (BCM Mode)

Physical Pin Layout:
┌─────────────────────┐
│  3.3V    1 ● ● 2    5V
│  GPIO2   3 ● ● 4    5V
│  GPIO3   5 ● ● 6    GND  ← Use this GND
│  GPIO4   7 ● ● 8    GPIO14
│  GND     9 ● ● 10   GPIO15  ← Or this GND
│  GPIO17  11● ● 12   GPIO18  ← CAMERA 1 (r1)
│  GPIO27  13● ● 14   GND     ← Or this GND
│  ...
│  GPIO19  35● ● 36   GPIO16  ← CAMERA 2 (r2) at Pin 35
│  GPIO26  37● ● 38   GPIO20  ← CAMERA 3 (r3) at Pin 38
│  GND     39● ● 40   GPIO21  ← Or this GND
└─────────────────────┘
```

### Connection Diagram

```
Camera 1 Trigger Device:
    └─→ GPIO 18 (Pin 12) + GND (Pin 6 or 9 or 14...)

Camera 2 Trigger Device:
    └─→ GPIO 19 (Pin 35) + Any GND Pin

Camera 3 Trigger Device:
    └─→ GPIO 20 (Pin 38) + Any GND Pin
```

**How to Connect:**
1. One wire from trigger device to GPIO pin (12, 35, or 38)
2. One wire from trigger device to any GND pin
3. When trigger device activates → Connects GPIO to GND → Image captured!

---

## 🧪 Step-by-Step Testing Procedure

### Test 1: Verify GPIO is Available

```bash
python test_gpio_simple.py
```

**Expected:**
```
✓ RPi.GPIO imported successfully
✓ GPIO pins configured
```

**If fails:**
- Not on Raspberry Pi
- RPi.GPIO not installed
- Try: `pip install RPi.GPIO`

### Test 2: Test Manual Trigger

**While script is running:**

1. Get a jumper wire
2. Connect one end to **GPIO 18** (Physical Pin 12)
3. Touch the other end to **GND** (Physical Pin 6)
4. **You should immediately see:**
   ```
   🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
   ⚡ TRIGGER DETECTED! Pin 18 → CAMERA_1
   ⏰ Time: 14:23:45.123
   📊 Count: 1
   🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
   ```

5. Disconnect wire
6. Reconnect → Count should increase to 2

### Test 3: Test with Full System

```bash
# Terminal 1: Run system
python main.py

# Terminal 2: Watch logs
tail -f camera_system.log | grep TRIGGER
```

**Connect Pin 18 to GND**

**Terminal 2 should show:**
```
🔔 GPIO TRIGGER: camera_1 (pin 18) - Count: 1
camera_1 (r1): Image captured -> r1_1234567890.jpg
```

**Web Interface should show:**
- Green pulsing light on Camera 1 trigger
- Count increases
- Image appears in Images tab

---

## 🐛 Troubleshooting

### Problem: Script says "RPi.GPIO not available"

**Solution:**
```bash
pip install RPi.GPIO

# If that fails:
sudo apt-get install python3-rpi.gpio
```

### Problem: "Permission denied" or GPIO errors

**Solution:**
```bash
# Run with sudo
sudo python test_gpio_simple.py
```

### Problem: No trigger detected when connecting to GND

**Check:**

1. **Using correct pins?**
   - GPIO 18 = Physical Pin 12 (not pin 18!)
   - Use BCM numbering

2. **Connecting to actual GND?**
   ```bash
   # Test GND pin with multimeter
   # Should show 0V
   ```

3. **Good connection?**
   - Wire might be loose
   - Try different GND pin
   - Try different jumper wire

4. **GPIO_ENABLED in .env?**
   ```bash
   cat .env | grep GPIO_ENABLED
   # Should be: GPIO_ENABLED=true
   ```

### Problem: Trigger detected but no image captured

**This is normal for test scripts!**

The test scripts only detect GPIO triggers, they don't capture images.

**To capture images:** Run full system:
```bash
python main.py
```

Then triggers will both detect AND capture images.

---

## 📊 Test Script Comparison

| Feature | test_gpio_simple.py | test_gpio_triggers.py | main.py --test-gpio |
|---------|-------------------|---------------------|-------------------|
| **Standalone** | ✓ Yes | ❌ Needs config.py | ❌ Needs config.py |
| **Live Monitoring** | ✓ Yes | ✓ Yes | ❌ No (one-time check) |
| **Show Triggers** | ✓ Yes | ✓ Yes | ❌ No |
| **Captures Images** | ❌ No | ❌ No | ❌ No |
| **Best For** | Quick hardware test | Config-based test | Verify GPIO available |

**For capturing images:** Use `python main.py` (full system)

---

## 🎯 Recommended Testing Sequence

### First Time Setup:

```bash
# 1. Quick GPIO check
python test_gpio_simple.py
# → Connect Pin 18 to GND
# → Should see trigger message
# → Ctrl+C to stop

# 2. Test with config
python test_gpio_triggers.py
# → Connect Pin 18 to GND
# → Should see trigger message
# → Ctrl+C to stop

# 3. Test camera capture
python main.py --test-capture
# → Should capture test images

# 4. Run full system
python main.py
# → Connect Pin 18 to GND
# → Should capture AND save image
# → Check web interface for animation
```

---

## 🔧 Advanced Testing

### Test Debounce Time

```bash
# Connect and disconnect rapidly
# Pin 18 to GND multiple times quickly

# Should NOT trigger multiple times rapidly
# Debounce time (300ms) prevents bounce
```

### Test All Pins Simultaneously

```bash
# Connect Pin 18 to GND
# Then Pin 19 to GND (while 18 still connected)
# Then Pin 20 to GND (while both connected)

# All should trigger independently
# Counts should be: 1, 1, 1
```

### Test Pin States

Add this to test script:
```python
while True:
    state_18 = GPIO.input(18)
    state_19 = GPIO.input(19)
    state_20 = GPIO.input(20)
    
    print(f"Pin 18: {state_18}, Pin 19: {state_19}, Pin 20: {state_20}")
    time.sleep(1)
```

Should show:
- `1` when pin is HIGH (not connected)
- `0` when pin is LOW (connected to GND)

---

## 📝 Test Logs

### Expected Output (Success)

**Starting:**
```
✓ RPi.GPIO imported successfully
✓ GPIO pins configured
✓ Event detection enabled
🎯 GPIO MONITORING ACTIVE
Waiting for GPIO triggers...
💚 Monitoring...
```

**During Trigger:**
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
⚡ TRIGGER DETECTED! Pin 18 → CAMERA_1
⏰ Time: 14:23:45.123
📊 Count: 1
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔

💚 Monitoring... (Triggers: Pin 18=1, Pin 19=0, Pin 20=0)
```

**Stopping:**
```
🛑 Stopping test...

============================================================
Test Summary
============================================================
Camera 1 (Pin 18) triggers: 5
Camera 2 (Pin 19) triggers: 3
Camera 3 (Pin 20) triggers: 2
Total triggers detected: 10
============================================================

✓ GPIO cleanup complete
```

### Error Output (Failure)

**Not on Raspberry Pi:**
```
❌ Failed to import RPi.GPIO
Error: No module named 'RPi.GPIO'

Solutions:
1. Install RPi.GPIO: pip install RPi.GPIO
2. Make sure you're on Raspberry Pi
```

**Permission Denied:**
```
❌ Failed to initialize GPIO: [Errno 13] Permission denied
```

**Solution:** Run with sudo:
```bash
sudo python test_gpio_simple.py
```

---

## 🎬 Video Testing Workflow

### Step-by-Step Visual Test:

1. **Start Test Script:**
   ```bash
   python test_gpio_simple.py
   ```

2. **Prepare Wires:**
   - Get 2 jumper wires (male-to-female work best)

3. **Connect GND:**
   - Connect one wire firmly to Physical Pin 6 (GND)
   - Leave other end free

4. **Test Trigger:**
   - Touch free end of GND wire to Physical Pin 12 (GPIO 18)
   - **Watch terminal - should see trigger message immediately!**
   - Remove wire
   - Touch again - should trigger again

5. **Test Other Pins:**
   - Touch GND wire to Physical Pin 35 (GPIO 19)
   - Should trigger Camera 2
   - Touch GND wire to Physical Pin 38 (GPIO 20)
   - Should trigger Camera 3

6. **Stop Test:**
   - Press Ctrl+C
   - See summary with trigger counts

---

## 🔍 Common Issues

### Issue: No triggers detected

**Checklist:**
- [ ] Script shows "GPIO MONITORING ACTIVE"
- [ ] Using Physical Pin 12 (not pin 18!)
- [ ] Connecting to actual GND pin
- [ ] Wire making good contact
- [ ] Script is running (not stopped)

**Debug:**
```python
# Add this to script to see pin values continuously
while True:
    print(f"Pin 18 value: {GPIO.input(18)}")
    time.sleep(0.5)
```

Should show:
- `1` normally (HIGH)
- `0` when connected to GND (LOW)

### Issue: Multiple triggers from one connection

**Normal!** This is bounce. The script has debounce (300ms) which helps.

**If too sensitive:**
- Increase `GPIO_BOUNCE_TIME` in .env
- Use better quality wires
- Ensure solid connections

### Issue: Trigger detected but wrong pin

**Check:**
- Pin mapping in script matches your wiring
- Using BCM mode (not BOARD mode)

---

## 🎓 Understanding the Output

### Pin States

**HIGH (Normal):**
```
Pin 18: HIGH (Normal)
```
- Pin not connected to GND
- Pull-up resistor pulling to 3.3V
- NOT triggered

**LOW (Triggered):**
```
Pin 18: LOW (Connected to GND)
```
- Pin connected to GND
- Trigger should fire
- Image should be captured (in full system)

### Trigger Messages

**Successful Trigger:**
```
⚡ TRIGGER DETECTED! Pin 18 → CAMERA_1
📊 Count: 1
```

**Means:**
- ✓ GPIO event detected
- ✓ Callback fired
- ✓ Hardware working correctly

**In full system, you'll also see:**
```
camera_1 (r1): Image captured -> r1_1234567890.jpg
```

---

## 🚀 After Successful Test

Once test scripts show triggers working:

1. **Stop test script** (Ctrl+C)

2. **Run full system:**
   ```bash
   python main.py
   ```

3. **Open web interface:**
   ```
   http://your-pi-ip:9000
   ```

4. **Watch Dashboard:**
   - Look at ⚡ GPIO Triggers card
   - Connect Pin 18 to GND
   - **Green light should pulse!**
   - Count should increase
   - Image should appear in Images tab

5. **Verify Image Captured:**
   ```bash
   ls -lt images/r1_*.jpg | head -5
   ```

---

## 📋 Quick Reference

**Test GPIO quickly:**
```bash
python test_gpio_simple.py
```

**Test with config:**
```bash
python test_gpio_triggers.py
```

**Test initialization:**
```bash
python main.py --test-gpio
```

**Run full system:**
```bash
python main.py
```

**Watch logs:**
```bash
tail -f camera_system.log | grep TRIGGER
```

**List captured images:**
```bash
ls -lt images/*.jpg | head -10
```

---

## ✅ Success Criteria

**GPIO is working when:**
- ✓ Test script shows "TRIGGER DETECTED" messages
- ✓ Count increases each time you connect to GND
- ✓ Full system shows green pulsing animation
- ✓ Images are captured and saved
- ✓ Logs show "Image captured" messages

**If all above pass:** Your GPIO triggering is working perfectly! 🎉

---

## 🎁 Bonus: Create Hardware Test Switch

### Simple Test Switch

**Materials:**
- Push button or toggle switch
- 2 wires

**Wiring:**
```
Switch Pin 1 → GPIO 18 (Pin 12)
Switch Pin 2 → GND (Pin 6)

When you press switch → Connects GPIO 18 to GND → Trigger!
```

**Testing:**
1. Run: `python test_gpio_simple.py`
2. Press switch
3. Should see trigger message
4. Release switch
5. Press again → Another trigger

---

**Good luck testing! Your GPIO triggers will work perfectly!** ⚡🎉

