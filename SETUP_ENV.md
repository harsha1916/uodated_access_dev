# 📝 .env File Setup Guide

Since your `.env` file is protected, here's how to create it:

## Quick Setup

### 1. Create .env file

Create a file named `.env` in the project root (`D:\nmr_plate\uodated_access_dev\`) with this content:

```bash
# Camera Configuration
CAMERA_USERNAME=admin
CAMERA_PASSWORD=admin

CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202
CAMERA_3_IP=192.168.1.203

# Custom RTSP URLs (optional)
CAMERA_1_RTSP=
CAMERA_2_RTSP=
CAMERA_3_RTSP=

# Enable/Disable cameras
CAMERA_1_ENABLED=true
CAMERA_2_ENABLED=true
CAMERA_3_ENABLED=true

# S3 Upload Configuration
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
UPLOAD_QUEUE_SIZE=100
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60

# GPIO Configuration
GPIO_ENABLED=false
GPIO_TRIGGER_ENABLED=true
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20
GPIO_BOUNCE_TIME=300

# Network Configuration
MAX_RETRIES=5
RETRY_DELAY=5
BIND_IP=192.168.1.33
BIND_PORT=9000

# Storage Configuration
IMAGE_STORAGE_PATH=images
IMAGE_RETENTION_DAYS=120
CLEANUP_INTERVAL_HOURS=24

# Web Authentication
WEB_AUTH_ENABLED=true

# Password hash for: admin123
PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G

# Flask secret key (change this!)
SECRET_KEY=your-random-secret-key-change-in-production
```

### 2. Customize Settings

Edit the values in `.env` to match your setup:

- **CAMERA_X_IP**: Your camera IP addresses
- **BIND_IP**: Your server IP address
- **GPIO_ENABLED**: Set to `true` if running on Raspberry Pi

### 3. Change Password (Optional)

To change from the default password `admin123`:

```bash
python setup_password.py your_new_password
```

This will update the `PASSWORD_HASH` in your `.env` file.

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `CAMERA_USERNAME` | Camera login username | `admin` |
| `CAMERA_PASSWORD` | Camera login password | `admin` |
| `CAMERA_X_IP` | Camera IP addresses | `192.168.1.20X` |
| `CAMERA_X_ENABLED` | Enable/disable camera | `true` |
| `UPLOAD_ENABLED` | Enable S3 uploads | `true` |
| `GPIO_ENABLED` | Enable GPIO (Raspberry Pi) | `false` |
| `BIND_IP` | Web server bind IP | `192.168.1.33` |
| `BIND_PORT` | Web server port | `9000` |
| `IMAGE_RETENTION_DAYS` | Keep images for N days | `120` |
| `WEB_AUTH_ENABLED` | Enable web login | `true` |
| `PASSWORD_HASH` | Bcrypt password hash | (for admin123) |

## Testing Your Setup

1. **Start the system**:
   ```bash
   python main.py
   ```

2. **Open browser**:
   ```
   http://192.168.1.33:9000
   ```

3. **Login**:
   - Password: `admin123`

4. **Check dashboard**:
   - Camera health should show online/offline status
   - System monitor shows Raspberry Pi temperature (if available)
   - Storage analysis shows image breakdown

## Troubleshooting

### Can't find .env file
Make sure it's in the same directory as `main.py`:
```
D:\nmr_plate\uodated_access_dev\.env
```

### Camera offline
1. Check camera IPs are correct
2. Test RTSP URL with VLC
3. Verify username/password

### No temperature
- Normal on Windows (only works on Raspberry Pi)
- System Monitor will show "N/A" if temperature not available

### Can't login
1. Verify `PASSWORD_HASH` is set correctly
2. Try regenerating: `python setup_password.py admin123`
3. Check `WEB_AUTH_ENABLED=true`

## Quick Copy-Paste for .env

Save this to `.env` file:

```
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
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
UPLOAD_ENABLED=true
BACKGROUND_UPLOAD=true
UPLOAD_QUEUE_SIZE=100
OFFLINE_RETRY_INTERVAL=60
CONNECTIVITY_CHECK_INTERVAL=60
GPIO_ENABLED=false
GPIO_TRIGGER_ENABLED=true
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19
GPIO_CAMERA_3_PIN=20
GPIO_BOUNCE_TIME=300
MAX_RETRIES=5
RETRY_DELAY=5
BIND_IP=192.168.1.33
BIND_PORT=9000
IMAGE_STORAGE_PATH=images
IMAGE_RETENTION_DAYS=120
CLEANUP_INTERVAL_HOURS=24
WEB_AUTH_ENABLED=true
PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYT5RQl8G
SECRET_KEY=your-random-secret-key-change-in-production
```

**That's it!** You're ready to run the system.

