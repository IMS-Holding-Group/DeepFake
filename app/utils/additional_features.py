"""
Additional features for DeepFake detection system
ميزات إضافية لنظام كشف DeepFake
"""

import os
import json
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import cv2
import numpy as np
from PIL import Image as PILImage
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class ReportGenerator:
    """Generate detailed PDF reports"""
    
    def __init__(self):
        """Initialize report generator"""
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for PDF"""
        self.styles.add(ParagraphStyle(
            name='ArabicTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArabicHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.darkgreen,
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArabicBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6
        ))
    
    def generate_pdf_report(self, job_id, results, output_path):
        """Generate comprehensive PDF report"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            
            # Title
            title = Paragraph("تقرير تحليل DeepFake", self.styles['ArabicTitle'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Job information
            job_info = f"""
            <b>معرف المهمة:</b> {job_id}<br/>
            <b>تاريخ التحليل:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>نوع الملف:</b> {results.get('file_type', 'غير محدد')}<br/>
            """
            story.append(Paragraph(job_info, self.styles['ArabicBody']))
            story.append(Spacer(1, 12))
            
            # Summary
            summary_title = Paragraph("ملخص النتائج", self.styles['ArabicHeading'])
            story.append(summary_title)
            
            summary = results.get('summary', {})
            real_score = summary.get('real_score', 0.5)
            fake_score = summary.get('fake_score', 0.5)
            
            summary_text = f"""
            <b>احتمال الحقيقة:</b> {real_score:.1%}<br/>
            <b>احتمال التزوير:</b> {fake_score:.1%}<br/>
            <b>مستوى الثقة:</b> {summary.get('confidence', 0.5):.1%}<br/>
            """
            story.append(Paragraph(summary_text, self.styles['ArabicBody']))
            story.append(Spacer(1, 12))
            
            # Detailed analysis
            if 'explanations' in summary:
                details_title = Paragraph("تفاصيل التحليل", self.styles['ArabicHeading'])
                story.append(details_title)
                
                for explanation in summary['explanations']:
                    exp_text = f"""
                    <b>{explanation.get('type', 'غير محدد')}:</b><br/>
                    {explanation.get('detail', 'لا توجد تفاصيل')}<br/>
                    """
                    story.append(Paragraph(exp_text, self.styles['ArabicBody']))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            return output_path
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None
    
    def generate_json_report(self, job_id, results, output_path):
        """Generate detailed JSON report"""
        try:
            report_data = {
                'job_id': job_id,
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'metadata': {
                    'version': '1.0',
                    'generator': 'DeepFake Detection System'
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            return output_path
            
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")
            return None

class FileTypeSupport:
    """Extended file type support"""
    
    def __init__(self):
        """Initialize file type support"""
        self.supported_formats = {
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            'videos': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            'documents': ['.pdf', '.doc', '.docx']  # For future expansion
        }
    
    def is_supported(self, filename):
        """Check if file type is supported"""
        ext = os.path.splitext(filename)[1].lower()
        all_formats = []
        for formats in self.supported_formats.values():
            all_formats.extend(formats)
        return ext in all_formats
    
    def get_file_category(self, filename):
        """Get file category"""
        ext = os.path.splitext(filename)[1].lower()
        
        for category, formats in self.supported_formats.items():
            if ext in formats:
                return category
        
        return 'unknown'
    
    def convert_to_supported_format(self, input_path, output_path, target_format):
        """Convert file to supported format"""
        try:
            if target_format in ['png', 'jpg', 'jpeg']:
                # Convert image
                img = PILImage.open(input_path)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, target_format.upper())
                return output_path
            
            elif target_format in ['mp4', 'avi']:
                # Convert video (requires ffmpeg)
                import subprocess
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-y', output_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return output_path
            
            return None
            
        except Exception as e:
            print(f"❌ File conversion failed: {e}")
            return None

class LiveStreamAnalyzer:
    """Analyze live video streams"""
    
    def __init__(self):
        """Initialize live stream analyzer"""
        self.is_analyzing = False
        self.analysis_results = []
    
    def start_live_analysis(self, stream_url, callback_func):
        """Start live stream analysis"""
        try:
            self.is_analyzing = True
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open stream: {stream_url}")
            
            frame_count = 0
            while self.is_analyzing:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Analyze every 30th frame
                if frame_count % 30 == 0:
                    result = self._analyze_frame(frame, frame_count)
                    if callback_func:
                        callback_func(result)
                
                frame_count += 1
            
            cap.release()
            
        except Exception as e:
            print(f"❌ Live analysis failed: {e}")
        finally:
            self.is_analyzing = False
    
    def _analyze_frame(self, frame, frame_number):
        """Analyze single frame"""
        try:
            from app.models.ensemble import DeepFakeDetector
            
            detector = DeepFakeDetector()
            result = detector.analyze_image_frame(frame, frame_number)
            
            return {
                'frame_number': frame_number,
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
            
        except Exception as e:
            return {
                'frame_number': frame_number,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def stop_live_analysis(self):
        """Stop live analysis"""
        self.is_analyzing = False

class NotificationSystem:
    """Notification system for analysis results"""
    
    def __init__(self):
        """Initialize notification system"""
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
    
    def send_email_notification(self, to_email, subject, body, attachment_path=None):
        """Send email notification"""
        try:
            if not self.email_config['username'] or not self.email_config['password']:
                print("⚠️ Email credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['username'], to_email, text)
            server.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    
    def send_telegram_notification(self, bot_token, chat_id, message):
        """Send Telegram notification"""
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram notification failed: {e}")
            return False
    
    def create_notification_message(self, job_id, results):
        """Create notification message"""
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
        
        return message

class BatchProcessor:
    """Process multiple files in batch"""
    
    def __init__(self):
        """Initialize batch processor"""
        self.results = []
        self.errors = []
    
    def process_batch(self, file_paths, output_dir):
        """Process multiple files"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for i, file_path in enumerate(file_paths):
                try:
                    print(f"🔄 Processing {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                    
                    # Analyze file
                    result = self._analyze_file(file_path)
                    
                    # Save result
                    output_file = os.path.join(output_dir, f"result_{i+1}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    self.results.append(result)
                    
                except Exception as e:
                    error = {
                        'file': file_path,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.errors.append(error)
                    print(f"❌ Error processing {file_path}: {e}")
            
            # Generate batch summary
            summary = self._generate_batch_summary()
            summary_file = os.path.join(output_dir, 'batch_summary.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Batch processing completed: {len(self.results)} successful, {len(self.errors)} errors")
            return summary
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            return None
    
    def _analyze_file(self, file_path):
        """Analyze single file"""
        from app.models.ensemble import DeepFakeDetector
        
        detector = DeepFakeDetector()
        
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            result = detector.analyze_image(file_path)
        else:
            result = detector.analyze_video(file_path)
        
        result['file_path'] = file_path
        result['timestamp'] = datetime.now().isoformat()
        
        return result
    
    def _generate_batch_summary(self):
        """Generate batch processing summary"""
        summary = {
            'total_files': len(self.results) + len(self.errors),
            'successful': len(self.results),
            'errors': len(self.errors),
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'errors': self.errors
        }
        
        if self.results:
            # Calculate average scores
            real_scores = [r['summary']['real_score'] for r in self.results if 'summary' in r]
            if real_scores:
                summary['average_real_score'] = np.mean(real_scores)
                summary['average_fake_score'] = 1 - np.mean(real_scores)
        
        return summary
