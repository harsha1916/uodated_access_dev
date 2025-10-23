import os
import time
import threading
import signal
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template_string, send_from_directory, request, redirect, url_for
from gpiozero import Button
from rtsp_capture import grab_jpeg
from storage import init_db, add_image, list_recent, delete_older_than
from uploader import Uploader

load_dotenv(".env" if os.path.exists(".env") else "config.example.env")

BTN1_GPIO = int(os.getenv("BTN1_GPIO", "18"))
BTN2_GPIO = int(os.getenv("BTN2_GPIO", "23"))
CAM1_RTSP = os.getenv("CAM1_RTSP", "")
CAM2_RTSP = os.getenv("CAM2_RTSP", "")
MEDIA_DIR  = os.getenv("MEDIA_DIR", os.path.expanduser("~/camcap/images"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "120"))

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "8080"))
FLASK_DEBUG = bool(int(os.getenv("FLASK_DEBUG", "0")))

UPLOAD_MODE = os.getenv("UPLOAD_MODE", "POST").upper()
UPLOAD_ENDPOINT = os.getenv("UPLOAD_ENDPOINT", "")
UPLOAD_AUTH_BEARER = os.getenv("UPLOAD_AUTH_BEARER", "")
UPLOAD_FIELD_NAME = os.getenv("UPLOAD_FIELD_NAME", "file")

os.makedirs(MEDIA_DIR, exist_ok=True)
init_db()

app = Flask(__name__, static_folder=None)

GALLERY_TMPL = """<!doctype html>
<html>
<head>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>CamCap</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 10px; }
    img { width: 100%; height: auto; border-radius: 8px; display:block; }
    .meta { font-size: 12px; color:#555; margin-top:6px; }
    .topbar { display:flex; gap:8px; align-items:center; margin-bottom:12px; }
    .topbar form { display:inline-flex; gap:6px; align-items:center; }
    button { padding:6px 10px; border:1px solid #aaa; background:#f7f7f7; border-radius:6px; cursor:pointer; }
  </style>
</head>
<body>
  <div class="topbar">
    <h2 style="margin:0;">📷 CamCap Gallery</h2>
    <form method="post" action="/snap">
      <button name="which" value="r1">Snap R1</button>
      <button name="which" value="r2">Snap R2</button>
    </form>
    <form method="post" action="/cleanup">
      <button>Run Cleanup</button>
    </form>
  </div>
  <div class="grid">
    {% for it in items %}
    <div class="card">
      <a href="{{ url_for('image_raw', filename=it['basename']) }}" target="_blank">
        <img src="{{ url_for('image_raw', filename=it['basename']) }}" loading="lazy"/>
      </a>
      <div class="meta">
        <div><b>{{ it['source'] }}</b> • {{ it['dt'] }}</div>
        <div>{{ it['basename'] }}</div>
      </div>
    </div>
    {% endfor %}
  </div>
</body>
</html>
"""

def epoch_now() -> int:
    return int(time.time())

def filename_for(source: str, ts: int) -> str:
    return os.path.join(MEDIA_DIR, f"{source}_{ts}.jpg")

# Button setup (pull-up assumed; button shorts to GND)
btn1 = Button(BTN1_GPIO, pull_up=True, bounce_time=0.1)
btn2 = Button(BTN2_GPIO, pull_up=True, bounce_time=0.1)

def snap(source: str, rtsp_url: str):
    ts = epoch_now()
    out_path = filename_for(source, ts)
    ok = grab_jpeg(rtsp_url, out_path)
    if ok:
        add_image(out_path, source, ts)
        print(f"[SNAP] {source} -> {out_path}")
    else:
        print(f"[SNAP][FAIL] {source}")

def btn1_pressed():
    if CAM1_RTSP:
        snap("r1", CAM1_RTSP)

def btn2_pressed():
    if CAM2_RTSP:
        snap("r2", CAM2_RTSP)

btn1.when_pressed = btn1_pressed
btn2.when_pressed = btn2_pressed

# --- Uploader ---
def simple_presigner(filename: str):
    """Replace to call your API and return a presigned PUT URL per filename."""
    return None  # not used by default (POST mode)

uploader = Uploader(
    mode=UPLOAD_MODE,
    endpoint=UPLOAD_ENDPOINT,
    bearer_token=UPLOAD_AUTH_BEARER or None,
    field_name=UPLOAD_FIELD_NAME,
    presigner=simple_presigner if UPLOAD_MODE == "PUT" else None,
    batch_size=5
)

def uploader_thread():
    uploader.run_forever()

th = threading.Thread(target=uploader_thread, daemon=True)
th.start()

# --- Cleanup task (daily) ---
def cleanup_thread():
    while True:
        cutoff = epoch_now() - RETENTION_DAYS * 24 * 3600
        delete_older_than(cutoff)
        time.sleep(24 * 3600)

ct = threading.Thread(target=cleanup_thread, daemon=True)
ct.start()

# --- Flask routes ---
@app.get("/")
def index():
    items = []
    for r in list_recent(limit=200):
        items.append({
            **r,
            "basename": os.path.basename(r["filename"]),
            "dt": datetime.fromtimestamp(r["epoch"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    return render_template_string(GALLERY_TMPL, items=items)

@app.get("/images/<path:filename>")
def image_raw(filename):
    return send_from_directory(MEDIA_DIR, filename)

@app.post("/snap")
def snap_manual():
    which = request.form.get("which", "r1")
    if which == "r2":
        snap("r2", CAM2_RTSP)
    else:
        snap("r1", CAM1_RTSP)
    return redirect(url_for("index"))

@app.post("/cleanup")
def cleanup_now():
    cutoff = epoch_now() - RETENTION_DAYS * 24 * 3600
    delete_older_than(cutoff)
    return redirect(url_for("index"))

def handle_signal(signum, frame):
    uploader.stop()
    os._exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

if __name__ == "__main__":
    # run with sudo if GPIO access requires it
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
