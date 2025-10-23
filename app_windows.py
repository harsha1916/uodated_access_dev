import os
import time
import threading
import signal
import hashlib
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv, set_key
from flask import Flask, render_template_string, send_from_directory, request, redirect, url_for, session, jsonify, flash

# Try to import GPIO modules, but don't fail if they're not available (Windows compatibility)
try:
    from gpiozero import Button
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARNING] GPIO modules not available (Windows/Non-Raspberry Pi)")

try:
    from rtsp_capture import grab_jpeg
    RTSP_AVAILABLE = True
except ImportError:
    RTSP_AVAILABLE = False
    print("[WARNING] RTSP capture not available")

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
UPLOAD_FIELD_NAME = os.getenv("UPLOAD_FIELD_NAME", "singleFile")
UPLOAD_ENABLED = os.getenv("UPLOAD_ENABLED", "true").lower() == "true"

# Offline mode settings
OFFLINE_RETRY_INTERVAL = int(os.getenv("OFFLINE_RETRY_INTERVAL", "60"))
CONNECTIVITY_CHECK_INTERVAL = int(os.getenv("CONNECTIVITY_CHECK_INTERVAL", "60"))

# Initialize Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize services
init_db()
uploader = Uploader(mode=UPLOAD_MODE, endpoint=UPLOAD_ENDPOINT, bearer_token=UPLOAD_AUTH_BEARER, field_name=UPLOAD_FIELD_NAME)
health_monitor = HealthMonitor()

# GPIO state tracking
gpio_triggers = {"r1": False, "r2": False}

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
        return password == "admin123"  # Default password
    # SHA256 hash comparison
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return password_hash == WEB_PASSWORD_HASH

# Helper functions
def epoch_now() -> int:
    return int(time.time())

def is_camera_enabled(source: str) -> bool:
    """Dynamically check if camera is enabled."""
    if source == "r1":
        return os.getenv("CAM1_ENABLED", "true").lower() == "true"
    elif source == "r2":
        return os.getenv("CAM2_ENABLED", "true").lower() == "true"
    return False

def get_rtsp_url(source: str) -> str:
    """Dynamically get RTSP URL from env."""
    if source == "r1":
        return os.getenv("CAM1_RTSP", "")
    elif source == "r2":
        return os.getenv("CAM2_RTSP", "")
    return ""

def snap(source: str) -> bool:
    """Capture image from RTSP camera."""
    try:
        if not RTSP_AVAILABLE:
            print(f"[SNAP] RTSP capture not available (Windows mode)")
            return False
            
        rtsp_url = get_rtsp_url(source)
        if not rtsp_url:
            print(f"[SNAP] No RTSP URL configured for {source}")
            return False
        
        if not is_camera_enabled(source):
            print(f"[SNAP] Camera {source} is disabled")
            return False
        
        timestamp = epoch_now()
        filename = f"{source}_{timestamp}.jpg"
        filepath = os.path.join(MEDIA_DIR, filename)
        
        print(f"[SNAP] Capturing {source} from {rtsp_url}")
        success = grab_jpeg(rtsp_url, filepath)
        
        if success:
            add_image(filename, source, timestamp, uploaded=False)
            print(f"[SNAP] ✓ Captured {filename}")
            return True
        else:
            print(f"[SNAP] ✗ Failed to capture {source}")
            return False
            
    except Exception as e:
        print(f"[SNAP] Error capturing {source}: {e}")
        return False

def snap_async(source: str):
    """Capture image in background thread (non-blocking)."""
    def _snap():
        snap(source)
    
    thread = threading.Thread(target=_snap, daemon=True)
    thread.start()

# GPIO Button Handlers
def on_button_press(source: str):
    """Handle GPIO button press."""
    print(f"[GPIO] Button {source} pressed!")
    gpio_triggers[source] = True
    snap_async(source)  # Non-blocking capture

