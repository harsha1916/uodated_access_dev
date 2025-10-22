import os
import time
import requests
import logging
import threading
import queue
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import S3_API_URL, MAX_RETRIES, RETRY_DELAY, UPLOAD_ENABLED, BACKGROUND_UPLOAD, UPLOAD_QUEUE_SIZE

class ImageUploader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Persistent queue file for failed/pending uploads
        self.pending_queue_file = "pending_uploads.json"
        
        # Thread-safe queue for background uploads
        self.upload_queue = queue.Queue(maxsize=UPLOAD_QUEUE_SIZE)
        self.upload_thread = None
        self.retry_thread = None
        self.running = False
        self._lock = threading.Lock()
        
        # Track internet connectivity
        self.is_online = True
        self.last_connectivity_check = 0
        self.connectivity_check_interval = 60  # Check every 60 seconds
        
        # Upload statistics
        self.stats = {
            'total_queued': 0,
            'total_uploaded': 0,
            'total_failed': 0,
            'queue_size': 0,
            'pending_retry': 0,
            'offline_mode': False
        }
        
        # Create optimized session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]  # Updated from method_whitelist
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Maximum number of connections in pool
            pool_block=False      # Don't block when pool is full
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set optimized headers
        self.session.headers.update({
            'User-Agent': 'MaxPark-RFID-System/1.0',
            'Connection': 'keep-alive',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })

    def upload(self, filepath: str) -> Optional[str]:
        """Upload image file to S3-compatible API with optimized settings."""
        if not os.path.exists(filepath):
            self.logger.error(f"File does not exist: {filepath}")
            return None
            
        if not os.path.isfile(filepath):
            self.logger.error(f"Path is not a file: {filepath}")
            return None
            
        # Check file size (limit to 15MB - increased for better quality images)
        file_size = os.path.getsize(filepath)
        if file_size > 15 * 1024 * 1024:  # 15MB
            self.logger.error(f"File too large: {filepath} ({file_size} bytes)")
            return None
            
        try:
            with open(filepath, "rb") as image_file:
                files = {
                    "singleFile": (os.path.basename(filepath), image_file, "image/jpeg")
                }
                # Use optimized session with connection pooling
                response = self.session.post(
                    S3_API_URL, 
                    files=files, 
                    timeout=45,  # Increased from 30 to 45 seconds
                    stream=False  # Disable streaming for better performance
                )

                if response.status_code == 200:
                    self.logger.info(f"Successfully uploaded: {filepath}")
                    try:
                        response_json = response.json()
                        location = response_json.get("Location")
                        if location:
                            self.logger.debug(f"S3 Response: {response_json}")
                            # Don't remove file - keep for gallery display
                            return location
                        else:
                            self.logger.error(f"No Location in response: {response_json}")
                    except ValueError as e:
                        self.logger.error(f"Invalid JSON response: {e}")
                        self.logger.error(f"Response content: {response.text}")
                elif response.status_code == 413:
                    self.logger.error(f"File too large for upload: {filepath}")
                    return None  # Don't retry for file size errors
                else:
                    self.logger.error(f"Upload failed {filepath}: {response.status_code} - {response.text}")
                    return None  # Let the retry strategy handle retries

        except requests.exceptions.Timeout:
            self.logger.warning(f"Upload timeout for {filepath}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error for {filepath}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Upload error for {filepath}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during upload of {filepath}: {e}")
            return None
    
    def check_internet_connectivity(self) -> bool:
        """Check if internet connection is available."""
        current_time = time.time()
        
        # Only check if enough time has passed since last check
        if current_time - self.last_connectivity_check < self.connectivity_check_interval:
            return self.is_online
        
        self.last_connectivity_check = current_time
        
        try:
            # Try to reach a reliable endpoint with short timeout
            response = requests.get('https://www.google.com', timeout=5)
            self.is_online = response.status_code == 200
            
            if self.is_online and self.stats['offline_mode']:
                self.logger.info("✓ Internet connection restored - switching to online mode")
                with self._lock:
                    self.stats['offline_mode'] = False
            elif not self.is_online and not self.stats['offline_mode']:
                self.logger.warning("⚠ Internet connection lost - switching to offline mode")
                with self._lock:
                    self.stats['offline_mode'] = True
                    
        except Exception:
            self.is_online = False
            if not self.stats['offline_mode']:
                self.logger.warning("⚠ Internet connection lost - switching to offline mode")
                with self._lock:
                    self.stats['offline_mode'] = True
        
        return self.is_online
    
    def _load_pending_uploads(self) -> List[Dict]:
        """Load pending uploads from persistent queue file."""
        try:
            if os.path.exists(self.pending_queue_file):
                with open(self.pending_queue_file, 'r') as f:
                    pending = json.load(f)
                    self.logger.info(f"Loaded {len(pending)} pending uploads from disk")
                    return pending
        except Exception as e:
            self.logger.error(f"Error loading pending uploads: {e}")
        
        return []
    
    def _save_pending_uploads(self, pending_uploads: List[Dict]):
        """Save pending uploads to persistent queue file."""
        try:
            with open(self.pending_queue_file, 'w') as f:
                json.dump(pending_uploads, f, indent=2)
            
            with self._lock:
                self.stats['pending_retry'] = len(pending_uploads)
                
        except Exception as e:
            self.logger.error(f"Error saving pending uploads: {e}")
    
    def _add_to_pending_queue(self, filepath: str):
        """Add a failed upload to the persistent pending queue."""
        try:
            # Load existing pending uploads
            pending = self._load_pending_uploads()
            
            # Check if file already in pending queue
            if any(item['filepath'] == filepath for item in pending):
                return
            
            # Add new pending upload
            pending.append({
                'filepath': filepath,
                'added_timestamp': time.time(),
                'added_datetime': datetime.now().isoformat(),
                'retry_count': 0
            })
            
            # Save back to file
            self._save_pending_uploads(pending)
            
            self.logger.info(f"Added to pending queue (offline): {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error adding to pending queue: {e}")
    
    def _remove_from_pending_queue(self, filepath: str):
        """Remove an upload from the persistent pending queue."""
        try:
            pending = self._load_pending_uploads()
            pending = [item for item in pending if item['filepath'] != filepath]
            self._save_pending_uploads(pending)
        except Exception as e:
            self.logger.error(f"Error removing from pending queue: {e}")
    
    def queue_upload(self, filepath: str) -> bool:
        """Add image to background upload queue."""
        if not UPLOAD_ENABLED:
            self.logger.debug(f"Upload disabled, skipping: {filepath}")
            return False
            
        if not BACKGROUND_UPLOAD:
            # If background upload is disabled, upload synchronously
            result = self.upload(filepath)
            return result is not None
        
        try:
            # Add to queue with timeout to prevent blocking
            self.upload_queue.put(filepath, timeout=5)
            
            with self._lock:
                self.stats['total_queued'] += 1
                self.stats['queue_size'] = self.upload_queue.qsize()
            
            self.logger.debug(f"Queued for upload: {filepath}")
            return True
            
        except queue.Full:
            self.logger.error(f"Upload queue full, cannot queue: {filepath}")
            return False
        except Exception as e:
            self.logger.error(f"Error queuing upload for {filepath}: {e}")
            return False
    
    def _background_upload_worker(self):
        """Background worker thread that processes upload queue."""
        self.logger.info("Background upload worker started")
        
        while self.running:
            try:
                # Get filepath from queue with timeout
                try:
                    filepath = self.upload_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Update queue size
                with self._lock:
                    self.stats['queue_size'] = self.upload_queue.qsize()
                
                # Check internet connectivity before attempting upload
                if not self.check_internet_connectivity():
                    self.logger.info(f"No internet - adding to pending queue: {filepath}")
                    self._add_to_pending_queue(filepath)
                    self.upload_queue.task_done()
                    continue
                
                # Attempt upload
                try:
                    result = self.upload(filepath)
                    
                    with self._lock:
                        if result:
                            self.stats['total_uploaded'] += 1
                            self.logger.info(f"Background upload successful: {filepath}")
                        else:
                            # Upload failed - add to pending queue for retry
                            self.stats['total_failed'] += 1
                            self._add_to_pending_queue(filepath)
                            self.logger.warning(f"Background upload failed, added to retry queue: {filepath}")
                            
                except Exception as e:
                    with self._lock:
                        self.stats['total_failed'] += 1
                    self._add_to_pending_queue(filepath)
                    self.logger.error(f"Error in background upload, added to retry queue: {e}", exc_info=True)
                finally:
                    # Mark task as done
                    self.upload_queue.task_done()
                    
            except Exception as e:
                self.logger.error(f"Unexpected error in upload worker: {e}", exc_info=True)
        
        self.logger.info("Background upload worker stopped")
    
    def _retry_worker(self):
        """Background worker that retries pending uploads when internet is available."""
        self.logger.info("Retry worker started")
        
        # Initial delay before first retry attempt
        time.sleep(30)
        
        while self.running:
            try:
                # Load pending uploads
                pending = self._load_pending_uploads()
                
                if not pending:
                    # No pending uploads, wait before checking again
                    time.sleep(60)
                    continue
                
                # Check internet connectivity
                if not self.check_internet_connectivity():
                    self.logger.debug(f"Offline - {len(pending)} uploads pending")
                    time.sleep(60)
                    continue
                
                # Internet available - try to upload pending items
                self.logger.info(f"Online - attempting to upload {len(pending)} pending items")
                
                successful = []
                
                for item in pending:
                    if not self.running:
                        break
                    
                    filepath = item['filepath']
                    
                    # Check if file still exists
                    if not os.path.exists(filepath):
                        self.logger.warning(f"Pending file no longer exists: {filepath}")
                        successful.append(filepath)
                        continue
                    
                    # Attempt upload
                    try:
                        result = self.upload(filepath)
                        
                        if result:
                            self.logger.info(f"✓ Retry upload successful: {filepath}")
                            successful.append(filepath)
                            
                            with self._lock:
                                self.stats['total_uploaded'] += 1
                        else:
                            # Update retry count
                            item['retry_count'] = item.get('retry_count', 0) + 1
                            self.logger.warning(f"Retry upload failed (attempt {item['retry_count']}): {filepath}")
                            
                    except Exception as e:
                        item['retry_count'] = item.get('retry_count', 0) + 1
                        self.logger.error(f"Error retrying upload: {e}")
                    
                    # Small delay between retry uploads
                    time.sleep(2)
                
                # Remove successful uploads from pending queue
                if successful:
                    pending = [item for item in pending if item['filepath'] not in successful]
                    self._save_pending_uploads(pending)
                    self.logger.info(f"✓ Uploaded {len(successful)} pending items, {len(pending)} remaining")
                
                # Wait before next retry cycle
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Unexpected error in retry worker: {e}", exc_info=True)
                time.sleep(60)
        
        self.logger.info("Retry worker stopped")
    
    def start_background_upload(self):
        """Start the background upload worker thread and retry worker."""
        if not BACKGROUND_UPLOAD:
            self.logger.info("Background upload is disabled")
            return False
            
        if self.running:
            self.logger.warning("Background upload already running")
            return False
        
        try:
            self.running = True
            
            # Load any pending uploads from previous session
            pending = self._load_pending_uploads()
            if pending:
                self.logger.info(f"Found {len(pending)} pending uploads from previous session")
                with self._lock:
                    self.stats['pending_retry'] = len(pending)
            
            # Start main upload worker thread
            self.upload_thread = threading.Thread(
                target=self._background_upload_worker,
                daemon=True,
                name="ImageUploader-Worker"
            )
            self.upload_thread.start()
            
            # Start retry worker thread
            self.retry_thread = threading.Thread(
                target=self._retry_worker,
                daemon=True,
                name="ImageUploader-Retry"
            )
            self.retry_thread.start()
            
            self.logger.info("Background upload service started (with retry worker)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start background upload: {e}")
            self.running = False
            return False
    
    def stop_background_upload(self, wait_for_completion: bool = True):
        """Stop the background upload worker thread and retry worker."""
        if not self.running:
            return
        
        self.logger.info("Stopping background upload service...")
        self.running = False
        
        if wait_for_completion and self.upload_thread:
            # Wait for queue to be processed
            self.logger.info("Waiting for upload queue to complete...")
            self.upload_queue.join()
            
            # Wait for threads to finish
            self.upload_thread.join(timeout=10)
            
        if self.retry_thread:
            self.retry_thread.join(timeout=5)
            
        self.logger.info("Background upload service stopped")
    
    def get_stats(self) -> Dict:
        """Get upload statistics."""
        with self._lock:
            return self.stats.copy()
    
    def get_queue_size(self) -> int:
        """Get current upload queue size."""
        return self.upload_queue.qsize()
