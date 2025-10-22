# 🚀 Quick Start Guide

Get your Camera Capture System running in 5 minutes!

## For Raspberry Pi Users

### 1. Run the Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Install all dependencies
- Set up virtual environment (optional)
- Install GPIO support (for Raspberry Pi)
- Create configuration file
- Optionally set up systemd service

### 2. Set Up Password

```bash
python setup_password.py
```

This sets the default password: `admin123`

Or set a custom password:
```bash
python setup_password.py mypassword
```

### 3. Configure Your System

Edit the `.env` file with your settings:

```bash
nano .env
```

**Minimum required settings**:
```bash
# Your camera IPs
CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203

# Camera credentials
CAMERA_USERNAME=admin
CAMERA_PASSWORD=your_password

# Enable GPIO (for Raspberry Pi)
GPIO_ENABLED=true

# Your server IP
BIND_IP=192.168.1.33
```

### 4. Test Your Cameras

```bash
python3 main.py --test-capture
```

You should see messages like:
```
✓ camera_1 test successful: r1_1698765432.jpg
✓ camera_2 test successful: r2_1698765433.jpg
✓ camera_3 test successful: r3_1698765434.jpg
```

### 5. Start the System

```bash
python3 main.py
```

### 6. Open Web Interface and Login

Open your browser and go to:
```
http://192.168.1.33:9000
```
(Replace with your BIND_IP)

**Login with:**
- Password: `admin123` (or your custom password)

**Important:** Change your password immediately!
- Click "Change Password" button in the web interface
- Enter current password and new password

---

## For Non-Raspberry Pi Users (No GPIO)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
cp env.example .env
nano .env
```

**Important**: Set GPIO_ENABLED=false
```bash
GPIO_ENABLED=false
```

### 3. Test and Run

```bash
# Test cameras
python3 main.py --test-capture

# Start system
python3 main.py
```

### 4. Access Web Interface

```
http://localhost:9000
```

You can manually capture images from the web interface!

---

## 📡 Works Offline!

**No Internet? No Problem!**

The system works perfectly without internet:
- ✅ Images captured and saved locally
- ✅ Failed uploads saved to persistent queue
- ✅ Automatically uploads when internet returns
- ✅ Web interface shows offline/online status
- ✅ Pending uploads counter in dashboard

**You'll never lose an image!**

---

## Quick Configuration Reference

### Essential Settings

| Setting | What to Change | Example |
|---------|---------------|---------|
| `CAMERA_1_IP` | Your entry camera IP | `192.168.1.201` |
| `CAMERA_2_IP` | Your exit camera IP | `192.168.1.202` |
| `CAMERA_3_IP` | Your auxiliary camera IP | `192.168.1.203` |
| `CAMERA_USERNAME` | Camera login username | `admin` |
| `CAMERA_PASSWORD` | Camera login password | `your_password` |
| `GPIO_ENABLED` | Enable GPIO (Raspberry Pi only) | `true` or `false` |
| `BIND_IP` | Your server IP address | `192.168.1.33` |

### Optional Settings

| Setting | Purpose | Default |
|---------|---------|---------|
| `UPLOAD_ENABLED` | Enable S3 uploads | `true` |
| `BACKGROUND_UPLOAD` | Upload in background | `true` |
| `IMAGE_RETENTION_DAYS` | Keep images for N days | `120` |
| `GPIO_CAMERA_1_PIN` | GPIO pin for camera 1 | `18` |

---

## GPIO Wiring (Raspberry Pi)

Connect your trigger devices:

```
Entry Trigger    → GPIO 18 (Pin 12) + GND
Exit Trigger     → GPIO 19 (Pin 35) + GND
Auxiliary Trigger → GPIO 20 (Pin 38) + GND
```

**How it works**: When the trigger device connects GPIO to GND (LOW state), a photo is captured.

---

## Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### Camera Connection Failed
1. Test RTSP URL with VLC
2. Check camera IP is reachable: `ping 192.168.1.201`
3. Verify credentials are correct

### GPIO Not Working
1. Check if running on Raspberry Pi
2. Set `GPIO_ENABLED=true` in .env
3. Run with sudo: `sudo python3 main.py`
4. Install GPIO: `pip install RPi.GPIO`

### Web Interface Not Loading
1. Check firewall isn't blocking the port
2. Try localhost: `http://localhost:9000`
3. Check BIND_IP in .env matches your server IP

### Upload to S3 Failing
1. Check `S3_API_URL` is correct
2. Verify network connectivity
3. Check upload stats in web interface

---

## Testing Commands

```bash
# Test camera capture
python3 main.py --test-capture

# Test GPIO setup
python3 main.py --test-gpio

# Run cleanup manually
python3 main.py --cleanup-now
```

---

## Running as a Service

```bash
# Install service (after running setup.sh)
sudo systemctl enable camera-capture.service
sudo systemctl start camera-capture.service

# Check status
sudo systemctl status camera-capture.service

# View logs
sudo journalctl -u camera-capture.service -f

# Stop service
sudo systemctl stop camera-capture.service
```

---

## Next Steps

1. ✅ System running? Check the web interface dashboard
2. ✅ Test GPIO triggers by connecting pins to GND
3. ✅ Check upload stats to verify S3 uploads working
4. ✅ Set up systemd service for auto-start on boot
5. ✅ Configure firewall rules for remote access

---

## Need More Help?

- Read the full [README.md](README.md) for detailed documentation
- Check logs: `tail -f camera_system.log`
- View system stats in the web interface
- Test individual components with test commands

---

**Remember**: Images are named as `{r1/r2/r3}_{epochtime}.jpg`
- r1 = Entry camera
- r2 = Exit camera  
- r3 = Auxiliary camera

Images are kept for 120 days by default, then automatically deleted.

