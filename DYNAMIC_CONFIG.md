# 🔄 Dynamic Configuration Reload

Your system now supports **dynamic configuration reloading** - change settings in `.env` without restarting!

## ✨ What Can Be Changed Dynamically?

### ✅ **Reload Automatically** (No Restart Needed)

1. **RTSP URLs**
   - `CAMERA_1_RTSP`
   - `CAMERA_2_RTSP`
   - `CAMERA_3_RTSP`
   - `CAMERA_USERNAME`
   - `CAMERA_PASSWORD`
   - `CAMERA_X_IP`

2. **Enable/Disable Cameras**
   - `CAMERA_1_ENABLED`
   - `CAMERA_2_ENABLED`
   - `CAMERA_3_ENABLED`

### How It Works

The system **reads from .env file on every access** for:
- RTSP URLs (via `get_rtsp_cameras()`)
- Camera enable/disable status (via `is_camera_enabled()`)

**No restart required!** Changes take effect on the next camera check.

## 🚀 How to Change Settings

### Method 1: Reload Config Button (Recommended)

1. Edit `.env` file with your changes
2. Open web interface
3. Click **"🔄 Reload Config"** button (top right)
4. Confirm the reload
5. Settings updated immediately!

**Example**:
```bash
# Edit .env
CAMERA_1_ENABLED=false    # Disable camera 1
CAMERA_2_RTSP=rtsp://admin:newpass@192.168.1.205:554/stream

# Click "Reload Config" button in web interface
# Changes applied instantly!
```

### Method 2: Automatic (Wait for Next Check)

Settings are reloaded automatically:
- **RTSP URLs**: Next time camera is accessed
- **Enable/Disable**: Next capture or health check (every 60 seconds)

**Example**:
```bash
# Edit .env
CAMERA_1_ENABLED=false

# Wait up to 60 seconds
# System automatically detects the change
```

## 📋 Step-by-Step Example

### Scenario: Change Camera 2 IP Address

**Current:**
```bash
CAMERA_2_IP=192.168.1.202
```

**Steps:**

1. **Edit .env file**:
   ```bash
   # Change to new IP
   CAMERA_2_IP=192.168.1.205
   ```

2. **Two Options:**
   
   **Option A - Use Reload Button (Instant)**:
   - Open web interface: `http://192.168.1.33:9000`
   - Click "🔄 Reload Config" button
   - Click "OK" on confirmation
   - Done! ✓

   **Option B - Wait for Auto-reload**:
   - Just wait (changes apply on next access)
   - Usually within 60 seconds

3. **Verify**:
   - Check "Camera Health" card
   - Should show new camera status

### Scenario: Disable Camera 3 Temporarily

**Current:**
```bash
CAMERA_3_ENABLED=true
```

**Steps:**

1. **Edit .env**:
   ```bash
   CAMERA_3_ENABLED=false
   ```

2. **Reload** (click button or wait)

3. **Verify**:
   - Camera 3 shows "DISABLED" in dashboard
   - No more captures from camera 3
   - Health monitoring skips camera 3

### Scenario: Change All Camera Passwords

**Current:**
```bash
CAMERA_USERNAME=admin
CAMERA_PASSWORD=oldpass
```

**Steps:**

1. **Edit .env**:
   ```bash
   CAMERA_USERNAME=admin
   CAMERA_PASSWORD=newpass123
   ```

2. **Click "Reload Config"** button

3. **Done!** All cameras now use new password

## ⚙️ Settings That DO Require Restart

Some settings require full restart because they're loaded once at startup:

### ❌ **Requires Restart**

- `BIND_IP` - Server IP address
- `BIND_PORT` - Server port
- `GPIO_ENABLED` - GPIO initialization
- `GPIO_CAMERA_X_PIN` - GPIO pin numbers
- `IMAGE_STORAGE_PATH` - Storage directory
- `WEB_AUTH_ENABLED` - Authentication enable/disable
- `PASSWORD_HASH` - Login password

**To apply these:** Stop and restart the system:
```bash
# Stop (Ctrl+C)
# Start again
python main.py
```

## 🎯 Quick Reference

| Setting | Reload Method | Takes Effect |
|---------|--------------|--------------|
| `CAMERA_X_RTSP` | Button or Auto | Immediately |
| `CAMERA_X_IP` | Button or Auto | Immediately |
| `CAMERA_USERNAME` | Button or Auto | Immediately |
| `CAMERA_PASSWORD` | Button or Auto | Immediately |
| `CAMERA_X_ENABLED` | Button or Auto | Immediately |
| `BIND_IP` | **Restart** | On restart |
| `BIND_PORT` | **Restart** | On restart |
| `GPIO_ENABLED` | **Restart** | On restart |
| `IMAGE_STORAGE_PATH` | **Restart** | On restart |

