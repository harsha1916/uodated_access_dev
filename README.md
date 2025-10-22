# 🎥 Camera Capture System with GPIO Triggers and S3 Upload

A comprehensive image capture system for Raspberry Pi (or any Linux system) that captures images from RTSP cameras when hardware GPIO pins are triggered, uploads them to S3 in the background, and provides a beautiful web interface for viewing captured images.

## ✨ Features

- **🔌 GPIO Hardware Triggers**: Capture images automatically when GPIO pins go LOW
- **☁️ Background S3 Upload**: Thread-safe background upload queue with automatic retries
- **📡 Offline Operation**: Works without internet - automatically uploads cached images when connection returns
- **🔄 Persistent Queue**: Failed uploads are saved to disk and retried when online
- **🖼️ Web Interface**: Beautiful, modern web UI to view captured images and system status
- **💾 Automatic Cleanup**: Automatically delete images older than 120 days (configurable)
- **📹 Multi-Camera Support**: Support for 3 cameras (Entry/Exit/Auxiliary)
- **⚙️ Highly Configurable**: Enable/disable cameras, RTSP URLs, GPIO triggering, and more
- **📊 Real-time Statistics**: Monitor capture success, upload queue, storage usage, offline status
- **🔒 Secure**: Environment variable-based configuration for credentials

## 📋 System Requirements

- **Hardware**: Raspberry Pi (any model with GPIO) or any Linux system
- **OS**: Raspberry Pi OS, Ubuntu, or any Debian-based Linux
- **Python**: Python 3.7 or higher
- **Network**: Access to RTSP cameras and S3-compatible API

## 🚀 Installation

### 1. Clone the Repository

```bash
cd /path/to/your/project
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**For Raspberry Pi with GPIO support**, uncomment the RPi.GPIO line in `requirements.txt`:

```bash
# Edit requirements.txt and uncomment:
# RPi.GPIO==0.7.1

pip install RPi.GPIO
```

### 3. Set Up Password (Important!)

Set up the admin password (default: admin123):

```bash
python setup_password.py
```

Or set a custom password:

```bash
python setup_password.py your_custom_password
```

This will create/update your `.env` file with the password hash.

### 4. Configure the System

Copy the example configuration file if you haven't run the password setup:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```bash
nano .env
```

**Important Configuration Options**:

```bash
# Camera IPs and credentials
CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203
CAMERA_USERNAME=admin
CAMERA_PASSWORD=your_password

# Enable/Disable cameras
CAMERA_1_ENABLED=true
CAMERA_2_ENABLED=true
CAMERA_3_ENABLED=true

# GPIO Configuration (set to true on Raspberry Pi)
GPIO_ENABLED=false
GPIO_TRIGGER_ENABLED=true

# GPIO Pins (BCM numbering)
GPIO_CAMERA_1_PIN=18  # r1 (Entry)
GPIO_CAMERA_2_PIN=19  # r2 (Exit)
GPIO_CAMERA_3_PIN=20  # r3 (Auxiliary)

# Upload Configuration
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr

# Storage Configuration
IMAGE_RETENTION_DAYS=120
IMAGE_STORAGE_PATH=images

# Web Server
BIND_IP=192.168.1.33
BIND_PORT=9000
```

## 🎯 Usage

### Start the System

```bash
python main.py
```

The web interface will be available at: `http://<BIND_IP>:<BIND_PORT>` (default: http://192.168.1.33:9000)

### Test Modes

**Test Camera Capture**:
```bash
python main.py --test-capture
```

**Test GPIO Setup**:
```bash
python main.py --test-gpio
```

**Run Cleanup Manually**:
```bash
python main.py --cleanup-now
```

## 🔧 System Architecture

```
┌─────────────────┐
│   GPIO Pins     │ ──> Trigger on LOW state
│  (18, 19, 20)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GPIO Service   │ ──> Detects triggers, calls capture
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Capture Service │ ──> Captures from RTSP, saves locally
│                 │     Filename: {r1/r2/r3}_{epochtime}.jpg
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upload Service  │ ──> Background thread uploads to S3
│  (Queue-based)  │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Cleanup Service │ ──> Deletes images > 120 days old
│  (Every 24h)    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Web Interface  │ ──> View images, stats, manual capture
│  (Flask App)    │
└─────────────────┘
```

## 📁 Project Structure

