# 📂 Project Structure

Complete overview of all files and their purposes.

## 🎯 Core Application Files

### `main.py`
**Main Application Entry Point**
- Initializes all services
- Handles command-line arguments
- Provides test modes (--test-capture, --test-gpio, --cleanup-now)
- Sets up logging
- Manages graceful shutdown

**Usage**:
```bash
python main.py                    # Start normally
python main.py --test-capture     # Test camera captures
python main.py --test-gpio        # Test GPIO setup
python main.py --cleanup-now      # Run cleanup
```

### `config.py`
**Configuration Management**
- Loads environment variables from .env file
- Defines camera naming (r1/r2/r3)
- Manages camera enable/disable settings
- Configures GPIO pins
- Sets upload and storage settings
- Dynamic RTSP URL generation

**Key Features**:
- Environment variable support
- Default values for all settings
- Camera-specific configurations
- Flexible RTSP URL configuration

### `capture_service.py`
**Camera Capture Service**
- Captures images from RTSP cameras
- Implements retry logic with configurable attempts
- Names images as {r1/r2/r3}_{epochtime}.jpg
- Queues images for background upload
- Tracks capture statistics per camera
- Checks camera enable/disable status

**Methods**:
- `capture_camera_1()` - Capture from camera 1 (r1/entry)
- `capture_camera_2()` - Capture from camera 2 (r2/exit)
- `capture_camera_3()` - Capture from camera 3 (r3/auxiliary)
- `capture_by_key(camera_key)` - Generic capture method
- `get_stats()` - Get capture statistics

### `uploader.py`
**Background S3 Upload Service**
- Thread-safe upload queue
- Background worker thread for uploads
- Connection pooling for better performance
- Automatic retry with exponential backoff
- Upload statistics tracking
- Synchronous and asynchronous upload modes

**Features**:
- Queue-based background uploads
- Thread-safe operations with locks
- HTTP session reuse and connection pooling
- Configurable retry strategy
- Real-time statistics

**Methods**:
- `upload(filepath)` - Synchronous upload
- `queue_upload(filepath)` - Queue for background upload
- `start_background_upload()` - Start worker thread
- `stop_background_upload()` - Stop worker thread
- `get_stats()` - Get upload statistics

### `gpio_service.py`
**GPIO Hardware Trigger Service**
- Monitors GPIO pins for triggers
- Triggers on LOW state (connection to GND)
- Debounce protection
- Executes callbacks in separate threads
- Safe cleanup on shutdown

**Features**:
- Trigger on LOW state
- Configurable debounce time
- Thread-safe callback execution
- Pin state monitoring
- Graceful error handling

**Methods**:
- `register_callback(camera_key, callback)` - Register trigger callback
- `start_monitoring()` - Start GPIO monitoring
- `stop_monitoring()` - Stop GPIO monitoring
- `get_pin_state(camera_key)` - Get current pin state
- `cleanup()` - Cleanup GPIO resources

### `cleanup_service.py`
**Automatic Image Cleanup Service**
- Deletes images older than retention period (default: 120 days)
- Runs automatically at configured intervals
- Provides manual cleanup trigger
- Tracks cleanup statistics
- Lists and manages stored images

**Features**:
- Automatic scheduled cleanup
- Configurable retention period
- Storage statistics
- Image metadata tracking
- Pagination support for large image sets

**Methods**:
- `run_cleanup()` - Run cleanup once
- `start()` - Start background cleanup service
- `stop()` - Stop cleanup service
- `get_stats()` - Get cleanup and storage statistics
- `get_image_list(limit, offset)` - Get paginated image list

### `web_app.py`
**Flask Web Application**
- Provides web interface for system monitoring
- REST API for system control
- Serves captured images
- Real-time statistics display
- Manual capture triggers

**API Endpoints**:
- `GET /` - Main dashboard
- `GET /api/status` - System status
- `GET /api/stats` - Statistics
- `GET /api/images` - List images (paginated)
- `GET /api/images/<filename>` - Serve image
- `POST /api/capture/<camera_key>` - Manual capture
- `POST /api/cleanup/run` - Manual cleanup
- `GET /api/gpio/status` - GPIO pin states

---

## 🎨 Frontend Files

### `templates/index.html`
**Web Interface Template**
- Beautiful, modern dashboard design
- Real-time status updates (auto-refresh every 10s)
- Camera status display
- Capture and upload statistics
- Storage statistics
- Image gallery with filtering
- Pagination for large image sets
- Full-screen image viewer
- Manual capture buttons
- Manual cleanup trigger

**Features**:
- Responsive design (mobile-friendly)
- Real-time updates with AJAX
- Filter images by camera
- Click to view full-size images
- Beautiful gradient UI
- Statistics cards
- Pagination controls

---

## ⚙️ Configuration Files

### `.env` (Create from env.example)
**Environment Configuration**
- Camera IPs and credentials
- GPIO pin assignments
- Enable/disable settings
- Upload configuration
- Storage settings
- Network configuration

**Note**: This file should NOT be committed to git (contains sensitive data)

