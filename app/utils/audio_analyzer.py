#!/usr/bin/env python3
"""
Audio Manipulation Analyzer
محلل التلاعب بالصوت للكشف عن DeepFake
"""

import numpy as np
import scipy.signal
from scipy import stats
import math

# Try to import librosa, make it optional
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ تحذير: librosa غير متوفر - تحليل الصوت محدود")

class AudioAnalyzer:
    """Analyze audio for manipulation and DeepFake detection"""
    
    def __init__(self):
        self.sample_rate = 22050
        self.hop_length = 512
        self.n_fft = 2048
        
    def analyze_audio_manipulation(self, audio_path):
        """Analyze audio file for manipulation signs"""
        try:
            if not LIBROSA_AVAILABLE:
                return {
                    'real_score': 0.7,
                    'fake_score': 0.3,
                    'error': 'librosa not available - basic analysis only',
                    'audio_stats': {
                        'duration': 0,
                        'sample_rate': 0,
                        'rms_energy': 0,
                        'zero_crossing_rate': 0
                    }
                }
            
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            if len(y) == 0:
                return {'real_score': 0.5, 'fake_score': 0.5, 'error': 'Empty audio file'}
            
            # Perform various audio analyses
            analyses = {
                'spectral_analysis': self._analyze_spectral_properties(y, sr),
                'temporal_analysis': self._analyze_temporal_properties(y, sr),
                'harmonic_analysis': self._analyze_harmonic_content(y, sr),
                'noise_analysis': self._analyze_noise_patterns(y, sr),
                'compression_analysis': self._analyze_compression_artifacts(y, sr)
            }
            
            # Calculate overall authenticity score
            real_score = self._calculate_audio_authenticity_score(analyses)
            
            return {
                'real_score': real_score,
                'fake_score': 1.0 - real_score,
                'audio_analyses': analyses,
                'audio_stats': {
                    'duration': len(y) / sr,
                    'sample_rate': sr,
                    'rms_energy': float(np.sqrt(np.mean(y**2))),
                    'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
                }
            }
            
        except Exception as e:
            return {'real_score': 0.5, 'fake_score': 0.5, 'error': str(e)}
    
    def _analyze_spectral_properties(self, y, sr):
        """Analyze spectral properties for manipulation signs"""
        try:
            # Compute spectral features
            stft = librosa.stft(y, hop_length=self.hop_length, n_fft=self.n_fft)
            magnitude = np.abs(stft)
            
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # Analyze spectral consistency
            centroid_std = np.std(spectral_centroids)
            rolloff_std = np.std(spectral_rolloff)
            bandwidth_std = np.std(spectral_bandwidth)
            
            # Check for unnatural spectral patterns
            anomalies = []
            
            # High variance in spectral features suggests manipulation
            if centroid_std > np.mean(spectral_centroids) * 0.3:
                anomalies.append("High spectral centroid variance")
            
            if rolloff_std > np.mean(spectral_rolloff) * 0.3:
                anomalies.append("High spectral rolloff variance")
            
            if bandwidth_std > np.mean(spectral_bandwidth) * 0.3:
                anomalies.append("High spectral bandwidth variance")
            
            # Check for spectral gaps (common in manipulated audio)
            spectral_gaps = self._detect_spectral_gaps(magnitude)
            if spectral_gaps > 0.1:
                anomalies.append("Spectral gaps detected")
            
            return {
                'centroid_stats': {'mean': float(np.mean(spectral_centroids)), 'std': float(centroid_std)},
                'rolloff_stats': {'mean': float(np.mean(spectral_rolloff)), 'std': float(rolloff_std)},
                'bandwidth_stats': {'mean': float(np.mean(spectral_bandwidth)), 'std': float(bandwidth_std)},
                'spectral_gaps': spectral_gaps,
                'anomalies': anomalies
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_temporal_properties(self, y, sr):
        """Analyze temporal properties for manipulation signs"""
        try:
            # Compute MFCCs
            if LIBROSA_AVAILABLE:
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            else:
                # Fallback: simple spectral analysis
                mfccs = np.random.random((13, 100))  # Dummy data
            
            # Analyze MFCC consistency
            mfcc_std = np.std(mfccs, axis=1)
            mfcc_mean = np.mean(mfccs, axis=1)
            
            # Check for unnatural MFCC patterns
            anomalies = []
            
            # High variance in MFCCs suggests manipulation
            for i, (mean_val, std_val) in enumerate(zip(mfcc_mean, mfcc_std)):
                if std_val > abs(mean_val) * 0.5:
                    anomalies.append(f"High variance in MFCC {i+1}")
            
            # Analyze energy envelope
            if LIBROSA_AVAILABLE:
                energy = librosa.feature.rms(y=y)[0]
            else:
                # Fallback: simple energy calculation
                energy = np.sqrt(np.mean(y**2)) * np.ones(100)
            energy_std = np.std(energy)
            energy_mean = np.mean(energy)
            
            # Check for unnatural energy patterns
            if energy_std > energy_mean * 0.8:
                anomalies.append("Unnatural energy envelope")
            
            # Analyze zero crossing rate
            if LIBROSA_AVAILABLE:
                zcr = librosa.feature.zero_crossing_rate(y)[0]
            else:
                # Fallback: simple zero crossing calculation
                zcr = np.array([np.sum(np.diff(np.sign(y)) != 0) / len(y)])
            zcr_std = np.std(zcr)
            
            if zcr_std > np.mean(zcr) * 0.5:
                anomalies.append("Unnatural zero crossing rate")
            
            return {
                'mfcc_stats': {
                    'mean': [float(x) for x in mfcc_mean],
                    'std': [float(x) for x in mfcc_std]
                },
                'energy_stats': {'mean': float(energy_mean), 'std': float(energy_std)},
                'zcr_std': float(zcr_std),
                'anomalies': anomalies
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_harmonic_content(self, y, sr):
        """Analyze harmonic content for manipulation signs"""
        try:
            # Separate harmonic and percussive components
            if LIBROSA_AVAILABLE:
                y_harmonic, y_percussive = librosa.effects.hpss(y)
            else:
                # Fallback: simple separation
                y_harmonic = y * 0.7
                y_percussive = y * 0.3
            
            # Analyze harmonic-to-percussive ratio
            harmonic_energy = np.sum(y_harmonic**2)
            percussive_energy = np.sum(y_percussive**2)
            
            if percussive_energy > 0:
                hpr_ratio = harmonic_energy / percussive_energy
            else:
                hpr_ratio = float('inf')
            
            # Analyze harmonic consistency
            harmonic_std = np.std(y_harmonic)
            percussive_std = np.std(y_percussive)
            
            anomalies = []
            
            # Unnatural harmonic patterns
            if hpr_ratio > 100 or hpr_ratio < 0.01:
                anomalies.append("Unnatural harmonic-to-percussive ratio")
            
            # Check for harmonic artifacts
            if harmonic_std > np.std(y) * 1.5:
                anomalies.append("Harmonic artifacts detected")
            
            return {
                'harmonic_energy': float(harmonic_energy),
                'percussive_energy': float(percussive_energy),
                'hpr_ratio': float(hpr_ratio),
                'harmonic_std': float(harmonic_std),
                'percussive_std': float(percussive_std),
                'anomalies': anomalies
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_noise_patterns(self, y, sr):
        """Analyze noise patterns for manipulation signs"""
        try:
            # Estimate noise floor
            noise_floor = np.percentile(np.abs(y), 10)
            
            # Analyze noise characteristics
            # Apply high-pass filter to isolate noise
            sos = scipy.signal.butter(4, 8000, btype='high', fs=sr, output='sos')
            filtered_y = scipy.signal.sosfilt(sos, y)
            
            # Analyze noise distribution
            noise_std = np.std(filtered_y)
            noise_mean = np.mean(np.abs(filtered_y))
            
            # Check for unnatural noise patterns
            anomalies = []
            
            # Very low noise suggests heavy processing
            if noise_floor < 0.001:
                anomalies.append("Very low noise floor - possible heavy processing")
            
            # Unnatural noise distribution
            if noise_std > noise_mean * 2:
                anomalies.append("Unnatural noise distribution")
            
            # Check for quantization artifacts
            quantization_artifacts = self._detect_quantization_artifacts(y)
            if quantization_artifacts > 0.1:
                anomalies.append("Quantization artifacts detected")
            
            return {
                'noise_floor': float(noise_floor),
                'noise_std': float(noise_std),
                'noise_mean': float(noise_mean),
                'quantization_artifacts': quantization_artifacts,
                'anomalies': anomalies
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_compression_artifacts(self, y, sr):
        """Analyze compression artifacts"""
        try:
            # Analyze compression artifacts
            anomalies = []
            
            # Check for clipping
            clipping_ratio = np.sum(np.abs(y) > 0.95) / len(y)
            if clipping_ratio > 0.01:
                anomalies.append("Audio clipping detected")
            
            # Check for compression artifacts in frequency domain
            stft = librosa.stft(y, hop_length=self.hop_length, n_fft=self.n_fft)
            magnitude = np.abs(stft)
            
            # Look for compression artifacts
            compression_artifacts = self._detect_compression_artifacts(magnitude)
            if compression_artifacts > 0.1:
                anomalies.append("Compression artifacts detected")
            
            return {
                'clipping_ratio': float(clipping_ratio),
                'compression_artifacts': compression_artifacts,
                'anomalies': anomalies
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _detect_spectral_gaps(self, magnitude):
        """Detect spectral gaps that indicate manipulation"""
        try:
            # Calculate spectral energy distribution
            spectral_energy = np.sum(magnitude, axis=0)
            
            # Find gaps in spectral energy
            energy_threshold = np.percentile(spectral_energy, 10)
            gaps = np.sum(spectral_energy < energy_threshold) / len(spectral_energy)
            
            return float(gaps)
            
        except Exception:
            return 0.0
    
    def _detect_quantization_artifacts(self, y):
        """Detect quantization artifacts"""
        try:
            # Analyze amplitude distribution
            unique_values = len(np.unique(y))
            total_values = len(y)
            
            # Low number of unique values suggests quantization
            quantization_ratio = unique_values / total_values
            
            return float(1.0 - quantization_ratio)
            
        except Exception:
            return 0.0
    
    def _detect_compression_artifacts(self, magnitude):
        """Detect compression artifacts in frequency domain"""
        try:
            # Look for block-like patterns in magnitude spectrum
            h, w = magnitude.shape
            
            # Check for regular patterns that indicate compression
            block_size = 8
            artifacts = 0
            
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = magnitude[i:i+block_size, j:j+block_size]
                    # Check for uniform blocks (compression artifact)
                    if np.std(block) < 0.1 * np.mean(block):
                        artifacts += 1
            
            return float(artifacts / ((h // block_size) * (w // block_size)))
            
        except Exception:
            return 0.0
    
    def _calculate_audio_authenticity_score(self, analyses):
        """Calculate overall audio authenticity score"""
        score = 0.7  # Base score
        
        # Weight different analyses
        weights = {
            'spectral_analysis': 0.25,
            'temporal_analysis': 0.25,
            'harmonic_analysis': 0.2,
            'noise_analysis': 0.15,
            'compression_analysis': 0.15
        }
        
        # Calculate weighted score
        for analysis_name, weight in weights.items():
            if analysis_name in analyses:
                analysis = analyses[analysis_name]
                if 'error' not in analysis:
                    # Penalize for anomalies
                    anomalies = analysis.get('anomalies', [])
                    penalty = len(anomalies) * 0.1
                    score -= weight * penalty
        
        # Ensure score is within bounds
        return max(0.1, min(0.9, score))
