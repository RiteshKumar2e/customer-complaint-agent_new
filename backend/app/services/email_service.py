import os
import threading
import traceback
import json
import requests
from datetime import datetime

class EmailService:
    """
    Fixed & Optimized Email Service.
    Uses Brevo (formerly Sendinblue) API.
    Reliable HTTPS-based delivery (avoids SMTP network errors).
    """

    def __init__(self):
        # Configuration
        self.api_key = os.getenv("BREVO_API_KEY")
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@quickfix.com")
        self.admin_email = "riteshkumar90359@gmail.com"
        self.company_name = "Quickfix"
        
        # Validation
        if not self.api_key:
            print("\n⚠️  BREVO_API_KEY not found in .env!")
            print("📝 Get one at: https://www.brevo.com/")
            print("ℹ️  DURING DEVELOPMENT: Emails will be printed to Console only.\n")

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email in background"""
        thread = threading.Thread(
            target=self._worker_send_all,
            args=("confirmation", user_name, user_email, complaint_data)
        )
        thread.daemon = True
        thread.start()
        return True

    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email in background"""
        thread = threading.Thread(
            target=self._worker_send_all,
            args=("resolution", user_name, user_email, complaint_data)
        )
        thread.daemon = True
        thread.start()
        return True

    # ------------------------------------------------------------------
    # Worker Logic
    # ------------------------------------------------------------------

    def _worker_send_all(self, type: str, user_name: str, user_email: str, complaint_data: dict):
        """Unified background worker for all email types"""
        try:
            if type == "confirmation":
                # 1. User Confirmation
                subject = f"✅ Complaint Received - {user_name}"
                html = self._generate_confirmation_html(user_name, complaint_data)
                self._dispatch(user_email, subject, html)
                
                # 2. Admin Alert
                admin_subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
                admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
                self._dispatch(self.admin_email, admin_subject, admin_html)
                
            elif type == "resolution":
                # 1. User Resolution
                subject = f"✅ RESOLVED - {user_name}'s Complaint"
                html = self._generate_resolution_html(user_name, complaint_data)
                self._dispatch(user_email, subject, html)
                
                # 2. Admin Alert
                admin_subject = f"✅ RESOLVED: {user_name}"
                admin_html = self._generate_admin_resolution_html(user_name, user_email, complaint_data)
                self._dispatch(self.admin_email, admin_subject, admin_html)
                
        except Exception as e:
            print(f"❌ Email Delivery failed: {str(e)}")

    def _dispatch(self, to_email: str, subject: str, html_body: str):
        """Internal dispatcher: API vs Console"""
        if not self.api_key:
            print(f"\n--- [MOCK EMAIL] ---")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: [HTML Content Hidden]")
            print(f"---------------------\n")
            return

        # Brevo API Call
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
                print(f"✅ Email sent to {to_email}")
        except Exception as e:
            print(f"❌ Brevo Connection Error: {str(e)}")

    # ------------------------------------------------------------------
    # HTML Templates
    # ------------------------------------------------------------------

    def _generate_confirmation_html(self, user_name: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                    <div style="background: #4F46E5; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Quickfix Confirmation</h1>
                    </div>
                    <div style="padding: 20px;">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>We've received your complaint and it's being analyzed by our AI system.</p>
                        <div style="background: #F3F4F6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                            <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                            <p><strong>Description:</strong> {complaint_data.get('complaint_text', 'N/A')[:100]}...</p>
                        </div>
                        <p>You can track the progress on your dashboard.</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_resolution_html(self, user_name: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                    <div style="background: #10B981; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Complaint Resolved</h1>
                    </div>
                    <div style="padding: 20px;">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>Your issue has been resolved successfully.</p>
                        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 15px; border-radius: 4px; margin: 20px 0;">
                            <p><strong>Solution:</strong> {complaint_data.get('solution', 'N/A')}</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_notification_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <body>
                <h2 style="color: #DC2626;">🚨 New System Complaint</h2>
                <p><strong>User:</strong> {user_name} ({user_email})</p>
                <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                <p><strong>Text:</strong> {complaint_data.get('complaint_text', 'N/A')}</p>
                <hr>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
        </html>
        """

    def _generate_admin_resolution_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <body>
                <h2 style="color: #059669;">✅ Resolution Update</h2>
                <p>Complaint from <strong>{user_name}</strong> ({user_email}) has been marked as resolved.</p>
            </body>
        </html>
        """

# Initialize service
email_service = EmailService()