import os
import time
import threading
import signal
import bcrypt
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv, set_key
from flask import Flask, render_template_string, send_from_directory, request, redirect, url_for, session, jsonify, flash
from gpiozero import Button
from rtsp_capture import grab_jpeg
from storage import (init_db, add_image, list_recent, delete_older_than, 
                     get_storage_stats, get_images_by_date, get_images_by_date_count, get_date_list, get_pending_batch)
from uploader import Uploader
from health_monitor import HealthMonitor

# Load environment
load_dotenv(".env" if os.path.exists(".env") else "config.example.env")

# GPIO Configuration
BTN1_GPIO = int(os.getenv("BTN1_GPIO", "18"))
BTN2_GPIO = int(os.getenv("BTN2_GPIO", "19"))

# Camera Configuration
CAM1_RTSP = os.getenv("CAM1_RTSP", "")
CAM2_RTSP = os.getenv("CAM2_RTSP", "")
CAM1_ENABLED = os.getenv("CAM1_ENABLED", "true").lower() == "true"
CAM2_ENABLED = os.getenv("CAM2_ENABLED", "true").lower() == "true"

# Storage
MEDIA_DIR = os.getenv("MEDIA_DIR", os.path.expanduser("~/camcap/images"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "120"))

# Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "8080"))
FLASK_DEBUG = bool(int(os.getenv("FLASK_DEBUG", "0")))

# Authentication
WEB_AUTH_ENABLED = os.getenv("WEB_AUTH_ENABLED", "true").lower() == "true"
WEB_PASSWORD_HASH = os.getenv("WEB_PASSWORD_HASH", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")

# Upload
UPLOAD_MODE = os.getenv("UPLOAD_MODE", "POST").upper()
UPLOAD_ENDPOINT = os.getenv("UPLOAD_ENDPOINT", "")
UPLOAD_AUTH_BEARER = os.getenv("UPLOAD_AUTH_BEARER", "")
UPLOAD_FIELD_NAME = os.getenv("UPLOAD_FIELD_NAME", "file")
UPLOAD_ENABLED = os.getenv("UPLOAD_ENABLED", "true").lower() == "true"

# Initialize
os.makedirs(MEDIA_DIR, exist_ok=True)
init_db()

app = Flask(__name__, static_folder=None)
app.secret_key = SECRET_KEY

# Global services
health_monitor = HealthMonitor()
uploader = None
gpio_triggers = {'r1': 0, 'r2': 0}
gpio_trigger_lock = threading.Lock()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not WEB_AUTH_ENABLED:
            return f(*args, **kwargs)
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def verify_password(password: str) -> bool:
    """Verify password against stored hash."""
    if not WEB_PASSWORD_HASH:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), WEB_PASSWORD_HASH.encode('utf-8'))
    except:
        return False

# Helper functions
def epoch_now() -> int:
    return int(time.time())

def filename_for(source: str, ts: int) -> str:
    return os.path.join(MEDIA_DIR, f"{source}_{ts}.jpg")

def is_camera_enabled(source: str) -> bool:
    """Dynamically check if camera is enabled."""
    load_dotenv()
    if source == "r1":
        return os.getenv("CAM1_ENABLED", "true").lower() == "true"
    elif source == "r2":
        return os.getenv("CAM2_ENABLED", "true").lower() == "true"
    return False

def get_rtsp_url(source: str) -> str:
    """Dynamically get RTSP URL from env."""
    load_dotenv()
    if source == "r1":
        return os.getenv("CAM1_RTSP", "")
    elif source == "r2":
        return os.getenv("CAM2_RTSP", "")
    return ""

# Capture function
def snap(source: str, rtsp_url: str):
    ts = epoch_now()
    out_path = filename_for(source, ts)
    
    if not is_camera_enabled(source):
        print(f"[SNAP] {source} is disabled, skipping")
        return
    
    ok = grab_jpeg(rtsp_url, out_path)
    if ok:
        add_image(out_path, source, ts)
        print(f"[SNAP] ✓ {source} -> {out_path}")
    else:
        print(f"[SNAP] ✗ {source} failed")

# GPIO Button callbacks
def btn1_pressed():
    print(f"[GPIO] 🔔 BUTTON 1 PRESSED - Capturing r1...")
    with gpio_trigger_lock:
        gpio_triggers['r1'] += 1
    rtsp = get_rtsp_url("r1")
    if rtsp and is_camera_enabled("r1"):
        snap("r1", rtsp)