```
.
├── main.py                 # Main application entry point
├── config.py               # Configuration management
├── capture_service.py      # Camera capture logic
├── uploader.py             # S3 upload with background queue
├── gpio_service.py         # GPIO trigger handling
├── cleanup_service.py      # Automatic image cleanup
├── web_app.py              # Flask web application
├── templates/
│   └── index.html          # Web interface template
├── images/                 # Image storage directory (auto-created)
├── requirements.txt        # Python dependencies
├── env.example             # Example configuration
└── README.md               # This file
```

## 📡 Offline Operation & Automatic Retry

The system is designed to **work seamlessly without internet connection**.

### How It Works

1. **No Internet**: When internet is unavailable, images are captured and saved locally as normal
2. **Persistent Queue**: Failed uploads are saved to `pending_uploads.json` on disk
3. **Automatic Detection**: System checks connectivity every 60 seconds (configurable)
4. **Auto-Retry**: When internet returns, a retry worker automatically uploads all pending images
5. **Resume on Restart**: If system restarts, pending uploads are loaded and retried

### Offline Mode Indicators

- **Web Interface**: Shows 🔴 OFFLINE or 🟢 ONLINE status
- **Pending Retry Counter**: Shows how many images are waiting to upload
- **Logs**: Clear messages about offline mode and retry attempts

### Configuration

```bash
# Control offline behavior in .env
OFFLINE_RETRY_INTERVAL=60          # How often to retry pending uploads (seconds)
CONNECTIVITY_CHECK_INTERVAL=60     # How often to check internet (seconds)
```

### What Happens Offline

1. **Capture**: Images are captured normally from cameras
2. **Local Storage**: Images saved to `images/` directory immediately
3. **Queue Saved**: Failed uploads added to `pending_uploads.json`
4. **Web Interface**: Still works - you can view all captured images
5. **Statistics**: Shows pending upload count

### What Happens When Online Returns

1. **Auto-Detection**: System detects internet is back
2. **Retry Worker**: Starts processing pending uploads
3. **Sequential Upload**: Uploads queued images one by one
4. **Status Update**: Web interface shows online status
5. **Queue Cleared**: Successfully uploaded images removed from queue

### Manual Control

You can view pending uploads in the web interface or check the file directly:

```bash
cat pending_uploads.json
```

The system will **never lose images** - they are always saved locally first!

## 🎨 Image Naming Convention

Images are named with the following format:

```
{camera_name}_{epoch_timestamp}.jpg
```

Where:
- `r1` = Entry camera (camera_1)
- `r2` = Exit camera (camera_2)
- `r3` = Auxiliary camera (camera_3)

**Examples**:
- `r1_1698765432.jpg` - Entry camera at timestamp 1698765432
- `r2_1698765433.jpg` - Exit camera at timestamp 1698765433
- `r3_1698765434.jpg` - Auxiliary camera at timestamp 1698765434

## 🔌 GPIO Wiring (Raspberry Pi)

Connect your trigger devices to the following GPIO pins:

| Camera | GPIO Pin (BCM) | Physical Pin | Function |
|--------|---------------|--------------|----------|
| r1 (Entry) | GPIO 18 | Pin 12 | Trigger on LOW |
| r2 (Exit) | GPIO 19 | Pin 35 | Trigger on LOW |
| r3 (Auxiliary) | GPIO 20 | Pin 38 | Trigger on LOW |

**Important**: The system triggers on **LOW state** (when pin goes to GND). Each pin has an internal pull-up resistor enabled.

**Typical Wiring**:
```
Trigger Device ──┐
                 │
                GND ─── GPIO Pin ─── (Pull-up to 3.3V)
```

When the trigger device closes the circuit to GND, the GPIO pin goes LOW and triggers a capture.

## 🌐 Web Interface

The web interface provides:

- **📊 Real-time Dashboard**: System status, camera status, GPIO status
- **📈 Statistics**: Capture stats, upload stats, storage usage
- **🖼️ Image Gallery**: View all captured images with filtering by camera
- **📸 Manual Capture**: Trigger captures manually from any camera
- **🧹 Manual Cleanup**: Run cleanup operation on demand
- **🔄 Auto-refresh**: Statistics update every 10 seconds

**Access**: Open `http://<BIND_IP>:<BIND_PORT>` in your web browser

## ⚙️ Configuration Options

### Camera Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CAMERA_1_ENABLED` | Enable camera 1 (r1/entry) | `true` |
| `CAMERA_2_ENABLED` | Enable camera 2 (r2/exit) | `true` |
| `CAMERA_3_ENABLED` | Enable camera 3 (r3/auxiliary) | `true` |
| `CAMERA_1_RTSP` | Custom RTSP URL for camera 1 | Auto-generated |
| `CAMERA_USERNAME` | RTSP username | `admin` |
| `CAMERA_PASSWORD` | RTSP password | `admin` |

