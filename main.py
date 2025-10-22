#!/usr/bin/env python3
"""
Camera Capture System with GPIO Triggers and S3 Upload

This application captures images from RTSP cameras when GPIO pins are triggered (LOW state),
uploads them to S3 in the background, and provides a web interface for viewing captured images.

Features:
- GPIO hardware triggers (on LOW state)
- Background threaded S3 uploads
- Automatic image cleanup after 120 days (configurable)
- Web interface for viewing images and system status
- Configurable camera enable/disable
- Support for 3 cameras: r1 (entry), r2 (exit), r3 (auxiliary)
"""

import os
import sys
import signal
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('camera_system.log')
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')
    
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        import flask_cors
    except ImportError:
        missing.append('flask-cors')
    
    try:
        import requests
    except ImportError:
        missing.append('requests')
    
    try:
        import dotenv
    except ImportError:
        missing.append('python-dotenv')
    
    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
        logger.error("Please install them using: pip install -r requirements.txt")
        return False
    
    return True


def setup_environment():
    """Setup environment and load configuration."""
    try:
        from dotenv import load_dotenv
        
        # Load .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv()
            logger.info("Loaded configuration from .env file")
        else:
            logger.warning(".env file not found, using default configuration")
            logger.info("You can create a .env file based on .env.example")
        
        # Import and log configuration
        from config import (
            BIND_IP, BIND_PORT, GPIO_ENABLED, GPIO_TRIGGER_ENABLED,
            UPLOAD_ENABLED, BACKGROUND_UPLOAD, IMAGE_RETENTION_DAYS,
            CAMERA_1_ENABLED, CAMERA_2_ENABLED, CAMERA_3_ENABLED
        )
        
        logger.info("=== System Configuration ===")
        logger.info(f"Web Server: {BIND_IP}:{BIND_PORT}")
        logger.info(f"GPIO Enabled: {GPIO_ENABLED}")
        logger.info(f"GPIO Triggering: {GPIO_TRIGGER_ENABLED}")
        logger.info(f"Upload Enabled: {UPLOAD_ENABLED}")
        logger.info(f"Background Upload: {BACKGROUND_UPLOAD}")
        logger.info(f"Image Retention: {IMAGE_RETENTION_DAYS} days")
        logger.info(f"Camera 1 (r1/entry): {'ENABLED' if CAMERA_1_ENABLED else 'DISABLED'}")
        logger.info(f"Camera 2 (r2/exit): {'ENABLED' if CAMERA_2_ENABLED else 'DISABLED'}")
        logger.info(f"Camera 3 (r3/auxiliary): {'ENABLED' if CAMERA_3_ENABLED else 'DISABLED'}")
        logger.info("===========================")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up environment: {e}", exc_info=True)
        return False


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Camera Capture System')
    parser.add_argument('--test-capture', action='store_true',
                        help='Test capture from all enabled cameras and exit')
    parser.add_argument('--test-gpio', action='store_true',
                        help='Test GPIO setup and exit')
    parser.add_argument('--cleanup-now', action='store_true',
                        help='Run cleanup immediately and exit')
    args = parser.parse_args()
    
    logger.info("=== Camera Capture System Starting ===")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    try:
        # Test mode: Capture
        if args.test_capture:
            logger.info("Running test capture mode...")
            from capture_service import CameraService
            
            service = CameraService()
            
            for camera_key in ['camera_1', 'camera_2', 'camera_3']:
                logger.info(f"Testing {camera_key}...")
                result = service.capture_by_key(camera_key)
                if result:
                    logger.info(f"✓ {camera_key} test successful: {result['filename']}")
                else:
                    logger.error(f"✗ {camera_key} test failed")
            
            return 0
        
        # Test mode: GPIO
        if args.test_gpio:
            logger.info("Running GPIO test mode...")
            from gpio_service import GPIOService
            
            gpio = GPIOService()
            if gpio.is_available():
                logger.info("✓ GPIO service initialized successfully")
                
                # Check pin states
                for camera_key in ['camera_1', 'camera_2', 'camera_3']:
                    state = gpio.get_pin_state(camera_key)
                    logger.info(f"{camera_key} pin state: {state}")
                
                gpio.cleanup()
            else:
                logger.error("✗ GPIO service not available")
            
            return 0
        
        # Cleanup mode
        if args.cleanup_now:
            logger.info("Running cleanup mode...")
            from cleanup_service import CleanupService
            
            cleanup = CleanupService()
            deleted = cleanup.run_cleanup()
            logger.info(f"✓ Cleanup completed: {deleted} images deleted")
            
            return 0
        
        # Normal mode: Start web application
        logger.info("Starting web application...")
        from web_app import app, init_services, cleanup_on_shutdown
        from config import BIND_IP, BIND_PORT
        
        # Initialize all services
        init_services()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            cleanup_on_shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start Flask application
        logger.info(f"Web interface available at http://{BIND_IP}:{BIND_PORT}")
        logger.info("Press Ctrl+C to stop")
        
        app.run(
            host=BIND_IP,
            port=BIND_PORT,
            debug=False,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        logger.info("=== Camera Capture System Stopped ===")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