### `env.example`
**Configuration Template**
- Example configuration file
- Documents all available settings
- Provides default values
- Safe to commit to git

---

## 📦 Dependency Files

### `requirements.txt`
**Python Dependencies**
- opencv-python - Camera capture
- Flask - Web framework
- flask-cors - CORS support
- requests - HTTP client
- python-dotenv - Environment variables
- RPi.GPIO - GPIO support (optional, Raspberry Pi only)

---

## 🚀 Setup and Service Files

### `setup.sh`
**Automated Setup Script**
- Installs system dependencies
- Creates virtual environment (optional)
- Installs Python packages
- Detects Raspberry Pi and installs GPIO
- Creates .env from template
- Tests installation
- Sets up systemd service (optional)

**Usage**:
```bash
chmod +x setup.sh
./setup.sh
```

### `camera-capture.service`
**Systemd Service File**
- Auto-start on boot
- Automatic restart on failure
- Proper logging to journalctl
- Configured for user 'pi'

**Installation**:
```bash
sudo cp camera-capture.service /etc/systemd/system/
sudo systemctl enable camera-capture.service
sudo systemctl start camera-capture.service
```

---

## 📚 Documentation Files

### `README.md`
**Comprehensive Documentation**
- Feature overview
- Installation instructions
- Configuration guide
- Usage examples
- API documentation
- Troubleshooting guide
- Security considerations

### `QUICKSTART.md`
**Quick Start Guide**
- Get running in 5 minutes
- Essential configuration only
- Common troubleshooting
- Testing commands
- Next steps

### `PROJECT_STRUCTURE.md` (This File)
**Project Overview**
- File-by-file breakdown
- Purpose of each component
- How components interact
- File organization

---

## 📁 Directories

### `images/` (Auto-created)
**Image Storage Directory**
- Stores all captured images
- Named as {r1/r2/r3}_{epochtime}.jpg
- Automatically cleaned after retention period
- Served by web interface

### `templates/`
**Flask Template Directory**
- Contains HTML templates
- Currently: index.html (dashboard)

---

## 📝 Generated Files

### `camera_system.log`
**Application Log File**
- All system logs
- Rotation recommended for production
- Debug information
- Error traces

---

## 🔄 Data Flow

```
GPIO Trigger (LOW state)
    ↓
gpio_service.py (detects trigger)
    ↓
capture_service.py (captures image)
    ↓
Save to images/ as {r1/r2/r3}_{epochtime}.jpg
    ↓
uploader.py (background thread uploads to S3)
    ↓
cleanup_service.py (deletes after 120 days)
```

---

## 📊 Service Dependencies

```
main.py
  ├── config.py (configuration)
  ├── web_app.py (web interface)
  │   ├── capture_service.py
  │   │   └── uploader.py
  │   ├── cleanup_service.py
  │   └── gpio_service.py
  └── Templates
      └── index.html
```

---

## 🔧 Development vs Production

### Development Mode
```bash
# Run directly
python main.py

# View logs in console
# Hot reload on code changes (if using Flask debug)
```

### Production Mode
```bash
# Run as systemd service
sudo systemctl start camera-capture.service

# View logs with journalctl
sudo journalctl -u camera-capture.service -f

# Auto-start on boot
sudo systemctl enable camera-capture.service
```

---

## 🛠️ Customization Points

### Adding a New Camera
1. Update `config.py` - Add CAMERA_4_IP, etc.
2. Update `CAMERA_NAMES` dict
3. Update `gpio_service.py` - Add GPIO_CAMERA_4_PIN
4. Update `capture_service.py` - Add capture_camera_4() method
5. Update `templates/index.html` - Add UI elements

### Changing Image Naming
1. Modify `capture_service.py` - `_capture_image()` method
2. Update filename generation logic
3. Update documentation

### Adding Upload Providers
1. Create new uploader class (inherit from ImageUploader)
2. Implement upload() method
3. Update config.py with new settings
4. Update capture_service.py to use new uploader

### Customizing Web Interface
1. Edit `templates/index.html` - Modify HTML/CSS/JS
2. Add new API endpoints in `web_app.py`
3. Add new statistics or features

---

## 📋 File Checklist

When deploying, ensure you have:

- [x] All Python files (*.py)
- [x] requirements.txt
- [x] env.example (for reference)
- [x] .env (configured with your settings)
- [x] templates/index.html
- [x] README.md and documentation
- [x] setup.sh (optional, for easy setup)
- [x] camera-capture.service (optional, for systemd)

**Never commit**:
- .env (contains credentials)
- images/ directory contents
- *.log files
- __pycache__/
- venv/

---

## 🔐 Security Files

### `.gitignore` (Recommended to create)
```
.env
*.log
images/
__pycache__/
*.pyc
venv/
.vscode/
.idea/
```

This prevents committing sensitive data to version control.

---

## 📈 Monitoring Files

### System Logs
- `camera_system.log` - Application logs
- `journalctl` - Systemd service logs (if using service)

### Statistics
- Available via web interface at `/api/stats`
- Real-time monitoring dashboard at `/`

---

**For detailed information about any component, refer to its source code docstrings or the main README.md file.**

