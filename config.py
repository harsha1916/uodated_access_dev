import os
from typing import Dict

# Camera credentials and URLs - use environment variables for security
CAMERA_USERNAME = os.getenv("CAMERA_USERNAME", "admin")
CAMERA_PASSWORD = os.getenv("CAMERA_PASSWORD", "admin")
CAMERA_1_IP = os.getenv("CAMERA_1_IP", "192.168.1.201")
CAMERA_2_IP = os.getenv("CAMERA_2_IP", "192.168.1.202")
CAMERA_3_IP = os.getenv("CAMERA_3_IP", "192.168.1.203")

# Camera naming configuration (r1=entry, r2=exit, r3=auxiliary)
CAMERA_NAMES = {
    "camera_1": "r1",  # Entry
    "camera_2": "r2",  # Exit
    "camera_3": "r3"   # Auxiliary
}

# Enable/Disable individual cameras (for backward compatibility)
CAMERA_1_ENABLED = os.getenv("CAMERA_1_ENABLED", "true").lower() == "true"
CAMERA_2_ENABLED = os.getenv("CAMERA_2_ENABLED", "true").lower() == "true"
CAMERA_3_ENABLED = os.getenv("CAMERA_3_ENABLED", "true").lower() == "true"

# Function to dynamically get camera enabled status
def is_camera_enabled(camera_key: str) -> bool:
    """
    Dynamically check if a camera is enabled by reading from environment.
    This allows enable/disable changes without restart.
    
    Args:
        camera_key: 'camera_1', 'camera_2', or 'camera_3'
    
    Returns:
        True if camera is enabled, False otherwise
    """
    from dotenv import load_dotenv
    load_dotenv()  # Reload environment variables
    
    if camera_key == "camera_1":
        return os.getenv("CAMERA_1_ENABLED", "true").lower() == "true"
    elif camera_key == "camera_2":
        return os.getenv("CAMERA_2_ENABLED", "true").lower() == "true"
    elif camera_key == "camera_3":
        return os.getenv("CAMERA_3_ENABLED", "true").lower() == "true"
    
    return False

# Function to get current RTSP URLs (reads from environment each time)
def get_rtsp_cameras():
    """Get current RTSP camera URLs, reading from environment variables each time."""
    # Reload environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get current values
    camera_username = os.getenv("CAMERA_USERNAME", "admin")
    camera_password = os.getenv("CAMERA_PASSWORD", "admin")
    camera_1_ip = os.getenv("CAMERA_1_IP", "192.168.1.201")
    camera_2_ip = os.getenv("CAMERA_2_IP", "192.168.1.202")
    camera_3_ip = os.getenv("CAMERA_3_IP", "192.168.1.203")
    camera_1_rtsp = os.getenv("CAMERA_1_RTSP", "")
    camera_2_rtsp = os.getenv("CAMERA_2_RTSP", "")
    camera_3_rtsp = os.getenv("CAMERA_3_RTSP", "")
    
    # Use custom RTSP URLs if provided, otherwise generate from IP/credentials
    return {
        "camera_1": camera_1_rtsp if camera_1_rtsp else f"rtsp://{camera_username}:{camera_password}@{camera_1_ip}:554/avstream/channel=1/stream=0.sdp",
        "camera_2": camera_2_rtsp if camera_2_rtsp else f"rtsp://{camera_username}:{camera_password}@{camera_2_ip}:554/avstream/channel=1/stream=0.sdp",
        "camera_3": camera_3_rtsp if camera_3_rtsp else f"rtsp://{camera_username}:{camera_password}@{camera_3_ip}:554/avstream/channel=1/stream=0.sdp"
    }

# For backward compatibility, create a property-like access
class RTSPCameras:
    def __getitem__(self, key):
        return get_rtsp_cameras()[key]
    
    def get(self, key, default=None):
        return get_rtsp_cameras().get(key, default)
    
    def keys(self):
        return get_rtsp_cameras().keys()

# Create instance for backward compatibility
RTSP_CAMERAS = RTSPCameras()

# API Configuration
S3_API_URL = os.getenv("S3_API_URL", "https://api.easyparkai.com/api/Common/Upload?modulename=anpr")

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# Server Configuration
BIND_IP = os.getenv("BIND_IP", "192.168.1.33")
BIND_PORT = int(os.getenv("BIND_PORT", "9000"))

# GPIO Configuration for Raspberry Pi
GPIO_CAMERA_1_PIN = int(os.getenv("GPIO_CAMERA_1_PIN", "18"))  # GPIO pin for camera 1 (r1/entry) trigger
GPIO_CAMERA_2_PIN = int(os.getenv("GPIO_CAMERA_2_PIN", "19"))  # GPIO pin for camera 2 (r2/exit) trigger
GPIO_CAMERA_3_PIN = int(os.getenv("GPIO_CAMERA_3_PIN", "20"))  # GPIO pin for camera 3 (r3/auxiliary) trigger
GPIO_ENABLED = os.getenv("GPIO_ENABLED", "false").lower() == "true"  # Enable GPIO functionality
GPIO_TRIGGER_ENABLED = os.getenv("GPIO_TRIGGER_ENABLED", "true").lower() == "true"  # Enable GPIO triggering
GPIO_BOUNCE_TIME = int(os.getenv("GPIO_BOUNCE_TIME", "300"))  # Debounce time in milliseconds

# Image Storage Configuration
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", "images")
IMAGE_RETENTION_DAYS = int(os.getenv("IMAGE_RETENTION_DAYS", "120"))  # Keep images for 120 days
CLEANUP_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))  # Run cleanup every 24 hours

# Upload Configuration
UPLOAD_ENABLED = os.getenv("UPLOAD_ENABLED", "true").lower() == "true"  # Enable S3 uploads
BACKGROUND_UPLOAD = os.getenv("BACKGROUND_UPLOAD", "true").lower() == "true"  # Upload in background thread
UPLOAD_QUEUE_SIZE = int(os.getenv("UPLOAD_QUEUE_SIZE", "100"))  # Max queue size for uploads
OFFLINE_RETRY_INTERVAL = int(os.getenv("OFFLINE_RETRY_INTERVAL", "60"))  # Retry interval in seconds when offline
CONNECTIVITY_CHECK_INTERVAL = int(os.getenv("CONNECTIVITY_CHECK_INTERVAL", "60"))  # Internet check interval in seconds

# Authentication Configuration
WEB_AUTH_ENABLED = os.getenv("WEB_AUTH_ENABLED", "true").lower() == "true"  # Enable web authentication
PASSWORD_HASH = os.getenv("PASSWORD_HASH", "")  # Bcrypt password hash
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")  # Flask secret key for sessions
