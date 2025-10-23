import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

class HealthMonitor:
    """Monitor camera and system health."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.camera_health = {
            'r1': {'online': None, 'last_check': None, 'error': None},
            'r2': {'online': None, 'last_check': None, 'error': None}
        }
        self.system_stats = {
            'cpu_temp': None,
            'last_update': None
        }
    
    def check_camera(self, rtsp_url: str) -> bool:
        """Check if camera is reachable using ffprobe."""
        if not rtsp_url:
            return False
        
        try:
            cmd = [
                "ffprobe",
                "-rtsp_transport", "tcp",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                rtsp_url
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_rpi_temperature(self) -> Optional[float]:
        """Get Raspberry Pi CPU temperature."""
        try:
            temp_file = Path('/sys/class/thermal/thermal_zone0/temp')
            if temp_file.exists():
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return round(temp, 1)
        except Exception:
            pass
        
        try:
            result = subprocess.run(
                ['vcgencmd', 'measure_temp'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if 'temp=' in result.stdout:
                temp = float(result.stdout.replace("temp=", "").replace("'C\n", ""))
                return round(temp, 1)
        except Exception:
            pass
        
        return None
    
    def update_camera_health(self, source: str, rtsp_url: str):
        """Update health status for a camera."""
        is_online = self.check_camera(rtsp_url)
        
        with self._lock:
            self.camera_health[source] = {
                'online': is_online,
                'last_check': time.time(),
                'error': None if is_online else 'Camera offline or unreachable'
            }
    
    def update_system_stats(self):
        """Update system statistics."""
        temp = self.get_rpi_temperature()
        
        with self._lock:
            self.system_stats = {
                'cpu_temp': temp,
                'last_update': time.time()
            }
    
    def get_camera_health(self) -> Dict:
        """Get current camera health status."""
        with self._lock:
            return {k: v.copy() for k, v in self.camera_health.items()}
    
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