## 💡 Best Practices

### 1. Use Reload Button for Immediate Effect

**Good**:
```bash
# Edit .env
CAMERA_1_ENABLED=false

# Click "Reload Config" button immediately
# Change applied instantly
```

**Also Works** (but slower):
```bash
# Edit .env
CAMERA_1_ENABLED=false

# Wait up to 60 seconds
# Change applied automatically
```

### 2. Batch Multiple Changes

**Good**:
```bash
# Edit multiple settings at once
CAMERA_1_IP=192.168.1.210
CAMERA_2_IP=192.168.1.211
CAMERA_3_ENABLED=false

# Click "Reload Config" once
# All changes applied together
```

**Less Efficient**:
```bash
# Change one setting
CAMERA_1_IP=192.168.1.210
# Click reload

# Change another
CAMERA_2_IP=192.168.1.211
# Click reload again

# (Works, but unnecessary)
```

### 3. Verify Changes

After reloading, check:
- **Dashboard** → Camera Health card
- Look for online/offline status
- Check enable/disable status

### 4. Test Camera After URL Change

**Recommended**:
1. Change RTSP URL in .env
2. Click "Reload Config"
3. Check "Camera Health" (should show online/offline)
4. Try manual capture to verify

## 🔍 Troubleshooting

### Camera still offline after URL change

**Check**:
1. Did you click "Reload Config" button?
2. Is new URL correct? Test with VLC
3. Are credentials correct?
4. Wait 60 seconds for health check

**Solution**:
```bash
# Verify .env has new settings
cat .env | grep CAMERA_1

# Click "Reload Config" button
# Check "Camera Health" card
```

### Enable/disable not working

**Check**:
1. Spelling correct? `CAMERA_1_ENABLED=true` (lowercase "true")
2. Did you reload config?
3. Check dashboard - should show ENABLED/DISABLED

**Solution**:
```bash
# Correct format:
CAMERA_1_ENABLED=true   ✓
CAMERA_1_ENABLED=TRUE   ✗ (wrong)
CAMERA_1_ENABLED=1      ✗ (wrong)
```

### "Reload Config" button does nothing

**Possible causes**:
1. Not logged in
2. Browser console shows error
3. Network issue

**Solution**:
1. Refresh page
2. Login again
3. Check browser console (F12)

### Changes revert after reload

**Problem**: Editing wrong .env file or typo

**Solution**:
```bash
# Make sure you're editing the right file
cd D:\nmr_plate\uodated_access_dev
notepad .env

# Save and close
# Click "Reload Config"
```

## 🔄 Behind the Scenes

### How Dynamic Reload Works

**RTSP URLs**:
```python
# config.py
def get_rtsp_cameras():
    load_dotenv()  # Reloads .env every time
    # Returns fresh URLs from environment
```

**Enable/Disable**:
```python
# config.py
def is_camera_enabled(camera_key):
    load_dotenv()  # Reloads .env every time
    return os.getenv("CAMERA_1_ENABLED") == "true"
```

**When Called**:
- Every camera capture
- Every health check (60s interval)
- Every status API call
- On manual "Reload Config"

## 🎓 Advanced Usage

### Programmatic Reload

Use API endpoint:
```bash
curl -X POST http://192.168.1.33:9000/api/config/reload \
  -H "Cookie: session=your_session_cookie"
```

**Response**:
```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Automation Script

```python
import requests

def reload_config():
    session = requests.Session()
    # Login first
    session.post('http://192.168.1.33:9000/login',
                 data={'password': 'admin123'})
    
    # Reload config
    response = session.post('http://192.168.1.33:9000/api/config/reload')
    print(response.json())

reload_config()
```

## 📊 Comparison

### Before (Old System)
```bash
# Edit .env
vim .env

# Stop system
Ctrl+C

# Start again
python main.py

# Total: 30-60 seconds downtime
```

### After (New System)
```bash
# Edit .env
vim .env

# Click "Reload Config" button

# Total: 1 second, no downtime!
```

## 🎉 Summary

**Dynamic Reload Features:**
- ✅ Change RTSP URLs without restart
- ✅ Enable/disable cameras on the fly
- ✅ Update credentials instantly
- ✅ One-click reload button
- ✅ Automatic detection
- ✅ No system downtime

**How to Use:**
1. Edit `.env` file
2. Click "🔄 Reload Config" button
3. Done!

**That's it!** Your changes take effect immediately without restarting the system. 🚀

---

For more information, see:
- **[README.md](README.md)** - Full documentation
- **[SETUP_ENV.md](SETUP_ENV.md)** - .env file guide
- **[NEW_FEATURES_SUMMARY.md](NEW_FEATURES_SUMMARY.md)** - New features overview

