"""
Ensemble DeepFake detector combining multiple models and forensic analysis
"""

import numpy as np
import cv2
import os
from datetime import datetime
from app.models.xception_detector import XceptionDetector
from app.utils.image_utils import ImageProcessor
from app.utils.video_utils import VideoProcessor
from app.utils.forensics import ForensicAnalyzer
from app.utils.eye_blinking_analyzer import EyeBlinkingAnalyzer
from app.utils.lighting_analyzer import LightingAnalyzer
from app.utils.audio_analyzer import AudioAnalyzer

class DeepFakeDetector:
    """Main ensemble detector combining multiple analysis methods"""
    
    def __init__(self):
        """Initialize the ensemble detector"""
        self.xception_detector = XceptionDetector()
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()
        self.forensic_analyzer = ForensicAnalyzer()
        self.eye_blinking_analyzer = EyeBlinkingAnalyzer()
        self.lighting_analyzer = LightingAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        
        # Ensemble weights (can be tuned based on performance)
        self.model_weights = {
            'xception': 0.6,
            'forensics': 0.3,
            'metadata': 0.1
        }
    
    def analyze_image(self, image_path):
        """Analyze a single image for DeepFake detection"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not load image")
            
            # Enhance image quality
            image = self.image_processor.enhance_image_quality(image)
            
            # Detect faces
            faces = self.image_processor.detect_faces(image)
            
            if len(faces) == 0:
                # Analyze entire image if no faces detected
                return self._analyze_full_image(image, image_path)
            
            # Analyze each face
            face_results = []
            for i, face in enumerate(faces):
                # Xception analysis
                xception_result = self.xception_detector.analyze_face_region(image, face)
                
                # Forensic analysis
                forensic_result = self.forensic_analyzer.analyze_face_region(image, face)
                
                # Metadata analysis
                metadata_result = self.forensic_analyzer.analyze_metadata(image_path)
                
            # Add image quality analysis
            quality_score = self._analyze_image_quality(image)
            
            # Combine results with quality score
            combined_score = self._combine_scores([
                xception_result['real_score'],
                forensic_result['real_score'],
                metadata_result['real_score'],
                quality_score
            ])
            
            face_results.append({
                'face_id': i,
                'bbox': face.tolist(),
                'real_score': combined_score,
                'fake_score': 1.0 - combined_score,
                'components': {
                    'xception': xception_result,
                    'forensics': forensic_result,
                    'metadata': metadata_result
                }
            })
            
            # Aggregate results across all faces
            if len(face_results) == 1:
                final_result = face_results[0]
            else:
                # Average scores across all faces
                avg_real_score = np.mean([r['real_score'] for r in face_results])
                final_result = {
                    'real_score': avg_real_score,
                    'fake_score': 1.0 - avg_real_score,
                    'face_count': len(face_results)
                }
            
            # Generate explanations
            explanations = self._generate_explanations(face_results)
            
            # Create artifacts
            artifacts = self._create_artifacts(image_path, image, faces, face_results)
            
            # Add lighting analysis for images with faces
            lighting_result = self.lighting_analyzer.analyze_lighting_consistency(image)
            
            return {
                'summary': {
                    'real_score': final_result['real_score'],
                    'fake_score': final_result['fake_score'],
                    'explanations': explanations,
                    'face_count': len(face_results)
                },
                'advanced_analysis': {
                    'lighting': lighting_result,
                    'face_analysis': {
                        'faces_detected': len(face_results),
                        'face_scores': [r['real_score'] for r in face_results]
                    }
                },
                'artifacts': artifacts
            }
            
        except Exception as e:
            return {
                'summary': {
                    'real_score': 0.5,
                    'fake_score': 0.5,
                    'explanations': [
                        {
                            'type': 'error',
                            'detail': f'Analysis failed: {str(e)}'
                        }
                    ]
                },
                'artifacts': {}
            }
    
    def analyze_video(self, video_path):
        """Analyze a video for DeepFake detection"""
        try:
            # Extract frames from video
            frames = self.video_processor.extract_frames(video_path, max_frames=30)
            
            if len(frames) == 0:
                return {
                    'summary': {
                        'real_score': 0.5,
                        'fake_score': 0.5,
                        'explanations': [
                            {
                                'type': 'video_processing',
                                'detail': 'Could not extract frames from video'
                            }
                        ]
                    },
                    'artifacts': {}
                }
            
            # Analyze each frame
            frame_results = []
            for i, frame in enumerate(frames):
                frame_result = self.analyze_image_frame(frame, i)
                frame_results.append(frame_result)
            
            # Temporal consistency analysis
            temporal_result = self._analyze_temporal_consistency(frame_results)
            
            # Advanced video analysis
            eye_blinking_result = self.eye_blinking_analyzer.analyze_blinking_pattern(video_path, max_frames=50)
            lighting_result = self.lighting_analyzer.analyze_video_lighting_consistency(video_path, max_frames=30)
            
            # Audio analysis (if audio track exists)
            audio_result = {'real_score': 0.7, 'fake_score': 0.3}  # Default if no audio
            try:
                # Try to extract and analyze audio
                audio_path = video_path.replace('.mp4', '_audio.wav').replace('.avi', '_audio.wav')
                if os.path.exists(audio_path):
                    audio_result = self.audio_analyzer.analyze_audio_manipulation(audio_path)
            except Exception as e:
                print(f"⚠️ Audio analysis failed: {e}")
            
            # Aggregate results
            frame_scores = [r['real_score'] for r in frame_results if 'real_score' in r]
            
            if len(frame_scores) == 0:
                avg_real_score = 0.6  # Higher default for videos
            else:
                avg_real_score = np.mean(frame_scores)
            
            # Add variance analysis
            if len(frame_scores) > 1:
                score_variance = np.var(frame_scores)
                # High variance suggests manipulation
                if score_variance > 0.1:
                    avg_real_score -= 0.2
            
            # Combine with temporal analysis and advanced features
            final_real_score = (
                0.4 * avg_real_score + 
                0.2 * temporal_result['consistency_score'] +
                0.2 * eye_blinking_result.get('real_score', 0.7) +
                0.1 * lighting_result.get('real_score', 0.7) +
                0.1 * audio_result.get('real_score', 0.7)
            )
            
            # Ensure score is within bounds
            final_real_score = max(0.1, min(0.9, final_real_score))
            
            # Generate explanations
            explanations = self._generate_video_explanations(frame_results, temporal_result)
            
            # Create artifacts
            artifacts = self._create_video_artifacts(video_path, frames, frame_results)
            
            return {
                'summary': {
                    'real_score': final_real_score,
                    'fake_score': 1.0 - final_real_score,
                    'explanations': explanations,
                    'frame_level': [
                        {
                            'frame': i,
                            'score': r.get('real_score', 0.5)
                        }
                        for i, r in enumerate(frame_results)
                    ]
                },
                'advanced_analysis': {
                    'eye_blinking': eye_blinking_result,
                    'lighting': lighting_result,
                    'audio': audio_result
                },
                'artifacts': artifacts
            }
            
        except Exception as e:
            return {
                'summary': {
                    'real_score': 0.5,
                    'fake_score': 0.5,
                    'explanations': [
                        {
                            'type': 'error',
                            'detail': f'Video analysis failed: {str(e)}'
                        }
                    ]
                },
                'artifacts': {}
            }
    
    def analyze_image_frame(self, frame, frame_id):
        """Analyze a single frame from video"""
        # Detect faces
        faces = self.image_processor.detect_faces(frame)
        
        if len(faces) == 0:
            # Analyze full frame if no faces
            quality_score = self._analyze_image_quality(frame)
            return {'real_score': quality_score, 'face_count': 0}
        
        # Analyze faces
        face_scores = []
        for face in faces:
            xception_result = self.xception_detector.analyze_face_region(frame, face)
            face_scores.append(xception_result['real_score'])
        
        # Add frame quality analysis
        quality_score = self._analyze_image_quality(frame)
        
        # Combine face analysis with quality
        face_score = np.mean(face_scores) if face_scores else 0.7
        combined_score = 0.7 * face_score + 0.3 * quality_score
        
        return {
            'real_score': combined_score,
            'face_count': len(faces),
            'face_score': face_score,
            'quality_score': quality_score
        }
    
    def _combine_scores(self, scores):
        """Combine multiple scores using weighted average"""
        if not scores:
            return 0.5
        
        # Ensure we have the same number of weights as scores
        weights = list(self.model_weights.values())
        
        # If we have more scores than weights, pad with equal weights
        if len(scores) > len(weights):
            weights.extend([0.1] * (len(scores) - len(weights)))
        # If we have more weights than scores, truncate weights
        elif len(weights) > len(scores):
            weights = weights[:len(scores)]
        
        # Normalize weights to sum to 1
        if sum(weights) > 0:
            weights = [w / sum(weights) for w in weights]
        else:
            weights = [1.0 / len(scores)] * len(scores)
        
        return np.average(scores, weights=weights)
    
    def _analyze_temporal_consistency(self, frame_results):
        """Analyze temporal consistency across video frames"""
        scores = [r.get('real_score', 0.5) for r in frame_results]
        
        if len(scores) < 2:
            return {'consistency_score': 0.5, 'variance': 0.0}
        
        # Calculate variance in scores
        variance = np.var(scores)
        
        # High variance suggests inconsistency (possible DeepFake)
        # Low variance suggests consistency (likely real)
        consistency_score = max(0.0, 1.0 - variance * 2)
        
        return {
            'consistency_score': consistency_score,
            'variance': variance,
            'score_range': [min(scores), max(scores)]
        }
    
    def _generate_explanations(self, face_results):
        """Generate human-readable explanations for the analysis"""
        explanations = []
        
        if len(face_results) == 0:
            explanations.append({
                'type': 'face_detection',
                'detail': 'No faces detected in the image'
            })
            return explanations
        
        # Model ensemble explanation
        if len(face_results) == 1:
            result = face_results[0]
            xception_score = result['components']['xception']['real_score']
            forensic_score = result['components']['forensics']['real_score']
            metadata_score = result['components']['metadata']['real_score']
            
            explanations.append({
                'type': 'model_ensemble',
                'detail': f'Xception: {xception_score:.2f} real, Forensics: {forensic_score:.2f} real, Metadata: {metadata_score:.2f} real, Ensemble: {result["real_score"]:.3f}'
            })
        else:
            avg_score = np.mean([r['real_score'] for r in face_results])
            explanations.append({
                'type': 'model_ensemble',
                'detail': f'Analyzed {len(face_results)} faces, average real score: {avg_score:.3f}'
            })
        
        # Add forensic explanations
        for result in face_results:
            if 'components' in result:
                forensic_detail = result['components']['forensics'].get('detail', '')
                if forensic_detail:
                    explanations.append({
                        'type': 'forensics',
                        'detail': forensic_detail
                    })
        
        return explanations
    
    def _generate_video_explanations(self, frame_results, temporal_result):
        """Generate explanations for video analysis"""
        explanations = []
        
        # Frame analysis summary
        valid_frames = [r for r in frame_results if 'real_score' in r]
        if valid_frames:
            avg_score = np.mean([r['real_score'] for r in valid_frames])
            explanations.append({
                'type': 'frame_analysis',
                'detail': f'Analyzed {len(valid_frames)} frames, average real score: {avg_score:.3f}'
            })
        
        # Temporal consistency
        consistency = temporal_result['consistency_score']
        variance = temporal_result['variance']
        
        if variance > 0.1:
            explanations.append({
                'type': 'temporal_consistency',
                'detail': f'High variance in frame scores ({variance:.3f}) suggests possible manipulation'
            })
        else:
            explanations.append({
                'type': 'temporal_consistency',
                'detail': f'Consistent scores across frames (variance: {variance:.3f})'
            })
        
        return explanations
    
    def _create_artifacts(self, image_path, image, faces, face_results):
        """Create visualization artifacts"""
        artifacts = {}
        
        try:
            # Create preview with face detection boxes
            preview_image = image.copy()
            for i, face in enumerate(faces):
                x, y, w, h = face
                cv2.rectangle(preview_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(preview_image, f'Face {i+1}', (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save preview
            job_id = os.path.basename(image_path).split('_')[0]
            preview_path = f'static/analysis/{job_id}_preview.jpg'
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            cv2.imwrite(preview_path, preview_image)
            artifacts['preview_image'] = f'/{preview_path}'
            
        except Exception as e:
            print(f"Warning: Could not create preview image: {e}")
        
        return artifacts
    
    def _create_video_artifacts(self, video_path, frames, frame_results):
        """Create video analysis artifacts"""
        artifacts = {}
        
        try:
            # Create frame montage
            if len(frames) > 0:
                job_id = os.path.basename(video_path).split('_')[0]
                montage_path = f'static/analysis/{job_id}_frames.jpg'
                os.makedirs(os.path.dirname(montage_path), exist_ok=True)
                
                # Create a simple montage of first 9 frames
                montage_frames = frames[:9]
                if len(montage_frames) > 0:
                    h, w = montage_frames[0].shape[:2]
                    cols = 3
                    rows = (len(montage_frames) + cols - 1) // cols
                    
                    montage = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
                    
                    for i, frame in enumerate(montage_frames):
                        row = i // cols
                        col = i % cols
                        montage[row*h:(row+1)*h, col*w:(col+1)*w] = frame
                    
                    cv2.imwrite(montage_path, montage)
                    artifacts['frame_montage'] = f'/{montage_path}'
        
        except Exception as e:
            print(f"Warning: Could not create video artifacts: {e}")
        
        return artifacts
    
    def _analyze_full_image(self, image, image_path):
        """Analyze full image when no faces are detected"""
        try:
            # Resize image for analysis
            resized_image = self.image_processor.resize_image(image, max_size=512)
            
            # Xception analysis on full image
            xception_result = self.xception_detector.predict(resized_image)
            
            # Forensic analysis on full image
            forensic_result = self.forensic_analyzer.analyze_frequency_domain(resized_image)
            
            # Metadata analysis
            metadata_result = self.forensic_analyzer.analyze_metadata(image_path)
            
            # Add image quality analysis
            quality_score = self._analyze_image_quality(resized_image)
            
            # Add lighting analysis
            lighting_result = self.lighting_analyzer.analyze_lighting_consistency(resized_image)
            
            # Combine results with adjusted weights for full image
            combined_score = self._combine_scores([
                xception_result['real_score'],
                forensic_result['real_score'],
                metadata_result['real_score'],
                quality_score,
                lighting_result.get('real_score', 0.7)
            ])
            
            # Generate explanations
            explanations = [
                {
                    'type': 'face_detection',
                    'detail': 'No faces detected - analyzing full image'
                },
                {
                    'type': 'model_ensemble',
                    'detail': f'Full image analysis: Xception: {xception_result["real_score"]:.2f}, Forensics: {forensic_result["real_score"]:.2f}, Metadata: {metadata_result["real_score"]:.2f}, Combined: {combined_score:.3f}'
                }
            ]
            
            # Add forensic explanations
            if forensic_result.get('anomaly_detected'):
                explanations.append({
                    'type': 'forensics',
                    'detail': 'Frequency domain anomalies detected in full image'
                })
            
            return {
                'summary': {
                    'real_score': combined_score,
                    'fake_score': 1.0 - combined_score,
                    'explanations': explanations,
                    'face_count': 0
                },
                'advanced_analysis': {
                    'lighting': lighting_result,
                    'quality': {'real_score': quality_score, 'fake_score': 1.0 - quality_score}
                },
                'artifacts': {}
            }
            
        except Exception as e:
            return {
                'summary': {
                    'real_score': 0.5,
                    'fake_score': 0.5,
                    'explanations': [
                        {
                            'type': 'error',
                            'detail': f'Full image analysis failed: {str(e)}'
                        }
                    ]
                },
                'artifacts': {}
            }
    
    def _analyze_image_quality(self, image):
        """Analyze image quality for authenticity indicators"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate quality metrics
            brightness = np.mean(gray)
            contrast = np.std(gray)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Analyze color distribution
            if len(image.shape) == 3:
                b, g, r = cv2.split(image)
                color_variance = np.var([np.std(b), np.std(g), np.std(r)])
            else:
                color_variance = 0
            
            # Score based on quality indicators
            score = 0.7  # Base score
            
            # High quality indicators (suggest real image)
            if 30 < brightness < 200:  # Normal brightness
                score += 0.1
            if contrast > 20:  # Good contrast
                score += 0.1
            if sharpness > 50:  # Good sharpness
                score += 0.1
            if color_variance < 100:  # Consistent colors
                score += 0.1
            
            # Low quality indicators (suggest manipulation)
            if brightness < 10 or brightness > 245:  # Extreme brightness
                score -= 0.2
            if contrast < 5:  # Very low contrast
                score -= 0.3
            if sharpness < 10:  # Very low sharpness
                score -= 0.2
            if color_variance > 500:  # Inconsistent colors
                score -= 0.2
            
            # Ensure score is within bounds
            score = max(0.1, min(0.9, score))
            
            return score
            
        except Exception as e:
            print(f"⚠️ Image quality analysis failed: {e}")
            return 0.7  # Default score
