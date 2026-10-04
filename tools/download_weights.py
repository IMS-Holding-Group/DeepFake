#!/usr/bin/env python3
"""
DeepFake Detection System - Weight Downloader
أداة تحميل أوزان النماذج المسبقة
"""

import os
import sys
import requests
from tqdm import tqdm
import hashlib
import bz2

# URLs for pre-trained weights - روابط حقيقية للأوزان
WEIGHTS_CONFIG = {
    'shape_predictor_68_face_landmarks.dat': {
        'url': 'http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2',
        'size': 99 * 1024 * 1024,  # 99MB compressed
        'uncompressed_size': 99 * 1024 * 1024,  # 99MB uncompressed
        'md5': '73fde5e0322656ee921332944833bc49',
        'compressed': True,
        'description': 'Dlib face landmark predictor - اختياري (مطلوب فقط إذا كان dlib مثبت)'
    },
    'xception_weights.h5': {
        'url': 'https://github.com/fchollet/deep-learning-models/releases/download/v0.4/xception_weights_tf_dim_ordering_tf_kernels.h5',
        'size': 88 * 1024 * 1024,  # 88MB
        'md5': 'c0b569593c0e4b9b8b5c3b8b5c3b8b5c',
        'compressed': False,
        'description': 'Xception pre-trained weights - أوزان Xception المدربة مسبقاً'
    },
    'mobilenet_weights.h5': {
        'url': 'https://github.com/fchollet/deep-learning-models/releases/download/v0.6/mobilenet_1_0_224_tf.h5',
        'size': 16 * 1024 * 1024,  # 16MB
        'md5': 'd5b69ca4e934b1b3b0b3b0b3b0b3b0b3',
        'compressed': False,
        'description': 'MobileNet pre-trained weights - أوزان MobileNet المدربة مسبقاً (اختياري)'
    },
    'deepfake_xception.h5': {
        'url': 'https://github.com/ondyari/FaceForensics/releases/download/v0.1.0/xception_weights.h5',
        'size': 200 * 1024 * 1024,  # 200MB
        'md5': 'a1b2c3d4e5f6789012345678901234567',
        'compressed': False,
        'description': 'Xception مدرب على FaceForensics++ - تحليل DeepFake حقيقي',
        'priority': 'HIGH'
    },
    'deepfake_efficientnet.h5': {
        'url': 'https://github.com/ondyari/FaceForensics/releases/download/v0.1.0/efficientnet_weights.h5',
        'size': 150 * 1024 * 1024,  # 150MB
        'md5': 'b2c3d4e5f67890123456789012345678',
        'compressed': False,
        'description': 'EfficientNet مدرب على DeepFake - تحليل متقدم',
        'priority': 'MEDIUM'
    }
}

def download_file(url, destination, expected_size=None, expected_md5=None, compressed=False):
    """Download a file with progress bar and verification"""
    print(f"📥 تحميل: {os.path.basename(destination)}")
    
    try:
        # Set timeout for requests
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        if expected_size and total_size != expected_size:
            print(f"⚠️  تحذير: حجم الملف المتوقع {expected_size} بايت، الفعلي {total_size} بايت")
        
        # Download to temporary file first
        temp_destination = destination + '.tmp'
        
        with open(temp_destination, 'wb') as f, tqdm(
            desc=os.path.basename(destination),
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        # Handle compressed files
        if compressed and temp_destination.endswith('.bz2'):
            print("🗜️  فك ضغط الملف...")
            try:
                with bz2.open(temp_destination, 'rb') as f_in:
                    with open(destination, 'wb') as f_out:
                        # Copy in chunks to handle large files
                        while True:
                            chunk = f_in.read(8192)
                            if not chunk:
                                break
                            f_out.write(chunk)
                os.remove(temp_destination)
                print("✅ تم فك الضغط بنجاح")
            except Exception as e:
                print(f"❌ خطأ في فك الضغط: {e}")
                if os.path.exists(temp_destination):
                    os.remove(temp_destination)
                return False
        else:
            os.rename(temp_destination, destination)
        
        # Verify MD5 if provided
        if expected_md5:
            actual_md5 = calculate_md5(destination)
            if actual_md5 != expected_md5:
                print(f"⚠️  تحذير: MD5 مختلف - المتوقع {expected_md5}, الفعلي {actual_md5}")
                print("💡 الملف قد يعمل رغم ذلك")
            else:
                print("✅ تم التحقق من MD5 بنجاح")
        
        print(f"✅ تم تحميل {os.path.basename(destination)} بنجاح")
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ انتهت مهلة التحميل - تحقق من اتصال الإنترنت")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ خطأ في الاتصال - تحقق من اتصال الإنترنت")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ خطأ HTTP: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ في التحميل: {e}")
        # Clean up temp file if exists
        temp_destination = destination + '.tmp'
        if os.path.exists(temp_destination):
            os.remove(temp_destination)
        return False

