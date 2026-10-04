"""
Performance optimization utilities
أدوات تحسين الأداء
"""

import os
import gc
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import numpy as np
import cv2
from functools import lru_cache
import tensorflow as tf

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        """Initialize performance optimizer"""
        self.gpu_available = self._check_gpu_availability()
        self.cpu_count = psutil.cpu_count()
        self.memory_info = psutil.virtual_memory()
        self.optimize_tensorflow()
    
    def _check_gpu_availability(self):
        """Check if GPU is available"""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            return len(gpus) > 0
        except:
            return False
    
    def optimize_tensorflow(self):
        """Optimize TensorFlow settings"""
        try:
            # Set memory growth for GPU
            if self.gpu_available:
                gpus = tf.config.experimental.list_physical_devices('GPU')
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
            
            # Optimize CPU usage
            tf.config.threading.set_inter_op_parallelism_threads(self.cpu_count)
            tf.config.threading.set_intra_op_parallelism_threads(self.cpu_count)
            
            # Enable mixed precision for better performance
            tf.config.optimizer.set_jit(True)
            
            print(f"✅ TensorFlow optimized - GPU: {self.gpu_available}, CPU cores: {self.cpu_count}")
            
        except Exception as e:
            print(f"⚠️ TensorFlow optimization failed: {e}")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear TensorFlow session
            tf.keras.backend.clear_session()
            
            # Get memory info
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            print(f"💾 Memory optimized - Available: {available_gb:.1f}GB")
            
            return available_gb
            
        except Exception as e:
            print(f"⚠️ Memory optimization failed: {e}")
            return 0
    
    def compress_video(self, input_path, output_path, quality=23):
        """Compress video for faster processing"""
        try:
            import subprocess
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-crf', str(quality),
                '-c:a', 'aac', '-b:a', '128k',
                '-preset', 'fast',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Get file sizes
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                print(f"📹 Video compressed - Ratio: {compression_ratio:.1f}%")
                return output_path
            else:
                print(f"⚠️ Video compression failed: {result.stderr}")
                return input_path
                
        except Exception as e:
            print(f"⚠️ Video compression error: {e}")
            return input_path
    
    def resize_image_optimized(self, image, max_size=1024):
        """Optimized image resizing"""
        try:
            h, w = image.shape[:2]
            
            if max(h, w) <= max_size:
                return image
            
            # Calculate optimal size
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Use optimized interpolation
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return resized
            
        except Exception as e:
            print(f"⚠️ Image resize error: {e}")
            return image

class ParallelProcessor:
    """Parallel processing utilities"""
    
    def __init__(self, max_workers=None):
        """Initialize parallel processor"""
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def process_frames_parallel(self, frames, process_func, chunk_size=10):
        """Process video frames in parallel"""
        try:
            # Split frames into chunks
            frame_chunks = [frames[i:i+chunk_size] for i in range(0, len(frames), chunk_size)]
            
            # Process chunks in parallel
            futures = []
            for chunk in frame_chunks:
                future = self.executor.submit(self._process_chunk, chunk, process_func)
                futures.append(future)
            
            # Collect results
            results = []
            for future in futures:
                chunk_results = future.result()
                results.extend(chunk_results)
            
            return results
            
        except Exception as e:
            print(f"⚠️ Parallel processing error: {e}")
            return []
    
    def _process_chunk(self, chunk, process_func):
        """Process a chunk of frames"""
        results = []
        for frame in chunk:
            try:
                result = process_func(frame)
                results.append(result)
            except Exception as e:
                print(f"⚠️ Frame processing error: {e}")
                results.append(None)
        return results
    
    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=True)

class CacheManager:
    """Cache management for models and results"""
    
    def __init__(self, max_size=100):
        """Initialize cache manager"""
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, key):
        """Get item from cache"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key, value):
        """Set item in cache"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_times.clear()

class ModelLoader:
    """Lazy loading for models"""
    
    def __init__(self):
        """Initialize model loader"""
        self.models = {}
        self.loading = {}
        self.lock = threading.Lock()
    
    def get_model(self, model_name, loader_func):
        """Get model with lazy loading"""
        if model_name in self.models:
            return self.models[model_name]
        
        with self.lock:
            # Double-check after acquiring lock
            if model_name in self.models:
                return self.models[model_name]
            
            # Check if already loading
            if model_name in self.loading:
                # Wait for loading to complete
                while model_name in self.loading:
                    time.sleep(0.1)
                return self.models.get(model_name)
            
            # Start loading
            self.loading[model_name] = True
            
            try:
                print(f"🔄 Loading model: {model_name}")
                model = loader_func()
                self.models[model_name] = model
                print(f"✅ Model loaded: {model_name}")
                return model
            except Exception as e:
                print(f"❌ Model loading failed: {model_name} - {e}")
                return None
            finally:
                del self.loading[model_name]

class PerformanceMonitor:
    """Performance monitoring"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {}
        self.start_time = time.time()
    
    def start_operation(self, operation_name):
        """Start monitoring an operation"""
        self.metrics[operation_name] = {
            'start_time': time.time(),
            'end_time': None,
            'duration': None
        }
    
    def end_operation(self, operation_name):
        """End monitoring an operation"""
        if operation_name in self.metrics:
            end_time = time.time()
            self.metrics[operation_name]['end_time'] = end_time
            self.metrics[operation_name]['duration'] = end_time - self.metrics[operation_name]['start_time']
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.metrics
    
    def print_summary(self):
        """Print performance summary"""
        print("\n📊 Performance Summary:")
        print("=" * 50)
        
        total_time = time.time() - self.start_time
        print(f"Total time: {total_time:.2f}s")
        
        for operation, metrics in self.metrics.items():
            if metrics['duration']:
                print(f"{operation}: {metrics['duration']:.2f}s")
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"Memory usage: {memory.percent:.1f}%")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU usage: {cpu_percent:.1f}%")
        
        print("=" * 50)

# Global instances
performance_optimizer = PerformanceOptimizer()
parallel_processor = ParallelProcessor()
cache_manager = CacheManager()
model_loader = ModelLoader()
performance_monitor = PerformanceMonitor()
