import os
import time
import requests
import threading
from typing import Optional, Dict
from storage import get_pending_batch, mark_uploaded, mark_failed


class Uploader:
    """Background uploader for queued images with offline support."""
    
    def __init__(
        self,
        mode: str,
        endpoint: Optional[str] = None,
        bearer_token: Optional[str] = None,
        field_name: str = "singleFile",  # Changed to match uploader1.py
        presigner=None,
        batch_size: int = 5,
        sleep_ok: float = 5.0,
        sleep_fail: float = 15.0,
        timeout: int = 30  # Increased to match uploader1.py
    ):
        self.mode = (mode or "POST").upper()
        self.endpoint = endpoint
        self.bearer_token = bearer_token
        self.field_name = field_name
        self.batch_size = batch_size
        self.sleep_ok = sleep_ok
        self.sleep_fail = sleep_fail
        self.timeout = timeout
        self._stop = False
        
        # Offline mode tracking
        self._lock = threading.Lock()
        self.is_online = True
        self.last_connectivity_check = 0
        self.connectivity_check_interval = int(os.getenv('CONNECTIVITY_CHECK_INTERVAL', '60'))
        
        # Statistics
        self.stats = {
            'total_uploaded': 0,
            'total_failed': 0,
            'offline_mode': False,
            'last_check': None
        }
        
        # Retry configuration (like uploader1.py)
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))

    def stop(self):
        self._stop = True

    def _headers(self):
        """Build request headers."""
        h = {"User-Agent": "camcap-uploader/1.0"}
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        return h

    def check_internet_connectivity(self) -> bool:
        """Check if internet connection is available."""
        current_time = time.time()
        
        # Only check if enough time has passed
        if current_time - self.last_connectivity_check < self.connectivity_check_interval:
            return self.is_online
        
        self.last_connectivity_check = current_time
        
        try:
            # Try to reach a reliable endpoint
            response = requests.get('https://www.google.com', timeout=5)
            self.is_online = response.status_code == 200
            
            with self._lock:
                if self.is_online and self.stats['offline_mode']:
                    print("[UPLOADER] ✓ Internet connection restored - switching to online mode")
                    self.stats['offline_mode'] = False
                elif not self.is_online and not self.stats['offline_mode']:
                    print("[UPLOADER] ⚠ Internet connection lost - switching to offline mode")
                    self.stats['offline_mode'] = True
                self.stats['last_check'] = current_time
                    
        except Exception:
            self.is_online = False
            with self._lock:
                if not self.stats['offline_mode']:
                    print("[UPLOADER] ⚠ Internet connection lost - switching to offline mode")
                    self.stats['offline_mode'] = True
                self.stats['last_check'] = current_time
        
        return self.is_online

    def upload_single(self, filepath: str) -> bool:
        """
        Upload single image file to S3 (based on uploader1.py pattern).
        Returns True on success, False on failure.
        """
        if not os.path.exists(filepath):
            print(f"[UPLOADER] File does not exist: {filepath}")
            return False
            
        if not os.path.isfile(filepath):
            print(f"[UPLOADER] Path is not a file: {filepath}")
            return False
        
        # Check file size (limit to 15MB)
        file_size = os.path.getsize(filepath)
        if file_size > 15 * 1024 * 1024:
            print(f"[UPLOADER] File too large: {filepath} ({file_size} bytes)")
            return False
        
        # Retry logic (like uploader1.py)
        attempts = 0
        while attempts < self.max_retries:
            try:
                with open(filepath, "rb") as image_file:
                    files = {
                        self.field_name: (os.path.basename(filepath), image_file, "image/jpeg")
                    }
                    response = requests.post(
                        self.endpoint,
                        files=files,
                        headers=self._headers(),
                        timeout=self.timeout
                    )
                
                # Check response
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        location = response_json.get("Location")
                        if location:
                            print(f"[UPLOADER] ✓ Uploaded: {os.path.basename(filepath)}")
                            return True
                        else:
                            print(f"[UPLOADER] ⚠ No Location in response")
                    except ValueError:
                        print(f"[UPLOADER] ⚠ Invalid JSON response")
                    
                    # Even without Location, 200 = success
                    if response.status_code == 200:
                        return True
                else:
                    print(f"[UPLOADER] ✗ Upload failed: HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                print(f"[UPLOADER] ⚠ Upload timeout for {os.path.basename(filepath)}")
            except requests.exceptions.ConnectionError:
                print(f"[UPLOADER] ⚠ Connection error for {os.path.basename(filepath)}")
            except requests.exceptions.RequestException as e:
                print(f"[UPLOADER] ✗ Upload error: {type(e).__name__}")
            except Exception as e:
                print(f"[UPLOADER] ✗ Unexpected error: {type(e).__name__}: {str(e)[:100]}")
            
            # Retry logic
            attempts += 1
            if attempts < self.max_retries:
                print(f"[UPLOADER] Retrying in {self.retry_delay}s... (attempt {attempts + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
        
        # All retries failed
        print(f"[UPLOADER] ✗ Giving up on {os.path.basename(filepath)} after {self.max_retries} attempts")
        return False

    def get_stats(self) -> Dict:
        """Get uploader statistics."""
        with self._lock:
            return self.stats.copy()

    def run_forever(self):
        """Background upload worker thread."""
        print("[UPLOADER] Background upload thread started")
        print(f"[UPLOADER] Mode: {self.mode}, Endpoint: {self.endpoint or 'NOT SET'}")
        print(f"[UPLOADER] Retries: {self.max_retries}, Batch size: {self.batch_size}")
        
        while not self._stop:
            try:
                # Check internet connectivity
                is_online = self.check_internet_connectivity()
                
                # Get pending uploads
                items = get_pending_batch(self.batch_size)
                
                if not items:
                    # No pending items, sleep and continue
                    time.sleep(self.sleep_ok)
                    continue
                
                # If offline, skip upload and retry later
                if not is_online:
                    print(f"[UPLOADER] Offline - {len(items)} images pending, will retry when online")
                    time.sleep(self.sleep_fail)
                    continue
                
                # Online - process uploads
                print(f"[UPLOADER] Processing {len(items)} pending uploads...")
                
                had_error = False
                for item in items:
                    fid = item["id"]
                    filepath = item["filename"]
                    
                    # Check if file still exists
                    if not os.path.exists(filepath):
                        print(f"[UPLOADER] File gone, marking as uploaded: {os.path.basename(filepath)}")
                        mark_uploaded(fid)
                        continue
                    
                    # Attempt upload
                    success = self.upload_single(filepath)
                    
                    if success:
                        # Mark as successfully uploaded
                        mark_uploaded(fid)
                        with self._lock:
                            self.stats['total_uploaded'] += 1
                    else:
                        # Mark as failed (will retry later)
                        had_error = True
                        mark_failed(fid, "Upload failed after retries")
                        with self._lock:
                            self.stats['total_failed'] += 1
                
                # Sleep before next batch
                time.sleep(self.sleep_fail if had_error else self.sleep_ok)
                
            except Exception as e:
                print(f"[UPLOADER] ✗ Error in upload loop: {type(e).__name__}: {str(e)[:100]}")
                time.sleep(self.sleep_fail)
        
        print("[UPLOADER] Background upload thread stopped")
