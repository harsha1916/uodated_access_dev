import os
import time
import requests
import threading
from datetime import datetime
from typing import Optional, Dict

from json_uploader import JSONUploader
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
        
        filename = os.path.basename(filepath)
        print(f"[UPLOADER] Uploading {filename} ({file_size} bytes)...")
        
        # Retry logic (like uploader1.py)
        attempts = 0
        while attempts < self.max_retries:
            try:
                with open(filepath, "rb") as image_file:
                    # Use exact pattern from uploader1.py
                    files = {
                        self.field_name: (filename, image_file, "image/jpeg")
                    }
                    
                    # Debug: Show request details
                    print(f"[UPLOADER] Attempt {attempts + 1}/{self.max_retries}")
                    print(f"[UPLOADER] → Endpoint: {self.endpoint}")
                    print(f"[UPLOADER] → Field name: {self.field_name}")
                    print(f"[UPLOADER] → Filename: {filename}")
                    
                    response = requests.post(
                        self.endpoint,
                        files=files,
                        headers=self._headers(),
                        timeout=self.timeout
                    )
                    
                    print(f"[UPLOADER] ← Response: HTTP {response.status_code}")
                
                # Check response
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        location = response_json.get("Location")
                        if location:
                            print(f"[UPLOADER] ✓ Success! Location: {location}")
                            return True
                        else:
                            print(f"[UPLOADER] ✓ Success (no Location in response)")
                            return True
                    except ValueError:
                        # Not JSON, but 200 = success
                        print(f"[UPLOADER] ✓ Success (non-JSON response)")
                        return True
                else:
                    # Show error details for debugging
                    print(f"[UPLOADER] ✗ Upload failed: HTTP {response.status_code}")
                    print(f"[UPLOADER] ✗ Response: {response.text[:500]}")
                
            except requests.exceptions.Timeout:
                print(f"[UPLOADER] ⚠ Upload timeout after {self.timeout}s")
            except requests.exceptions.ConnectionError as e:
                print(f"[UPLOADER] ⚠ Connection error: {str(e)[:200]}")
            except requests.exceptions.RequestException as e:
                print(f"[UPLOADER] ✗ Request error: {type(e).__name__}: {str(e)[:200]}")
            except Exception as e:
                print(f"[UPLOADER] ✗ Unexpected error: {type(e).__name__}: {str(e)[:200]}")
            
            # Retry logic
            attempts += 1
            if attempts < self.max_retries:
                print(f"[UPLOADER] Retrying in {self.retry_delay}s... (attempt {attempts + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
        
        # All retries failed
        print(f"[UPLOADER] ✗ Giving up on {filename} after {self.max_retries} attempts")
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


class JSONQueueWorker:
    """Upload queued images as compressed base64 JSON payloads."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        batch_size: int = 5,
        sleep_ok: float = 5.0,
        sleep_fail: float = 15.0,
    ):
        self.endpoint = endpoint or os.getenv("JSON_UPLOAD_URL", "")
        self.batch_size = batch_size
        self.sleep_ok = sleep_ok
        self.sleep_fail = sleep_fail
        self.timeout = int(os.getenv("JSON_UPLOAD_TIMEOUT", "60"))
        self._stop = False

        # Offline tracking
        self._lock = threading.Lock()
        self.is_online = True
        self.last_connectivity_check = 0
        self.connectivity_check_interval = int(os.getenv("CONNECTIVITY_CHECK_INTERVAL", "60"))

        # Statistics
        self.stats = {
            "total_uploaded": 0,
            "total_failed": 0,
            "offline_mode": False,
            "last_check": None,
        }

        self.json_uploader = JSONUploader()
        if self.endpoint:
            self.json_uploader.custom_url = self.endpoint

        self.reader_map = {
            "r1": int(os.getenv("READER_ID_R1", "1")),
            "r2": int(os.getenv("READER_ID_R2", "2")),
        }

    def stop(self):
        self._stop = True

    def set_endpoint(self, endpoint: str):
        with self._lock:
            self.endpoint = endpoint
            self.json_uploader.custom_url = endpoint

    def _headers(self):
        return self.json_uploader.session.headers

    def get_stats(self) -> Dict:
        with self._lock:
            stats = self.stats.copy()
            stats["endpoint"] = self.endpoint
            return stats

    def check_internet_connectivity(self) -> bool:
        current_time = time.time()
        if current_time - self.last_connectivity_check < self.connectivity_check_interval:
            return self.is_online

        self.last_connectivity_check = current_time

        try:
            response = requests.get("https://www.google.com", timeout=5)
            self.is_online = response.status_code == 200
            with self._lock:
                if self.is_online and self.stats["offline_mode"]:
                    print("[JSON-UPLOADER] ✓ Internet connection restored - switching to online mode")
                    self.stats["offline_mode"] = False
                elif not self.is_online and not self.stats["offline_mode"]:
                    print("[JSON-UPLOADER] ⚠ Internet connection lost - switching to offline mode")
                    self.stats["offline_mode"] = True
                self.stats["last_check"] = current_time
        except Exception:
            self.is_online = False
            with self._lock:
                if not self.stats["offline_mode"]:
                    print("[JSON-UPLOADER] ⚠ Internet connection lost - switching to offline mode")
                    self.stats["offline_mode"] = True
                self.stats["last_check"] = current_time

        return self.is_online

    def _build_payload(self, item: Dict) -> Optional[Dict]:
        filepath = item["filename"]
        base64_image = self.json_uploader.image_to_base64(filepath, compress=True)
        if not base64_image:
            return None

        timestamp = item.get("epoch") or int(time.time())
        reader_id = self.reader_map.get(item.get("source", ""), 0)

        return {
            "reader_id": reader_id,
            "timestamp": timestamp,
            "iso_timestamp": datetime.fromtimestamp(timestamp).isoformat(),
            "filename": os.path.basename(filepath),
            "image_base64": base64_image,
        }

    def upload_item(self, item: Dict) -> bool:
        if not self.endpoint:
            print("[JSON-UPLOADER] No endpoint configured for JSON upload")
            return False

        filepath = item["filename"]
        if not os.path.exists(filepath):
            print(f"[JSON-UPLOADER] File missing, marking uploaded: {os.path.basename(filepath)}")
            return True

        payload = self._build_payload(item)
        if not payload:
            print(f"[JSON-UPLOADER] Failed to build payload for {os.path.basename(filepath)}")
            return False

        self.json_uploader.custom_url = self.endpoint
        print(f"[JSON-UPLOADER] Uploading {os.path.basename(filepath)} to {self.endpoint}")
        return self.json_uploader.upload(payload)

    def run_forever(self):
        print("[JSON-UPLOADER] Background JSON upload thread started")
        print(f"[JSON-UPLOADER] Endpoint: {self.endpoint or 'NOT SET'}")

        while not self._stop:
            try:
                is_online = self.check_internet_connectivity()
                items = get_pending_batch(self.batch_size)

                if not items:
                    time.sleep(self.sleep_ok)
                    continue

                if not is_online:
                    print(f"[JSON-UPLOADER] Offline - {len(items)} images pending, will retry when online")
                    time.sleep(self.sleep_fail)
                    continue

                had_error = False
                for item in items:
                    fid = item["id"]
                    filepath = item["filename"]

                    if not os.path.exists(filepath):
                        print(f"[JSON-UPLOADER] File gone, marking as uploaded: {os.path.basename(filepath)}")
                        mark_uploaded(fid)
                        continue

                    success = self.upload_item(item)
                    if success:
                        mark_uploaded(fid)
                        with self._lock:
                            self.stats["total_uploaded"] += 1
                    else:
                        had_error = True
                        mark_failed(fid, "JSON upload failed")
                        with self._lock:
                            self.stats["total_failed"] += 1

                time.sleep(self.sleep_fail if had_error else self.sleep_ok)

            except Exception as e:
                print(f"[JSON-UPLOADER] ✗ Error in upload loop: {type(e).__name__}: {str(e)[:100]}")
                time.sleep(self.sleep_fail)

        print("[JSON-UPLOADER] Background JSON upload thread stopped")
