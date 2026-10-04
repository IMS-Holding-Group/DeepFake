#!/usr/bin/env python3
"""
Lighting and Shadow Consistency Analyzer
محلل تناسق الإضاءة والظلال للكشف عن DeepFake
"""

import cv2
import numpy as np
from scipy import ndimage
import math

class LightingAnalyzer:
    """Analyze lighting and shadow consistency for DeepFake detection"""
    
    def __init__(self):
        self.face_landmarks = None
        
    def analyze_lighting_consistency(self, image, face_bbox=None):
        """Analyze lighting consistency in image"""
        try:
            if face_bbox is not None:
                x, y, w, h = face_bbox
                face_region = image[y:y+h, x:x+w]
            else:
                face_region = image
            
            # Analyze lighting patterns
            lighting_analysis = {
                'lighting_direction': self._analyze_lighting_direction(face_region),
                'shadow_consistency': self._analyze_shadow_consistency(face_region),
                'lighting_intensity': self._analyze_lighting_intensity(face_region),
                'color_temperature': self._analyze_color_temperature(face_region),
                'anomalies': []
            }
            
            # Calculate authenticity score
            real_score = self._calculate_lighting_score(lighting_analysis)
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'lighting_analysis': lighting_analysis
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'error': str(e)}
    
    def _analyze_lighting_direction(self, face_region):
        """Analyze lighting direction consistency"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate gradients
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate gradient magnitude and direction
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            direction = np.arctan2(grad_y, grad_x)
            
            # Analyze lighting direction consistency
            # Natural lighting should have consistent direction
            direction_std = np.std(direction[magnitude > np.percentile(magnitude, 50)])
            
            # Calculate lighting direction score
            consistency_score = 1.0 - min(1.0, direction_std / (np.pi / 2))
            
            return {
                'consistency_score': consistency_score,
                'direction_std': direction_std,
                'dominant_direction': np.mean(direction[magnitude > np.percentile(magnitude, 50)])
            }
            
        except Exception as e:
            return {'consistency_score': 0.5, 'error': str(e)}
    
    def _analyze_shadow_consistency(self, face_region):
        """Analyze shadow consistency and patterns"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to smooth the image
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Calculate local mean and standard deviation
            local_mean = cv2.blur(blurred, (15, 15))
            local_std = cv2.sqrt(cv2.blur((blurred - local_mean)**2, (15, 15)))
            
            # Identify shadow regions (low intensity, low variance)
            shadow_mask = (blurred < local_mean - 0.5 * local_std) & (local_std < np.percentile(local_std, 30))
            
            # Analyze shadow patterns
            shadow_regions = np.where(shadow_mask)
            
            if len(shadow_regions[0]) == 0:
                return {'consistency_score': 0.5, 'shadow_coverage': 0}
            
            # Calculate shadow coverage
            shadow_coverage = np.sum(shadow_mask) / shadow_mask.size
            
            # Analyze shadow distribution
            shadow_y = shadow_regions[0]
            shadow_x = shadow_regions[1]
            
            # Check for natural shadow distribution
            # Natural shadows should be distributed somewhat evenly
            y_std = np.std(shadow_y)
            x_std = np.std(shadow_x)
            
            # Calculate consistency score
            consistency_score = 1.0 - min(1.0, abs(y_std - x_std) / max(y_std, x_std, 1))
            
            return {
                'consistency_score': consistency_score,
                'shadow_coverage': shadow_coverage,
                'shadow_distribution': {
                    'y_std': y_std,
                    'x_std': x_std
                }
            }
            
        except Exception as e:
            return {'consistency_score': 0.5, 'error': str(e)}
    
    def _analyze_lighting_intensity(self, face_region):
        """Analyze lighting intensity distribution"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate intensity distribution
            intensity_hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # Analyze intensity distribution
            # Natural lighting should have smooth intensity distribution
            intensity_std = np.std(intensity_hist)
            intensity_mean = np.mean(intensity_hist)
            
            # Check for unnatural intensity spikes
            spikes = np.sum(intensity_hist > intensity_mean + 2 * intensity_std)
            
            # Calculate smoothness score
            smoothness_score = 1.0 - min(1.0, spikes / 10)
            
            # Analyze intensity range
            intensity_range = np.max(gray) - np.min(gray)
            range_score = min(1.0, intensity_range / 100)
            
            return {
                'smoothness_score': smoothness_score,
                'range_score': range_score,
                'intensity_range': intensity_range,
                'spikes_detected': spikes
            }
            
        except Exception as e:
            return {'smoothness_score': 0.5, 'error': str(e)}
    
    def _analyze_color_temperature(self, face_region):
        """Analyze color temperature consistency"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(face_region, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Analyze color temperature (a and b channels)
            a_std = np.std(a)
            b_std = np.std(b)
            
            # Natural lighting should have consistent color temperature
            color_consistency = 1.0 - min(1.0, (a_std + b_std) / 200)
            
            # Analyze color temperature distribution
            a_mean = np.mean(a)
            b_mean = np.mean(b)
            
            # Calculate color temperature score
            temp_score = 1.0 - min(1.0, abs(a_mean - 128) / 128 + abs(b_mean - 128) / 128)
            
            return {
                'consistency_score': color_consistency,
                'temperature_score': temp_score,
                'a_channel_stats': {'mean': a_mean, 'std': a_std},
                'b_channel_stats': {'mean': b_mean, 'std': b_std}
            }
            
        except Exception as e:
            return {'consistency_score': 0.5, 'error': str(e)}
    
    def _calculate_lighting_score(self, lighting_analysis):
        """Calculate overall lighting authenticity score"""
        score = 0.7  # Base score
        
        # Weight different lighting aspects
        weights = {
            'lighting_direction': 0.3,
            'shadow_consistency': 0.25,
            'lighting_intensity': 0.25,
            'color_temperature': 0.2
        }
        
        # Calculate weighted score
        if 'lighting_direction' in lighting_analysis:
            direction_score = lighting_analysis['lighting_direction'].get('consistency_score', 0.5)
            score += weights['lighting_direction'] * (direction_score - 0.5)
        
        if 'shadow_consistency' in lighting_analysis:
            shadow_score = lighting_analysis['shadow_consistency'].get('consistency_score', 0.5)
            score += weights['shadow_consistency'] * (shadow_score - 0.5)
        
        if 'lighting_intensity' in lighting_analysis:
            intensity_score = (
                lighting_analysis['lighting_intensity'].get('smoothness_score', 0.5) +
                lighting_analysis['lighting_intensity'].get('range_score', 0.5)
            ) / 2
            score += weights['lighting_intensity'] * (intensity_score - 0.5)
        
        if 'color_temperature' in lighting_analysis:
            color_score = (
                lighting_analysis['color_temperature'].get('consistency_score', 0.5) +
                lighting_analysis['color_temperature'].get('temperature_score', 0.5)
            ) / 2
            score += weights['color_temperature'] * (color_score - 0.5)
        
        # Penalize for anomalies
        score -= len(lighting_analysis.get('anomalies', [])) * 0.1
        
        # Ensure score is within bounds
        return max(0.1, min(0.9, score))
    
    def analyze_video_lighting_consistency(self, video_path, max_frames=50):
        """Analyze lighting consistency across video frames"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'real_score': 0.5, 'fake_score': 0.5, 'error': 'Could not open video'}
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames_to_analyze = min(max_frames, frame_count)
            frame_interval = max(1, frame_count // frames_to_analyze)
            
            lighting_scores = []
            frame_idx = 0
            
            while frame_idx < frames_to_analyze:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % frame_interval == 0:
                    # Analyze lighting in this frame
                    result = self.analyze_lighting_consistency(frame)
                    if 'real_score' in result:
                        lighting_scores.append(result['real_score'])
                
                frame_idx += 1
            
            cap.release()
            
            if len(lighting_scores) == 0:
                return {'real_score': 0.5, 'fake_score': 0.5, 'error': 'No frames analyzed'}
            
            # Analyze lighting consistency across frames
            lighting_std = np.std(lighting_scores)
            lighting_mean = np.mean(lighting_scores)
            
            # High variance in lighting scores suggests manipulation
            consistency_score = 1.0 - min(1.0, lighting_std / 0.2)
            
            # Calculate final score
            final_score = 0.7 * lighting_mean + 0.3 * consistency_score
            
            return {
                'real_score': final_score,
                'fake_score': 1.0 - final_score,
                'lighting_consistency': {
                    'mean_score': lighting_mean,
                    'std_score': lighting_std,
                    'consistency_score': consistency_score,
                    'frames_analyzed': len(lighting_scores)
                }
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'error': str(e)}
