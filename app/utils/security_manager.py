"""
Security and privacy management
إدارة الأمان والخصوصية
"""

import os
import hashlib
import secrets
import threading
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import cv2
import numpy as np
from PIL import Image
import magic

class SecurityManager:
    """Security and privacy management"""
    
    def __init__(self):
        """Initialize security manager"""
        self.encryption_key = self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.file_hashes = {}
        self.access_log = []
        self.lock = threading.Lock()
    
    def _generate_encryption_key(self):
        """Generate encryption key"""
        key_file = 'security/encryption.key'
        os.makedirs('security', exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_file(self, file_path, encrypted_path):
        """Encrypt file during processing"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.cipher.encrypt(file_data)
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            return encrypted_path
            
        except Exception as e:
            print(f"❌ File encryption failed: {e}")
            return None
    
    def decrypt_file(self, encrypted_path, decrypted_path):
        """Decrypt file for processing"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            return decrypted_path
            
        except Exception as e:
            print(f"❌ File decryption failed: {e}")
            return None
    
    def generate_file_hash(self, file_path):
        """Generate secure hash for file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"❌ Hash generation failed: {e}")
            return None
    
    def verify_file_integrity(self, file_path, expected_hash):
        """Verify file integrity"""
        try:
            actual_hash = self.generate_file_hash(file_path)
            return actual_hash == expected_hash
        except:
            return False
    
    def scan_for_malware(self, file_path):
        """Basic malware scanning"""
        try:
            # Check file type consistency
            file_type = magic.from_file(file_path, mime=True)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Basic type checking
            expected_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff',
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska'
            }
            
            if file_extension in expected_types:
                if file_type != expected_types[file_extension]:
                    return {
                        'safe': False,
                        'reason': 'File type mismatch',
                        'detected_type': file_type,
                        'expected_type': expected_types[file_extension]
                    }
            
            # Check for suspicious patterns
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB
                
                # Check for executable signatures
                executable_signatures = [b'MZ', b'\x7fELF', b'\xca\xfe\xba\xbe']
                for sig in executable_signatures:
                    if sig in content:
                        return {
                            'safe': False,
                            'reason': 'Executable file detected',
                            'signature': sig.hex()
                        }
            
            return {'safe': True, 'file_type': file_type}
            
        except Exception as e:
            return {'safe': False, 'reason': f'Scan error: {e}'}
    
    def log_access(self, action, file_path, user_ip=None):
        """Log file access"""
        try:
            with self.lock:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'action': action,
                    'file_path': file_path,
                    'user_ip': user_ip,
                    'file_hash': self.generate_file_hash(file_path) if os.path.exists(file_path) else None
                }
                self.access_log.append(log_entry)
                
                # Keep only last 1000 entries
                if len(self.access_log) > 1000:
                    self.access_log = self.access_log[-1000:]
                    
        except Exception as e:
            print(f"❌ Access logging failed: {e}")
    
    def get_access_log(self, limit=100):
        """Get access log"""
        return self.access_log[-limit:] if self.access_log else []

class FileCleanupManager:
    """Automatic file cleanup"""
    
    def __init__(self, cleanup_interval=3600):  # 1 hour
        """Initialize cleanup manager"""
        self.cleanup_interval = cleanup_interval
        self.cleanup_thread = None
        self.is_running = False
        self.file_lifetimes = {}
    
    def start_cleanup_service(self):
        """Start automatic cleanup service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        print("🧹 Cleanup service started")
    
    def stop_cleanup_service(self):
        """Stop cleanup service"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        print("🧹 Cleanup service stopped")
    
    def _cleanup_loop(self):
        """Cleanup loop"""
        while self.is_running:
            try:
                self._cleanup_files()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def _cleanup_files(self):
        """Clean up old files"""
        try:
            current_time = datetime.now()
            files_to_delete = []
            
            # Check uploads directory
            uploads_dir = 'uploads'
            if os.path.exists(uploads_dir):
                for filename in os.listdir(uploads_dir):
                    file_path = os.path.join(uploads_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if current_time - file_time > timedelta(hours=24):
                            files_to_delete.append(file_path)
            
            # Check analysis directory
            analysis_dir = 'static/analysis'
            if os.path.exists(analysis_dir):
                for filename in os.listdir(analysis_dir):
                    file_path = os.path.join(analysis_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if current_time - file_time > timedelta(hours=24):
                            files_to_delete.append(file_path)
            
            # Delete old files
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Could not delete {file_path}: {e}")
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old files")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def schedule_file_deletion(self, file_path, delay_hours=24):
        """Schedule file for deletion"""
        deletion_time = datetime.now() + timedelta(hours=delay_hours)
        self.file_lifetimes[file_path] = deletion_time
    
    def cancel_file_deletion(self, file_path):
        """Cancel scheduled file deletion"""
        if file_path in self.file_lifetimes:
            del self.file_lifetimes[file_path]

class PrivacyProtection:
    """Privacy protection utilities"""
    
    def __init__(self):
        """Initialize privacy protection"""
        pass
    
    def anonymize_image(self, image_path, output_path):
        """Anonymize image by removing faces"""
        try:
            from app.utils.image_utils import ImageProcessor
            
            image_processor = ImageProcessor()
            image = cv2.imread(image_path)
            
            # Detect faces
            faces = image_processor.detect_faces(image)
            
            # Blur faces
            for face in faces:
                x, y, w, h = face
                face_region = image[y:y+h, x:x+w]
                blurred_face = cv2.GaussianBlur(face_region, (99, 99), 30)
                image[y:y+h, x:x+w] = blurred_face
            
            # Save anonymized image
            cv2.imwrite(output_path, image)
            return output_path
            
        except Exception as e:
            print(f"❌ Image anonymization failed: {e}")
            return None
    
    def remove_metadata(self, file_path, output_path):
        """Remove metadata from file"""
        try:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                # Remove EXIF data
                image = Image.open(file_path)
                data = list(image.getdata())
                image_without_exif = Image.new(image.mode, image.size)
                image_without_exif.putdata(data)
                image_without_exif.save(output_path)
                return output_path
            
            return None
            
        except Exception as e:
            print(f"❌ Metadata removal failed: {e}")
            return None
    
    def generate_privacy_report(self, file_path):
        """Generate privacy report for file"""
        try:
            report = {
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'privacy_risks': [],
                'recommendations': []
            }
            
            # Check for metadata
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                with Image.open(file_path) as img:
                    if hasattr(img, '_getexif') and img._getexif():
                        report['privacy_risks'].append('EXIF metadata present')
                        report['recommendations'].append('Remove EXIF data before sharing')
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                report['privacy_risks'].append('Large file size')
                report['recommendations'].append('Consider compressing file')
            
            return report
            
        except Exception as e:
            return {'error': str(e)}

class DDOSProtection:
    """DDoS protection"""
    
    def __init__(self, max_requests_per_minute=60):
        """Initialize DDoS protection"""
        self.max_requests = max_requests_per_minute
        self.request_counts = {}
        self.blocked_ips = set()
        self.lock = threading.Lock()
    
    def check_rate_limit(self, client_ip):
        """Check if client exceeds rate limit"""
        try:
            with self.lock:
                current_time = time.time()
                
                # Clean old entries
                self.request_counts = {
                    ip: times for ip, times in self.request_counts.items()
                    if current_time - min(times) < 60  # Keep only last minute
                }
                
                # Check if IP is blocked
                if client_ip in self.blocked_ips:
                    return False
                
                # Add current request
                if client_ip not in self.request_counts:
                    self.request_counts[client_ip] = []
                
                self.request_counts[client_ip].append(current_time)
                
                # Check rate limit
                if len(self.request_counts[client_ip]) > self.max_requests:
                    self.blocked_ips.add(client_ip)
                    print(f"🚫 Blocked IP: {client_ip} (rate limit exceeded)")
                    return False
                
                return True
                
        except Exception as e:
            print(f"❌ Rate limit check failed: {e}")
            return True  # Allow request on error
    
    def unblock_ip(self, client_ip):
        """Unblock IP address"""
        with self.lock:
            self.blocked_ips.discard(client_ip)
            if client_ip in self.request_counts:
                del self.request_counts[client_ip]
    
    def get_blocked_ips(self):
        """Get list of blocked IPs"""
        return list(self.blocked_ips)

# Global instances
security_manager = SecurityManager()
cleanup_manager = FileCleanupManager()
privacy_protection = PrivacyProtection()
ddos_protection = DDOSProtection()
