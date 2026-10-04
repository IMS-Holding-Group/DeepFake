"""
Configuration settings for DeepFake Detection System
إعدادات التكوين لنظام كشف DeepFake
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'deepfake-detection-secret-key-2024'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    ANALYSIS_FOLDER = 'static/analysis'
    WEIGHTS_FOLDER = 'weights'
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
    
    # Analysis settings
    DEFAULT_MAX_FRAMES = 30
    DEFAULT_SAMPLE_RATE = 1
    FACE_DETECTION_CONFIDENCE = 0.9
    
    # Model settings
    XCEPTION_INPUT_SIZE = (299, 299)
    ENSEMBLE_WEIGHTS = {
        'xception': 0.6,
        'forensics': 0.3,
        'metadata': 0.1
    }
    
    # File cleanup settings
    FILE_CLEANUP_HOURS = 24  # Delete files after 24 hours
    
    # Performance settings
    THREADED = True
    PROCESSES = 1
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        for folder in [Config.UPLOAD_FOLDER, Config.ANALYSIS_FOLDER, Config.WEIGHTS_FOLDER]:
            os.makedirs(folder, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB for production
    DEFAULT_MAX_FRAMES = 20  # Fewer frames for faster processing

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Testing-specific settings
    UPLOAD_FOLDER = 'test_uploads'
    ANALYSIS_FOLDER = 'test_analysis'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
