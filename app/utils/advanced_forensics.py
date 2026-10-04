"""
Advanced digital forensics for DeepFake detection
تحليل جنائي رقمي متقدم لكشف DeepFake
"""

import cv2
import numpy as np
from scipy import fftpack
from scipy.signal import find_peaks
import librosa
from PIL import Image, ExifTags
import os

class AdvancedForensicAnalyzer:
    """Advanced forensic analysis for DeepFake detection"""
    
    def __init__(self):
        """Initialize advanced forensic analyzer"""
        pass
    
    def analyze_frequency_domain(self, image):
        """Advanced frequency domain analysis"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply 2D FFT
            f_transform = fftpack.fft2(gray)
            f_shift = fftpack.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)
            
            # Analyze frequency patterns
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2
            
            # Check for grid patterns (common in GAN-generated images)
            grid_score = self._detect_grid_patterns(magnitude_spectrum)
            
            # Check for frequency anomalies
            anomaly_score = self._detect_frequency_anomalies(magnitude_spectrum)
            
            # Check for compression artifacts
            compression_score = self._analyze_compression_artifacts(magnitude_spectrum)
            
            # Combine scores
            fake_score = (grid_score + anomaly_score + compression_score) / 3
            
            return {
                'fake_score': fake_score,
                'real_score': 1.0 - fake_score,
                'components': {
                    'grid_patterns': grid_score,
                    'frequency_anomalies': anomaly_score,
                    'compression_artifacts': compression_score
                }
            }
            
        except Exception as e:
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': str(e)}
    
    def _detect_grid_patterns(self, magnitude_spectrum):
        """Detect grid patterns in frequency domain"""
        try:
            # Look for regular patterns that indicate GAN generation
            h, w = magnitude_spectrum.shape
            
            # Check for horizontal and vertical lines
            horizontal_lines = np.sum(magnitude_spectrum[h//2-5:h//2+5, :])
            vertical_lines = np.sum(magnitude_spectrum[:, w//2-5:w//2+5])
            
            # Normalize
            total_energy = np.sum(magnitude_spectrum)
            grid_score = (horizontal_lines + vertical_lines) / (2 * total_energy)
            
            return min(grid_score * 10, 1.0)  # Scale to 0-1
            
        except:
            return 0.5
    
    def _detect_frequency_anomalies(self, magnitude_spectrum):
        """Detect frequency domain anomalies"""
        try:
            # Look for unusual frequency distributions
            h, w = magnitude_spectrum.shape
            
            # Divide into frequency bands
            low_freq = magnitude_spectrum[h//4:3*h//4, w//4:3*w//4]
            mid_freq = magnitude_spectrum[h//8:7*h//8, w//8:7*w//8]
            high_freq = magnitude_spectrum
            
            # Calculate energy distribution
            low_energy = np.sum(low_freq)
            mid_energy = np.sum(mid_freq) - low_energy
            high_energy = np.sum(high_freq) - np.sum(mid_freq)
            
            total_energy = low_energy + mid_energy + high_energy
            
            if total_energy == 0:
                return 0.5
            
            # Check for unusual distributions
            low_ratio = low_energy / total_energy
            high_ratio = high_energy / total_energy
            
            # Unusual high-frequency content suggests manipulation
            anomaly_score = max(0, high_ratio - 0.3) * 2
            
            return min(anomaly_score, 1.0)
            
        except:
            return 0.5
    
    def _analyze_compression_artifacts(self, magnitude_spectrum):
        """Analyze compression artifacts in frequency domain"""
        try:
            # Look for block-based compression artifacts
            h, w = magnitude_spectrum.shape
            
            # Check for 8x8 block patterns (JPEG compression)
            block_size = 8
            artifact_score = 0
            
            for i in range(0, h, block_size):
                for j in range(0, w, block_size):
                    block = magnitude_spectrum[i:i+block_size, j:j+block_size]
                    if block.size > 0:
                        # Check for high-frequency content in blocks
                        high_freq_energy = np.sum(block[4:, 4:])
                        total_block_energy = np.sum(block)
                        
                        if total_block_energy > 0:
                            ratio = high_freq_energy / total_block_energy
                            if ratio > 0.2:  # Unusual high-frequency content
                                artifact_score += ratio
            
            # Normalize
            num_blocks = (h // block_size) * (w // block_size)
            if num_blocks > 0:
                artifact_score /= num_blocks
            
            return min(artifact_score, 1.0)
            
        except:
            return 0.5
    
    def analyze_lighting_consistency(self, image):
        """Analyze lighting consistency across the image"""
        try:
            # Convert to LAB color space for better lighting analysis
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]  # Lightness channel
            
            # Divide image into regions
            h, w = l_channel.shape
            regions = [
                l_channel[0:h//2, 0:w//2],      # Top-left
                l_channel[0:h//2, w//2:w],      # Top-right
                l_channel[h//2:h, 0:w//2],      # Bottom-left
                l_channel[h//2:h, w//2:w]       # Bottom-right
            ]
            
            # Calculate lighting statistics for each region
            lighting_stats = []
            for region in regions:
                if region.size > 0:
                    stats = {
                        'mean': np.mean(region),
                        'std': np.std(region),
                        'min': np.min(region),
                        'max': np.max(region)
                    }
                    lighting_stats.append(stats)
            
            # Check for inconsistencies
            if len(lighting_stats) >= 2:
                means = [stat['mean'] for stat in lighting_stats]
                stds = [stat['std'] for stat in lighting_stats]
                
                # Calculate variance in lighting
                mean_variance = np.var(means)
                std_variance = np.var(stds)
                
                # High variance suggests inconsistent lighting (possible manipulation)
                inconsistency_score = (mean_variance + std_variance) / 200  # Normalize
                
                return {
                    'fake_score': min(inconsistency_score, 1.0),
                    'real_score': 1.0 - min(inconsistency_score, 1.0),
                    'lighting_variance': mean_variance,
                    'std_variance': std_variance
                }
            
            return {'fake_score': 0.5, 'real_score': 0.5}
            
        except Exception as e:
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': str(e)}
    
    def analyze_eye_blinking(self, video_frames):
        """Analyze eye blinking patterns in video"""
        try:
            from app.utils.image_utils import ImageProcessor
            
            image_processor = ImageProcessor()
            eye_states = []
            
            for frame in video_frames:
                # Detect faces
                faces = image_processor.detect_faces(frame)
                
                if len(faces) > 0:
                    # Analyze first face
                    face = faces[0]
                    x, y, w, h = face
                    face_region = frame[y:y+h, x:x+w]
                    
                    # Simple eye detection (would need more sophisticated method)
                    eye_state = self._detect_eye_state(face_region)
                    eye_states.append(eye_state)
            
            # Analyze blinking pattern
            if len(eye_states) > 10:
                blinking_score = self._analyze_blinking_pattern(eye_states)
                return {
                    'fake_score': blinking_score,
                    'real_score': 1.0 - blinking_score,
                    'blinking_analysis': 'completed'
                }
            
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': 'insufficient_frames'}
            
        except Exception as e:
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': str(e)}
    
    def _detect_eye_state(self, face_region):
        """Detect if eyes are open or closed"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Simple eye detection using Haar cascades
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(eyes) >= 2:
                return 'open'
            else:
                return 'closed'
                
        except:
            return 'unknown'
    
    def _analyze_blinking_pattern(self, eye_states):
        """Analyze blinking pattern for anomalies"""
        try:
            # Count transitions
            transitions = 0
            for i in range(1, len(eye_states)):
                if eye_states[i] != eye_states[i-1]:
                    transitions += 1
            
            # Calculate blinking rate
            blinking_rate = transitions / len(eye_states)
            
            # Unusual blinking patterns suggest manipulation
            if blinking_rate < 0.01 or blinking_rate > 0.1:  # Too few or too many blinks
                return 0.8  # High fake score
            
            return 0.2  # Low fake score
            
        except:
            return 0.5
    
    def analyze_audio_consistency(self, video_path):
        """Analyze audio consistency in video"""
        try:
            # Extract audio from video
            audio, sr = librosa.load(video_path, sr=None)
            
            # Analyze audio features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)[0]
            
            # Check for audio anomalies
            mfcc_variance = np.var(mfccs)
            spectral_variance = np.var(spectral_centroids)
            zcr_variance = np.var(zero_crossing_rate)
            
            # High variance suggests audio manipulation
            anomaly_score = (mfcc_variance + spectral_variance + zcr_variance) / 3
            
            # Normalize score
            normalized_score = min(anomaly_score / 1000, 1.0)
            
            return {
                'fake_score': normalized_score,
                'real_score': 1.0 - normalized_score,
                'audio_analysis': 'completed'
            }
            
        except Exception as e:
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': str(e)}
    
    def analyze_advanced_metadata(self, file_path):
        """Advanced metadata analysis"""
        try:
            metadata_info = {
                'fake_score': 0.3,  # Default low fake score
                'real_score': 0.7,
                'anomalies': [],
                'metadata': {}
            }
            
            # Get file stats
            stat_info = os.stat(file_path)
            metadata_info['metadata']['file_size'] = stat_info.st_size
            metadata_info['metadata']['modified_time'] = stat_info.st_mtime
            
            # Analyze image metadata
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                with Image.open(file_path) as img:
                    # Get EXIF data
                    exif_data = img._getexif()
                    if exif_data:
                        exif_dict = {}
                        for tag_id, value in exif_data.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            exif_dict[tag] = value
                        
                        metadata_info['metadata']['exif'] = exif_dict
                        
                        # Advanced EXIF analysis
                        self._analyze_exif_anomalies(exif_dict, metadata_info)
                    
                    # Analyze image properties
                    metadata_info['metadata']['format'] = img.format
                    metadata_info['metadata']['mode'] = img.mode
                    metadata_info['metadata']['size'] = img.size
                    
                    # Check for unusual properties
                    if img.mode == 'RGBA' and file_path.lower().endswith('.jpg'):
                        metadata_info['anomalies'].append('RGBA mode in JPEG file')
                        metadata_info['fake_score'] += 0.2
            
            # Generate final score
            if metadata_info['anomalies']:
                metadata_info['fake_score'] = min(metadata_info['fake_score'], 0.9)
                metadata_info['real_score'] = 1.0 - metadata_info['fake_score']
            
            return metadata_info
            
        except Exception as e:
            return {'fake_score': 0.5, 'real_score': 0.5, 'error': str(e)}
    
    def _analyze_exif_anomalies(self, exif_dict, metadata_info):
        """Analyze EXIF data for anomalies"""
        try:
            # Check for editing software
            software_tags = ['Software', 'ProcessingSoftware', 'CreatorTool', 'Artist']
            for tag in software_tags:
                if tag in exif_dict:
                    software = str(exif_dict[tag]).lower()
                    if any(editor in software for editor in ['photoshop', 'gimp', 'paint', 'editor', 'deepfake']):
                        metadata_info['anomalies'].append(f'Editing software detected: {exif_dict[tag]}')
                        metadata_info['fake_score'] += 0.3
            
            # Check for unusual camera settings
            if 'ISOSpeedRatings' in exif_dict:
                iso = exif_dict['ISOSpeedRatings']
                if iso > 6400 or iso < 50:  # Unusual ISO values
                    metadata_info['anomalies'].append(f'Unusual ISO value: {iso}')
                    metadata_info['fake_score'] += 0.1
            
            # Check for missing essential EXIF data
            essential_tags = ['DateTime', 'Make', 'Model']
            missing_tags = [tag for tag in essential_tags if tag not in exif_dict]
            if len(missing_tags) > 1:
                metadata_info['anomalies'].append(f'Missing EXIF data: {missing_tags}')
                metadata_info['fake_score'] += 0.2
                
        except:
            pass
