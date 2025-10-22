import os
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from config import IMAGE_STORAGE_PATH, IMAGE_RETENTION_DAYS, CLEANUP_INTERVAL_HOURS


class CleanupService:
    """Service to automatically delete old images based on retention policy."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.cleanup_thread = None
        self.stats = {
            'total_cleaned': 0,
            'last_cleanup': None,
            'last_cleanup_count': 0,
            'errors': 0
        }
        self._lock = threading.Lock()
        
        self.logger.info(
            f"Cleanup service initialized: Retention={IMAGE_RETENTION_DAYS} days, "
            f"Interval={CLEANUP_INTERVAL_HOURS} hours"
        )
    
    def _get_image_files(self) -> List[Path]:
        """Get all image files in the storage directory."""
        try:
            storage_path = Path(IMAGE_STORAGE_PATH)
            if not storage_path.exists():
                self.logger.warning(f"Storage path does not exist: {IMAGE_STORAGE_PATH}")
                return []
            
            # Get all .jpg and .jpeg files
            image_files = []
            image_files.extend(storage_path.glob("*.jpg"))
            image_files.extend(storage_path.glob("*.jpeg"))
            image_files.extend(storage_path.glob("*.JPG"))
            image_files.extend(storage_path.glob("*.JPEG"))
            
            return image_files
            
        except Exception as e:
            self.logger.error(f"Error getting image files: {e}", exc_info=True)
            return []
    
    def _delete_old_images(self) -> int:
        """
        Delete images older than retention period.
        
        Returns:
            Number of images deleted
        """
        deleted_count = 0
        cutoff_time = time.time() - (IMAGE_RETENTION_DAYS * 24 * 60 * 60)
        
        try:
            image_files = self._get_image_files()
            self.logger.info(f"Found {len(image_files)} image files to check")
            
            for image_path in image_files:
                try:
                    # Get file modification time
                    file_mtime = image_path.stat().st_mtime
                    
                    # Check if file is older than retention period
                    if file_mtime < cutoff_time:
                        file_age_days = (time.time() - file_mtime) / (24 * 60 * 60)
                        self.logger.info(
                            f"Deleting old image: {image_path.name} "
                            f"(age: {file_age_days:.1f} days)"
                        )
                        
                        # Delete the file
                        image_path.unlink()
                        deleted_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Error deleting file {image_path}: {e}")
                    with self._lock:
                        self.stats['errors'] += 1
            
            self.logger.info(f"Cleanup completed: {deleted_count} images deleted")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
            with self._lock:
                self.stats['errors'] += 1
            return deleted_count
    
    def run_cleanup(self) -> int:
        """
        Run cleanup operation once.
        
        Returns:
            Number of images deleted
        """
        self.logger.info("Starting cleanup operation...")
        
        deleted_count = self._delete_old_images()
        
        # Update statistics
        with self._lock:
            self.stats['total_cleaned'] += deleted_count
            self.stats['last_cleanup'] = datetime.now().isoformat()
            self.stats['last_cleanup_count'] = deleted_count
        
        return deleted_count
    
    def _cleanup_worker(self):
        """Background worker thread that runs periodic cleanup."""
        self.logger.info("Cleanup worker started")
        
        # Run initial cleanup
        self.run_cleanup()
        
        # Calculate sleep interval in seconds
        sleep_interval = CLEANUP_INTERVAL_HOURS * 60 * 60
        
        while self.running:
            try:
                # Sleep in small intervals to allow responsive shutdown
                elapsed = 0
                while elapsed < sleep_interval and self.running:
                    time.sleep(60)  # Sleep 1 minute at a time
                    elapsed += 60
                
                if self.running:
                    self.run_cleanup()
                    
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}", exc_info=True)
                with self._lock:
                    self.stats['errors'] += 1
        
        self.logger.info("Cleanup worker stopped")
    
    def start(self):
        """Start the background cleanup service."""
        if self.running:
            self.logger.warning("Cleanup service already running")
            return False
        
        try:
            self.running = True
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True,
                name="CleanupService-Worker"
            )
            self.cleanup_thread.start()
            self.logger.info("Cleanup service started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start cleanup service: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the background cleanup service."""
        if not self.running:
            return
        
        self.logger.info("Stopping cleanup service...")
        self.running = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        
        self.logger.info("Cleanup service stopped")
    
    def get_stats(self) -> dict:
        """Get cleanup statistics."""
        with self._lock:
            stats = self.stats.copy()
        
        # Add current storage info
        try:
            image_files = self._get_image_files()
            stats['current_image_count'] = len(image_files)
            
            # Calculate total storage size
            total_size = sum(f.stat().st_size for f in image_files)
            stats['total_storage_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Get oldest and newest file info
            if image_files:
                oldest_file = min(image_files, key=lambda f: f.stat().st_mtime)
                newest_file = max(image_files, key=lambda f: f.stat().st_mtime)
                
                oldest_age_days = (time.time() - oldest_file.stat().st_mtime) / (24 * 60 * 60)
                
                stats['oldest_image'] = oldest_file.name
                stats['oldest_image_age_days'] = round(oldest_age_days, 1)
                stats['newest_image'] = newest_file.name
                
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
        
        return stats
    
    def get_image_list(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """
        Get list of images with metadata.
        
        Args:
            limit: Maximum number of images to return
            offset: Number of images to skip
            
        Returns:
            List of dictionaries with image information
        """
        try:
            image_files = self._get_image_files()
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Apply pagination
            paginated_files = image_files[offset:offset + limit]
            
            result = []
            for image_path in paginated_files:
                try:
                    stat_info = image_path.stat()
                    result.append({
                        'filename': image_path.name,
                        'path': str(image_path),
                        'size_bytes': stat_info.st_size,
                        'size_kb': round(stat_info.st_size / 1024, 2),
                        'created_timestamp': int(stat_info.st_mtime),
                        'created_datetime': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        'age_days': round((time.time() - stat_info.st_mtime) / (24 * 60 * 60), 1)
                    })
                except Exception as e:
                    self.logger.error(f"Error getting info for {image_path}: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting image list: {e}", exc_info=True)
            return []