def btn2_pressed():
    print(f"[GPIO] 🔔 BUTTON 2 PRESSED - Capturing r2...")
    with gpio_trigger_lock:
        gpio_triggers['r2'] += 1
    rtsp = get_rtsp_url("r2")
    if rtsp and is_camera_enabled("r2"):
        snap("r2", rtsp)

# Setup GPIO buttons
try:
    btn1 = Button(BTN1_GPIO, pull_up=True, bounce_time=0.3)
    btn2 = Button(BTN2_GPIO, pull_up=True, bounce_time=0.3)
    btn1.when_pressed = btn1_pressed
    btn2.when_pressed = btn2_pressed
    print(f"[GPIO] ✓ Buttons configured: GPIO {BTN1_GPIO} (r1), GPIO {BTN2_GPIO} (r2)")
except Exception as e:
    print(f"[GPIO] ⚠ Failed to initialize buttons: {e}")
    btn1 = btn2 = None

# Initialize uploader
def simple_presigner(filename: str):
    return None

uploader = Uploader(
    mode=UPLOAD_MODE,
    endpoint=UPLOAD_ENDPOINT if UPLOAD_ENABLED else None,
    bearer_token=UPLOAD_AUTH_BEARER or None,
    field_name=UPLOAD_FIELD_NAME,
    presigner=simple_presigner if UPLOAD_MODE == "PUT" else None,
    batch_size=5
)

def uploader_thread():
    uploader.run_forever()

th = threading.Thread(target=uploader_thread, daemon=True)
th.start()

# Cleanup task
def cleanup_thread():
    while True:
        cutoff = epoch_now() - RETENTION_DAYS * 24 * 3600
        delete_older_than(cutoff)
        time.sleep(24 * 3600)

ct = threading.Thread(target=cleanup_thread, daemon=True)
ct.start()

# Health monitoring task
def health_monitor_thread():
    while True:
        health_monitor.update_camera_health("r1", get_rtsp_url("r1"))
        health_monitor.update_camera_health("r2", get_rtsp_url("r2"))
        health_monitor.update_system_stats()
        time.sleep(60)

ht = threading.Thread(target=health_monitor_thread, daemon=True)
ht.start()

