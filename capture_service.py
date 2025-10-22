import cv2
import time
import datetime
import os
import threading
import logging
from typing import Optional, Dict
from config import (
    RTSP_CAMERAS, MAX_RETRIES, RETRY_DELAY, IMAGE_STORAGE_PATH,
    CAMERA_NAMES, UPLOAD_ENABLED, is_camera_enabled
)
from uploader import ImageUploader


class CameraService:
    """Service to capture images from RTSP cameras."""
    
    def __init__(self):
        self.uploader = ImageUploader()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Capture statistics
        self.stats = {
            'camera_1': {'total_captures': 0, 'successful': 0, 'failed': 0},
            'camera_2': {'total_captures': 0, 'successful': 0, 'failed': 0},
            'camera_3': {'total_captures': 0, 'successful': 0, 'failed': 0}
        }
        
        # Ensure images directory exists
        os.makedirs(IMAGE_STORAGE_PATH, exist_ok=True)
        self.logger.info(f"Image storage path: {IMAGE_STORAGE_PATH}")
        
        # Check camera status
        self._log_camera_status()
    
    def _log_camera_status(self):
        """Log enabled/disabled status of cameras."""
        status = {
            'camera_1 (r1/entry)': 'ENABLED' if is_camera_enabled('camera_1') else 'DISABLED',
            'camera_2 (r2/exit)': 'ENABLED' if is_camera_enabled('camera_2') else 'DISABLED',
            'camera_3 (r3/auxiliary)': 'ENABLED' if is_camera_enabled('camera_3') else 'DISABLED'
        }
        for camera, state in status.items():
            self.logger.info(f"{camera}: {state}")
    
    def _is_camera_enabled(self, camera_key: str) -> bool:
        """Check if a camera is enabled (dynamically from .env)."""
        return is_camera_enabled(camera_key)
    
    def _get_camera_name(self, camera_key: str) -> str:
        """Get the camera name (r1/r2/r3) from camera key."""
        return CAMERA_NAMES.get(camera_key, camera_key)
    
    def _capture_image(self, camera_key: str) -> Optional[Dict[str, str]]:
        """
        Capture image from specified camera and queue for upload.
        
        Args:
            camera_key: Camera identifier (camera_1, camera_2, camera_3)
            
        Returns:
            Dictionary with 'local_path' and 'camera_name' if successful, None otherwise
        """
        # Update statistics
        with self._lock:
            self.stats[camera_key]['total_captures'] += 1
        
        # Check if camera is enabled
        if not self._is_camera_enabled(camera_key):
            self.logger.warning(f"{camera_key} is disabled, skipping capture")
            with self._lock:
                self.stats[camera_key]['failed'] += 1
            return None
        
        # Validate camera key
        if camera_key not in RTSP_CAMERAS.keys():
            self.logger.error(f"Invalid camera key: {camera_key}")
            with self._lock:
                self.stats[camera_key]['failed'] += 1
            return None
        
        # Get camera name (r1, r2, r3)
        camera_name = self._get_camera_name(camera_key)
        rtsp_url = RTSP_CAMERAS.get(camera_key)
        retries = 0

        while retries < MAX_RETRIES:
            cap = None
            try:
                self.logger.debug(f"{camera_key} ({camera_name}): Attempting to connect to camera...")
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for faster capture

                if not cap.isOpened():
                    self.logger.warning(
                        f"{camera_key} ({camera_name}): Camera not available. "
                        f"Retrying ({retries + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(RETRY_DELAY)
                    retries += 1
                    continue

                # Read frame
                ret, frame = cap.read()

                if ret and frame is not None:
                    # Generate filename: {camera_name}_{epochtime}.jpg
                    timestamp = int(time.time())
                    filename = f"{camera_name}_{timestamp}.jpg"
                    filepath = os.path.join(IMAGE_STORAGE_PATH, filename)
                    
                    # Save image locally
                    if cv2.imwrite(filepath, frame):
                        self.logger.info(
                            f"{camera_key} ({camera_name}): Image captured -> {filename}"
                        )
                        
                        # Update success statistics
                        with self._lock:
                            self.stats[camera_key]['successful'] += 1
                        
                        # Queue for background upload if enabled
                        if UPLOAD_ENABLED:
                            upload_queued = self.uploader.queue_upload(filepath)
                            if upload_queued:
                                self.logger.debug(f"{camera_key} ({camera_name}): Queued for S3 upload")
                            else:
                                self.logger.warning(
                                    f"{camera_key} ({camera_name}): Failed to queue for upload"
                                )
                        
                        return {
                            'local_path': filepath,
                            'camera_name': camera_name,
                            'camera_key': camera_key,
                            'timestamp': timestamp,
                            'filename': filename
                        }
                    else:
                        self.logger.error(
                            f"{camera_key} ({camera_name}): Failed to save image to {filepath}"
                        )
                        retries += 1
                        continue

                self.logger.warning(
                    f"{camera_key} ({camera_name}): Failed to capture frame. Retrying..."
                )
                retries += 1
                time.sleep(RETRY_DELAY)
                
            except Exception as e:
                self.logger.error(
                    f"{camera_key} ({camera_name}): Error during capture: {e}",
                    exc_info=True
                )
                retries += 1
                time.sleep(RETRY_DELAY)
            finally:
                if cap is not None:
                    cap.release()

        # Max retries reached
        self.logger.error(f"{camera_key} ({camera_name}): Max retries reached. Capture failed.")
        with self._lock:
            self.stats[camera_key]['failed'] += 1
        return None

    def capture_camera_1(self) -> Optional[Dict[str, str]]:
        """Capture image from camera 1 (r1/entry)."""
        return self._capture_image("camera_1")

    def capture_camera_2(self) -> Optional[Dict[str, str]]:
        """Capture image from camera 2 (r2/exit)."""
        return self._capture_image("camera_2")

    def capture_camera_3(self) -> Optional[Dict[str, str]]:
        """Capture image from camera 3 (r3/auxiliary)."""
        return self._capture_image("camera_3")
    
    def capture_by_key(self, camera_key: str) -> Optional[Dict[str, str]]:
        """
        Capture image from camera by key.
        
        Args:
            camera_key: Camera identifier (camera_1, camera_2, camera_3)
            
        Returns:
            Dictionary with capture information if successful, None otherwise
        """
        if camera_key == "camera_1":
            return self.capture_camera_1()
        elif camera_key == "camera_2":
            return self.capture_camera_2()
        elif camera_key == "camera_3":
            return self.capture_camera_3()
        else:
            self.logger.error(f"Invalid camera key: {camera_key}")
            return None
    
    def get_stats(self) -> Dict:
        """Get capture statistics for all cameras."""
        with self._lock:
            return {
                'cameras': self.stats.copy(),
                'upload_stats': self.uploader.get_stats()
            }
    
    def start_upload_service(self):
        """Start the background upload service."""
        return self.uploader.start_background_upload()
    
    def stop_upload_service(self, wait_for_completion: bool = True):
        """Stop the background upload service."""
        self.uploader.stop_background_upload(wait_for_completion)
