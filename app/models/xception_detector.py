"""
Xception-based DeepFake detector
Uses pre-trained Xception model for face authenticity detection
"""

import numpy as np
import cv2
from tensorflow.keras.applications.xception import Xception, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
import tensorflow as tf
import os

class XceptionDetector:
    """Xception-based DeepFake detector"""
    
    def __init__(self, weights_path=None):
        """Initialize the Xception detector"""
        self.model = None
        self.input_size = (299, 299)
        self.weights_path = weights_path
        self._build_model()
    
    def _build_model(self):
        """Build the Xception model for DeepFake detection"""
        # Load pre-trained Xception model
        base_model = Xception(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.input_size, 3)
        )
        
        # Add custom layers for binary classification
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        predictions = Dense(1, activation='sigmoid')(x)
        
        # Create the model
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Load custom weights if available
        if self.weights_path and os.path.exists(self.weights_path):
            try:
                self.model.load_weights(self.weights_path)
                print(f"Loaded weights from {self.weights_path}")
            except Exception as e:
                print(f"Warning: Could not load weights from {self.weights_path}: {e}")
                print("Using ImageNet pre-trained weights only")
        else:
            print("Using ImageNet pre-trained weights only")
            print("For better accuracy, train the model on DeepFake datasets")
    
    def preprocess_image(self, image):
        """Preprocess image for Xception model"""
        # Resize image
        image = cv2.resize(image, self.input_size)
        
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Expand dimensions for batch
        image = np.expand_dims(image, axis=0)
        
        # Preprocess for Xception
        image = preprocess_input(image)
        
        return image
    
    def predict(self, image):
        """Predict if image is real or fake"""
        if self.model is None:
            raise ValueError("Model not initialized")
        
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # Make prediction
        prediction = self.model.predict(processed_image, verbose=0)
        
        # Convert to probability of being real
        raw_score = float(prediction[0][0])
        
        # Apply calibration for better results
        # Since we're using ImageNet weights, we need to calibrate the output
        calibrated_score = self._calibrate_prediction(raw_score, image)
        
        fake_probability = 1.0 - calibrated_score
        
        return {
            'real_score': calibrated_score,
            'fake_score': fake_probability,
            'confidence': max(calibrated_score, fake_probability),
            'raw_score': raw_score
        }
    
    def _calibrate_prediction(self, raw_score, image):
        """Calibrate prediction based on image characteristics"""
        try:
            # Analyze image characteristics
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate image quality metrics
            brightness = np.mean(gray)
            contrast = np.std(gray)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Apply calibration based on image quality
            calibration_factor = 1.0
            
            # High contrast and sharpness suggest real image
            if contrast > 30 and sharpness > 100:
                calibration_factor += 0.2
            
            # Very low contrast suggests possible manipulation
            if contrast < 10:
                calibration_factor -= 0.3
            
            # Extreme brightness suggests possible manipulation
            if brightness < 20 or brightness > 235:
                calibration_factor -= 0.2
            
            # Apply calibration
            calibrated_score = raw_score * calibration_factor
            
            # Ensure score is within bounds
            calibrated_score = max(0.1, min(0.9, calibrated_score))
            
            return calibrated_score
            
        except:
            # Fallback to raw score if calibration fails
            return max(0.1, min(0.9, raw_score))
    
    def analyze_face_region(self, image, face_box):
        """Analyze a specific face region in the image"""
        x, y, w, h = face_box
        
        # Extract face region
        face_region = image[y:y+h, x:x+w]
        
        if face_region.size == 0:
            return {'real_score': 0.5, 'fake_score': 0.5, 'confidence': 0.5}
        
        return self.predict(face_region)
