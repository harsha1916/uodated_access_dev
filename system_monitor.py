import os
import logging
import threading
import time
import cv2
from typing import Dict, Optional
from pathlib import Path
from config import RTSP_CAMERAS, is_camera_enabled


class SystemMonitor:
    """Monitor system health including cameras and Raspberry Pi temperature."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Camera health status
        self.camera_health = {
            'camera_1': {'online': None, 'last_check': None, 'error': None},
            'camera_2': {'online': None, 'last_check': None, 'error': None},
            'camera_3': {'online': None, 'last_check': None, 'error': None}
        }
        
        # System stats
        self.system_stats = {
            'cpu_temp': None,
            'cpu_temp_unit': '°C',
            'last_update': None
        }
        
        self.monitoring_thread = None
        self.running = False
    
    def check_camera_health(self, camera_key: str) -> bool:
        """
        Check if camera is online by attempting to connect.
        
        Returns:
            True if camera is online, False otherwise
        """
        # Check if camera is enabled (dynamically from .env)
        if not is_camera_enabled(camera_key):
            return False
        
        try:
            rtsp_url = RTSP_CAMERAS.get(camera_key)
            if not rtsp_url:
                return False
            
            # Try to open camera with short timeout
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Check if opened
            is_online = cap.isOpened()
            
            # Try to read one frame
            if is_online:
                ret, _ = cap.read()
                is_online = ret
            
            cap.release()
            
            return is_online
            
        except Exception as e:
            self.logger.error(f"Error checking {camera_key} health: {e}")
            return False
    
    def get_raspberry_pi_temperature(self) -> Optional[float]:
        """
        Get Raspberry Pi CPU temperature.
        
        Returns:
            Temperature in Celsius, or None if not available
        """
        try:
            # Try Raspberry Pi thermal zone
            temp_file = Path('/sys/class/thermal/thermal_zone0/temp')
            if temp_file.exists():
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return round(temp, 1)
        except Exception:
            pass
        
        try:
            # Try alternative method (vcgencmd)
            result = os.popen('vcgencmd measure_temp').read()
            if 'temp=' in result:
                temp = float(result.replace("temp=", "").replace("'C\n", ""))
                return round(temp, 1)
        except Exception:
            pass
        
        return None
    
    def update_camera_health(self):
        """Update health status for all cameras."""
        for camera_key in ['camera_1', 'camera_2', 'camera_3']:
            try:
                is_online = self.check_camera_health(camera_key)
                
                with self._lock:
                    self.camera_health[camera_key] = {
                        'online': is_online,
                        'last_check': time.time(),
                        'error': None if is_online else 'Camera offline or unreachable'
                    }
                
                status = "✓ ONLINE" if is_online else "✗ OFFLINE"
                self.logger.debug(f"{camera_key}: {status}")
                
            except Exception as e:
                with self._lock:
                    self.camera_health[camera_key] = {
                        'online': False,
                        'last_check': time.time(),
                        'error': str(e)
                    }
                self.logger.error(f"Error updating {camera_key} health: {e}")
    
    def update_system_stats(self):
        """Update system statistics."""
        try:
            temp = self.get_raspberry_pi_temperature()
            
            with self._lock:
                self.system_stats = {
                    'cpu_temp': temp,
                    'cpu_temp_unit': '°C',
                    'last_update': time.time()
                }
                
            if temp:
                self.logger.debug(f"System temperature: {temp}°C")
                
        except Exception as e:
            self.logger.error(f"Error updating system stats: {e}")
    
    def _monitoring_worker(self):
        """Background worker thread for continuous monitoring."""
        self.logger.info("System monitoring worker started")
        
        # Initial check
        self.update_camera_health()
        self.update_system_stats()
        
        while self.running:
            try:
                # Update camera health every 60 seconds
                time.sleep(60)
                
                if self.running:
                    self.update_camera_health()
                    self.update_system_stats()
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring worker: {e}", exc_info=True)
                time.sleep(60)
        
        self.logger.info("System monitoring worker stopped")
    
    def start(self):
        """Start background monitoring."""
        if self.running:
            self.logger.warning("System monitoring already running")
            return False
        
        try:
            self.running = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_worker,
                daemon=True,
                name="SystemMonitor-Worker"
            )
            self.monitoring_thread.start()
            self.logger.info("System monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system monitoring: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop background monitoring."""
        if not self.running:
            return
        
        self.logger.info("Stopping system monitoring...")
        self.running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("System monitoring stopped")
    
    def get_camera_health(self) -> Dict:
        """Get current camera health status."""
        with self._lock:
            return {
                k: v.copy() for k, v in self.camera_health.items()
            }
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics."""
        with self._lock:
            return self.system_stats.copy()
    
    def get_all_status(self) -> Dict:
        """Get all monitoring data."""
        return {
            'camera_health': self.get_camera_health(),
            'system_stats': self.get_system_stats()
        }

