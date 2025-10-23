# 📋 Quick Reference Card

## ⚡ Quick Commands

```bash
# Create .env from template
cp config.example.env .env

# Install dependencies
pip install -r requirements.txt

# Run system
python app.py

# Run with sudo (if GPIO needs permission)
sudo python app.py

# Run as service
sudo systemctl start camcap
```

## 🌐 Web Access

**URL:** `http://raspberry-pi-ip:8080`  
**Password:** `admin123`

## 🔌 GPIO Wiring

| Button | GPIO Pin | Physical Pin | Connect To |
|--------|----------|--------------|------------|
| Button 1 (r1) | 18 | Pin 12 | One side to Pin 12, other to GND (Pin 6) |
| Button 2 (r2) | 19 | Pin 35 | One side to Pin 35, other to GND (Pin 9) |

## 🎯 Web Dashboard Tabs

1. **🏠 Dashboard** - Health, status, recent images
2. **⚙️ Configuration** - Change RTSP URLs, enable/disable cameras
3. **💾 Storage** - Analytics by camera
4. **📅 Images** - View by date with pagination

## 📝 Key Configuration (.env)

```bash
# Must change:
CAM1_RTSP=rtsp://admin:admin@192.168.1.201:554/stream
CAM2_RTSP=rtsp://admin:admin@192.168.1.202:554/stream
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=anpr

# Can change:
BTN1_GPIO=18
BTN2_GPIO=19
CAM1_ENABLED=true
CAM2_ENABLED=true
FLASK_PORT=8080
RETENTION_DAYS=120
UPLOAD_ENABLED=true
```

## 🔧 Common Tasks

### Change Camera URL (No Restart!)
1. Web → Configuration tab
2. Edit RTSP URL
3. Click "💾 Save"
4. Done!

### Disable Camera Temporarily
1. Web → Configuration tab
2. Uncheck camera checkbox
3. Click "💾 Save"
4. Camera disabled!

### View Images from Yesterday
1. Web → Images tab
2. Select yesterday's date
3. Click "Load"
4. Browse images

### Check Camera Health
1. Web → Dashboard tab
2. Look at "Camera Health" card
3. Shows 🟢 ONLINE or 🔴 OFFLINE

### Check Upload Status
1. Web → Dashboard tab
2. Look at "Upload Status" card
3. Shows online/offline and pending count

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Button press no capture | Check wiring, check terminal for "[GPIO] BUTTON PRESSED" |
| Camera offline | Test RTSP URL in VLC, check IP reachable |
| Web won't load | Check `python app.py` is running, try `http://localhost:8080` |
| No upload | Check dashboard upload status, verify UPLOAD_ENDPOINT |
| Can't login | Password is `admin123`, check WEB_AUTH_ENABLED=true |

## 📊 What to Watch

### Terminal Output

**Good:**
```
[GPIO] 🔔 BUTTON 1 PRESSED - Capturing r1...
[SNAP] ✓ r1 -> /home/maxpark/r1_1698765432.jpg
[UPLOADER] ✓ Uploaded: r1_1698765432.jpg
```

**Warnings:**
```
[UPLOADER] ⚠ Internet connection lost - switching to offline mode
[UPLOADER] Offline - 5 images pending, will retry when online
```

**Errors:**
```
[SNAP] ✗ r1 failed
[GPIO] ⚠ Failed to initialize buttons: ...
```

### Web Dashboard

**Healthy System:**
- Camera Health: 🟢 ONLINE for both
- Upload Status: 🟢 ONLINE
- Pending: 0
- Temperature: < 60°C

**Issues:**
- Camera Health: 🔴 OFFLINE → Check camera connection
- Upload Status: 🔴 OFFLINE → Internet down (normal, will retry)
- Pending: High number → Backlog uploading or offline

## 🔑 Files You Need

**Must have:**
- `app.py` ← Main application
- `rtsp_capture.py` ← Capture logic
- `storage.py` ← Database
- `uploader.py` ← Upload logic
- `health_monitor.py` ← Health monitoring
- `requirements.txt` ← Dependencies
- `.env` ← **Your configuration (create this!)**

**Optional:**
- `camcap.service` ← For auto-start on boot
- `README.md` ← Full documentation
- `QUICKSTART.md` ← Setup guide

## 💡 Pro Tips

1. **Test cameras first** - Use VLC to verify RTSP URLs work
2. **Use Configuration tab** - Easier than editing .env
3. **Monitor terminal** - See button presses in real-time
4. **Check health status** - Know camera status before pressing buttons
5. **Works offline** - Don't worry about internet outages

## 🎯 Expected Behavior

### When You Press Button 1:

**Terminal:**
```
[GPIO] 🔔 BUTTON 1 PRESSED - Capturing r1...
[SNAP] ✓ r1 -> /home/maxpark/r1_1698765432.jpg
```

**Web Dashboard (within 10 seconds):**
- GPIO Triggers count increases
- New image appears in Recent Images
- (If online) Upload status shows uploaded count increase

### When System is Offline:

**Terminal:**
```
[UPLOADER] Offline - 3 images pending, will retry when online
```

**Web Dashboard:**
- Upload Status: 🔴 OFFLINE
- Pending: 3 (or whatever number)
- Images still appear (captured locally)

### When Internet Returns:

**Terminal:**
```
[UPLOADER] ✓ Internet connection restored - switching to online mode
[UPLOADER] ✓ Uploaded: r1_1698765432.jpg
[UPLOADER] ✓ Uploaded: r1_1698765433.jpg
```

**Web Dashboard:**
- Upload Status: 🟢 ONLINE
- Pending: 0 (after uploads complete)

## 📞 Get Help

**Read:**
- `QUICKSTART.md` - Step-by-step setup
- `README.md` - Complete documentation
- `SYSTEM_COMPLETE.md` - Feature overview

**Check:**
```bash
# System status
ps aux | grep app.py

# System logs (if service)
sudo journalctl -u camcap -f

# Test cameras
ffplay "your-rtsp-url"

# Check GPIO
python3 -c "import gpiozero; print('GPIO OK')"
```

---

## 🎉 You're Ready!

**To start:** Create `.env`, run `python app.py`, open `http://pi-ip:8080`

**Default password:** `admin123`

**Your system has everything you asked for!** 🚀