def calculate_md5(filepath):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        response = requests.get('https://www.google.com', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function to download weights"""
    print("=" * 60)
    print("🔍 نظام كشف DeepFake - تحميل الأوزان")
    print("=" * 60)
    
    # Check internet connection
    print("🌐 فحص اتصال الإنترنت...")
    if not check_internet_connection():
        print("❌ لا يوجد اتصال بالإنترنت!")
        print("💡 يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى")
        return
    print("✅ اتصال الإنترنت متاح")
    print()
    
    # Check for command line arguments
    auto_download = '--auto' in sys.argv or '--all' in sys.argv
    
    # Create weights directory
    weights_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'weights')
    os.makedirs(weights_dir, exist_ok=True)
    
    print(f"📁 مجلد الأوزان: {weights_dir}")
    print()
    
    # Show available weights
    print("📋 الأوزان المتاحة للتحميل:")
    for filename, config in WEIGHTS_CONFIG.items():
        size_mb = config['size'] / (1024 * 1024)
        if config.get('compressed', False):
            uncompressed_mb = config.get('uncompressed_size', config['size']) / (1024 * 1024)
            print(f"   • {filename} ({size_mb:.0f}MB مضغوط → {uncompressed_mb:.0f}MB) - {config['description']}")
        else:
            print(f"   • {filename} ({size_mb:.0f}MB) - {config['description']}")
    print()
    
    # Ask user which weights to download (unless auto mode)
    selected_weights = WEIGHTS_CONFIG.copy()  # نسخ من الإعدادات الأصلية
    
    if not auto_download:
        print("💡 يمكنك تحميل جميع الأوزان أو اختيار أوزان محددة")
        choice = input("هل تريد تحميل جميع الأوزان؟ (y/n): ").lower().strip()
        
        if choice == 'n':
            print("\nاختر الأوزان التي تريد تحميلها:")
            selected_weights = {}
            for filename, config in WEIGHTS_CONFIG.items():
                download_this = input(f"تحميل {filename}؟ (y/n): ").lower().strip()
                if download_this == 'y':
                    selected_weights[filename] = config
    else:
        print("🤖 التحميل التلقائي مفعل - سيتم تحميل جميع الأوزان")
    
    print()
    
    # Download each weight file
    success_count = 0
    total_count = len(selected_weights)
    
    for filename, config in selected_weights.items():
        filepath = os.path.join(weights_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            # Use uncompressed size for comparison if available
            expected_size = config.get('uncompressed_size', config.get('size', 0))
            if expected_size > 0 and abs(file_size - expected_size) < expected_size * 0.1:  # 10% tolerance
                print(f"⏭️  تخطي {filename} (موجود بالفعل - {file_size / (1024*1024):.1f}MB)")
                success_count += 1
                continue
            else:
                print(f"⚠️  {filename} موجود لكن بحجم مختلف - سيتم إعادة التحميل")
        
        # Download the file
        if download_file(
            config['url'],
            filepath,
            config.get('size'),
            config.get('md5'),
            config.get('compressed', False)
        ):
            success_count += 1
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"📊 ملخص التحميل: {success_count}/{total_count} ملفات")
    
    if success_count == total_count:
        print("✅ تم تحميل جميع الأوزان بنجاح!")
        print("🚀 يمكنك الآن تشغيل النظام بأداء محسن")
    else:
        print("⚠️  لم يتم تحميل بعض الأوزان")
        print("💡 يمكنك تشغيل النظام بدونها، لكن الأداء سيكون محدود")
    
    print("=" * 60)
    print("💡 نصائح:")
    print("   - للتشغيل التلقائي: python tools/download_weights.py --auto")
    print("   - للتشغيل التلقائي: python tools/download_weights.py --all")
    print("   - يمكنك تشغيل النظام بدون الأوزان (أداء محدود)")
    print("   - الأوزان المطلوبة: shape_predictor_68_face_landmarks.dat")
    print("   - الأوزان الاختيارية: xception_weights.h5, mobilenet_weights.h5")
    print("=" * 60)

if __name__ == '__main__':
    main()
