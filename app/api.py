"""
REST API endpoints for DeepFake detection
"""

from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import json
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
# Try to import magic, but don't fail if it's not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️  تحذير: python-magic غير متوفر - سيتم استخدام فحص نوع الملف البديل")

api_bp = Blueprint('api', __name__)

# Global storage for job results (in production, use Redis or database)
job_results = {}
_job_lock = threading.Lock()


def _sanitize_for_json(obj):
    """Make API payloads JSON-serializable (numpy scalars/arrays, etc.)."""
    try:
        import numpy as np
    except ImportError:
        np = None

    if np is not None:
        if isinstance(obj, np.ndarray):
            return _sanitize_for_json(obj.tolist())
        if isinstance(obj, np.generic):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.bool_):
                return bool(obj)

    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")
    return obj


def _run_image_analysis(app, job_id, file_path):
    """Run heavy model work off the request thread so the client gets a job ID quickly."""
    with app.app_context():
        from app.models.ensemble import DeepFakeDetector
        try:
            detector = DeepFakeDetector()
            result = detector.analyze_image(file_path)
            with _job_lock:
                if job_id in job_results:
                    job_results[job_id].update({
                        'status': 'done',
                        'summary': result['summary'],
                        'artifacts': result.get('artifacts', {}),
                    })
                    if 'advanced_analysis' in result:
                        job_results[job_id]['advanced_analysis'] = result['advanced_analysis']
        except Exception as e:
            with _job_lock:
                if job_id in job_results:
                    job_results[job_id].update({
                        'status': 'error',
                        'error': str(e),
                    })


def _run_video_analysis(app, job_id, file_path):
    with app.app_context():
        from app.models.ensemble import DeepFakeDetector
        try:
            detector = DeepFakeDetector()
            result = detector.analyze_video(file_path)
            with _job_lock:
                if job_id in job_results:
                    job_results[job_id].update({
                        'status': 'done',
                        'summary': result['summary'],
                        'artifacts': result.get('artifacts', {}),
                    })
                    if 'advanced_analysis' in result:
                        job_results[job_id]['advanced_analysis'] = result['advanced_analysis']
        except Exception as e:
            with _job_lock:
                if job_id in job_results:
                    job_results[job_id].update({
                        'status': 'error',
                        'error': str(e),
                    })

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(file_path):
    """Get file type using python-magic or file extension"""
    if MAGIC_AVAILABLE:
        try:
            mime = magic.from_file(file_path, mime=True)
            if mime.startswith('image/'):
                return 'image'
            elif mime.startswith('video/'):
                return 'video'
            else:
                return 'unknown'
        except:
            pass
    
    # Fallback to file extension
    ext = os.path.splitext(file_path)[1].lower()
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    
    if ext in image_extensions:
        return 'image'
    elif ext in video_extensions:
        return 'video'
    else:
        return 'unknown'

@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Upload and analyze image file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, TIFF'}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(file_path)
    
    # Verify file type
    file_type = get_file_type(file_path)
    if file_type != 'image':
        os.remove(file_path)
        return jsonify({'error': 'File is not a valid image'}), 400
    
    with _job_lock:
        job_results[job_id] = {
            'id': job_id,
            'status': 'processing',
            'file_type': 'image',
            'filename': filename,
            'file_path': file_path,
            'created_at': datetime.now().isoformat(),
            'summary': None,
            'artifacts': {}
        }

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_image_analysis,
        args=(app, job_id, file_path),
        daemon=True,
    )
    thread.start()

    return jsonify({
        'id': job_id,
        'status': 'processing'
    })

@api_bp.route('/upload-video', methods=['POST'])
def upload_video():
    """Upload and analyze video file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({'error': 'Invalid file type. Allowed: MP4, AVI, MOV, MKV, WMV, FLV, WEBM'}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(file_path)
    
    # Verify file type
    file_type = get_file_type(file_path)
    if file_type != 'video':
        os.remove(file_path)
        return jsonify({'error': 'File is not a valid video'}), 400
    
    with _job_lock:
        job_results[job_id] = {
            'id': job_id,
            'status': 'processing',
            'file_type': 'video',
            'filename': filename,
            'file_path': file_path,
            'created_at': datetime.now().isoformat(),
            'summary': None,
            'artifacts': {}
        }

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_video_analysis,
        args=(app, job_id, file_path),
        daemon=True,
    )
    thread.start()

    return jsonify({
        'id': job_id,
        'status': 'processing'
    })

@api_bp.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    """Get analysis result for a job"""
    # Validate job_id format
    if not job_id or len(job_id) < 10 or job_id == 'invalid':
        return jsonify({'error': 'Invalid job ID format'}), 400
    
    if job_id not in job_results:
        return jsonify({'error': 'Job not found'}), 404

    with _job_lock:
        payload = _sanitize_for_json(job_results[job_id])

    return jsonify(payload)

@api_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get job status"""
    if job_id not in job_results:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'id': job_id,
        'status': job_results[job_id]['status']
    })
