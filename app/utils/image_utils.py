"""
Image processing utilities for DeepFake detection
"""

import cv2
import numpy as np
from mtcnn import MTCNN
import os

# Try to import dlib, but don't fail if it's not available
try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("⚠️  تحذير: dlib غير متوفر - سيتم استخدام MTCNN فقط")

class ImageProcessor:
    """Image processing utilities for face detection and preprocessing"""
    
    def __init__(self):
        """Initialize image processor"""
        self.face_detector = MTCNN()
        self.landmark_predictor = None
        
        # Try to initialize dlib face landmark predictor
        self.landmark_predictor = None
        if DLIB_AVAILABLE:
            try:
                # Path to shape predictor (68 face landmarks)
                predictor_path = 'weights/shape_predictor_68_face_landmarks.dat'
                if os.path.exists(predictor_path):
                    self.landmark_predictor = dlib.shape_predictor(predictor_path)
            except Exception as e:
                print(f"Warning: Could not load dlib landmark predictor: {e}")
    
    def detect_faces(self, image):
        """Detect faces in image using MTCNN"""
        try:
            # Convert BGR to RGB for MTCNN
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            results = self.face_detector.detect_faces(rgb_image)
            
            # Extract bounding boxes
            faces = []
            for result in results:
                if result['confidence'] > 0.9:  # High confidence threshold
                    x, y, width, height = result['box']
                    faces.append([x, y, width, height])
            
            return np.array(faces)
            
        except Exception as e:
            print(f"Error in face detection: {e}")
            return np.array([])
    
    def detect_faces_dlib(self, image):
        """Detect faces using dlib (fallback method)"""
        if not DLIB_AVAILABLE:
            print("dlib غير متوفر - استخدام MTCNN بدلاً منه")
            return self.detect_faces(image)
            
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Use dlib's face detector
            detector = dlib.get_frontal_face_detector()
            faces = detector(gray)
            
            # Convert to numpy array format
            face_boxes = []
            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                face_boxes.append([x, y, w, h])
            
            return np.array(face_boxes)
            
        except Exception as e:
            print(f"Error in dlib face detection: {e}")
            return np.array([])
    
    def extract_face_landmarks(self, image, face_box):
        """Extract facial landmarks for a detected face"""
        if not DLIB_AVAILABLE or self.landmark_predictor is None:
            return None
        
        try:
            x, y, w, h = face_box
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Create dlib rectangle
            rect = dlib.rectangle(x, y, x + w, y + h)
            
            # Get landmarks
            landmarks = self.landmark_predictor(gray, rect)
            
            # Convert to numpy array
            points = []
            for i in range(68):
                point = landmarks.part(i)
                points.append([point.x, point.y])
            
            return np.array(points)
            
        except Exception as e:
            print(f"Error extracting landmarks: {e}")
            return None
    
    def align_face(self, image, face_box, landmarks=None):
        """Align face to standard position"""
        try:
            x, y, w, h = face_box
            
            # Extract face region
            face_region = image[y:y+h, x:x+w]
            
            if face_region.size == 0:
                return None
            
            # If landmarks are available, use them for alignment
            if landmarks is not None:
                # Simple alignment based on eye positions
                # This is a simplified version - in practice, more sophisticated alignment is used
                left_eye = landmarks[36:42].mean(axis=0)
                right_eye = landmarks[42:48].mean(axis=0)
                
                # Calculate angle between eyes
                eye_vector = right_eye - left_eye
                angle = np.arctan2(eye_vector[1], eye_vector[0]) * 180 / np.pi
                
                # Rotate image to align eyes horizontally
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                aligned_face = cv2.warpAffine(face_region, rotation_matrix, (w, h))
            else:
                # Simple resize alignment
                aligned_face = cv2.resize(face_region, (224, 224))
            
            return aligned_face
            
        except Exception as e:
            print(f"Error aligning face: {e}")
            return None
    
    def preprocess_face(self, image, face_box):
        """Preprocess face for analysis"""
        try:
            # Extract and align face
            aligned_face = self.align_face(image, face_box)
            
            if aligned_face is None:
                return None
            
            # Normalize pixel values
            normalized_face = aligned_face.astype(np.float32) / 255.0
            
            # Apply histogram equalization for better contrast
            if len(normalized_face.shape) == 3:
                # Convert to LAB color space for better equalization
                lab = cv2.cvtColor((normalized_face * 255).astype(np.uint8), cv2.COLOR_BGR2LAB)
                lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
                normalized_face = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR).astype(np.float32) / 255.0
            
            return normalized_face
            
        except Exception as e:
            print(f"Error preprocessing face: {e}")
            return None
    
    def create_face_mask(self, image, face_box, landmarks=None):
        """Create a mask for the face region"""
        try:
            h, w = image.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            
            x, y, face_w, face_h = face_box
            
            # Create rectangular mask
            mask[y:y+face_h, x:x+face_w] = 255
            
            # If landmarks are available, create more precise mask
            if landmarks is not None:
                # Create convex hull from facial landmarks
                hull = cv2.convexHull(landmarks.astype(np.int32))
                cv2.fillPoly(mask, [hull], 255)
            
            return mask
            
        except Exception as e:
            print(f"Error creating face mask: {e}")
            return None
    
    def enhance_image_quality(self, image):
        """Enhance image quality for better analysis"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Apply slight sharpening
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # Blend original and sharpened
            result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
            
            return result
            
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return image
    
    def resize_image(self, image, max_size=1024):
        """Resize image while maintaining aspect ratio"""
        try:
            h, w = image.shape[:2]
            
            if max(h, w) <= max_size:
                return image
            
            # Calculate scaling factor
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize image
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return resized
            
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image
