"""
DeepFake Detection Application
Flask application package initialization
"""

from flask import Flask
import os

def create_app(config_class=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_class:
        app.config.from_object(config_class)
        config_class.init_app(app)
    else:
        # Default configuration
        app.config['SECRET_KEY'] = 'deepfake-detection-secret-key-2024'
        app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
        app.config['UPLOAD_FOLDER'] = 'uploads'
        app.config['ANALYSIS_FOLDER'] = 'static/analysis'
        
        # Create necessary directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)
        os.makedirs('weights', exist_ok=True)
    
    # Register blueprints
    from app.routes import main_bp
    from app.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
