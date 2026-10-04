"""
Main routes for the DeepFake detection application
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page with file upload interface"""
    return render_template('index.html')

@main_bp.route('/result/<job_id>')
def result(job_id):
    """Results page for a specific analysis job"""
    # Validate job_id format (should be UUID-like)
    if not job_id or len(job_id) < 10:
        return render_template('result.html', job_id='invalid')
    
    return render_template('result.html', job_id=job_id)

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'DeepFake Detection API is running'
    })

@main_bp.route('/assets/fonts/<filename>')
def serve_fonts(filename):
    """Serve font files"""
    from flask import send_from_directory
    import os
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'fonts')
    return send_from_directory(fonts_dir, filename)
