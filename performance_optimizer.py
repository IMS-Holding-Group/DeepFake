#!/usr/bin/env python3
"""
DeepFake Detection System - Performance Optimizer
محسن الأداء لنظام كشف DeepFake
"""

import os
import sys
import psutil
import gc
import warnings
from contextlib import contextmanager

# Suppress warnings
warnings.filterwarnings('ignore')

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.original_settings = {}
    
    def optimize_system(self):
        """Apply system-wide optimizations"""
        print("🔧 تطبيق تحسينات الأداء...")
        
        # TensorFlow optimizations
        self.optimize_tensorflow()
        
        # Memory optimizations
        self.optimize_memory()
        
        # CPU optimizations
        self.optimize_cpu()
        
        print("✅ تم تطبيق تحسينات الأداء")
    
    def optimize_tensorflow(self):
        """Optimize TensorFlow settings"""
        try:
            import tensorflow as tf
            
            # Set TensorFlow to use only necessary memory
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                try:
                    # Enable memory growth
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print("✅ تم تحسين إعدادات GPU")
                except RuntimeError as e:
                    print(f"⚠️  تحذير GPU: {e}")
            
            # Set CPU optimizations
            tf.config.threading.set_inter_op_parallelism_threads(0)
            tf.config.threading.set_intra_op_parallelism_threads(0)
            
            # Disable TensorFlow logging
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
            
        except ImportError:
            print("⚠️  TensorFlow غير مثبت")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        # Force garbage collection
        gc.collect()
        
        # Set memory limits if possible
        try:
            # Get available memory
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            print(f"💾 الذاكرة المتاحة: {available_gb:.1f} GB")
            
            if available_gb < 2:
                print("⚠️  تحذير: ذاكرة قليلة، قد يؤثر على الأداء")
            
        except Exception as e:
            print(f"⚠️  تحذير: لا يمكن فحص الذاكرة: {e}")
    
    def optimize_cpu(self):
        """Optimize CPU usage"""
        try:
            # Get CPU count
            cpu_count = psutil.cpu_count()
            print(f"🖥️  عدد المعالجات: {cpu_count}")
            
            # Set process priority to normal
            current_process = psutil.Process()
            current_process.nice(0)
            
        except Exception as e:
            print(f"⚠️  تحذير: لا يمكن تحسين CPU: {e}")
    
    @contextmanager
    def memory_monitor(self):
        """Context manager to monitor memory usage"""
        try:
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            yield
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            print(f"💾 استهلاك الذاكرة: {memory_used:.1f} MB")
            
        except Exception as e:
            print(f"⚠️  تحذير: لا يمكن مراقبة الذاكرة: {e}")
            yield
    
    def cleanup_memory(self):
        """Clean up memory"""
        gc.collect()
        
        try:
            import tensorflow as tf
            tf.keras.backend.clear_session()
        except:
            pass

def get_system_info():
    """Get system information"""
    info = {
        'python_version': sys.version,
        'platform': sys.platform,
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
        'memory_available': psutil.virtual_memory().available / (1024**3),  # GB
    }
    
    return info

def print_system_info():
    """Print system information"""
    info = get_system_info()
    
    print("=" * 60)
    print("🖥️  معلومات النظام")
    print("=" * 60)
    print(f"Python: {info['python_version'].split()[0]}")
    print(f"النظام: {info['platform']}")
    print(f"المعالجات: {info['cpu_count']}")
    print(f"الذاكرة الإجمالية: {info['memory_total']:.1f} GB")
    print(f"الذاكرة المتاحة: {info['memory_available']:.1f} GB")
    print("=" * 60)

def main():
    """Main function"""
    print_system_info()
    
    optimizer = PerformanceOptimizer()
    optimizer.optimize_system()
    
    print("\n💡 نصائح لتحسين الأداء:")
    print("   - أغلق التطبيقات غير الضرورية")
    print("   - استخدم عدد إطارات أقل للفيديوهات الطويلة")
    print("   - قلل معدل أخذ العينات للفيديوهات عالية الدقة")
    print("   - تأكد من وجود مساحة كافية على القرص الصلب")

if __name__ == '__main__':
    main()
