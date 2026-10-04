#!/usr/bin/env python3
"""
DeepFake Detection System - Main Entry Point
تشغيل نظام كشف DeepFake
"""

import os
import sys
import warnings
from app import create_app
from config import config

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore', category=FutureWarning)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask', 'numpy', 'cv2', 'PIL', 'tensorflow',
        'sklearn', 'skimage', 'mtcnn', 'imutils',
        'imageio', 'pandas', 'tqdm', 'werkzeug',
        'keras', 'tensorboard', 'matplotlib', 'seaborn',
        'joblib', 'requests', 'sympy', 'scipy'
    ]
    
    advanced_packages = [
        'flask_socketio', 'reportlab', 'librosa', 
        'cryptography', 'albumentations'
    ]
    
    optional_packages = ['dlib', 'magic']
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    # Check advanced packages
    missing_advanced = []
    for package in advanced_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_advanced.append(package)
    
    # Check optional packages
    missing_optional = []
    for package in optional_packages:
        try:
            if package == 'magic':
                try:
                    __import__('magic')  # python-magic imports as 'magic'
                except ImportError:
                    # Check if it's a libmagic issue
                    try:
                        import magic
                        # If we get here, magic is installed but libmagic is missing
                        missing_optional.append(f'{package} (libmagic missing)')
                    except:
                        missing_optional.append(package)
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    if missing_packages:
        print("❌ مكتبات مطلوبة مفقودة:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 قم بتثبيت المكتبات المفقودة:")
        print("   pip install -r requirements.txt")
        return False
    
    if missing_advanced:
        print("⚠️  مكتبات متقدمة مفقودة:")
        for package in missing_advanced:
            print(f"   - {package}")
        print("💡 بعض الميزات المتقدمة لن تعمل")
    
    if missing_optional:
        print("⚠️  مكتبات اختيارية مفقودة:")
        for package in missing_optional:
            print(f"   - {package}")
        print("💡 النظام سيعمل بدونها لكن ببعض القيود")
    
    return True

def main():
    """Main function to run the DeepFake detection application"""
    
    print("=" * 60)
    print("🔍 نظام كشف DeepFake - DeepFake Detection System")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get configuration
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    app_config = config[config_name]
    
    # Create Flask application
    app = create_app(app_config)
    
    # Configuration
    debug_mode = app_config.DEBUG
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"🌐 الخادم: http://{host}:{port}")
    print(f"🔧 وضع التطوير: {'مفعل' if debug_mode else 'معطل'}")
    print(f"📁 مجلد التحميل: {app.config['UPLOAD_FOLDER']}")
    print(f"📊 مجلد التحليل: {app.config['ANALYSIS_FOLDER']}")
    print(f"⚙️  التكوين: {config_name}")
    print("=" * 60)
    print("💡 نصائح:")
    print("   - تأكد من تثبيت جميع المكتبات المطلوبة")
    print("   - لتحسين الأداء، قم بتحميل أوزان النماذج المسبقة")
    print("   - استخدم Ctrl+C لإيقاف الخادم")
    print("   - للاستخدام الإنتاجي: gunicorn -w 4 run:app")
    print("=" * 60)
    
    try:
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=app_config.THREADED,
            processes=app_config.PROCESSES
        )
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
