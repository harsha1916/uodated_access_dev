import os
import time
import requests
from typing import Optional, Callable
from storage import get_pending_batch, mark_uploaded, mark_failed

class Uploader:
    """Background uploader for queued images.
    Modes:
      - POST: multipart upload to a single endpoint
      - PUT: presigned PUT per file via presigner() callback
    """
    def __init__(
        self,
        mode: str,
        endpoint: Optional[str] = None,
        bearer_token: Optional[str] = None,
        field_name: str = "file",
        presigner: Optional[Callable[[str], Optional[str]]] = None,
        batch_size: int = 5,
        sleep_ok: float = 5.0,
        sleep_fail: float = 15.0,
        timeout: int = 20
    ):
        self.mode = (mode or "POST").upper()
        self.endpoint = endpoint
        self.bearer_token = bearer_token
        self.field_name = field_name
        self.presigner = presigner
        self.batch_size = batch_size
        self.sleep_ok = sleep_ok
        self.sleep_fail = sleep_fail
        self.timeout = timeout
        self._stop = False

    def stop(self):
        self._stop = True

    def _headers(self):
        h = {"User-Agent": "camcap-uploader/1.0"}
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        return h

    def _upload_post(self, filepath: str) -> requests.Response:
        with open(filepath, "rb") as f:
            files = {self.field_name: (os.path.basename(filepath), f, "image/jpeg")}
            return requests.post(self.endpoint, files=files, headers=self._headers(), timeout=self.timeout)

    def _upload_put(self, url: str, filepath: str) -> requests.Response:
        with open(filepath, "rb") as f:
            data = f.read()
        return requests.put(url, data=data, headers={"Content-Type": "image/jpeg", **self._headers()}, timeout=self.timeout)

    def run_forever(self):
        while not self._stop:
            items = get_pending_batch(self.batch_size)
            if not items:
                time.sleep(self.sleep_ok)
                continue

            had_error = False
            for it in items:
                fid = it["id"]
                fp = it["filename"]
                try:
                    if not os.path.exists(fp):
                        mark_uploaded(fid)  # avoid stuck queue
                        continue

                    if self.mode == "POST":
                        if not self.endpoint:
                            raise RuntimeError("POST mode requires UPLOAD_ENDPOINT")
                        resp = self._upload_post(fp)
                        if 200 <= resp.status_code < 300:
                            mark_uploaded(fid)
                        else:
                            had_error = True
                            mark_failed(fid, f"HTTP {resp.status_code}: {resp.text[:200]}")
                    elif self.mode == "PUT":
                        if self.presigner is None:
                            raise RuntimeError("PUT mode requires presigner(filename) -> presigned_url")
                        presigned_url = self.presigner(os.path.basename(fp))
                        if not presigned_url:
                            had_error = True
                            mark_failed(fid, "presigner returned no URL")
                            continue
                        resp = self._upload_put(presigned_url, fp)
                        if 200 <= resp.status_code < 300:
                            mark_uploaded(fid)
                        else:
                            had_error = True
                            mark_failed(fid, f"PUT {resp.status_code}: {resp.text[:200]}")
                    else:
                        had_error = True
                        mark_failed(fid, f"Unknown mode {self.mode}")

                except requests.RequestException as re:
                    had_error = True
                    mark_failed(fid, f"net:{type(re).__name__}:{str(re)[:160]}")
                except Exception as e:
                    had_error = True
                    mark_failed(fid, f"err:{type(e).__name__}:{str(e)[:160]}")

            time.sleep(self.sleep_fail if had_error else self.sleep_ok)
