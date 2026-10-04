"""
Digital forensics utilities for DeepFake detection
Includes noise analysis, metadata analysis, and steganography detection
"""

import cv2
import numpy as np
from PIL import Image, ExifTags
import os
import json
from datetime import datetime

class ForensicAnalyzer:
    """Digital forensics analyzer for DeepFake detection"""
    
    def __init__(self):
        """Initialize forensic analyzer"""
        pass
    
    def analyze_face_region(self, image, face_box):
        """Analyze a face region for forensic evidence"""
        try:
            x, y, w, h = face_box
            face_region = image[y:y+h, x:x+w]
            
            if face_region.size == 0:
                return {'real_score': 0.5, 'fake_score': 0.5, 'detail': 'Empty face region'}
            
            # Perform multiple forensic analyses
            noise_analysis = self.analyze_noise_patterns(face_region)
            compression_analysis = self.analyze_compression_artifacts(face_region)
            frequency_analysis = self.analyze_frequency_domain(face_region)
            
            # Combine results
            scores = [
                noise_analysis['real_score'],
                compression_analysis['real_score'],
                frequency_analysis['real_score']
            ]
            
            combined_score = np.mean(scores)
            
            # Generate explanation
            details = []
            if noise_analysis['anomaly_detected']:
                details.append("Inconsistent noise patterns detected")
            if compression_analysis['anomaly_detected']:
                details.append("Unusual compression artifacts found")
            if frequency_analysis['anomaly_detected']:
                details.append("Abnormal frequency domain characteristics")
            
            detail_text = "; ".join(details) if details else "No significant forensic anomalies detected"
            
            return {
                'real_score': combined_score,
                'fake_score': 1.0 - combined_score,
                'detail': detail_text,
                'components': {
                    'noise': noise_analysis,
                    'compression': compression_analysis,
                    'frequency': frequency_analysis
                }
            }
            
        except Exception as e:
            return {
                'real_score': 0.5,
                'fake_score': 0.5,
                'detail': f'Forensic analysis error: {str(e)}'
            }
    
    def analyze_noise_patterns(self, image):
        """Analyze noise patterns for inconsistencies"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate noise variance in different regions
            h, w = gray.shape
            regions = [
                gray[0:h//2, 0:w//2],      # Top-left
                gray[0:h//2, w//2:w],      # Top-right
                gray[h//2:h, 0:w//2],      # Bottom-left
                gray[h//2:h, w//2:w]       # Bottom-right
            ]
            
            noise_variances = []
            for region in regions:
                if region.size > 0:
                    # Apply high-pass filter to extract noise
                    kernel = np.array([[-1, -1, -1],
                                      [-1,  8, -1],
                                      [-1, -1, -1]])
                    noise = cv2.filter2D(region.astype(np.float32), -1, kernel)
                    variance = np.var(noise)
                    noise_variances.append(variance)
            
            if len(noise_variances) < 2:
                return {'real_score': 0.6, 'fake_score': 0.4, 'anomaly_detected': False}
            
            # Check for inconsistencies in noise patterns
            noise_std = np.std(noise_variances)
            noise_mean = np.mean(noise_variances)
            
            # More sophisticated noise analysis
            if noise_mean < 5:  # Very low noise (suspicious)
                anomaly_detected = True
                real_score = 0.2
            elif noise_std > noise_mean * 0.8:  # High variance
                anomaly_detected = True
                real_score = 0.3
            elif noise_mean > 50:  # Very high noise (suspicious)
                anomaly_detected = True
                real_score = 0.4
            else:  # Normal noise patterns
                anomaly_detected = False
                real_score = 0.8
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'anomaly_detected': anomaly_detected,
                'noise_variance': noise_variances,
                'noise_std': noise_std,
                'noise_mean': noise_mean
            }
            
        except Exception as e:
            return {'real_score': 0.6, 'fake_score': 0.4, 'anomaly_detected': False}
    
    def analyze_compression_artifacts(self, image):
        """Analyze compression artifacts"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply DCT to detect JPEG compression artifacts
            # Resize to 8x8 blocks for DCT analysis
            h, w = gray.shape
            block_size = 8
            
            # Ensure dimensions are multiples of block size
            new_h = (h // block_size) * block_size
            new_w = (w // block_size) * block_size
            gray = cv2.resize(gray, (new_w, new_h))
            
            # Split into 8x8 blocks and analyze
            artifacts_detected = 0
            total_blocks = 0
            
            for i in range(0, new_h, block_size):
                for j in range(0, new_w, block_size):
                    block = gray[i:i+block_size, j:j+block_size]
                    
                    # Apply DCT
                    dct_block = cv2.dct(block.astype(np.float32))
                    
                    # Check for quantization artifacts (high frequency components)
                    high_freq_energy = np.sum(np.abs(dct_block[4:, 4:]))
                    total_energy = np.sum(np.abs(dct_block))
                    
                    if total_energy > 0:
                        high_freq_ratio = high_freq_energy / total_energy
                        
                        # Unusually high high-frequency content suggests compression artifacts
                        if high_freq_ratio > 0.1:
                            artifacts_detected += 1
                    
                    total_blocks += 1
            
            # Calculate anomaly score
            artifact_ratio = artifacts_detected / total_blocks if total_blocks > 0 else 0
            
            if artifact_ratio > 0.3:
                anomaly_detected = True
                real_score = 0.4  # Lower score for high compression artifacts
            else:
                anomaly_detected = False
                real_score = 0.8  # Higher score for natural compression
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'anomaly_detected': anomaly_detected,
                'artifact_ratio': artifact_ratio
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'anomaly_detected': False}
    
    def analyze_frequency_domain(self, image):
        """Analyze frequency domain characteristics"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply FFT
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)
            
            # Analyze frequency distribution
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2
            
            # Divide into frequency bands
            low_freq = magnitude_spectrum[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4]
            mid_freq = magnitude_spectrum[center_h-h//2:center_h+h//2, center_w-w//2:center_w+w//2]
            high_freq = magnitude_spectrum
            
            # Calculate energy in each band
            low_energy = np.sum(low_freq)
            mid_energy = np.sum(mid_freq) - low_energy
            high_energy = np.sum(high_freq) - np.sum(mid_freq)
            
            total_energy = low_energy + mid_energy + high_energy
            
            if total_energy == 0:
                return {'real_score': 0.5, 'fake_score': 0.5, 'anomaly_detected': False}
            
            # Calculate energy ratios
            low_ratio = low_energy / total_energy
            mid_ratio = mid_energy / total_energy
            high_ratio = high_energy / total_energy
            
            # Check for unusual frequency distribution
            # Natural images typically have more energy in low frequencies
            if low_ratio < 0.3 or high_ratio > 0.4:
                anomaly_detected = True
                real_score = 0.4  # Lower score for unusual frequency distribution
            else:
                anomaly_detected = False
                real_score = 0.8  # Higher score for natural frequency distribution
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'anomaly_detected': anomaly_detected,
                'frequency_ratios': {
                    'low': low_ratio,
                    'mid': mid_ratio,
                    'high': high_ratio
                }
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'anomaly_detected': False}
    
    def analyze_metadata(self, file_path):
        """Analyze file metadata for inconsistencies"""
        try:
            metadata_info = {
                'real_score': 0.8,  # Default higher score for real images
                'fake_score': 0.2,
                'anomalies': [],
                'metadata': {}
            }
            
            # Check if file exists
            if not os.path.exists(file_path):
                return {'real_score': 0.5, 'fake_score': 0.5, 'detail': 'File not found'}
            
            # Get file stats
            stat_info = os.stat(file_path)
            metadata_info['metadata']['file_size'] = stat_info.st_size
            metadata_info['metadata']['modified_time'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            
            # Analyze image metadata if it's an image
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.bmp')):
                try:
                    with Image.open(file_path) as img:
                        # Get EXIF data
                        exif_data = img._getexif()
                        if exif_data:
                            exif_dict = {}
                            for tag_id, value in exif_data.items():
                                tag = ExifTags.TAGS.get(tag_id, tag_id)
                                exif_dict[tag] = value
                            
                            metadata_info['metadata']['exif'] = exif_dict
                            
                        # Check for editing software indicators
                        software_tags = ['Software', 'ProcessingSoftware', 'CreatorTool']
                        for tag in software_tags:
                            if tag in exif_dict:
                                software = str(exif_dict[tag]).lower()
                                if any(editor in software for editor in ['photoshop', 'gimp', 'paint', 'editor', 'deepfake', 'face swap']):
                                    metadata_info['anomalies'].append(f'Editing software detected: {exif_dict[tag]}')
                                    metadata_info['real_score'] = 0.3
                                    metadata_info['fake_score'] = 0.7
                                elif any(editor in software for editor in ['camera', 'phone', 'canon', 'nikon', 'sony']):
                                    metadata_info['real_score'] = 0.9
                                    metadata_info['fake_score'] = 0.1
                        
                        # Get basic image info
                        metadata_info['metadata']['format'] = img.format
                        metadata_info['metadata']['mode'] = img.mode
                        metadata_info['metadata']['size'] = img.size
                        
                        # Check for unusual image properties
                        if img.mode == 'RGBA' and file_path.lower().endswith('.jpg'):
                            metadata_info['anomalies'].append('RGBA mode in JPEG file')
                            metadata_info['real_score'] -= 0.2
                        
                        # Check image size
                        width, height = img.size
                        if width < 100 or height < 100:
                            metadata_info['anomalies'].append('Very small image size')
                            metadata_info['real_score'] -= 0.1
                        
                        if width > 10000 or height > 10000:
                            metadata_info['anomalies'].append('Unusually large image size')
                            metadata_info['real_score'] -= 0.1
                        
                except Exception as e:
                    metadata_info['anomalies'].append(f'Could not read image metadata: {str(e)}')
            
            # Ensure scores are within bounds
            metadata_info['real_score'] = max(0.1, min(0.9, metadata_info['real_score']))
            metadata_info['fake_score'] = 1.0 - metadata_info['real_score']
            
            # Generate detail text
            if metadata_info['anomalies']:
                detail_text = "; ".join(metadata_info['anomalies'])
            else:
                detail_text = "No metadata anomalies detected - image appears authentic"
            
            return {
                'real_score': metadata_info['real_score'],
                'fake_score': metadata_info['fake_score'],
                'detail': detail_text,
                'metadata': metadata_info['metadata']
            }
            
        except Exception as e:
            return {
                'real_score': 0.5,
                'fake_score': 0.5,
                'detail': f'Metadata analysis error: {str(e)}'
            }
    
    def detect_steganography(self, image):
        """Basic steganography detection"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Analyze LSB (Least Significant Bit) patterns
            # This is a simplified steganography detection
            
            # Extract LSBs
            lsb_plane = gray & 1
            
            # Calculate LSB randomness
            # Natural images have more random LSB patterns
            # Steganographic content may show patterns in LSBs
            
            # Simple randomness test using entropy
            unique, counts = np.unique(lsb_plane, return_counts=True)
            probabilities = counts / np.sum(counts)
            entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
            
            # Normalize entropy (0-1 scale)
            normalized_entropy = entropy / 1.0  # Max entropy for binary data is 1
            
            # Low entropy suggests possible steganography
            if normalized_entropy < 0.8:
                steganography_detected = True
                real_score = 0.3
            else:
                steganography_detected = False
                real_score = 0.8
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'steganography_detected': steganography_detected,
                'entropy': normalized_entropy
            }
            
        except Exception as e:
            return {
                'real_score': 0.5,
                'fake_score': 0.5,
                'steganography_detected': False
            }
    
    def analyze_color_consistency(self, image):
        """Analyze color consistency across the image"""
        try:
            if len(image.shape) != 3:
                return {'real_score': 0.5, 'fake_score': 0.5}
            
            # Convert to different color spaces
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Analyze color distribution
            bgr_std = np.std(image, axis=(0, 1))
            hsv_std = np.std(hsv, axis=(0, 1))
            lab_std = np.std(lab, axis=(0, 1))
            
            # Check for unusual color variations
            # High standard deviation in color channels might indicate manipulation
            avg_std = np.mean([np.mean(bgr_std), np.mean(hsv_std), np.mean(lab_std)])
            
            # Threshold for anomaly detection (can be tuned)
            if avg_std > 50:  # High color variation
                anomaly_detected = True
                real_score = 0.4
            else:
                anomaly_detected = False
                real_score = 0.8
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'anomaly_detected': anomaly_detected,
                'color_variation': avg_std
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5}
