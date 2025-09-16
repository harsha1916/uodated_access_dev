import os
import time
import requests
import logging
from typing import Optional
from config import S3_API_URL, MAX_RETRIES, RETRY_DELAY, HTTP_TIMEOUT

class ImageUploader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def upload(self, filepath: str) -> Optional[str]:
        """Upload image file to S3-compatible API."""
        if not os.path.exists(filepath):
            self.logger.error(f"File does not exist: {filepath}")
            return None
            
        if not os.path.isfile(filepath):
            self.logger.error(f"Path is not a file: {filepath}")
            return None
            
        # Check file size (limit to 10MB)
        file_size = os.path.getsize(filepath)
        if file_size > 10 * 1024 * 1024:  # 10MB
            self.logger.error(f"File too large: {filepath} ({file_size} bytes)")
            return None
            
        attempts = 0
        while attempts < MAX_RETRIES:
            try:
                with open(filepath, "rb") as image_file:
                    files = {
                        "singleFile": (os.path.basename(filepath), image_file, "image/jpeg")
                    }
                    response = requests.post(S3_API_URL, files=files, timeout=HTTP_TIMEOUT)

                if response.status_code == 200:
                    self.logger.info(f"Successfully uploaded: {filepath}")
                    # Try robust parsing of common response shapes
                    try:
                        response_json = response.json()
                    except ValueError:
                        response_json = None

                    location_candidates = []
                    if isinstance(response_json, dict):
                        # Common keys: Location, location, url, data.location
                        location_candidates.append(response_json.get("Location"))
                        location_candidates.append(response_json.get("location"))
                        location_candidates.append(response_json.get("url"))
                        data = response_json.get("data") if isinstance(response_json.get("data"), dict) else None
                        if isinstance(data, dict):
                            location_candidates.append(data.get("Location"))
                            location_candidates.append(data.get("location"))
                            location_candidates.append(data.get("url"))

                    location = next((loc for loc in location_candidates if isinstance(loc, str) and len(loc) > 0), None)

                    if location:
                        self.logger.info(f"S3 Response OK: {response_json}")
                        return location
                    else:
                        self.logger.error(f"No usable location in response: {response_json if response_json is not None else response.text}")
                else:
                    self.logger.error(f"Upload failed {filepath}: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Upload error for {filepath}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error during upload of {filepath}: {e}")

            attempts += 1
            if attempts < MAX_RETRIES:
                # Exponential backoff with cap and jitter
                backoff = min(RETRY_DELAY * (2 ** attempts), 60)
                jitter = min(3, backoff / 3)
                wait = backoff + (jitter if attempts % 2 == 0 else -jitter)
                self.logger.info(f"Retrying upload in {int(wait)} seconds... (attempt {attempts + 1}/{MAX_RETRIES})")
                time.sleep(max(1, int(wait)))

        self.logger.error(f"Giving up on {filepath} after {MAX_RETRIES} attempts.")
        return None