### GPIO Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GPIO_ENABLED` | Enable GPIO functionality | `false` |
| `GPIO_TRIGGER_ENABLED` | Enable GPIO triggering | `true` |
| `GPIO_CAMERA_1_PIN` | GPIO pin for camera 1 | `18` |
| `GPIO_CAMERA_2_PIN` | GPIO pin for camera 2 | `19` |
| `GPIO_CAMERA_3_PIN` | GPIO pin for camera 3 | `20` |
| `GPIO_BOUNCE_TIME` | Debounce time (ms) | `300` |

### Upload Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_ENABLED` | Enable S3 uploads | `true` |
| `BACKGROUND_UPLOAD` | Upload in background thread | `true` |
| `S3_API_URL` | S3 API endpoint | easyparkai.com |
| `UPLOAD_QUEUE_SIZE` | Max queue size | `100` |

### Storage Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `IMAGE_RETENTION_DAYS` | Keep images for N days | `120` |
| `CLEANUP_INTERVAL_HOURS` | Cleanup frequency | `24` |
| `IMAGE_STORAGE_PATH` | Local image directory | `images` |

## 🚦 Running as a Service (Systemd)

To run the system as a service on boot:

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/camera-capture.service
```

2. Add the following content:

```ini
[Unit]
Description=Camera Capture System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python3 /path/to/your/project/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable camera-capture.service
sudo systemctl start camera-capture.service
```

4. Check status:

```bash
sudo systemctl status camera-capture.service
```

## 📊 Monitoring and Logs

View logs in real-time:

```bash
tail -f camera_system.log
```

Or with systemd:

```bash
sudo journalctl -u camera-capture.service -f
```

## 🔍 Troubleshooting

### GPIO Not Working

1. Check if RPi.GPIO is installed: `pip list | grep RPi.GPIO`
2. Run with sudo: `sudo python main.py`
3. Test GPIO: `python main.py --test-gpio`
4. Verify GPIO_ENABLED=true in .env

### Camera Not Capturing

1. Test RTSP URL manually with VLC or ffplay
2. Check camera credentials in .env
3. Verify camera is enabled in .env
4. Test capture: `python main.py --test-capture`
5. Check logs for connection errors

### Images Not Uploading

1. Check UPLOAD_ENABLED=true in .env
2. Verify S3_API_URL is correct
3. Check network connectivity
4. View upload stats in web interface - look for offline status
5. Check logs for upload errors
6. If offline, images are queued in `pending_uploads.json` and will auto-upload when online
7. Check pending retry count in web interface

### Web Interface Not Loading

1. Verify BIND_IP and BIND_PORT in .env
2. Check if port is not blocked by firewall
3. Try accessing from localhost first
4. Check if Flask is installed: `pip list | grep Flask`

## 🔐 Security & Authentication

### Web Interface Login

The system includes password protection for the web interface:

**Default Credentials:**
- Password: `admin123` (change immediately after setup!)

**First Time Setup:**
```bash
python setup_password.py
```

**Change Password:**
1. Login to web interface
2. Click "Change Password" button
3. Enter current password and new password
4. Click "Change Password"

**Reset Password:**
```bash
python setup_password.py new_password
```

### Disable Authentication (Not Recommended)

In `.env`:
```bash
WEB_AUTH_ENABLED=false
```

### Security Best Practices

- ✅ Change default password immediately
- ✅ Use strong passwords (8+ characters, mix of letters/numbers/symbols)
- ✅ Store credentials in `.env` file, never commit to git
- ✅ Use strong passwords for camera access
- ✅ Restrict web interface access with firewall rules
- ✅ Consider using HTTPS with a reverse proxy (nginx)
- ✅ Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- ✅ Enable authentication (`WEB_AUTH_ENABLED=true`)

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/status` | GET | System status |
| `/api/stats` | GET | Statistics |
| `/api/images` | GET | List images (with pagination) |
| `/api/images/<filename>` | GET | Serve image file |
| `/api/capture/<camera_key>` | POST | Manual capture |
| `/api/cleanup/run` | POST | Manual cleanup |
| `/api/gpio/status` | GET | GPIO pin states |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

This project is provided as-is for your use.

## 👨‍💻 Author

Created for parking/access control systems with RTSP cameras and GPIO triggers.

---

**Need Help?** Check the logs in `camera_system.log` or run test modes to diagnose issues.

