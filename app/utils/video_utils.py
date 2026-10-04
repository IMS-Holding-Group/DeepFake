"""
Video processing utilities for DeepFake detection
"""

import cv2
import numpy as np
import imageio
from tqdm import tqdm
import os

class VideoProcessor:
    """Video processing utilities for frame extraction and analysis"""
    
    def __init__(self):
        """Initialize video processor"""
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    def extract_frames(self, video_path, max_frames=30, sample_rate=1):
        """Extract frames from video for analysis"""
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Calculate frame sampling
            if total_frames <= max_frames:
                frame_indices = list(range(0, total_frames, sample_rate))
            else:
                # Sample frames evenly across the video
                step = max(1, total_frames // max_frames)
                frame_indices = list(range(0, total_frames, step))[:max_frames]
            
            # Extract frames
            frames = []
            for frame_idx in tqdm(frame_indices, desc="Extracting frames"):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    frames.append(frame)
                else:
                    break
            
            cap.release()
            
            return frames
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return []
    
    def extract_frames_uniform(self, video_path, num_frames=30):
        """Extract frames uniformly distributed across video duration"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                cap.release()
                return []
            
            # Calculate frame indices for uniform distribution
            if total_frames <= num_frames:
                frame_indices = list(range(total_frames))
            else:
                frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            
            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    frames.append(frame)
            
            cap.release()
            return frames
            
        except Exception as e:
            print(f"Error extracting uniform frames: {e}")
            return []
    
    def get_video_info(self, video_path):
        """Get video information"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            info = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': 0,
                'codec': None
            }
            
            if info['fps'] > 0:
                info['duration'] = info['frame_count'] / info['fps']
            
            # Try to get codec info
            try:
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                info['codec'] = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            except:
                pass
            
            cap.release()
            return info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def extract_face_frames(self, video_path, max_frames=30):
        """Extract frames containing faces"""
        from app.utils.image_utils import ImageProcessor
        
        try:
            # Extract all frames first
            all_frames = self.extract_frames(video_path, max_frames * 2)  # Get more frames to filter
            
            if not all_frames:
                return []
            
            # Initialize face detector
            image_processor = ImageProcessor()
            
            # Filter frames with faces
            face_frames = []
            for frame in all_frames:
                faces = image_processor.detect_faces(frame)
                if len(faces) > 0:
                    face_frames.append(frame)
                
                if len(face_frames) >= max_frames:
                    break
            
            return face_frames
            
        except Exception as e:
            print(f"Error extracting face frames: {e}")
            return []
    
    def create_frame_montage(self, frames, cols=3, max_frames=9):
        """Create a montage of frames"""
        try:
            if not frames:
                return None
            
            # Limit number of frames
            frames = frames[:max_frames]
            
            # Get frame dimensions
            h, w = frames[0].shape[:2]
            
            # Calculate grid dimensions
            rows = (len(frames) + cols - 1) // cols
            
            # Create montage
            montage = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
            
            for i, frame in enumerate(frames):
                row = i // cols
                col = i % cols
                
                # Resize frame if necessary
                if frame.shape[:2] != (h, w):
                    frame = cv2.resize(frame, (w, h))
                
                montage[row*h:(row+1)*h, col*w:(col+1)*w] = frame
            
            return montage
            
        except Exception as e:
            print(f"Error creating frame montage: {e}")
            return None
    
    def analyze_video_quality(self, video_path):
        """Analyze video quality metrics"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            # Get a few frames for analysis
            frames = []
            for i in range(10):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                else:
                    break
            
            cap.release()
            
            if not frames:
                return None
            
            # Calculate quality metrics
            quality_metrics = {
                'brightness': [],
                'contrast': [],
                'sharpness': []
            }
            
            for frame in frames:
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Brightness (mean pixel value)
                brightness = np.mean(gray)
                quality_metrics['brightness'].append(brightness)
                
                # Contrast (standard deviation)
                contrast = np.std(gray)
                quality_metrics['contrast'].append(contrast)
                
                # Sharpness (Laplacian variance)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                quality_metrics['sharpness'].append(laplacian_var)
            
            # Calculate averages
            result = {
                'avg_brightness': np.mean(quality_metrics['brightness']),
                'avg_contrast': np.mean(quality_metrics['contrast']),
                'avg_sharpness': np.mean(quality_metrics['sharpness']),
                'brightness_std': np.std(quality_metrics['brightness']),
                'contrast_std': np.std(quality_metrics['contrast']),
                'sharpness_std': np.std(quality_metrics['sharpness'])
            }
            
            return result
            
        except Exception as e:
            print(f"Error analyzing video quality: {e}")
            return None
    
    def detect_scene_changes(self, video_path, threshold=0.3):
        """Detect scene changes in video"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return []
            
            scene_changes = []
            prev_frame = None
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_score = np.mean(diff) / 255.0
                    
                    if diff_score > threshold:
                        scene_changes.append(frame_count)
                
                prev_frame = gray
                frame_count += 1
            
            cap.release()
            return scene_changes
            
        except Exception as e:
            print(f"Error detecting scene changes: {e}")
            return []
    
    def compress_video(self, input_path, output_path, quality=23):
        """Compress video for faster processing"""
        try:
            # Use FFmpeg for compression (if available)
            import subprocess
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-crf', str(quality),
                '-c:a', 'aac', '-b:a', '128k',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return output_path
            else:
                print(f"FFmpeg compression failed: {result.stderr}")
                return input_path
                
        except Exception as e:
            print(f"Error compressing video: {e}")
            return input_path