# ==== FLASK ROUTES ====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not WEB_AUTH_ENABLED:
        return redirect(url_for('index'))
    
    if 'logged_in' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if verify_password(password):
            session['logged_in'] = True
            session.permanent = True
            return redirect(request.args.get('next') or url_for('index'))
        else:
            flash('Invalid password', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.get("/images/<path:filename>")
@login_required
def image_raw(filename):
    return send_from_directory(MEDIA_DIR, filename)

# API Endpoints
@app.get("/api/status")
@login_required
def api_status():
    """Get system status."""
    stats = get_storage_stats()
    upload_stats = uploader.get_stats()
    
    # Get pending count
    pending_upload = get_pending_batch(100)
    
    return jsonify({
        'cameras': {
            'r1': {'enabled': is_camera_enabled('r1'), 'rtsp_configured': bool(get_rtsp_url('r1'))},
            'r2': {'enabled': is_camera_enabled('r2'), 'rtsp_configured': bool(get_rtsp_url('r2'))}
        },
        'storage': stats,
        'upload': {
            **upload_stats,
            'pending_count': len(pending_upload),
            'enabled': UPLOAD_ENABLED
        },
        'gpio_triggers': gpio_triggers.copy()
    })

@app.get("/api/health")
@login_required
def api_health():
    """Get camera and system health."""
    return jsonify(health_monitor.get_all_status())

@app.get("/api/images/recent")
@login_required
def api_images_recent():
    """Get recent images."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    source_filter = request.args.get('source', '')
    
    offset = (page - 1) * per_page
    
    all_images = list_recent(limit=1000, offset=0)
    
    # Filter by source if specified
    if source_filter:
        all_images = [img for img in all_images if img['source'] == source_filter]
    
    total = len(all_images)
    paginated = all_images[offset:offset + per_page]
    
    items = []
    for r in paginated:
        items.append({
            **r,
            "basename": os.path.basename(r["filename"]),
            "dt": datetime.fromtimestamp(r["epoch"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return jsonify({
        'images': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@app.get("/api/images/by-date")
@login_required
def api_images_by_date():
    """Get images for a specific date."""
    date_str = request.args.get('date')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    source_filter = request.args.get('source', '')
    
    if not date_str:
        return jsonify({'error': 'Date required'}), 400
    
    offset = (page - 1) * per_page
    images = get_images_by_date(date_str, source_filter or None, per_page, offset)
    total = get_images_by_date_count(date_str, source_filter or None)
    
    items = []
    for r in images:
        items.append({
            **r,
            "basename": os.path.basename(r["filename"]),
            "dt": datetime.fromtimestamp(r["epoch"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return jsonify({
        'date': date_str,
        'images': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@app.get("/api/dates")
@login_required
def api_dates():
    """Get list of dates that have images."""
    return jsonify({'dates': get_date_list()})

@app.get("/api/config")
@login_required
def api_get_config():
    """Get current configuration."""
    load_dotenv()
    return jsonify({
        'cameras': {
            'r1': {
                'enabled': is_camera_enabled('r1'),
                'rtsp_url': os.getenv('CAM1_RTSP', ''),
                'ip': os.getenv('CAM1_IP', ''),
                'username': os.getenv('CAM_USERNAME', 'admin')
            },
            'r2': {
                'enabled': is_camera_enabled('r2'),
                'rtsp_url': os.getenv('CAM2_RTSP', ''),
                'ip': os.getenv('CAM2_IP', ''),
                'username': os.getenv('CAM_USERNAME', 'admin')
            }
        },
        'upload': {
            'enabled': UPLOAD_ENABLED,
            'endpoint': os.getenv('UPLOAD_ENDPOINT', '')
        }
    })

@app.post("/api/config")
@login_required
def api_update_config():
    """Update configuration."""
    data = request.get_json()
    env_file = '.env' if os.path.exists('.env') else 'config.example.env'
    
    try:
        if 'cameras' in data:
            if 'r1' in data['cameras']:
                if 'enabled' in data['cameras']['r1']:
                    set_key(env_file, 'CAM1_ENABLED', str(data['cameras']['r1']['enabled']).lower())
                if 'rtsp_url' in data['cameras']['r1']:
                    set_key(env_file, 'CAM1_RTSP', data['cameras']['r1']['rtsp_url'])
                if 'ip' in data['cameras']['r1']:
                    set_key(env_file, 'CAM1_IP', data['cameras']['r1']['ip'])
            
            if 'r2' in data['cameras']:
                if 'enabled' in data['cameras']['r2']:
                    set_key(env_file, 'CAM2_ENABLED', str(data['cameras']['r2']['enabled']).lower())
                if 'rtsp_url' in data['cameras']['r2']:
                    set_key(env_file, 'CAM2_RTSP', data['cameras']['r2']['rtsp_url'])
                if 'ip' in data['cameras']['r2']:
                    set_key(env_file, 'CAM2_IP', data['cameras']['r2']['ip'])
            
            if 'username' in data['cameras']:
                set_key(env_file, 'CAM_USERNAME', data['cameras']['username'])
            if 'password' in data['cameras'] and data['cameras']['password']:
                set_key(env_file, 'CAM_PASSWORD', data['cameras']['password'])
        
        if 'upload' in data:
            if 'enabled' in data['upload']:
                set_key(env_file, 'UPLOAD_ENABLED', str(data['upload']['enabled']).lower())
            if 'endpoint' in data['upload']:
                set_key(env_file, 'UPLOAD_ENDPOINT', data['upload']['endpoint'])
        
        load_dotenv(override=True)
        return jsonify({'success': True, 'message': 'Configuration updated'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post("/snap")
@login_required
def snap_manual():
    """Manual capture."""
    which = request.form.get("which", "r1")
    rtsp = get_rtsp_url(which)
    if rtsp and is_camera_enabled(which):
        snap(which, rtsp)
    return redirect(url_for("index"))

@app.post("/cleanup")
@login_required
def cleanup_now():
    """Manual cleanup."""
    cutoff = epoch_now() - RETENTION_DAYS * 24 * 3600
    delete_older_than(cutoff)
    return redirect(url_for("index"))

# Signal handling
def handle_signal(signum, frame):
    if uploader:
        uploader.stop()
    os._exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# ==== TEMPLATES ====

LOGIN_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login - CamCap</title>
<style>
body { font-family: system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
.login-box { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); width: 100%; max-width: 400px; }
.login-box h1 { margin: 0 0 20px 0; text-align: center; }
input[type="password"] { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; margin-bottom: 15px; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
button:hover { background: #5568d3; }
.error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
</style>
</head>
<body>
<div class="login-box">
<h1>🔒 CamCap Login</h1>
{% with messages = get_flashed_messages() %}
  {% if messages %}<div class="error">{{ messages[0] }}</div>{% endif %}
{% endwith %}
<form method="POST">
<input type="password" name="password" placeholder="Password" required autofocus>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CamCap Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
.container { max-width: 1400px; margin: 0 auto; }
.header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.tabs { background: white; padding: 10px; border-radius: 10px; margin-bottom: 20px; display: flex; gap: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.tab-btn { flex: 1; padding: 12px; background: #f5f5f5; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.3s; }
.tab-btn.active { background: #667eea; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
.card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.card h3 { margin-bottom: 15px; color: #333; }
.stat-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #666; }
.stat-value { font-weight: bold; color: #333; }
.btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; margin: 5px; }
.btn:hover { background: #5568d3; }
.btn-danger { background: #f44336; }
.btn-danger:hover { background: #da190b; }
.btn-success { background: #4CAF50; }
.btn-success:hover { background: #45a049; }
.online { color: #4CAF50; font-weight: bold; }
.offline { color: #f44336; font-weight: bold; }
.image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.image-card { border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: white; }
.image-card img { width: 100%; height: auto; border-radius: 8px; cursor: pointer; }
.image-meta { font-size: 12px; color: #555; margin-top: 6px; }
input, select { padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; }
.config-item { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.config-item label { display: block; font-weight: 600; margin-bottom: 5px; color: #555; }
.config-item input[type="text"] { width: 100%; margin-bottom: 10px; }
.config-item input[type="checkbox"] { width: 20px; height: 20px; margin-right: 10px; }
.trigger-indicator { background: #f5f5f5; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; gap: 15px; }
.trigger-light { width: 30px; height: 30px; border-radius: 50%; background: #ddd; }
.trigger-light.active { background: #4CAF50; box-shadow: 0 0 20px #4CAF50; animation: pulse 1s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.pagination { display: flex; gap: 10px; justify-content: center; margin-top: 20px; }
.pagination button { padding: 8px 16px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📷 CamCap Dashboard</h1>
    <div>
      <a href="/logout" class="btn btn-danger">🚪 Logout</a>
    </div>
  </div>
  
  <div class="tabs">
    <button class="tab-btn active" onclick="showTab('dashboard')">🏠 Dashboard</button>
    <button class="tab-btn" onclick="showTab('config')">⚙️ Configuration</button>
    <button class="tab-btn" onclick="showTab('storage')">💾 Storage</button>
    <button class="tab-btn" onclick="showTab('images')">📅 Images</button>
  </div>
  
  <!-- Dashboard Tab -->
  <div id="dashboard-tab" class="tab-content active">
    <div class="grid">
      <div class="card">
        <h3>📹 Camera Health</h3>
        <div id="camera-health">Loading...</div>
      </div>
      
      <div class="card">
        <h3>🌡️ System Monitor</h3>
        <div id="system-monitor">Loading...</div>
      </div>
      
      <div class="card">
        <h3>☁️ Upload Status</h3>
        <div id="upload-status">Loading...</div>
      </div>
      
      <div class="card">
        <h3>⚡ GPIO Triggers</h3>
        <div id="gpio-triggers">
          <div class="trigger-indicator" id="trigger-r1">
            <span class="trigger-light"></span>
            <div><strong>r1 (Entry)</strong><br><small>Count: <span id="count-r1">0</span></small></div>
          </div>
          <div class="trigger-indicator" id="trigger-r2">
            <span class="trigger-light"></span>
            <div><strong>r2 (Exit)</strong><br><small>Count: <span id="count-r2">0</span></small></div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
      <h3>🖼️ Recent Images (Last 10)</h3>
      <div id="recent-images" class="image-grid">Loading...</div>
    </div>
  </div>
  
  <!-- Configuration Tab -->
  <div id="config-tab" class="tab-content">
    <div class="card">
      <h3>⚙️ Camera Configuration</h3>
      <div id="config-cameras">Loading...</div>
      <h3 style="margin-top: 20px;">☁️ Upload Configuration</h3>
      <div id="config-upload">Loading...</div>
      <button class="btn btn-success" style="width: 100%; margin-top: 20px;" onclick="saveConfig()">💾 Save Configuration</button>
    </div>
  </div>
  
  <!-- Storage Tab -->
  <div id="storage-tab" class="tab-content">
    <div class="card">
      <h3>💾 Storage Analysis</h3>
      <div id="storage-analysis">Loading...</div>
    </div>
  </div>
  
  <!-- Images Tab -->
  <div id="images-tab" class="tab-content">
    <div class="card">
      <h3>📅 Images by Date</h3>
      <div style="margin-bottom: 20px;">
        <input type="date" id="date-picker">
        <select id="source-filter">
          <option value="">All Cameras</option>
          <option value="r1">r1 (Entry)</option>
          <option value="r2">r2 (Exit)</option>
        </select>
        <button class="btn" onclick="loadImagesByDate(1)">Load</button>
      </div>
      <div id="date-images" class="image-grid">Select a date to view images</div>
      <div class="pagination" id="date-pagination"></div>
    </div>
  </div>
</div>

<script>
let currentPage = 1;

function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(name + '-tab').classList.add('active');
  event.target.classList.add('active');
  
  if (name === 'config') loadConfig();
  else if (name === 'storage') loadStorage();
  else if (name === 'images') { document.getElementById('date-picker').value = new Date().toISOString().split('T')[0]; }
}

async function updateDashboard() {
  try {
    const [status, health] = await Promise.all([
      fetch('/api/status').then(r => r.json()),
      fetch('/api/health').then(r => r.json())
    ]);
    
    // Camera health
    let healthHTML = '';
    for (const [source, data] of Object.entries(health.camera_health || {})) {
      const isOnline = data.online;
      healthHTML += `<div class="stat-row">
        <span class="stat-label">${source.toUpperCase()}</span>
        <span class="stat-value ${isOnline ? 'online' : 'offline'}">${isOnline ? '🟢 ONLINE' : '🔴 OFFLINE'}</span>
      </div>`;
    }
    document.getElementById('camera-health').innerHTML = healthHTML;
    
    // System monitor
    const temp = health.system_stats?.cpu_temp;
    document.getElementById('system-monitor').innerHTML = `<div class="stat-row">
      <span class="stat-label">CPU Temp</span>
      <span class="stat-value">${temp ? temp + '°C' : 'N/A'}</span>
    </div>`;
    
    // Upload status
    const upload = status.upload;
    document.getElementById('upload-status').innerHTML = `
      <div class="stat-row">
        <span class="stat-label">Status</span>
        <span class="stat-value ${upload.offline_mode ? 'offline' : 'online'}">${upload.offline_mode ? '🔴 OFFLINE' : '🟢 ONLINE'}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Uploaded</span>
        <span class="stat-value">${upload.total_uploaded || 0}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Pending</span>
        <span class="stat-value">${upload.pending_count || 0}</span>
      </div>`;
    
    // GPIO triggers
    if (status.gpio_triggers) {
      document.getElementById('count-r1').textContent = status.gpio_triggers.r1 || 0;
      document.getElementById('count-r2').textContent = status.gpio_triggers.r2 || 0;
    }
    
    // Recent images
    const recent = await fetch('/api/images/recent?per_page=10').then(r => r.json());
    let imagesHTML = '';
    for (const img of recent.images) {
      imagesHTML += `<div class="image-card">
        <img src="/images/${img.basename}" onclick="window.open('/images/${img.basename}')" loading="lazy">
        <div class="image-meta"><b>${img.source}</b> • ${img.dt}</div>
      </div>`;
    }
    document.getElementById('recent-images').innerHTML = imagesHTML || 'No images yet';
    
  } catch (e) {
    console.error('Update error:', e);
  }
}

async function loadConfig() {
  try {
    const config = await fetch('/api/config').then(r => r.json());
    
    let camHTML = '';
    for (const [source, cam] of Object.entries(config.cameras)) {
      camHTML += `<div class="config-item">
        <label>
          <input type="checkbox" id="${source}-enabled" ${cam.enabled ? 'checked' : ''}>
          <strong>${source.toUpperCase()} ${source === 'r1' ? '(Entry)' : '(Exit)'}</strong>
        </label>
        <label>IP Address</label>
        <input type="text" id="${source}-ip" value="${cam.ip}" placeholder="192.168.1.20X">
        <label>RTSP URL</label>
        <input type="text" id="${source}-rtsp" value="${cam.rtsp_url}" placeholder="rtsp://user:pass@ip:port/stream">
      </div>`;
    }
    document.getElementById('config-cameras').innerHTML = camHTML;
    
    document.getElementById('config-upload').innerHTML = `<div class="config-item">
      <label><input type="checkbox" id="upload-enabled" ${config.upload.enabled ? 'checked' : ''}> <strong>Enable S3 Upload</strong></label>
      <label>S3 Endpoint URL</label>
      <input type="text" id="upload-endpoint" value="${config.upload.endpoint}">
    </div>`;
    
  } catch (e) {
    console.error('Load config error:', e);
  }
}

async function saveConfig() {
  try {
    const config = {
      cameras: {
        r1: {
          enabled: document.getElementById('r1-enabled').checked,
          ip: document.getElementById('r1-ip').value,
          rtsp_url: document.getElementById('r1-rtsp').value
        },
        r2: {
          enabled: document.getElementById('r2-enabled').checked,
          ip: document.getElementById('r2-ip').value,
          rtsp_url: document.getElementById('r2-rtsp').value
        }
      },
      upload: {
        enabled: document.getElementById('upload-enabled').checked,
        endpoint: document.getElementById('upload-endpoint').value
      }
    };
    
    const resp = await fetch('/api/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(config)
    });
    
    const result = await resp.json();
    alert(result.success ? '✓ Configuration saved!' : 'Error: ' + result.error);
    if (result.success) updateDashboard();
    
  } catch (e) {
    alert('Error saving: ' + e.message);
  }
}

async function loadStorage() {
  try {
    const stats = await fetch('/api/status').then(r => r.json());
    const storage = stats.storage;
    
    let html = `<div class="stat-row">
      <span class="stat-label">Total Images</span>
      <span class="stat-value">${storage.total || 0}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Uploaded</span>
      <span class="stat-value">${storage.uploaded || 0}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Pending Upload</span>
      <span class="stat-value">${storage.pending || 0}</span>
    </div>
    <h3 style="margin: 20px 0 10px 0;">By Camera</h3>`;
    
    for (const [source, count] of Object.entries(storage.by_source || {})) {
      html += `<div class="stat-row">
        <span class="stat-label">${source.toUpperCase()}</span>
        <span class="stat-value">${count}</span>
      </div>`;
    }
    
    document.getElementById('storage-analysis').innerHTML = html;
    
  } catch (e) {
    console.error('Load storage error:', e);
  }
}

async function loadImagesByDate(page = 1) {
  const date = document.getElementById('date-picker').value;
  const source = document.getElementById('source-filter').value;
  
  if (!date) {
    document.getElementById('date-images').innerHTML = 'Please select a date';
    return;
  }
  
  try {
    const data = await fetch(`/api/images/by-date?date=${date}&page=${page}&per_page=50&source=${source}`).then(r => r.json());
    
    if (!data.images || data.images.length === 0) {
      document.getElementById('date-images').innerHTML = 'No images found for this date';
      document.getElementById('date-pagination').innerHTML = '';
      return;
    }
    
    let html = '';
    for (const img of data.images) {
      html += `<div class="image-card">
        <img src="/images/${img.basename}" onclick="window.open('/images/${img.basename}')" loading="lazy">
        <div class="image-meta"><b>${img.source}</b> • ${img.dt}</div>
      </div>`;
    }
    document.getElementById('date-images').innerHTML = html;
    
    // Pagination
    const p = data.pagination;
    let pag = '';
    if (p.pages > 1) {
      pag = `<button onclick="loadImagesByDate(1)" ${page === 1 ? 'disabled' : ''}>First</button>
        <button onclick="loadImagesByDate(${page - 1})" ${page === 1 ? 'disabled' : ''}>Prev</button>
        <span style="padding: 8px;">Page ${page}/${p.pages}</span>
        <button onclick="loadImagesByDate(${page + 1})" ${page === p.pages ? 'disabled' : ''}>Next</button>
        <button onclick="loadImagesByDate(${p.pages})" ${page === p.pages ? 'disabled' : ''}>Last</button>`;
    }
    document.getElementById('date-pagination').innerHTML = pag;
    
  } catch (e) {
    console.error('Load images error:', e);
    document.getElementById('date-images').innerHTML = 'Error loading images';
  }
}

// Initialize
updateDashboard();
setInterval(updateDashboard, 10000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print(f"[APP] Starting CamCap on {FLASK_HOST}:{FLASK_PORT}")
    print(f"[APP] Authentication: {'ENABLED' if WEB_AUTH_ENABLED else 'DISABLED'}")
    print(f"[APP] Upload: {'ENABLED' if UPLOAD_ENABLED else 'DISABLED'}")
    print(f"[APP] Cameras: r1={'ENABLED' if is_camera_enabled('r1') else 'DISABLED'}, r2={'ENABLED' if is_camera_enabled('r2') else 'DISABLED'}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
