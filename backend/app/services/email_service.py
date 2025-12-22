import os
from datetime import datetime
import requests
import traceback

class EmailService:
    """Service for sending emails via Resend API"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        
        # ✅ UPDATED: Domain set to quickfix.com
        # Ensure you have verified 'quickfix.com' in Resend console!
        self.sender_email = "noreply@quickfix.com" 
        
        self.admin_email = "riteshkumar90359@gmail.com"
        
        if not self.api_key:
            print("⚠️ WARNING: RESEND_API_KEY not set!")

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email to the User"""
        try:
            # Determine Recipient based on Mode
            is_production = os.getenv("EMAIL_MODE") == "production"
            recipient = user_email if is_production else self.admin_email
            
            subject = f"✅ Complaint Received - {user_name}"
            
            # Add testing prefix if not in production
            if not is_production and user_email != self.admin_email:
                subject = f"[TESTING MODE - TO: {user_email}] {subject}"
            
            html_body = self._generate_confirmation_html(user_name, complaint_data, user_email)
            
            print(f"📧 Attempting to send User Confirmation to: {recipient} via {self.sender_email}")
            self._send_email(recipient, subject, html_body)
            print(f"✅ User confirmation sent successfully!")
            
            # Send Admin Notification
            self._send_admin_notification(user_name, user_email, complaint_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send confirmation: {str(e)}")
            traceback.print_exc()
            return False

    def _send_admin_notification(self, user_name: str, user_email: str, complaint_data: dict):
        """Helper to send the Admin Notification"""
        try:
            admin_subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
            admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
            self._send_email(self.admin_email, admin_subject, admin_html)
            print(f"✅ Admin notification sent")
        except Exception as e:
            print(f"❌ Failed to send admin notification: {str(e)}")

    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email when complaint is solved"""
        try:
            is_production = os.getenv("EMAIL_MODE") == "production"
            recipient = user_email if is_production else self.admin_email

            subject = f"✅ RESOLVED - {user_name}'s Complaint"
            if not is_production and user_email != self.admin_email:
                subject = f"[TESTING MODE - TO: {user_email}] {subject}"
            
            html_body = self._generate_resolution_html(user_name, complaint_data, user_email)
            self._send_email(recipient, subject, html_body)
            print(f"✅ Resolution email sent (intended for: {user_email})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send resolution email: {str(e)}")
            return False

    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Internal method to send email via Resend API"""
        if not self.api_key:
            raise Exception("RESEND_API_KEY not configured!")

        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": self.sender_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 403:
                error_data = response.json()
                msg = error_data.get("message", "").lower()
                if "domain" in msg or "verified" in msg:
                    raise Exception(
                        f"⛔ DOMAIN ERROR: Resend rejected emails from '{self.sender_email}'.\n"
                        f"Reason: The domain 'quickfix.com' is not verified in your Resend dashboard.\n"
                        f"Fix: Go to https://resend.com/domains and verify DNS records."
                    )
            
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"API Error {response.status_code}: {response.text}")

            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    # ---------------------------------------------------------
    # Paste your existing HTML generator methods below here
    # (_generate_confirmation_html, _generate_admin_notification_html, etc.)
    # ---------------------------------------------------------
    def _generate_confirmation_html(self, user_name, complaint_data, user_email):
        # (Keep your original HTML code here)
        return f"<h1>Complaint Received</h1><p>Hi {user_name}, we received your complaint.</p>"

    def _generate_admin_notification_html(self, user_name, user_email, complaint_data):
        # (Keep your original HTML code here)
        return f"<h1>New Complaint</h1><p>User: {user_name}</p>"

    def _generate_resolution_html(self, user_name, complaint_data, user_email):
        # (Keep your original HTML code here)
        return f"<h1>Resolved</h1><p>Hi {user_name}, your issue is fixed.</p>"
