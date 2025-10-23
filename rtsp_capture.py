import subprocess
import os

def grab_jpeg(rtsp_url: str, out_path: str, timeout_sec: int = 10) -> bool:
    """Use ffmpeg to pull a single frame from RTSP and save as JPEG.
    Returns True on success."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmpfile = out_path + ".tmp.jpg"

    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-y",
        "-i", rtsp_url,
        "-frames:v", "1",
        "-q:v", "2",
        tmpfile
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_sec, check=True)
        os.replace(tmpfile, out_path)
        return True
    except Exception:
        try:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)
        except Exception:
            pass
        return False
