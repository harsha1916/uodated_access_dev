import os
import json
import time
import base64
import logging
import shutil
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
import io

class JSONUploader:
    """
    Upload images as base64-encoded JSON to a custom API endpoint.
    Handles offline mode by saving JSON files locally for later upload.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Create optimized session with connection pooling
        self.session = requests.Session()
        
        # Get configuration
        self.custom_url = os.getenv("JSON_UPLOAD_URL", "")
        self.timeout = int(os.getenv("JSON_UPLOAD_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("JSON_UPLOAD_RETRY", "3"))
        
        # Configure retry strategy
        # Use try/except for compatibility with different urllib3 versions
        try:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]  # urllib3 >= 1.26
            )
        except TypeError:
            # Fall back to older parameter name for urllib3 < 1.26
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["POST"]
            )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set optimized headers
        self.session.headers.update({
            'User-Agent': 'MaxPark-RFID-System/2.0-JSON',
            'Connection': 'keep-alive',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    def image_to_base64(self, image_path: str, compress: bool = True, quality: int = 75, max_width: int = 1920) -> Optional[str]:
        """
        Convert image file to base64 string with optional compression.
        
        Args:
            image_path: Path to the image file
            compress: Whether to compress the image (default: True)
            quality: JPEG quality for compression (1-100, default: 75)
            max_width: Maximum width to resize to (default: 1920px)
        
        Returns:
            Base64 encoded string or None on error
        """
        try:
            if compress:
                # Open image with PIL
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary (handles RGBA, etc.)
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # Resize if image is too large
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height), Image.LANCZOS)
                        self.logger.info(f"Resized image from {img.width}x{img.height} to {max_width}x{new_height}")
                    
                    # Compress to bytes
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=quality, optimize=True)
                    image_data = buffer.getvalue()
                    
                    # Log compression results
                    original_size = os.path.getsize(image_path)
                    compressed_size = len(image_data)
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    self.logger.info(f"Compressed image: {original_size} → {compressed_size} bytes ({compression_ratio:.1f}% reduction)")
            else:
                # No compression - read file directly
                with open(image_path, "rb") as img_file:
                    image_data = img_file.read()
            
            # Convert to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
            
        except Exception as e:
            self.logger.error(f"Error converting image to base64: {e}")
            return None
    
    def create_json_payload(
        self, 
        image_path: str, 
        card_number: str, 
        reader_id: int, 
        status: str,
        user_name: str = None,
        timestamp: int = None,
        entity_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create JSON payload with base64 image and metadata.
        
        Args:
            image_path: Path to the image file
            card_number: Card number scanned
            reader_id: Reader ID (1, 2, or 3)
            status: Access status ("Access Granted", "Access Denied", "Blocked")
            user_name: Name of the user (optional)
            timestamp: Unix timestamp (optional, defaults to current time)
            entity_id: Entity ID (optional)
        
        Returns:
            Dictionary with JSON payload or None on error
        """
        try:
            # Get compression settings from environment
            quality = int(os.getenv("JSON_IMAGE_QUALITY", "75"))
            max_width = int(os.getenv("JSON_IMAGE_MAX_WIDTH", "1920"))
            
            # Convert image to base64 with compression
            base64_image = self.image_to_base64(image_path, compress=True, quality=quality, max_width=max_width)
            if not base64_image:
                return None
            
            # Use provided timestamp or current time
            if timestamp is None:
                timestamp = int(time.time())
            
            # Create ISO format timestamp
            created_at = datetime.fromtimestamp(timestamp).isoformat()
            
            # Build JSON payload
            payload = {
                "image_base64": base64_image,
                "timestamp": timestamp,
                "card_number": str(card_number),
                "reader_id": reader_id,
                "status": status,
                "user_name": user_name if user_name else "Unknown",
                "created_at": created_at
            }
            
            # Add entity_id if provided
            if entity_id:
                payload["entity_id"] = entity_id
            
            return payload
            
        except Exception as e:
            self.logger.error(f"Error creating JSON payload: {e}")
            return None
    
    def upload(self, json_payload: Dict[str, Any]) -> bool:
        """
        Upload JSON payload to custom URL.
        
        Args:
            json_payload: Dictionary containing the JSON data
        
        Returns:
            True if upload successful, False otherwise
        """
        if not self.custom_url:
            self.logger.error("No JSON upload URL configured")
            return False
        
        try:
            response = self.session.post(
                self.custom_url,
                json=json_payload,
                timeout=self.timeout,
                stream=False
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully uploaded JSON to {self.custom_url}")
                return True
            elif response.status_code == 201:
                # 201 Created is also acceptable
                self.logger.info(f"Successfully uploaded JSON to {self.custom_url} (201 Created)")
                return True
            else:
                self.logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.warning(f"Upload timeout to {self.custom_url}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error to {self.custom_url}")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Upload error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during upload: {e}")
            return False
    
    def save_json_locally(self, json_payload: Dict[str, Any], filename: str) -> Optional[str]:
        """
        Save JSON payload to local file.
        
        Args:
            json_payload: Dictionary containing the JSON data
            filename: Base filename (without path)
        
        Returns:
            Path to saved file or None on error
        """
        try:
            # Ensure pending directory exists
            pending_dir = os.path.join("json_uploads", "pending")
            os.makedirs(pending_dir, exist_ok=True)
            
            # Create filepath
            json_filename = filename.replace('.jpg', '.json').replace('.jpeg', '.json')
            filepath = os.path.join(pending_dir, json_filename)
            
            # Save JSON file
            with open(filepath, 'w') as f:
                json.dump(json_payload, f, indent=2)
            
            self.logger.info(f"Saved JSON locally: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving JSON locally: {e}")
            return None
    
    def upload_from_file(self, json_filepath: str) -> bool:
        """
        Load JSON from file and upload it.
        Move to uploaded folder on success.
        
        Args:
            json_filepath: Path to JSON file
        
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Load JSON from file
            with open(json_filepath, 'r') as f:
                json_payload = json.load(f)
            
            # Upload
            success = self.upload(json_payload)
            
            if success:
                # Move to uploaded folder
                uploaded_dir = os.path.join("json_uploads", "uploaded")
                os.makedirs(uploaded_dir, exist_ok=True)
                
                filename = os.path.basename(json_filepath)
                uploaded_path = os.path.join(uploaded_dir, filename)
                
                shutil.move(json_filepath, uploaded_path)
                self.logger.info(f"Moved to uploaded: {uploaded_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error uploading from file {json_filepath}: {e}")
            return False

