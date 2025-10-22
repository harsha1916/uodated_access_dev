import os
import logging
import bcrypt
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, session, flash
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv, set_key
from config import (
    BIND_IP, BIND_PORT, IMAGE_STORAGE_PATH,
    CAMERA_NAMES, GPIO_ENABLED, GPIO_TRIGGER_ENABLED, UPLOAD_ENABLED, BACKGROUND_UPLOAD,
    IMAGE_RETENTION_DAYS, get_rtsp_cameras, WEB_AUTH_ENABLED, PASSWORD_HASH, SECRET_KEY,
    is_camera_enabled
)
from capture_service import CameraService
from cleanup_service import CleanupService
from gpio_service import GPIOService
from system_monitor import SystemMonitor


# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
camera_service = None
cleanup_service = None
gpio_service = None
system_monitor = None


# Authentication decorator
def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not WEB_AUTH_ENABLED:
            # Authentication disabled, allow access
            return f(*args, **kwargs)
        
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def verify_password(password: str) -> bool:
    """Verify password against stored hash."""
    if not PASSWORD_HASH:
        logger.warning("No password hash configured - authentication will fail")
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), PASSWORD_HASH.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def hash_password(password: str) -> str:
    """Generate bcrypt hash for password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def update_password_hash(new_hash: str) -> bool:
    """Update password hash in .env file."""
    try:
        env_file = '.env'
        if not os.path.exists(env_file):
            # Create .env file if it doesn't exist
            with open(env_file, 'w') as f:
                f.write(f"PASSWORD_HASH={new_hash}\n")
        else:
            set_key(env_file, 'PASSWORD_HASH', new_hash)
        
        # Reload environment
        load_dotenv(override=True)
        logger.info("Password hash updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating password hash: {e}")
        return False


def init_services():
    """Initialize all services."""
    global camera_service, cleanup_service, gpio_service, system_monitor
    
    try:
        # Initialize camera service
        logger.info("Initializing camera service...")
        camera_service = CameraService()
        
        # Start background upload service
        if UPLOAD_ENABLED and BACKGROUND_UPLOAD:
            camera_service.start_upload_service()
        
        # Initialize cleanup service
        logger.info("Initializing cleanup service...")
        cleanup_service = CleanupService()
        cleanup_service.start()
        
        # Initialize GPIO service
        logger.info("Initializing GPIO service...")
        gpio_service = GPIOService()
        
        # Register GPIO callbacks
        if gpio_service.is_available() and GPIO_TRIGGER_ENABLED:
            gpio_service.register_callback("camera_1", camera_service.capture_by_key)
            gpio_service.register_callback("camera_2", camera_service.capture_by_key)
            gpio_service.register_callback("camera_3", camera_service.capture_by_key)
            gpio_service.start_monitoring()
        
        # Initialize system monitor
        logger.info("Initializing system monitor...")
        system_monitor = SystemMonitor()
        system_monitor.start()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing services: {e}", exc_info=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if not WEB_AUTH_ENABLED:
        # Auth disabled, redirect to dashboard
        return redirect(url_for('index'))
    
    if 'logged_in' in session:
        # Already logged in
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if verify_password(password):
            session['logged_in'] = True
            session.permanent = True
            logger.info("Successful login")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            logger.warning("Failed login attempt")
            flash('Invalid password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Verify current password
        if not verify_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('change_password.html')
        
        # Check new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters', 'error')
            return render_template('change_password.html')
        
        # Check passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        # Generate new hash and update
        new_hash = hash_password(new_password)
        if update_password_hash(new_hash):
            flash('Password changed successfully', 'success')
            logger.info("Password changed successfully")
            return redirect(url_for('index'))
        else:
            flash('Error updating password', 'error')
            logger.error("Failed to update password")
    
    return render_template('change_password.html')


@app.route('/')
@login_required
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
@login_required
def get_status():
    """Get system status and configuration."""
    try:
        # Get camera status (dynamically from .env)
        cameras = {}
        for camera_key, camera_name in CAMERA_NAMES.items():
            cameras[camera_key] = {
                'name': camera_name,
                'enabled': is_camera_enabled(camera_key),
                'rtsp_configured': bool(get_rtsp_cameras().get(camera_key))
            }
        
        # Get GPIO status
        gpio_status = {
            'available': gpio_service.is_available() if gpio_service else False,
            'enabled': GPIO_ENABLED,
            'trigger_enabled': GPIO_TRIGGER_ENABLED
        }
        
        # Get upload status
        upload_status = {
            'enabled': UPLOAD_ENABLED,
            'background': BACKGROUND_UPLOAD
        }
        
        # Get retention settings
        retention_settings = {
            'retention_days': IMAGE_RETENTION_DAYS
        }
        
        return jsonify({
            'success': True,
            'status': 'running',
            'cameras': cameras,
            'gpio': gpio_status,
            'upload': upload_status,
            'retention': retention_settings,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats')
@login_required
def get_stats():
    """Get statistics for all services."""
    try:
        stats = {
            'capture': camera_service.get_stats() if camera_service else {},
            'cleanup': cleanup_service.get_stats() if cleanup_service else {},
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images')
@login_required
def get_images():
    """Get list of captured images with pagination."""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        camera_filter = request.args.get('camera', None)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get images from cleanup service
        if cleanup_service:
            all_images = cleanup_service.get_image_list(limit=1000, offset=0)
            
            # Filter by camera if specified
            if camera_filter:
                all_images = [img for img in all_images if img['filename'].startswith(camera_filter)]
            
            # Paginate
            total_images = len(all_images)
            paginated_images = all_images[offset:offset + per_page]
            
            return jsonify({
                'success': True,
                'images': paginated_images,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_images,
                    'pages': (total_images + per_page - 1) // per_page
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Cleanup service not available'
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting images: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images/<path:filename>')
@login_required
def serve_image(filename):
    """Serve an image file."""
    try:
        return send_from_directory(IMAGE_STORAGE_PATH, filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({'success': False, 'error': 'Image not found'}), 404


@app.route('/api/capture/<camera_key>', methods=['POST'])
@login_required
def manual_capture(camera_key):
    """Manually trigger image capture for a camera."""
    try:
        if not camera_service:
            return jsonify({
                'success': False,
                'error': 'Camera service not available'
            }), 500
        
        # Validate camera key
        if camera_key not in ['camera_1', 'camera_2', 'camera_3']:
            return jsonify({
                'success': False,
                'error': 'Invalid camera key'
            }), 400
        
        # Capture image
        result = camera_service.capture_by_key(camera_key)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Image captured successfully',
                'image': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to capture image'
            }), 500
            
    except Exception as e:
        logger.error(f"Error capturing image: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cleanup/run', methods=['POST'])
@login_required
def run_cleanup():
    """Manually trigger cleanup operation."""
    try:
        if not cleanup_service:
            return jsonify({
                'success': False,
                'error': 'Cleanup service not available'
            }), 500
        
        deleted_count = cleanup_service.run_cleanup()
        
        return jsonify({
            'success': True,
            'message': f'Cleanup completed: {deleted_count} images deleted',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error running cleanup: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gpio/status')
@login_required
def gpio_status():
    """Get GPIO pin status."""
    try:
        if not gpio_service or not gpio_service.is_available():
            return jsonify({
                'success': False,
                'error': 'GPIO service not available'
            })
        
        pin_states = {
            'camera_1': gpio_service.get_pin_state('camera_1'),
            'camera_2': gpio_service.get_pin_state('camera_2'),
            'camera_3': gpio_service.get_pin_state('camera_3')
        }
        
        # Get trigger events for animation
        trigger_events = gpio_service.get_trigger_events()
        
        return jsonify({
            'success': True,
            'pin_states': pin_states,
            'trigger_events': trigger_events
        })
        
    except Exception as e:
        logger.error(f"Error getting GPIO status: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/get')
@login_required
def get_config():
    """Get current configuration."""
    try:
        config_data = {
            'cameras': {},
            'gpio': {
                'enabled': GPIO_ENABLED,
                'trigger_enabled': GPIO_TRIGGER_ENABLED,
                'pins': {
                    'camera_1': os.getenv('GPIO_CAMERA_1_PIN', '18'),
                    'camera_2': os.getenv('GPIO_CAMERA_2_PIN', '19'),
                    'camera_3': os.getenv('GPIO_CAMERA_3_PIN', '20')
                }
            },
            'upload': {
                'enabled': UPLOAD_ENABLED,
                'background': BACKGROUND_UPLOAD,
                's3_url': os.getenv('S3_API_URL', '')
            }
        }
        
        # Get camera configuration
        for camera_key, camera_name in CAMERA_NAMES.items():
            camera_num = camera_key.split('_')[1]
            config_data['cameras'][camera_key] = {
                'name': camera_name,
                'enabled': is_camera_enabled(camera_key),
                'ip': os.getenv(f'CAMERA_{camera_num}_IP', ''),
                'rtsp_url': os.getenv(f'CAMERA_{camera_num}_RTSP', ''),
                'username': os.getenv('CAMERA_USERNAME', 'admin'),
                'password': '****'  # Don't expose password
            }
        
        return jsonify({
            'success': True,
            'config': config_data
        })
        
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/update', methods=['POST'])
@login_required
def update_config():
    """Update configuration and save to .env file."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        env_file = '.env'
        updates = {}
        
        # Update camera settings
        if 'cameras' in data:
            for camera_key, settings in data['cameras'].items():
                camera_num = camera_key.split('_')[1]
                
                if 'enabled' in settings:
                    updates[f'CAMERA_{camera_num}_ENABLED'] = str(settings['enabled']).lower()
                
                if 'ip' in settings:
                    updates[f'CAMERA_{camera_num}_IP'] = settings['ip']
                
                if 'rtsp_url' in settings:
                    updates[f'CAMERA_{camera_num}_RTSP'] = settings['rtsp_url']
                
                if 'username' in settings:
                    updates['CAMERA_USERNAME'] = settings['username']
                
                if 'password' in settings and settings['password'] != '****':
                    updates['CAMERA_PASSWORD'] = settings['password']
        
        # Update GPIO settings
        if 'gpio' in data:
            if 'enabled' in data['gpio']:
                updates['GPIO_ENABLED'] = str(data['gpio']['enabled']).lower()
            
            if 'trigger_enabled' in data['gpio']:
                updates['GPIO_TRIGGER_ENABLED'] = str(data['gpio']['trigger_enabled']).lower()
        
        # Update upload settings
        if 'upload' in data:
            if 'enabled' in data['upload']:
                updates['UPLOAD_ENABLED'] = str(data['upload']['enabled']).lower()
            
            if 's3_url' in data['upload']:
                updates['S3_API_URL'] = data['upload']['s3_url']
        
        # Save to .env file
        for key, value in updates.items():
            set_key(env_file, key, value)
        
        # Reload environment
        load_dotenv(override=True)
        
        logger.info(f"Configuration updated: {list(updates.keys())}")
        
        return jsonify({
            'success': True,
            'message': f'Configuration updated: {len(updates)} settings changed',
            'updated_keys': list(updates.keys())
        })
        
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/reload', methods=['POST'])
@login_required
def reload_config():
    """Reload configuration from .env file without restart."""
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        logger.info("Configuration reloaded from .env file")
        
        return jsonify({
            'success': True,
            'message': 'Configuration reloaded successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error reloading config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health')
@login_required
def get_health():
    """Get system health status including camera health and RPi temperature."""
    try:
        health_data = {
            'camera_health': {},
            'system': {
                'cpu_temp': None,
                'cpu_temp_unit': '°C'
            }
        }
        
        if system_monitor:
            status = system_monitor.get_all_status()
            health_data['camera_health'] = status.get('camera_health', {})
            health_data['system'] = status.get('system_stats', {})
        
        return jsonify({
            'success': True,
            'health': health_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/storage/analysis')
@login_required
def get_storage_analysis():
    """Get storage analysis including breakdown by date and camera."""
    try:
        if not cleanup_service:
            return jsonify({
                'success': False,
                'error': 'Cleanup service not available'
            }), 500
        
        # Get all images
        images = cleanup_service.get_image_list(limit=10000, offset=0)
        
        # Analysis by date
        by_date = {}
        by_camera = {'r1': 0, 'r2': 0, 'r3': 0}
        total_size = 0
        
        for img in images:
            # Extract date from timestamp
            from datetime import datetime as dt
            date_obj = dt.fromtimestamp(img['created_timestamp'])
            date_str = date_obj.strftime('%Y-%m-%d')
            
            if date_str not in by_date:
                by_date[date_str] = {
                    'count': 0,
                    'size_bytes': 0,
                    'size_mb': 0
                }
            
            by_date[date_str]['count'] += 1
            by_date[date_str]['size_bytes'] += img['size_bytes']
            by_date[date_str]['size_mb'] = round(by_date[date_str]['size_bytes'] / (1024 * 1024), 2)
            
            # By camera
            filename = img['filename']
            if filename.startswith('r1'):
                by_camera['r1'] += 1
            elif filename.startswith('r2'):
                by_camera['r2'] += 1
            elif filename.startswith('r3'):
                by_camera['r3'] += 1
            
            total_size += img['size_bytes']
        
        # Sort dates (newest first)
        sorted_dates = sorted(by_date.items(), key=lambda x: x[0], reverse=True)
        
        return jsonify({
            'success': True,
            'analysis': {
                'by_date': dict(sorted_dates[:30]),  # Last 30 days
                'by_camera': by_camera,
                'total_images': len(images),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting storage analysis: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images/by-date')
@login_required
def get_images_by_date():
    """Get images for a specific date with pagination."""
    try:
        # Get parameters
        date_str = request.args.get('date')  # Format: YYYY-MM-DD
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        camera_filter = request.args.get('camera', None)
        
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'Date parameter required (format: YYYY-MM-DD)'
            }), 400
        
        if not cleanup_service:
            return jsonify({
                'success': False,
                'error': 'Cleanup service not available'
            }), 500
        
        # Get all images
        all_images = cleanup_service.get_image_list(limit=10000, offset=0)
        
        # Filter by date
        from datetime import datetime as dt
        filtered_images = []
        for img in all_images:
            img_date = dt.fromtimestamp(img['created_timestamp']).strftime('%Y-%m-%d')
            if img_date == date_str:
                # Apply camera filter if specified
                if camera_filter:
                    if img['filename'].startswith(camera_filter):
                        filtered_images.append(img)
                else:
                    filtered_images.append(img)
        
        # Sort by timestamp (newest first)
        filtered_images.sort(key=lambda x: x['created_timestamp'], reverse=True)
        
        # Paginate
        offset = (page - 1) * per_page
        paginated_images = filtered_images[offset:offset + per_page]
        
        return jsonify({
            'success': True,
            'date': date_str,
            'images': paginated_images,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(filtered_images),
                'pages': (len(filtered_images) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting images by date: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def cleanup_on_shutdown():
    """Cleanup function to run on app shutdown."""
    logger.info("Shutting down services...")
    
    try:
        if camera_service:
            camera_service.stop_upload_service()
        
        if cleanup_service:
            cleanup_service.stop()
        
        if gpio_service:
            gpio_service.cleanup()
        
        if system_monitor:
            system_monitor.stop()
        
        logger.info("All services stopped successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


if __name__ == '__main__':
    try:
        # Initialize services
        init_services()
        
        # Run Flask app
        logger.info(f"Starting web server on {BIND_IP}:{BIND_PORT}")
        app.run(
            host=BIND_IP,
            port=BIND_PORT,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error running web app: {e}", exc_info=True)
    finally:
        cleanup_on_shutdown()

