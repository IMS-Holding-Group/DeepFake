"""
External services integration
تكامل مع الخدمات الخارجية
"""

import os
import requests
import json
import base64
from datetime import datetime
import cv2
import numpy as np

class GoogleCloudVision:
    """Google Cloud Vision API integration"""
    
    def __init__(self, api_key=None):
        """Initialize Google Cloud Vision"""
        self.api_key = api_key or os.getenv('GOOGLE_CLOUD_API_KEY')
        self.base_url = 'https://vision.googleapis.com/v1/images:annotate'
    
    def analyze_image(self, image_path):
        """Analyze image using Google Cloud Vision"""
        try:
            if not self.api_key:
                return {'error': 'Google Cloud API key not configured'}
            
            # Encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Prepare request
            request_data = {
                'requests': [{
                    'image': {
                        'content': image_data
                    },
                    'features': [
                        {'type': 'FACE_DETECTION', 'maxResults': 10},
                        {'type': 'LABEL_DETECTION', 'maxResults': 10},
                        {'type': 'SAFE_SEARCH_DETECTION', 'maxResults': 1}
                    ]
                }]
            }
            
            # Make request
            response = requests.post(
                f'{self.base_url}?key={self.api_key}',
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_vision_response(result)
            else:
                return {'error': f'API request failed: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _process_vision_response(self, response):
        """Process Google Vision API response"""
        try:
            if 'responses' not in response or not response['responses']:
                return {'error': 'No response from API'}
            
            result = response['responses'][0]
            
            # Extract face information
            faces = result.get('faceAnnotations', [])
            face_count = len(faces)
            
            # Extract labels
            labels = result.get('labelAnnotations', [])
            label_scores = {label['description']: label['score'] for label in labels}
            
            # Extract safe search
            safe_search = result.get('safeSearchAnnotation', {})
            
            # Analyze for DeepFake indicators
            fake_indicators = []
            
            # Check for unusual face characteristics
            if faces:
                for face in faces:
                    # Check for unrealistic expressions
                    joy_likelihood = face.get('joyLikelihood', 'UNKNOWN')
                    if joy_likelihood == 'VERY_LIKELY':
                        fake_indicators.append('Unrealistic joy expression')
                    
                    # Check for unusual face angles
                    roll_angle = face.get('rollAngle', 0)
                    if abs(roll_angle) > 45:
                        fake_indicators.append('Unusual face rotation')
            
            # Check labels for manipulation indicators
            manipulation_labels = ['computer graphics', 'digital art', 'photoshop', 'edited']
            for label in manipulation_labels:
                if label in label_scores and label_scores[label] > 0.7:
                    fake_indicators.append(f'Manipulation detected: {label}')
            
            return {
                'face_count': face_count,
                'labels': label_scores,
                'safe_search': safe_search,
                'fake_indicators': fake_indicators,
                'fake_score': len(fake_indicators) * 0.2,  # Simple scoring
                'real_score': max(0, 1 - len(fake_indicators) * 0.2)
            }
            
        except Exception as e:
            return {'error': str(e)}

class AWSRekognition:
    """AWS Rekognition integration"""
    
    def __init__(self, access_key=None, secret_key=None, region='us-east-1'):
        """Initialize AWS Rekognition"""
        self.access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = region
        self.base_url = f'https://rekognition.{region}.amazonaws.com'
    
    def analyze_image(self, image_path):
        """Analyze image using AWS Rekognition"""
        try:
            if not self.access_key or not self.secret_key:
                return {'error': 'AWS credentials not configured'}
            
            # This would require boto3 for proper AWS integration
            # For now, return a placeholder
            return {
                'service': 'AWS Rekognition',
                'status': 'not_implemented',
                'message': 'AWS integration requires boto3 library'
            }
            
        except Exception as e:
            return {'error': str(e)}

class AzureCognitiveServices:
    """Azure Cognitive Services integration"""
    
    def __init__(self, subscription_key=None, endpoint=None):
        """Initialize Azure Cognitive Services"""
        self.subscription_key = subscription_key or os.getenv('AZURE_SUBSCRIPTION_KEY')
        self.endpoint = endpoint or os.getenv('AZURE_ENDPOINT')
    
    def analyze_image(self, image_path):
        """Analyze image using Azure Cognitive Services"""
        try:
            if not self.subscription_key or not self.endpoint:
                return {'error': 'Azure credentials not configured'}
            
            # This would require proper Azure SDK
            # For now, return a placeholder
            return {
                'service': 'Azure Cognitive Services',
                'status': 'not_implemented',
                'message': 'Azure integration requires Azure SDK'
            }
            
        except Exception as e:
            return {'error': str(e)}

class TelegramBot:
    """Telegram Bot integration"""
    
    def __init__(self, bot_token=None):
        """Initialize Telegram Bot"""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'
    
    def send_analysis_result(self, chat_id, job_id, results):
        """Send analysis result to Telegram"""
        try:
            if not self.bot_token:
                return {'error': 'Telegram bot token not configured'}
            
            # Create message
            summary = results.get('summary', {})
            real_score = summary.get('real_score', 0.5)
            
            if real_score > 0.7:
                status = "🟢 حقيقي"
            elif real_score < 0.3:
                status = "🔴 مزيف"
            else:
                status = "🟡 مشكوك فيه"
            
            message = f"""
            📊 نتائج تحليل DeepFake
            
            🆔 معرف المهمة: {job_id}
            📈 النتيجة: {status}
            📊 احتمال الحقيقة: {real_score:.1%}
            📊 احتمال التزوير: {1-real_score:.1%}
            ⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # Send message
            url = f'{self.base_url}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                return {'success': True, 'message_id': response.json()['result']['message_id']}
            else:
                return {'error': f'Telegram API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def send_file(self, chat_id, file_path, caption=None):
        """Send file to Telegram"""
        try:
            if not self.bot_token:
                return {'error': 'Telegram bot token not configured'}
            
            url = f'{self.base_url}/sendDocument'
            
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'chat_id': chat_id,
                    'caption': caption or 'DeepFake Analysis Result'
                }
                
                response = requests.post(url, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                return {'success': True, 'message_id': response.json()['result']['message_id']}
            else:
                return {'error': f'Telegram API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}

class EmailService:
    """Email service integration"""
    
    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None):
        """Initialize email service"""
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.username = username or os.getenv('EMAIL_USERNAME')
        self.password = password or os.getenv('EMAIL_PASSWORD')
    
    def send_analysis_result(self, to_email, job_id, results, attachment_path=None):
        """Send analysis result via email"""
        try:
            if not self.username or not self.password:
                return {'error': 'Email credentials not configured'}
            
            from app.utils.additional_features import NotificationSystem
            
            notification_system = NotificationSystem()
            notification_system.email_config = {
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'username': self.username,
                'password': self.password
            }
            
            # Create message
            message = notification_system.create_notification_message(job_id, results)
            
            # Send email
            success = notification_system.send_email_notification(
                to_email,
                f'DeepFake Analysis Result - {job_id}',
                message,
                attachment_path
            )
            
            return {'success': success}
            
        except Exception as e:
            return {'error': str(e)}

class ExternalAPIManager:
    """Manage external API integrations"""
    
    def __init__(self):
        """Initialize external API manager"""
        self.services = {
            'google_vision': GoogleCloudVision(),
            'aws_rekognition': AWSRekognition(),
            'azure_cognitive': AzureCognitiveServices(),
            'telegram': TelegramBot(),
            'email': EmailService()
        }
    
    def get_available_services(self):
        """Get list of available services"""
        available = []
        for name, service in self.services.items():
            if hasattr(service, 'api_key') or hasattr(service, 'bot_token') or hasattr(service, 'username'):
                # Check if service is configured
                if (hasattr(service, 'api_key') and service.api_key) or \
                   (hasattr(service, 'bot_token') and service.bot_token) or \
                   (hasattr(service, 'username') and service.username):
                    available.append(name)
        return available
    
    def analyze_with_external_services(self, image_path, selected_services=None):
        """Analyze image with external services"""
        try:
            results = {}
            
            if selected_services is None:
                selected_services = self.get_available_services()
            
            for service_name in selected_services:
                if service_name in self.services:
                    service = self.services[service_name]
                    
                    if hasattr(service, 'analyze_image'):
                        print(f"🔄 Analyzing with {service_name}...")
                        result = service.analyze_image(image_path)
                        results[service_name] = result
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def send_notifications(self, job_id, results, notification_config):
        """Send notifications to external services"""
        try:
            sent_notifications = []
            
            # Telegram notification
            if 'telegram' in notification_config:
                telegram_config = notification_config['telegram']
                if 'chat_id' in telegram_config:
                    result = self.services['telegram'].send_analysis_result(
                        telegram_config['chat_id'],
                        job_id,
                        results
                    )
                    sent_notifications.append(('telegram', result))
            
            # Email notification
            if 'email' in notification_config:
                email_config = notification_config['email']
                if 'to_email' in email_config:
                    result = self.services['email'].send_analysis_result(
                        email_config['to_email'],
                        job_id,
                        results,
                        email_config.get('attachment_path')
                    )
                    sent_notifications.append(('email', result))
            
            return sent_notifications
            
        except Exception as e:
            return [('error', {'error': str(e)})]

# Global instance
external_api_manager = ExternalAPIManager()
