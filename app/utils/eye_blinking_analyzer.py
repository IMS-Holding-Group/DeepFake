#!/usr/bin/env python3
"""
Eye Blinking Pattern Analyzer
محلل أنماط رمش العين للكشف عن DeepFake
"""

import cv2
import numpy as np
from scipy import signal
import math

class EyeBlinkingAnalyzer:
    """Analyze eye blinking patterns for DeepFake detection"""
    
    def __init__(self):
        self.eye_ar_threshold = 0.25  # Eye aspect ratio threshold for blinking
        self.blink_frames_threshold = 3  # Frames to consider a blink
        
    def analyze_blinking_pattern(self, video_path, max_frames=100):
        """Analyze blinking patterns in video"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'real_score': 0.5, 'fake_score': 0.5, 'error': 'Could not open video'}
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Limit frames for analysis
            frames_to_analyze = min(max_frames, frame_count)
            frame_interval = max(1, frame_count // frames_to_analyze)
            
            eye_ratios = []
            frame_numbers = []
            
            frame_idx = 0
            while frame_idx < frames_to_analyze:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames if needed
                if frame_idx % frame_interval != 0:
                    frame_idx += 1
                    continue
                
                # Detect face and extract eye landmarks
                eye_ratio = self._extract_eye_aspect_ratio(frame)
                if eye_ratio is not None:
                    eye_ratios.append(eye_ratio)
                    frame_numbers.append(frame_idx)
                
                frame_idx += 1
            
            cap.release()
            
            if len(eye_ratios) < 10:
                return {'real_score': 0.5, 'fake_score': 0.5, 'error': 'Not enough frames with eyes detected'}
            
            # Analyze blinking patterns
            return self._analyze_blinking_consistency(eye_ratios, frame_numbers, fps)
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'error': str(e)}
    
    def _extract_eye_aspect_ratio(self, frame):
        """Extract eye aspect ratio from frame"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use Haar cascade for face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return None
            
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Use Haar cascade for eye detection
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(face_roi, 1.1, 3)
            
            if len(eyes) < 2:
                return None
            
            # Calculate eye aspect ratio for both eyes
            eye_ratios = []
            for (ex, ey, ew, eh) in eyes:
                # Calculate eye aspect ratio (EAR)
                # EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
                # Simplified version using bounding box
                ear = (ew + eh) / (2.0 * max(ew, eh))
                eye_ratios.append(ear)
            
            # Return average eye aspect ratio
            return np.mean(eye_ratios) if eye_ratios else None
            
        except Exception as e:
            return None
    
    def _analyze_blinking_consistency(self, eye_ratios, frame_numbers, fps):
        """Analyze blinking consistency and patterns"""
        try:
            eye_ratios = np.array(eye_ratios)
            frame_numbers = np.array(frame_numbers)
            
            # Detect blinks (low eye aspect ratio)
            blinks = eye_ratios < self.eye_ar_threshold
            
            # Find blink events
            blink_events = []
            in_blink = False
            blink_start = 0
            
            for i, is_blink in enumerate(blinks):
                if is_blink and not in_blink:
                    # Start of blink
                    in_blink = True
                    blink_start = i
                elif not is_blink and in_blink:
                    # End of blink
                    in_blink = False
                    blink_duration = i - blink_start
                    if blink_duration >= self.blink_frames_threshold:
                        blink_events.append({
                            'start_frame': blink_start,
                            'end_frame': i,
                            'duration': blink_duration,
                            'start_time': frame_numbers[blink_start] / fps if fps > 0 else 0,
                            'end_time': frame_numbers[i] / fps if fps > 0 else 0
                        })
            
            # Analyze blinking patterns
            analysis = self._analyze_blink_patterns(blink_events, len(eye_ratios), fps)
            
            # Calculate authenticity score
            real_score = self._calculate_authenticity_score(analysis)
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'blink_analysis': analysis,
                'total_blinks': len(blink_events),
                'eye_ratios_stats': {
                    'mean': float(np.mean(eye_ratios)),
                    'std': float(np.std(eye_ratios)),
                    'min': float(np.min(eye_ratios)),
                    'max': float(np.max(eye_ratios))
                }
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'error': str(e)}
    
    def _analyze_blink_patterns(self, blink_events, total_frames, fps):
        """Analyze blinking patterns for authenticity"""
        analysis = {
            'blink_rate': 0,
            'blink_regularity': 0,
            'blink_duration_consistency': 0,
            'anomalies': []
        }
        
        if len(blink_events) == 0:
            analysis['anomalies'].append('No blinks detected - possible DeepFake')
            return analysis
        
        # Calculate blink rate (blinks per minute)
        if fps > 0 and total_frames > 0:
            video_duration = total_frames / fps
            analysis['blink_rate'] = (len(blink_events) / video_duration) * 60
        
        # Analyze blink regularity
        if len(blink_events) > 1:
            intervals = []
            for i in range(1, len(blink_events)):
                interval = blink_events[i]['start_time'] - blink_events[i-1]['end_time']
                intervals.append(interval)
            
            if intervals:
                interval_std = np.std(intervals)
                interval_mean = np.mean(intervals)
                
                # Regular blinking has low standard deviation
                if interval_mean > 0:
                    analysis['blink_regularity'] = 1.0 - min(1.0, interval_std / interval_mean)
                
                # Check for unnatural patterns
                if interval_std > interval_mean * 0.5:
                    analysis['anomalies'].append('Irregular blinking pattern detected')
        
        # Analyze blink duration consistency
        if len(blink_events) > 1:
            durations = [event['duration'] for event in blink_events]
            duration_std = np.std(durations)
            duration_mean = np.mean(durations)
            
            if duration_mean > 0:
                analysis['blink_duration_consistency'] = 1.0 - min(1.0, duration_std / duration_mean)
            
            # Check for unnatural blink durations
            if duration_mean < 2 or duration_mean > 20:
                analysis['anomalies'].append('Unnatural blink duration detected')
        
        # Check for realistic blink rate
        if analysis['blink_rate'] < 5 or analysis['blink_rate'] > 30:
            analysis['anomalies'].append('Unrealistic blink rate detected')
        
        return analysis
    
    def _calculate_authenticity_score(self, analysis):
        """Calculate authenticity score based on blinking analysis"""
        score = 0.7  # Base score
        
        # Penalize for anomalies
        score -= len(analysis['anomalies']) * 0.2
        
        # Reward for natural blinking patterns
        if analysis['blink_regularity'] > 0.7:
            score += 0.1
        
        if analysis['blink_duration_consistency'] > 0.7:
            score += 0.1
        
        # Check for realistic blink rate
        if 10 <= analysis['blink_rate'] <= 20:
            score += 0.1
        
        # Ensure score is within bounds
        return max(0.1, min(0.9, score))
