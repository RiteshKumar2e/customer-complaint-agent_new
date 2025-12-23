import os
import threading
import traceback
import requests
from datetime import datetime

class EmailService:
    """
    State-of-the-Art Email Service using Brevo API.
    Handles high-performance background sending to both User and Admin.
    """
    
    def __init__(self):
        # 🟢 Configuration (Uses Brevo for reliability)
        self.api_key = os.getenv("BREVO_API_KEY")
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@quickfix.com")
        self.admin_email = "riteshkumar90359@gmail.com"
        self.company_name = "Quickfix"
        
        # 🛡️ Safety Validation: Force valid email format if .env is wrong
        if "@" not in self.sender_email:
            self.sender_email = "noreply@quickfix.com"

        if not self.api_key:
            print("\n⚠️  CRITICAL: BREVO_API_KEY not set in .env!")
            print("📝 Get one at: https://www.brevo.com/")
            print("❌ Emails will print to console instead of sending.\n")

    # ------------------------------------------------------------------
    # PUBLIC METHODS (Threaded for Speed)
    # ------------------------------------------------------------------

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email to BOTH User and Admin in background"""
        thread = threading.Thread(
            target=self._worker_send_notification,
            args=("complaint", user_name, user_email, complaint_data)
        )
        thread.daemon = True
        thread.start()
        return True

    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email to BOTH User and Admin in background"""
        thread = threading.Thread(
            target=self._worker_send_notification,
            args=("resolution", user_name, user_email, complaint_data)
        )
        thread.daemon = True
        thread.start()
        return True

    # ------------------------------------------------------------------
    # BACKGROUND WORKER
    # ------------------------------------------------------------------

    def _worker_send_notification(self, type: str, user_name: str, user_email: str, complaint_data: dict):
        """Background logic to dispatch both emails"""
        try:
            if type == "complaint":
                # 1. Send to User
                subject = f"✅ Complaint Received - {user_name}"
                html_body = self._generate_confirmation_html(user_name, complaint_data, user_email)
                print(f"📧 Sending confirmation to USER: {user_email}...")
                self._dispatch_api(user_email, subject, html_body)
                
                # 2. Send to Admin
                admin_subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
                admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
                print(f"📧 Sending notification to ADMIN...")
                self._dispatch_api(self.admin_email, admin_subject, admin_html)

            elif type == "resolution":
                # 1. Send to User
                subject = f"✅ RESOLVED - {user_name}'s Complaint"
                html_body = self._generate_resolution_html(user_name, complaint_data, user_email)
                print(f"📧 Sending resolution to USER: {user_email}...")
                self._dispatch_api(user_email, subject, html_body)
                
                # 2. Send to Admin
                admin_subject = f"✅ RESOLVED: {user_name} - {complaint_data.get('category', 'General')}"
                admin_html = self._generate_admin_resolution_html(user_name, user_email, complaint_data)
                print(f"📧 Sending resolution alert to ADMIN...")
                self._dispatch_api(self.admin_email, admin_subject, admin_html)

        except Exception as e:
            print(f"❌ Background Email Error: {str(e)}")
            traceback.print_exc()

    def _dispatch_api(self, to_email: str, subject: str, html_body: str):
        """Internal dispatcher using Brevo HTTPS API"""
        if not self.api_key:
            print(f"\n📢 [MOCKED EMAIL] To: {to_email} | Subject: {subject}\n")
            return

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "sender": {"name": self.company_name, "email": self.sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code not in [200, 201, 202]:
                print(f"⚠️ Brevo Error ({response.status_code}): {response.text}")
            else:
                print(f"✅ Success: Email delivered to {to_email}")
        except Exception as e:
            print(f"❌ Error connecting to Brevo: {str(e)}")

    # ------------------------------------------------------------------
    # HTML GENERATION METHODS (Your Preferred Rich Templates)
    # ------------------------------------------------------------------

    def _generate_confirmation_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                    .content {{ padding: 30px; }}
                    .info-box {{ background: #f0f4ff; padding: 20px; margin: 20px 0; border-left: 4px solid #667eea; border-radius: 6px; }}
                    .info-box h3 {{ margin: 0 0 15px 0; color: #667eea; font-size: 16px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                    .footer {{ background: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 Thank You for Contacting Quickfix</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Your complaint has been received</p>
                    </div>
                    <div class="content">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>We have successfully received your complaint. Our AI-powered system is analyzing your issue to provide the best solution.</p>
                        
                        <div class="info-box">
                            <h3>📋 Your Complaint Details</h3>
                            <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                            <p><strong>Priority:</strong> <span style="color: #ff6b6b; font-weight: 600;">{complaint_data.get('priority', 'N/A')}</span></p>
                            <p><strong>Description:</strong> {complaint_data.get('complaint_text', 'N/A')[:150]}...</p>
                        </div>
                        
                        <div class="info-box">
                            <h3>🤖 AI Analysis Results</h3>
                            <p><strong>Sentiment:</strong> {complaint_data.get('sentiment', 'Analyzing...')}</p>
                            <p><strong>Our Response:</strong> {complaint_data.get('response', 'Processing...')}</p>
                            <p><strong>Proposed Solution:</strong> {complaint_data.get('solution', 'Generating solution...')}</p>
                        </div>
                        
                        <center>
                            <a href="http://localhost:5173/dashboard" class="button">📊 View Dashboard</a>
                        </center>
                        
                        <p style="margin-top: 30px;">Best regards,<br>The Quickfix Support Team</p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Quickfix. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_resolution_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .success-box {{ background: #f0fff4; padding: 20px; margin: 20px 0; border-left: 4px solid #38ef7d; border-radius: 6px; }}
                    .button {{ display: inline-block; background: #38ef7d; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                    .footer {{ background: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Complaint Resolved Successfully!</h1>
                    </div>
                    <div class="content">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>Great news! Our AI system has successfully analyzed and resolved your complaint.</p>
                        <div class="success-box">
                            <h3>📋 Complaint Summary</h3>
                            <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                            <p><strong>Solution:</strong> {complaint_data.get('solution', 'N/A')}</p>
                        </div>
                        <center>
                            <a href="http://localhost:5173/dashboard" class="button">📊 View Full Details</a>
                        </center>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_notification_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        priority_colors = {"High": "#ff4444", "Medium": "#ff9900", "Low": "#00cc66"}
        priority = complaint_data.get('priority', 'Medium')
        color = priority_colors.get(priority, "#0066cc")
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 700px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="background: #ff6b6b; color: white; padding: 20px; margin: 0;">🚨 New Complaint Alert</h2>
                    <div style="padding: 20px;">
                        <p><strong>Customer:</strong> {user_name} ({user_email})</p>
                        <p><strong>Priority:</strong> <span style="color: {color}; font-weight: bold;">{priority}</span></p>
                        <hr>
                        <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>                        
                        <p><strong>Description:</strong><br>{complaint_data.get('complaint_text', 'N/A')}</p>
                        <hr>
                        <h4>🤖 AI Analysis</h4>
                        <p><strong>Response:</strong> {complaint_data.get('response', '-')}</p>
                        <p><strong>Solution:</strong> {complaint_data.get('solution', '-')}</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_resolution_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 700px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="background: #38ef7d; color: white; padding: 20px; margin: 0;">✅ Complaint Resolved</h2>
                    <div style="padding: 20px;">
                        <p><strong>Customer:</strong> {user_name} ({user_email})</p>
                        <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                        <p><strong>Solution Provided:</strong><br>{complaint_data.get('solution', 'N/A')}</p>
                    </div>
                </div>
            </body>
        </html>
        """

# Initialize email service
email_service = EmailService()