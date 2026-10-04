"""
WebSocket handler for real-time analysis updates
معالج WebSocket للتحديثات المباشرة
"""

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import threading
import time

class WebSocketHandler:
    """WebSocket handler for real-time updates"""
    
    def __init__(self, app):
        """Initialize WebSocket handler"""
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.active_rooms = {}
        self.setup_events()
    
    def setup_events(self):
        """Setup WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            print(f"Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to DeepFake Analysis'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print(f"Client disconnected: {request.sid}")
            # Clean up rooms
            for room_id in list(self.active_rooms.keys()):
                if request.sid in self.active_rooms[room_id]:
                    self.active_rooms[room_id].remove(request.sid)
                    if not self.active_rooms[room_id]:
                        del self.active_rooms[room_id]
        
        @self.socketio.on('join_analysis')
        def handle_join_analysis(data):
            """Join analysis room"""
            job_id = data.get('job_id')
            if job_id:
                join_room(job_id)
                if job_id not in self.active_rooms:
                    self.active_rooms[job_id] = []
                self.active_rooms[job_id].append(request.sid)
                emit('joined', {'job_id': job_id, 'message': 'Joined analysis room'})
        
        @self.socketio.on('leave_analysis')
        def handle_leave_analysis(data):
            """Leave analysis room"""
            job_id = data.get('job_id')
            if job_id:
                leave_room(job_id)
                if job_id in self.active_rooms and request.sid in self.active_rooms[job_id]:
                    self.active_rooms[job_id].remove(request.sid)
                emit('left', {'job_id': job_id, 'message': 'Left analysis room'})
    
    def send_progress_update(self, job_id, progress_data):
        """Send progress update to room"""
        self.socketio.emit('progress_update', progress_data, room=job_id)
    
    def send_analysis_complete(self, job_id, results):
        """Send analysis completion to room"""
        self.socketio.emit('analysis_complete', results, room=job_id)
    
    def send_error(self, job_id, error_message):
        """Send error message to room"""
        self.socketio.emit('analysis_error', {'error': error_message}, room=job_id)
    
    def run(self, app, **kwargs):
        """Run SocketIO server"""
        return self.socketio.run(app, **kwargs)

class RealTimeAnalyzer:
    """Real-time analysis with WebSocket updates"""
    
    def __init__(self, websocket_handler):
        """Initialize real-time analyzer"""
        self.ws_handler = websocket_handler
        self.analysis_threads = {}
    
    def start_analysis(self, job_id, file_path, file_type):
        """Start analysis with real-time updates"""
        if job_id in self.analysis_threads:
            return False
        
        thread = threading.Thread(
            target=self._analyze_with_updates,
            args=(job_id, file_path, file_type)
        )
        thread.daemon = True
        thread.start()
        self.analysis_threads[job_id] = thread
        return True
    
    def _analyze_with_updates(self, job_id, file_path, file_type):
        """Analyze with real-time WebSocket updates"""
        try:
            # Send initial progress
            self.ws_handler.send_progress_update(job_id, {
                'status': 'started',
                'progress': 0,
                'message': 'بدء التحليل...'
            })
            
            # Import analysis modules
            from app.models.ensemble import DeepFakeDetector
            from app.models.advanced_models import AdvancedDeepFakeDetector
            from app.utils.advanced_forensics import AdvancedForensicAnalyzer
            
            # Initialize detectors
            detector = DeepFakeDetector()
            advanced_detector = AdvancedDeepFakeDetector()
            forensic_analyzer = AdvancedForensicAnalyzer()
            
            # Progress steps
            steps = [
                ('loading', 10, 'تحميل الملف...'),
                ('preprocessing', 20, 'معالجة أولية...'),
                ('face_detection', 30, 'اكتشاف الوجوه...'),
                ('basic_analysis', 50, 'تحليل أساسي...'),
                ('advanced_analysis', 70, 'تحليل متقدم...'),
                ('forensic_analysis', 85, 'تحليل جنائي...'),
                ('finalizing', 95, 'إنهاء التحليل...'),
                ('complete', 100, 'اكتمل التحليل!')
            ]
            
            results = {}
            
            for step, progress, message in steps:
                self.ws_handler.send_progress_update(job_id, {
                    'status': step,
                    'progress': progress,
                    'message': message
                })
                
                time.sleep(0.5)  # Simulate processing time
                
                if step == 'basic_analysis':
                    if file_type == 'image':
                        results['basic'] = detector.analyze_image(file_path)
                    else:
                        results['basic'] = detector.analyze_video(file_path)
                
                elif step == 'advanced_analysis':
                    # Advanced model analysis
                    if file_type == 'image':
                        import cv2
                        image = cv2.imread(file_path)
                        results['advanced'] = advanced_detector.predict_ensemble(image)
                
                elif step == 'forensic_analysis':
                    # Forensic analysis
                    if file_type == 'image':
                        import cv2
                        image = cv2.imread(file_path)
                        results['forensic'] = {
                            'frequency': forensic_analyzer.analyze_frequency_domain(image),
                            'lighting': forensic_analyzer.analyze_lighting_consistency(image),
                            'metadata': forensic_analyzer.analyze_advanced_metadata(file_path)
                        }
                    else:
                        results['forensic'] = {
                            'metadata': forensic_analyzer.analyze_advanced_metadata(file_path)
                        }
            
            # Combine results
            final_results = self._combine_results(results)
            
            # Send completion
            self.ws_handler.send_analysis_complete(job_id, final_results)
            
        except Exception as e:
            self.ws_handler.send_error(job_id, str(e))
        finally:
            # Clean up
            if job_id in self.analysis_threads:
                del self.analysis_threads[job_id]
    
    def _combine_results(self, results):
        """Combine all analysis results"""
        try:
            combined = {
                'status': 'completed',
                'summary': {
                    'real_score': 0.5,
                    'fake_score': 0.5,
                    'confidence': 0.5,
                    'explanations': []
                },
                'detailed_results': results
            }
            
            # Combine scores from different analyses
            scores = []
            weights = []
            
            if 'basic' in results and 'summary' in results['basic']:
                basic_score = results['basic']['summary']['real_score']
                scores.append(basic_score)
                weights.append(0.4)
            
            if 'advanced' in results:
                advanced_score = results['advanced']['ensemble_score']
                scores.append(advanced_score)
                weights.append(0.3)
            
            if 'forensic' in results:
                forensic_scores = []
                for analysis in results['forensic'].values():
                    if 'real_score' in analysis:
                        forensic_scores.append(analysis['real_score'])
                
                if forensic_scores:
                    avg_forensic = np.mean(forensic_scores)
                    scores.append(avg_forensic)
                    weights.append(0.3)
            
            # Calculate weighted average
            if scores and weights:
                combined['summary']['real_score'] = np.average(scores, weights=weights)
                combined['summary']['fake_score'] = 1.0 - combined['summary']['real_score']
                combined['summary']['confidence'] = max(scores) - min(scores)
            
            # Generate explanations
            explanations = []
            if 'basic' in results and 'explanations' in results['basic']['summary']:
                explanations.extend(results['basic']['summary']['explanations'])
            
            if 'advanced' in results:
                explanations.append({
                    'type': 'advanced_models',
                    'detail': f'Advanced ensemble: {results["advanced"]["ensemble_score"]:.3f} real score'
                })
            
            if 'forensic' in results:
                explanations.append({
                    'type': 'advanced_forensics',
                    'detail': 'Advanced forensic analysis completed'
                })
            
            combined['summary']['explanations'] = explanations
            
            return combined
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'summary': {
                    'real_score': 0.5,
                    'fake_score': 0.5,
                    'explanations': [{'type': 'error', 'detail': str(e)}]
                }
            }