# Initialize GPIO buttons (only if GPIO is available)
if GPIO_AVAILABLE:
    try:
        if CAM1_ENABLED:
            btn1 = Button(BTN1_GPIO, pull_up=True)
            btn1.when_pressed = lambda: on_button_press("r1")
            print(f"[GPIO] Button 1 (R1) configured on pin {BTN1_GPIO}")
        
        if CAM2_ENABLED:
            btn2 = Button(BTN2_GPIO, pull_up=True)
            btn2.when_pressed = lambda: on_button_press("r2")
            print(f"[GPIO] Button 2 (R2) configured on pin {BTN2_GPIO}")
            
    except Exception as e:
        print(f"[GPIO] Error initializing buttons: {e}")
else:
    print("[GPIO] GPIO not available - running in Windows/Desktop mode")

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not WEB_AUTH_ENABLED:
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
    
    # Apply pagination
    total = len(all_images)
    images = all_images[offset:offset + per_page]
    
    return jsonify({
        'images': images,
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
    date = request.args.get('date', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    source = request.args.get('source', '')
    
    if not date:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        images, total = get_images_by_date(date, page, per_page, source)
        return jsonify({
            'images': images,
            'total': total,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get("/api/images/dates")
@login_required
def api_images_dates():
    """Get list of dates that have images."""
    try:
        dates = get_date_list()
        return jsonify({'dates': dates})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get("/api/config")
@login_required
def api_config():
    """Get current configuration."""
    return jsonify({
        'cameras': {
            'r1': {
                'enabled': is_camera_enabled('r1'),
                'rtsp_url': get_rtsp_url('r1')
            },
            'r2': {
                'enabled': is_camera_enabled('r2'),
                'rtsp_url': get_rtsp_url('r2')
            }
        },
        'upload': {
            'enabled': UPLOAD_ENABLED,
            'endpoint': UPLOAD_ENDPOINT,
            'auth_bearer': UPLOAD_AUTH_BEARER
        }
    })

@app.post("/api/config")
@login_required
def api_config_update():
    """Update configuration."""
    try:
        data = request.get_json()
        env_file = ".env" if os.path.exists(".env") else "config.example.env"
        
        if 'cameras' in data:
            cameras = data['cameras']
            
            if 'r1' in cameras:
                if 'enabled' in cameras['r1']:
                    set_key(env_file, 'CAM1_ENABLED', str(cameras['r1']['enabled']).lower())
                if 'rtsp_url' in cameras['r1']:
                    set_key(env_file, 'CAM1_RTSP', cameras['r1']['rtsp_url'])
            
            if 'r2' in cameras:
                if 'enabled' in cameras['r2']:
                    set_key(env_file, 'CAM2_ENABLED', str(cameras['r2']['enabled']).lower())
                if 'rtsp_url' in cameras['r2']:
                    set_key(env_file, 'CAM2_RTSP', cameras['r2']['rtsp_url'])
            
            if 'username' in data['cameras']:
                set_key(env_file, 'CAM_USERNAME', data['cameras']['username'])
            if 'password' in data['cameras'] and data['cameras']['password']:
                set_key(env_file, 'CAM_PASSWORD', data['cameras']['password'])
        
        if 'upload' in data:
            if 'enabled' in data['upload']:
                set_key(env_file, 'UPLOAD_ENABLED', str(data['upload']['enabled']).lower())
            if 'endpoint' in data['upload']:
                set_key(env_file, 'UPLOAD_ENDPOINT', data['upload']['endpoint'])
            if 'auth_bearer' in data['upload']:
                set_key(env_file, 'UPLOAD_AUTH_BEARER', data['upload']['auth_bearer'])
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post("/snap")
@login_required
def manual_snap():
    """Manual capture (non-blocking)."""
    try:
        source = request.json.get('source', 'r1')
        snap_async(source)
        return jsonify({'success': True, 'message': f'Capture initiated for {source}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post("/cleanup")
@login_required
def manual_cleanup():
    """Manual cleanup."""
    try:
        deleted = delete_older_than(RETENTION_DAYS)
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Login Template
LOGIN_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CamCap Login</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
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
<h1>🔐 CamCap Login</h1>
{% with messages = get_flashed_messages() %}
  {% if messages %}<div class="error">{{ messages[0] }}</div>{% endif %}
{% endwith %}
<form method="POST">
<input type="password" name="password" placeholder="Password" required autofocus>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>"""

# Modern Dashboard Template (same as app_modern.py)
DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CamCap Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
  min-height: 100vh;
  color: #2c3e50;
}
.container { max-width: 1400px; margin: 0 auto; padding: 20px; }
.header { 
  background: rgba(255, 255, 255, 0.95); 
  backdrop-filter: blur(10px);
  padding: 25px 30px; 
  border-radius: 20px; 
  margin-bottom: 25px; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.header h1 { 
  font-size: 28px; 
  font-weight: 700; 
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}
.tabs { 
  background: rgba(255, 255, 255, 0.95); 
  backdrop-filter: blur(10px);
  padding: 8px; 
  border-radius: 20px; 
  margin-bottom: 25px; 
  display: flex; 
  gap: 8px; 
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.tab-btn { 
  flex: 1; 
  padding: 15px 20px; 
  background: transparent; 
  border: none; 
  border-radius: 15px; 
  cursor: pointer; 
  font-size: 15px; 
  font-weight: 600; 
  transition: all 0.3s ease;
  color: #7f8c8d;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.tab-btn:hover { 
  background: rgba(52, 152, 219, 0.1); 
  color: #3498db;
}
.tab-btn.active { 
  background: linear-gradient(135deg, #3498db, #2980b9); 
  color: white; 
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}
.tab-content { display: none; }
.tab-content.active { display: block; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
.card { 
  background: rgba(255, 255, 255, 0.95); 
  backdrop-filter: blur(10px);
  padding: 25px; 
  border-radius: 20px; 
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover { 
  transform: translateY(-2px); 
  box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}
.card h3 { 
  margin-bottom: 20px; 
  color: #2c3e50; 
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}
.stat-row { 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  padding: 12px 0; 
  border-bottom: 1px solid rgba(236, 240, 241, 0.8); 
  transition: background 0.2s ease;
}
.stat-row:hover { background: rgba(236, 240, 241, 0.3); }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #7f8c8d; font-weight: 500; }
.stat-value { font-weight: 600; color: #2c3e50; }
.btn { 
  padding: 12px 24px; 
  background: linear-gradient(135deg, #3498db, #2980b9); 
  color: white; 
  border: none; 
  border-radius: 12px; 
  cursor: pointer; 
  font-size: 14px; 
  font-weight: 600;
  margin: 5px; 
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.btn:hover { 
  background: linear-gradient(135deg, #2980b9, #1f4e79); 
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}
.btn-danger { background: linear-gradient(135deg, #e74c3c, #c0392b); }
.btn-danger:hover { background: linear-gradient(135deg, #c0392b, #a93226); }
.btn-success { background: linear-gradient(135deg, #27ae60, #229954); }
.btn-success:hover { background: linear-gradient(135deg, #229954, #1e8449); }
.online { color: #27ae60; font-weight: 600; }
.offline { color: #e74c3c; font-weight: 600; }
.image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
.image-card { 
  border: 1px solid rgba(236, 240, 241, 0.8); 
  border-radius: 15px; 
  padding: 15px; 
  background: rgba(255, 255, 255, 0.8); 
  transition: all 0.3s ease;
}
.image-card:hover { 
  transform: translateY(-2px); 
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}
.image-card img { 
  width: 100%; 
  height: auto; 
  border-radius: 12px; 
  cursor: pointer; 
  transition: transform 0.3s ease;
}
.image-card img:hover { transform: scale(1.02); }
.image-meta { font-size: 13px; color: #7f8c8d; margin-top: 10px; }
input, select { 
  padding: 12px 16px; 
  border: 2px solid rgba(236, 240, 241, 0.8); 
  border-radius: 12px; 
  font-size: 14px; 
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
  width: 100%;
}
input:focus, select:focus { 
  outline: none; 
  border-color: #3498db; 
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}
.config-item { 
  background: rgba(248, 249, 250, 0.8); 
  padding: 20px; 
  border-radius: 15px; 
  margin-bottom: 20px; 
  border: 1px solid rgba(236, 240, 241, 0.5);
}
.config-item label { 
  display: block; 
  font-weight: 600; 
  margin-bottom: 8px; 
  color: #2c3e50; 
  font-size: 14px;
}
.config-item input[type="text"] { width: 100%; margin-bottom: 15px; }

/* Toggle Switch Styles */
.toggle-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 10px 0;
}
.toggle-switch {
  position: relative;
  width: 50px;
  height: 26px;
  background: #bdc3c7;
  border-radius: 13px;
  cursor: pointer;
  transition: background 0.3s ease;
}
.toggle-switch.active {
  background: #27ae60;
}
.toggle-switch::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.toggle-switch.active::before {
  transform: translateX(24px);
}
.toggle-label {
  font-weight: 500;
  color: #2c3e50;
  cursor: pointer;
}

.trigger-indicator { 
  background: rgba(248, 249, 250, 0.8); 
  padding: 20px; 
  border-radius: 15px; 
  margin-bottom: 15px; 
  display: flex; 
  align-items: center; 
  gap: 20px;
  border: 1px solid rgba(236, 240, 241, 0.5);
}
.trigger-light { 
  width: 35px; 
  height: 35px; 
  border-radius: 50%; 
  background: #bdc3c7; 
  transition: all 0.3s ease;
  position: relative;
}
.trigger-light.active { 
  background: #27ae60; 
  box-shadow: 0 0 20px rgba(39, 174, 96, 0.5); 
  animation: pulse 1s infinite;
}
@keyframes pulse { 
  0%, 100% { transform: scale(1); } 
  50% { transform: scale(1.1); } 
}
.pagination { 
  display: flex; 
  gap: 8px; 
  justify-content: center; 
  margin-top: 25px; 
  flex-wrap: wrap;
}
.pagination button { 
  padding: 10px 16px; 
  border-radius: 10px;
  min-width: 40px;
}

/* Loading states */
.loading {
  opacity: 0.6;
  pointer-events: none;
}

/* Responsive design */
@media (max-width: 768px) {
  .container { padding: 15px; }
  .header { flex-direction: column; gap: 15px; text-align: center; }
  .tabs { flex-direction: column; }
  .grid { grid-template-columns: 1fr; }
  .image-grid { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📷 CamCap Dashboard</h1>
    <div>
      <button class="btn" onclick="manualSnap()">📸 Manual Snap</button>
      <a href="/logout" class="btn btn-danger">🚪 Logout</a>
    </div>
  </div>
  
  <div class="tabs">
    <button class="tab-btn active" onclick="showTab('dashboard')">📊 Dashboard</button>
    <button class="tab-btn" onclick="showTab('config')">⚙️ Configuration</button>
    <button class="tab-btn" onclick="showTab('storage')">💾 Storage</button>
    <button class="tab-btn" onclick="showTab('images')">🖼️ Images</button>
  </div>

  <!-- Dashboard Tab -->
  <div id="dashboard" class="tab-content active">
    <div class="grid">
      <div class="card">
        <h3>📊 System Status</h3>
        <div class="stat-row">
          <span class="stat-label">Upload Status:</span>
          <span class="stat-value" id="upload-status">Loading...</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Uploaded:</span>
          <span class="stat-value" id="uploaded-count">0</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Pending:</span>
          <span class="stat-value" id="pending-count">0</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Total Images:</span>
          <span class="stat-value" id="total-images">0</span>
        </div>
      </div>
      
      <div class="card">
        <h3>📷 Camera Health</h3>
        <div class="stat-row">
          <span class="stat-label">Entry Camera:</span>
          <span class="stat-value" id="cam1-status">Loading...</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Exit Camera:</span>
          <span class="stat-value" id="cam2-status">Loading...</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">System Temp:</span>
          <span class="stat-value" id="system-temp">Loading...</span>
        </div>
      </div>
      
      <div class="card">
        <h3>🔘 GPIO Triggers</h3>
        <div class="trigger-indicator">
          <div class="trigger-light" id="trigger-r1"></div>
          <span>Entry (R1) - Pin 18</span>
        </div>
        <div class="trigger-indicator">
          <div class="trigger-light" id="trigger-r2"></div>
          <span>Exit (R2) - Pin 19</span>
        </div>
      </div>
    </div>
    
    <div class="card" style="margin-top: 25px;">
      <h3>📸 Recent Images</h3>
      <div class="image-grid" id="recent-images">
        <div style="text-align: center; padding: 40px; color: #7f8c8d;">Loading recent images...</div>
      </div>
    </div>
  </div>

  <!-- Configuration Tab -->
  <div id="config" class="tab-content">
    <div class="card">
      <h3>📷 Camera Configuration</h3>
      <div class="config-item">
        <label>Entry Camera (R1) RTSP URL:</label>
        <input type="text" id="cam1-rtsp" placeholder="rtsp://username:password@ip:port/path">
        <div class="toggle-container">
          <div class="toggle-switch" id="cam1-toggle" onclick="toggleSwitch('cam1-toggle')"></div>
          <span class="toggle-label">Enable Entry Camera</span>
        </div>
      </div>
      <div class="config-item">
        <label>Exit Camera (R2) RTSP URL:</label>
        <input type="text" id="cam2-rtsp" placeholder="rtsp://username:password@ip:port/path">
        <div class="toggle-container">
          <div class="toggle-switch" id="cam2-toggle" onclick="toggleSwitch('cam2-toggle')"></div>
          <span class="toggle-label">Enable Exit Camera</span>
        </div>
      </div>
      <button class="btn btn-success" onclick="saveCameraConfig()">💾 Save Camera Settings</button>
    </div>
    
    <div class="card">
      <h3>☁️ Upload Configuration</h3>
      <div class="config-item">
        <label>Upload Endpoint:</label>
        <input type="text" id="upload-endpoint" placeholder="https://api.example.com/upload">
      </div>
      <div class="config-item">
        <label>Auth Bearer Token:</label>
        <input type="text" id="upload-auth" placeholder="Optional bearer token">
      </div>
      <div class="toggle-container">
        <div class="toggle-switch" id="upload-toggle" onclick="toggleSwitch('upload-toggle')"></div>
        <span class="toggle-label">Enable Upload</span>
      </div>
      <button class="btn btn-success" onclick="saveUploadConfig()">💾 Save Upload Settings</button>
    </div>
  </div>

  <!-- Storage Tab -->
  <div id="storage" class="tab-content">
    <div class="card">
      <h3>💾 Storage Analysis</h3>
      <div class="stat-row">
        <span class="stat-label">Total Images:</span>
        <span class="stat-value" id="storage-total">0</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Entry (R1):</span>
        <span class="stat-value" id="storage-r1">0</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Exit (R2):</span>
        <span class="stat-value" id="storage-r2">0</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Uploaded:</span>
        <span class="stat-value" id="storage-uploaded">0</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Pending:</span>
        <span class="stat-value" id="storage-pending">0</span>
      </div>
    </div>
  </div>

  <!-- Images Tab -->
  <div id="images" class="tab-content">
    <div class="card">
      <h3>🖼️ Image Gallery</h3>
      <div style="margin-bottom: 20px; display: flex; gap: 15px; flex-wrap: wrap;">
        <select id="date-filter" onchange="loadImagesByDate()" style="flex: 1; min-width: 200px;">
          <option value="">Select Date</option>
        </select>
        <select id="source-filter" onchange="loadImagesByDate()" style="flex: 1; min-width: 150px;">
          <option value="">All Sources</option>
          <option value="r1">Entry (R1)</option>
          <option value="r2">Exit (R2)</option>
        </select>
      </div>
      <div class="image-grid" id="images-grid">
        <div style="text-align: center; padding: 40px; color: #7f8c8d;">Select a date to view images</div>
      </div>
      <div class="pagination" id="images-pagination"></div>
    </div>
  </div>
</div>

<script>
let currentTab = 'dashboard';
let currentPage = 1;
let currentDate = '';
let currentSource = '';

function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Show selected tab
  document.getElementById(tabName).classList.add('active');
  event.target.classList.add('active');
  currentTab = tabName;
  
  // Load tab-specific data
  if (tabName === 'storage') {
    loadStorageStats();
  } else if (tabName === 'images') {
    loadDateList();
  } else if (tabName === 'config') {
    loadConfig();
  }
}

function toggleSwitch(toggleId) {
  const toggle = document.getElementById(toggleId);
  toggle.classList.toggle('active');
}

function manualSnap() {
  fetch('/snap', {method: 'POST'})
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('Image captured successfully!');
        loadRecentImages();
      } else {
        alert('Failed to capture image: ' + data.error);
      }
    });
}

function loadStatus() {
  fetch('/api/status')
    .then(response => response.json())
    .then(data => {
      document.getElementById('upload-status').textContent = data.upload.enabled ? '🟢 ONLINE' : '🔴 OFFLINE';
      document.getElementById('uploaded-count').textContent = data.upload.uploaded || 0;
      document.getElementById('pending-count').textContent = data.upload.pending_count || 0;
      document.getElementById('total-images').textContent = data.storage.total || 0;
      
      // Update GPIO triggers
      if (data.gpio_triggers && data.gpio_triggers.r1) {
        document.getElementById('trigger-r1').classList.add('active');
        setTimeout(() => document.getElementById('trigger-r1').classList.remove('active'), 2000);
      }
      if (data.gpio_triggers && data.gpio_triggers.r2) {
        document.getElementById('trigger-r2').classList.add('active');
        setTimeout(() => document.getElementById('trigger-r2').classList.remove('active'), 2000);
      }
    });
}

function loadHealth() {
  fetch('/api/health')
    .then(response => response.json())
    .then(data => {
      document.getElementById('cam1-status').textContent = data.cameras.cam1.online ? '🟢 ONLINE' : '🔴 OFFLINE';
      document.getElementById('cam2-status').textContent = data.cameras.cam2.online ? '🟢 ONLINE' : '🔴 OFFLINE';
      document.getElementById('system-temp').textContent = data.system.temperature + '°C';
    });
}

function loadRecentImages() {
  fetch('/api/images/recent?per_page=12')
    .then(response => response.json())
    .then(data => {
      const container = document.getElementById('recent-images');
      if (data.images && data.images.length > 0) {
        container.innerHTML = data.images.map(img => `
          <div class="image-card">
            <img src="/images/${img.filename}" alt="${img.filename}" onclick="openImageModal('/images/${img.filename}')">
            <div class="image-meta">
              <div><strong>${img.source.toUpperCase()}</strong></div>
              <div>${new Date(img.timestamp * 1000).toLocaleString()}</div>
              <div>${img.size} bytes</div>
            </div>
          </div>
        `).join('');
      } else {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">No recent images</div>';
      }
    });
}

function loadStorageStats() {
  fetch('/api/storage/stats')
    .then(response => response.json())
    .then(data => {
      document.getElementById('storage-total').textContent = data.total || 0;
      document.getElementById('storage-r1').textContent = data.by_source.r1 || 0;
      document.getElementById('storage-r2').textContent = data.by_source.r2 || 0;
      document.getElementById('storage-uploaded').textContent = data.uploaded || 0;
      document.getElementById('storage-pending').textContent = data.pending || 0;
    });
}

function loadDateList() {
  fetch('/api/images/dates')
    .then(response => response.json())
    .then(data => {
      const select = document.getElementById('date-filter');
      select.innerHTML = '<option value="">Select Date</option>';
      data.dates.forEach(date => {
        const option = document.createElement('option');
        option.value = date;
        option.textContent = date;
        select.appendChild(option);
      });
    });
}

function loadConfig() {
  fetch('/api/config')
    .then(response => response.json())
    .then(data => {
      document.getElementById('cam1-rtsp').value = data.cameras.r1.rtsp_url || '';
      document.getElementById('cam2-rtsp').value = data.cameras.r2.rtsp_url || '';
      document.getElementById('cam1-toggle').classList.toggle('active', data.cameras.r1.enabled);
      document.getElementById('cam2-toggle').classList.toggle('active', data.cameras.r2.enabled);
      document.getElementById('upload-endpoint').value = data.upload.endpoint || '';
      document.getElementById('upload-auth').value = data.upload.auth_bearer || '';
      document.getElementById('upload-toggle').classList.toggle('active', data.upload.enabled);
    });
}

function loadImagesByDate() {
  const date = document.getElementById('date-filter').value;
  const source = document.getElementById('source-filter').value;
  
  if (!date) {
    document.getElementById('images-grid').innerHTML = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">Select a date to view images</div>';
    return;
  }
  
  currentDate = date;
  currentSource = source;
  currentPage = 1;
  loadImagesPage();
}

function loadImagesPage() {
  if (!currentDate) return;
  
  const url = `/api/images/by-date?date=${currentDate}&page=${currentPage}&per_page=20${currentSource ? '&source=' + currentSource : ''}`;
  
  fetch(url)
    .then(response => response.json())
    .then(data => {
      const container = document.getElementById('images-grid');
      if (data.images && data.images.length > 0) {
        container.innerHTML = data.images.map(img => `
          <div class="image-card">
            <img src="/images/${img.filename}" alt="${img.filename}" onclick="openImageModal('/images/${img.filename}')">
            <div class="image-meta">
              <div><strong>${img.source.toUpperCase()}</strong></div>
              <div>${new Date(img.timestamp * 1000).toLocaleString()}</div>
              <div>${img.size} bytes</div>
            </div>
          </div>
        `).join('');
        
        // Update pagination
        const totalPages = Math.ceil(data.total / 20);
        const pagination = document.getElementById('images-pagination');
        pagination.innerHTML = '';
        
        for (let i = 1; i <= totalPages; i++) {
          const btn = document.createElement('button');
          btn.textContent = i;
          btn.className = i === currentPage ? 'btn btn-success' : 'btn';
          btn.onclick = () => {
            currentPage = i;
            loadImagesPage();
          };
          pagination.appendChild(btn);
        }
      } else {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">No images found for this date</div>';
        document.getElementById('images-pagination').innerHTML = '';
      }
    });
}

function openImageModal(imageSrc) {
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(0,0,0,0.8); display: flex; justify-content: center; 
    align-items: center; z-index: 1000;
  `;
  modal.innerHTML = `
    <div style="max-width: 90%; max-height: 90%;">
      <img src="${imageSrc}" style="max-width: 100%; max-height: 100%; border-radius: 15px;">
    </div>
  `;
  modal.onclick = () => document.body.removeChild(modal);
  document.body.appendChild(modal);
}

function saveCameraConfig() {
  const data = {
    cameras: {
      r1: {
        rtsp_url: document.getElementById('cam1-rtsp').value,
        enabled: document.getElementById('cam1-toggle').classList.contains('active')
      },
      r2: {
        rtsp_url: document.getElementById('cam2-rtsp').value,
        enabled: document.getElementById('cam2-toggle').classList.contains('active')
      }
    }
  };
  
  fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Camera configuration saved successfully!');
    } else {
      alert('Failed to save configuration: ' + data.error);
    }
  });
}

function saveUploadConfig() {
  const data = {
    upload: {
      endpoint: document.getElementById('upload-endpoint').value,
      auth_bearer: document.getElementById('upload-auth').value,
      enabled: document.getElementById('upload-toggle').classList.contains('active')
    }
  };
  
  fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Upload configuration saved successfully!');
    } else {
      alert('Failed to save configuration: ' + data.error);
    }
  });
}

// Load initial data
loadStatus();
loadHealth();
loadRecentImages();

// Auto-refresh every 5 seconds
setInterval(() => {
  if (currentTab === 'dashboard') {
    loadStatus();
    loadHealth();
  }
}, 5000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    # Start uploader in background
    if UPLOAD_ENABLED:
        uploader_thread = threading.Thread(target=uploader.run_forever, daemon=True)
        uploader_thread.start()
        print("[UPLOADER] Background uploader started")
    
    # Start cleanup service
    def cleanup_service():
        while True:
            try:
                deleted = delete_older_than(RETENTION_DAYS)
                if deleted > 0:
                    print(f"[CLEANUP] Deleted {deleted} old images")
            except Exception as e:
                print(f"[CLEANUP] Error: {e}")
            time.sleep(3600)  # Run every hour
    
    cleanup_thread = threading.Thread(target=cleanup_service, daemon=True)
    cleanup_thread.start()
    print("[CLEANUP] Background cleanup started")
    
    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\n[SHUTDOWN] Gracefully shutting down...")
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"[WEB] Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    print(f"[WEB] Dashboard: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"[WEB] Authentication: {'Enabled' if WEB_AUTH_ENABLED else 'Disabled'}")
    print(f"[WEB] GPIO Available: {'Yes' if GPIO_AVAILABLE else 'No (Windows mode)'}")
    print(f"[WEB] RTSP Available: {'Yes' if RTSP_AVAILABLE else 'No (Windows mode)'}")
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, threaded=True)
