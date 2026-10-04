"""
Advanced Machine Learning techniques
تقنيات تعلم آلي متقدمة
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import cv2
import os
from datetime import datetime

class ActiveLearning:
    """Active Learning for model improvement"""
    
    def __init__(self, base_model, uncertainty_threshold=0.3):
        """Initialize Active Learning"""
        self.base_model = base_model
        self.uncertainty_threshold = uncertainty_threshold
        self.pool_data = []
        self.labeled_data = []
        self.uncertain_samples = []
    
    def add_to_pool(self, image, features=None):
        """Add sample to unlabeled pool"""
        self.pool_data.append({
            'image': image,
            'features': features,
            'timestamp': datetime.now()
        })
    
    def predict_with_uncertainty(self, image):
        """Predict with uncertainty estimation"""
        try:
            # Get prediction
            prediction = self.base_model.predict(np.expand_dims(image, axis=0), verbose=0)
            
            # Calculate uncertainty (entropy)
            uncertainty = -np.sum(prediction * np.log(prediction + 1e-10))
            
            return {
                'prediction': prediction[0][0],
                'uncertainty': uncertainty,
                'needs_labeling': uncertainty > self.uncertainty_threshold
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def select_uncertain_samples(self, n_samples=10):
        """Select most uncertain samples for labeling"""
        try:
            uncertainties = []
            
            for i, sample in enumerate(self.pool_data):
                result = self.predict_with_uncertainty(sample['image'])
                if 'uncertainty' in result:
                    uncertainties.append((i, result['uncertainty']))
            
            # Sort by uncertainty (highest first)
            uncertainties.sort(key=lambda x: x[1], reverse=True)
            
            # Select top uncertain samples
            selected_indices = [idx for idx, _ in uncertainties[:n_samples]]
            selected_samples = [self.pool_data[i] for i in selected_indices]
            
            return selected_samples
            
        except Exception as e:
            print(f"❌ Sample selection failed: {e}")
            return []
    
    def update_model(self, new_labels):
        """Update model with new labels"""
        try:
            # This would implement model retraining with new labels
            print(f"🔄 Updating model with {len(new_labels)} new labels")
            # Implementation would go here
            return True
            
        except Exception as e:
            print(f"❌ Model update failed: {e}")
            return False

class TransferLearning:
    """Transfer Learning utilities"""
    
    def __init__(self):
        """Initialize Transfer Learning"""
        self.source_models = {}
        self.target_models = {}
    
    def load_pretrained_model(self, model_name, weights_path=None):
        """Load pre-trained model"""
        try:
            if model_name == 'xception':
                from tensorflow.keras.applications import Xception
                base_model = Xception(
                    weights='imagenet',
                    include_top=False,
                    input_shape=(299, 299, 3)
                )
            elif model_name == 'efficientnet':
                from tensorflow.keras.applications import EfficientNetB7
                base_model = EfficientNetB7(
                    weights='imagenet',
                    include_top=False,
                    input_shape=(600, 600, 3)
                )
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            # Add custom head for DeepFake detection
            x = base_model.output
            x = tf.keras.layers.GlobalAveragePooling2D()(x)
            x = Dense(512, activation='relu')(x)
            x = Dropout(0.5)(x)
            x = Dense(256, activation='relu')(x)
            x = Dropout(0.3)(x)
            predictions = Dense(1, activation='sigmoid')(x)
            
            model = Model(inputs=base_model.input, outputs=predictions)
            
            # Load custom weights if available
            if weights_path and os.path.exists(weights_path):
                model.load_weights(weights_path)
                print(f"✅ Loaded custom weights for {model_name}")
            
            self.source_models[model_name] = model
            return model
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return None
    
    def fine_tune_model(self, model_name, training_data, validation_data, epochs=10):
        """Fine-tune model on new data"""
        try:
            if model_name not in self.source_models:
                print(f"❌ Model {model_name} not loaded")
                return None
            
            model = self.source_models[model_name]
            
            # Freeze base layers
            for layer in model.layers[:-10]:
                layer.trainable = False
            
            # Compile model
            model.compile(
                optimizer=Adam(learning_rate=0.0001),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            # Setup callbacks
            callbacks = [
                EarlyStopping(patience=5, restore_best_weights=True),
                ReduceLROnPlateau(patience=3, factor=0.5)
            ]
            
            # Train model
            history = model.fit(
                training_data,
                validation_data=validation_data,
                epochs=epochs,
                callbacks=callbacks,
                verbose=1
            )
            
            # Save fine-tuned model
            fine_tuned_path = f'weights/{model_name}_fine_tuned.h5'
            model.save_weights(fine_tuned_path)
            
            self.target_models[model_name] = model
            return model, history
            
        except Exception as e:
            print(f"❌ Fine-tuning failed: {e}")
            return None, None

class FewShotLearning:
    """Few-Shot Learning for limited data"""
    
    def __init__(self, support_set_size=5):
        """Initialize Few-Shot Learning"""
        self.support_set_size = support_set_size
        self.support_set = []
        self.query_set = []
    
    def create_support_set(self, images, labels):
        """Create support set for few-shot learning"""
        try:
            # Select diverse samples
            unique_labels = np.unique(labels)
            support_indices = []
            
            for label in unique_labels:
                label_indices = np.where(labels == label)[0]
                # Select diverse samples for each label
                selected = np.random.choice(
                    label_indices,
                    size=min(self.support_set_size, len(label_indices)),
                    replace=False
                )
                support_indices.extend(selected)
            
            self.support_set = [
                {'image': images[i], 'label': labels[i]}
                for i in support_indices
            ]
            
            return len(self.support_set)
            
        except Exception as e:
            print(f"❌ Support set creation failed: {e}")
            return 0
    
    def predict_with_support_set(self, query_image):
        """Predict using support set"""
        try:
            # Calculate similarities to support set
            similarities = []
            
            for support_sample in self.support_set:
                # Calculate cosine similarity
                similarity = self._calculate_similarity(query_image, support_sample['image'])
                similarities.append((similarity, support_sample['label']))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Use k-nearest neighbors (k=3)
            k = 3
            top_k = similarities[:k]
            
            # Majority vote
            labels = [label for _, label in top_k]
            predicted_label = max(set(labels), key=labels.count)
            
            # Calculate confidence
            confidence = labels.count(predicted_label) / k
            
            return {
                'prediction': predicted_label,
                'confidence': confidence,
                'similarities': top_k
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_similarity(self, img1, img2):
        """Calculate similarity between two images"""
        try:
            # Flatten images
            flat1 = img1.flatten()
            flat2 = img2.flatten()
            
            # Calculate cosine similarity
            dot_product = np.dot(flat1, flat2)
            norm1 = np.linalg.norm(flat1)
            norm2 = np.linalg.norm(flat2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            similarity = dot_product / (norm1 * norm2)
            return similarity
            
        except:
            return 0

class AutoML:
    """AutoML for automatic model optimization"""
    
    def __init__(self):
        """Initialize AutoML"""
        self.model_configs = []
        self.best_model = None
        self.best_score = 0
    
    def search_hyperparameters(self, model_architectures, hyperparameter_ranges):
        """Search for best hyperparameters"""
        try:
            print("🔍 Starting hyperparameter search...")
            
            best_config = None
            best_score = 0
            
            for architecture in model_architectures:
                for lr in hyperparameter_ranges['learning_rates']:
                    for batch_size in hyperparameter_ranges['batch_sizes']:
                        for dropout_rate in hyperparameter_ranges['dropout_rates']:
                            
                            config = {
                                'architecture': architecture,
                                'learning_rate': lr,
                                'batch_size': batch_size,
                                'dropout_rate': dropout_rate
                            }
                            
                            # Train and evaluate model
                            score = self._evaluate_config(config)
                            
                            if score > best_score:
                                best_score = score
                                best_config = config
                            
                            print(f"Config: {config}, Score: {score:.3f}")
            
            print(f"✅ Best config: {best_config}, Score: {best_score:.3f}")
            return best_config, best_score
            
        except Exception as e:
            print(f"❌ Hyperparameter search failed: {e}")
            return None, 0
    
    def _evaluate_config(self, config):
        """Evaluate model configuration"""
        try:
            # This would implement model training and evaluation
            # For now, return a random score
            import random
            return random.uniform(0.5, 0.9)
            
        except:
            return 0
    
    def optimize_architecture(self, input_shape, num_classes=2):
        """Optimize model architecture"""
        try:
            print("🏗️ Optimizing model architecture...")
            
            # Define architecture search space
            architectures = [
                self._create_simple_architecture(input_shape, num_classes),
                self._create_medium_architecture(input_shape, num_classes),
                self._create_complex_architecture(input_shape, num_classes)
            ]
            
            best_architecture = None
            best_score = 0
            
            for arch in architectures:
                score = self._evaluate_architecture(arch)
                if score > best_score:
                    best_score = score
                    best_architecture = arch
            
            return best_architecture, best_score
            
        except Exception as e:
            print(f"❌ Architecture optimization failed: {e}")
            return None, 0
    
    def _create_simple_architecture(self, input_shape, num_classes):
        """Create simple architecture"""
        inputs = Input(shape=input_shape)
        x = tf.keras.layers.Conv2D(32, (3, 3), activation='relu')(inputs)
        x = tf.keras.layers.MaxPooling2D((2, 2))(x)
        x = tf.keras.layers.Flatten()(x)
        x = Dense(64, activation='relu')(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs)
    
    def _create_medium_architecture(self, input_shape, num_classes):
        """Create medium architecture"""
        inputs = Input(shape=input_shape)
        x = tf.keras.layers.Conv2D(64, (3, 3), activation='relu')(inputs)
        x = tf.keras.layers.MaxPooling2D((2, 2))(x)
        x = tf.keras.layers.Conv2D(128, (3, 3), activation='relu')(x)
        x = tf.keras.layers.MaxPooling2D((2, 2))(x)
        x = tf.keras.layers.Flatten()(x)
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs)
    
    def _create_complex_architecture(self, input_shape, num_classes):
        """Create complex architecture"""
        inputs = Input(shape=input_shape)
        x = tf.keras.layers.Conv2D(128, (3, 3), activation='relu')(inputs)
        x = tf.keras.layers.MaxPooling2D((2, 2))(x)
        x = tf.keras.layers.Conv2D(256, (3, 3), activation='relu')(x)
        x = tf.keras.layers.MaxPooling2D((2, 2))(x)
        x = tf.keras.layers.Conv2D(512, (3, 3), activation='relu')(x)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.3)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs)
    
    def _evaluate_architecture(self, architecture):
        """Evaluate architecture performance"""
        try:
            # This would implement architecture evaluation
            # For now, return a random score
            import random
            return random.uniform(0.6, 0.95)
            
        except:
            return 0

class ReinforcementLearning:
    """Reinforcement Learning for model improvement"""
    
    def __init__(self, state_size, action_size):
        """Initialize Reinforcement Learning"""
        self.state_size = state_size
        self.action_size = action_size
        self.q_network = self._build_q_network()
        self.target_network = self._build_q_network()
        self.memory = []
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
    
    def _build_q_network(self):
        """Build Q-network"""
        model = tf.keras.Sequential([
            Dense(64, activation='relu', input_shape=(self.state_size,)),
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(self.action_size, activation='linear')
        ])
        return model
    
    def act(self, state):
        """Choose action using epsilon-greedy policy"""
        if np.random.random() <= self.epsilon:
            return np.random.choice(self.action_size)
        
        q_values = self.q_network.predict(np.array([state]), verbose=0)
        return np.argmax(q_values[0])
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in memory"""
        self.memory.append((state, action, reward, next_state, done))
        
        # Limit memory size
        if len(self.memory) > 10000:
            self.memory.pop(0)
    
    def replay(self, batch_size=32):
        """Train model on past experiences"""
        if len(self.memory) < batch_size:
            return
        
        batch = np.random.choice(len(self.memory), batch_size, replace=False)
        states = np.array([self.memory[i][0] for i in batch])
        actions = np.array([self.memory[i][1] for i in batch])
        rewards = np.array([self.memory[i][2] for i in batch])
        next_states = np.array([self.memory[i][3] for i in batch])
        dones = np.array([self.memory[i][4] for i in batch])
        
        # Calculate target Q-values
        target_q_values = self.q_network.predict(states, verbose=0)
        next_q_values = self.target_network.predict(next_states, verbose=0)
        
        for i in range(batch_size):
            if dones[i]:
                target_q_values[i][actions[i]] = rewards[i]
            else:
                target_q_values[i][actions[i]] = rewards[i] + 0.95 * np.max(next_q_values[i])
        
        # Train model
        self.q_network.fit(states, target_q_values, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_network(self):
        """Update target network"""
        self.target_network.set_weights(self.q_network.get_weights())

# Global instances
active_learning = ActiveLearning(None)
transfer_learning = TransferLearning()
few_shot_learning = FewShotLearning()
automl = AutoML()
reinforcement_learning = ReinforcementLearning(10, 4)
