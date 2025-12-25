import os
import threading
import traceback
import requests
from datetime import datetime
from dotenv import load_dotenv
from app.db.database import get_ist_time

load_dotenv()

class EmailService:
    """
    State-of-the-Art Email Service using Brevo API.
    Handles high-performance background sending to both User and Admin.
    """
    
    def __init__(self):
        # 🟢 Configuration (Uses Brevo for reliability)
        load_dotenv()
        self.api_key = os.getenv("BREVO_API_KEY")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.admin_email = os.getenv("ADMIN_EMAIL", "riteshkumar90359@gmail.com")
        self.company_name = os.getenv("COMPANY_NAME", "Quickfix")
        self.app_url = os.getenv("APP_URL", "https://customer-complaint-agent-new.vercel.app")
        
        # 🛡️ Safety Validation: Force valid email format if .env is wrong
        if not self.sender_email or "@" not in self.sender_email:
            # If no sender email, use the admin email as a fallback sender (more likely to be verified)
            self.sender_email = self.admin_email if self.admin_email else "noreply@quickfix.com"
        
        if not self.api_key:
            print("\n⚠️ CRITICAL: BREVO_API_KEY not set in .env!")
            print("❌ Emails will be MOCKED (printed to console) instead of sending.\n")
    
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

    def send_otp(self, user_email: str, otp: str):
        """Send OTP to user in background"""
        thread = threading.Thread(
            target=self._worker_send_otp,
            args=(user_email, otp)
        )
        thread.daemon = True
        thread.start()
        return True
    
    def send_password_reset(self, user_email: str, user_name: str, reset_token: str):
        """Send password reset link to user in background"""
        thread = threading.Thread(
            target=self._worker_send_password_reset,
            args=(user_email, user_name, reset_token)
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
                subject = f"✅ Complaint Received - Ticket #{complaint_data.get('ticket_id', 'N/A')}"
                html_body = self._generate_confirmation_html(user_name, complaint_data, user_email)
                print(f"📧 Sending confirmation to USER: {user_email}...")
                self._dispatch_api(user_email, subject, html_body)
                
                # 2. Send to Admin
                admin_subject = f"🚨 NEW TICKET #{complaint_data.get('ticket_id', 'N/A')} - {complaint_data.get('category', 'General')}"
                admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
                print(f"📧 Sending notification to ADMIN...")
                self._dispatch_api(self.admin_email, admin_subject, admin_html)
                
            elif type == "resolution":
                # 1. Send to User
                subject = f"✅ Ticket #{complaint_data.get('ticket_id', 'N/A')} Resolved - Quickfix"
                html_body = self._generate_resolution_html(user_name, complaint_data, user_email)
                print(f"📧 Sending resolution to USER: {user_email}...")
                self._dispatch_api(user_email, subject, html_body)
                
                # 2. Send to Admin
                admin_subject = f"✅ RESOLVED: Ticket #{complaint_data.get('ticket_id', 'N/A')} - {user_name}"
                admin_html = self._generate_admin_resolution_html(user_name, user_email, complaint_data)
                print(f"📧 Sending resolution alert to ADMIN...")
                self._dispatch_api(self.admin_email, admin_subject, admin_html)
                
        except Exception as e:
            print(f"❌ Background Email Error: {str(e)}")
            traceback.print_exc()

    def _worker_send_otp(self, user_email: str, otp: str):
        """Background logic to send OTP"""
        try:
            subject = f"🔐 {otp} is your Quickfix Verification Code"
            html_body = self._generate_otp_html(otp)
            print(f"📧 Sending OTP to: {user_email}...")
            self._dispatch_api(user_email, subject, html_body)
        except Exception as e:
            print(f"❌ OTP Email Error: {str(e)}")
            traceback.print_exc()
    
    def _worker_send_password_reset(self, user_email: str, user_name: str, reset_token: str):
        """Background logic to send password reset link"""
        try:
            subject = "🔑 Reset Your Quickfix Password"
            html_body = self._generate_password_reset_html(user_name, reset_token, user_email)
            print(f"📧 Sending password reset link to: {user_email}...")
            self._dispatch_api(user_email, subject, html_body)
        except Exception as e:
            print(f"❌ Password Reset Email Error: {str(e)}")
            traceback.print_exc()
    
    def _generate_otp_html(self, otp: str) -> str:
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="400" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">Quickfix Auth</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px;">
                                Use the code below to sign in to your account. This code will expire in 10 minutes.
                            </p>
                            <div style="background-color: #f9fafb; border: 2px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                                <h2 style="margin: 0; color: #1f2937; font-size: 36px; font-weight: 700; letter-spacing: 5px;">
                                    {otp}
                                </h2>
                            </div>
                            <p style="margin: 0; color: #9ca3af; font-size: 13px;">
                                If you didn't request this code, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                                © {datetime.now().year} Quickfix. Secure Multi-Agent Intelligence.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _generate_password_reset_html(self, user_name: str, reset_token: str, user_email: str) -> str:
        reset_link = f"{self.app_url}/reset-password?token={reset_token}&email={user_email}"
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">Reset Your Password</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px;">
                                Hello {user_name},
                            </p>
                            <p style="margin: 0 0 30px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                We received a request to reset your password for your Quickfix account. Click the button below to create a new password.
                            </p>
                            <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                Reset Password
                            </a>
                            <p style="margin: 30px 0 0 0; color: #9ca3af; font-size: 13px; line-height: 1.6;">
                                This link will expire in 1 hour for security reasons.
                            </p>
                            <p style="margin: 20px 0 0 0; color: #9ca3af; font-size: 13px; line-height: 1.6;">
                                If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                                © {get_ist_time().year} Quickfix. Secure Multi-Agent Intelligence.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _dispatch_api(self, to_email: str, subject: str, html_body: str):
        """Internal dispatcher using Brevo HTTPS API"""
        if not self.api_key:
            print(f"\n📢 [MOCKED EMAIL] To: {to_email} | Subject: {subject}")
            print(f"   (Brevo API Key missing. Set BREVO_API_KEY in .env)\n")
            return
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "sender": {"name": self.company_name, "email": self.sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body
        }
        
        try:
            print(f"🚀 Dispatching email via Brevo... Sender: {self.sender_email}, To: {to_email}")
            response = requests.post(url, headers=headers, json=data, timeout=12)
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Success: Email delivered to {to_email} (ID: {response.json().get('messageId', 'N/A')})")
            else:
                print(f"⚠️ Brevo API Failure - Status: {response.status_code}")
                print(f"   Response Body: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error connecting to Brevo: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error in _dispatch_api: {str(e)}")
            traceback.print_exc()
    
    # ------------------------------------------------------------------
    # ADVANCED PROFESSIONAL HTML TEMPLATES
    # ------------------------------------------------------------------
    
    def _generate_confirmation_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        ticket_id = complaint_data.get('ticket_id', 'N/A')
        category = complaint_data.get('category', 'General')
        priority = complaint_data.get('priority', 'Medium')
        complaint_text = complaint_data.get('complaint_text', 'N/A')
        sentiment = complaint_data.get('sentiment', 'Analyzing...')
        response = complaint_data.get('response', 'Processing your request...')
        solution = complaint_data.get('solution', 'Generating solution...')
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
        priority_colors = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#10b981"}
        priority_color = priority_colors.get(priority, "#3b82f6")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complaint Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
                                🎯 Quickfix Support
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 14px;">
                                Ticket ID: {ticket_id}
                            </p>
                        </td>
                    </tr>

                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 0 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 20px; font-weight: 600;">
                                Hello {user_name},
                            </h3>
                            <p style="margin: 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                Thank you for reaching out to Quickfix. We've successfully received your complaint and our advanced AI system is already analyzing your issue to provide the most effective solution.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Complaint Details -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                            Category
                                        </p>
                                        <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 500;">
                                            {category}
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                            Priority Level
                                        </p>
                                        <span style="display: inline-block; background-color: {priority_color}; color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                            {priority}
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                            Submitted On
                                        </p>
                                        <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 500;">
                                            {timestamp}
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                            Your Message
                                        </p>
                                        <p style="margin: 0; color: #4b5563; font-size: 14px; line-height: 1.6; font-style: italic;">
                                            "{complaint_text[:200]}{'...' if len(complaint_text) > 200 else ''}"
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- AI Analysis -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; border-radius: 8px; padding: 20px;">
                                <h4 style="margin: 0 0 15px 0; color: #92400e; font-size: 16px; font-weight: 600;">
                                    🤖 AI-Powered Analysis
                                </h4>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #78350f; font-size: 13px; font-weight: 600;">
                                                Sentiment Analysis:
                                            </p>
                                            <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                                {sentiment}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #78350f; font-size: 13px; font-weight: 600;">
                                                Automated Response:
                                            </p>
                                            <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                                {response}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 5px 0; color: #78350f; font-size: 13px; font-weight: 600;">
                                                Proposed Solution:
                                            </p>
                                            <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                                {solution}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 10px 30px 30px 30px; text-align: center;">
                            <a href="{self.app_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                View Complete Dashboard
                            </a>
                        </td>
                    </tr>
                    
                    <!-- What's Next -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #eff6ff; border-radius: 8px; padding: 20px;">
                                <h4 style="margin: 0 0 12px 0; color: #1e40af; font-size: 15px; font-weight: 600;">
                                    📌 What Happens Next?
                                </h4>
                                <ul style="margin: 0; padding-left: 20px; color: #1e3a8a; font-size: 14px; line-height: 1.8;">
                                    <li>Our AI system is analyzing your complaint in real-time</li>
                                    <li>You'll receive updates via email as we progress</li>
                                    <li>A dedicated support agent will review if needed</li>
                                
                                </ul>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;">
                                Need immediate assistance? Reply to this email or visit our help center.
                            </p>
                            <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 12px;">
                                © {datetime.now().year} Quickfix. All rights reserved.
                            </p>
                            <div style="margin-top: 15px;">
                                <a href="{self.app_url}" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Help Center</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="{self.app_url}" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Privacy Policy</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="{self.app_url}" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Contact Us</a>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    def _generate_resolution_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        category = complaint_data.get('category', 'General')
        solution = complaint_data.get('solution', 'Your issue has been resolved.')
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complaint Resolved</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 20px; font-weight: 600;">
                                Dear {user_name},
                            </h3>
                            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                Great news! Your complaint has been successfully resolved by our AI-powered support system. We've implemented a comprehensive solution tailored to address your specific concern.
                            </p>
                            
                            <!-- Resolution Details -->
                            <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                <h4 style="margin: 0 0 12px 0; color: #065f46; font-size: 16px; font-weight: 600;">
                                    💡 Resolution Details
                                </h4>
                                <p style="margin: 0 0 10px 0; color: #047857; font-size: 14px; line-height: 1.6;">
                                    <strong>Category:</strong> {category}
                                </p>
                                <p style="margin: 0 0 10px 0; color: #047857; font-size: 14px; line-height: 1.6;">
                                    <strong>Resolved On:</strong> {timestamp}
                                </p>
                                <p style="margin: 0; color: #047857; font-size: 14px; line-height: 1.6;">
                                    <strong>Solution:</strong><br>
                                    {solution}
                                </p>
                            </div>
                            
                            <!-- Feedback Request -->
                            <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                <h4 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                    📊 How Was Your Experience?
                                </h4>
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                    Your feedback helps us improve our service. Please take a moment to rate your experience.
                                </p>
                                <div style="text-align: center;">
                                    <a href="{self.app_url}" style="display: inline-block; background-color: #10b981; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 6px; font-weight: 600; font-size: 14px; margin: 0 5px;">
                                        Rate Experience
                                    </a>
                                </div>
                            </div>
                            
                            <p style="margin: 25px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If you have any additional questions or concerns, please don't hesitate to reach out. We're here to help!
                            </p>
                        </td>
                    </tr>
                    
                    <!-- CTA -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <a href="{self.app_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 600; font-size: 15px;">
                                View Ticket History
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;">
                                Thank you for choosing Quickfix!
                            </p>
                            <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 12px;">
                                © {get_ist_time().year} Quickfix. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    def _generate_admin_notification_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        user_name = user_name or "Valued Customer"
        category = complaint_data.get('category', 'General')
        priority = complaint_data.get('priority', 'Medium')
        complaint_text = complaint_data.get('complaint_text', 'N/A')
        sentiment = complaint_data.get('sentiment', 'N/A')
        response = complaint_data.get('response', 'N/A')
        solution = complaint_data.get('solution', 'N/A')
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
        priority_colors = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#10b981"}
        priority_color = priority_colors.get(priority, "#3b82f6")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Complaint Alert</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="650" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 30px; text-align: center;">
                            <div style="font-size: 42px; margin-bottom: 10px;">🚨</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                New Complaint Received
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #fecaca; font-size: 14px;">
                                Immediate Action May Be Required
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Priority Badge -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 50%;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">
                                            Ticket ID
                                        </p>
                                        <h2 style="margin: 0; color: #1f2937; font-size: 24px; font-weight: 700;">
                                            {complaint_data.get('ticket_id', 'N/A')}
                                        </h2>
                                    </td>
                                    <td style="width: 50%; text-align: right;">
                                        <span style="display: inline-block; background-color: {priority_color}; color: #ffffff; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                                            {priority} Priority
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Customer Info -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                            👤 Customer Information
                                        </h3>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Email:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{user_email}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Submitted:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{timestamp}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Complaint Summary -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #991b1b; font-size: 16px; font-weight: 600;">
                                    📋 Complaint Details
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #7f1d1d; font-size: 13px; font-weight: 600;">
                                                Category:
                                            </p>
                                            <p style="margin: 0; color: #991b1b; font-size: 14px; line-height: 1.5;">
                                                {category}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 5px 0; color: #7f1d1d; font-size: 13px; font-weight: 600;">
                                                Customer Message:
                                            </p>
                                            <p style="margin: 0; color: #991b1b; font-size: 14px; line-height: 1.6; font-style: italic;">
                                                "{complaint_text}"
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- AI Analysis -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #1e40af; font-size: 16px; font-weight: 600;">
                                    🤖 AI Analysis Results
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 13px; font-weight: 600;">
                                                Sentiment Detected:
                                            </p>
                                            <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.5;">
                                                {sentiment}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 13px; font-weight: 600;">
                                                AI Response:
                                            </p>
                                            <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.5;">
                                                {response}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 13px; font-weight: 600;">
                                                Proposed Solution:
                                            </p>
                                            <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.5;">
                                                {solution}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Action Required -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #fef9c3; border-radius: 8px; padding: 20px; text-align: center;">

                                <a href="{self.app_url}" style="display: inline-block; background-color: #ef4444; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 6px; font-weight: 600; font-size: 14px;">
                                    View in Dashboard
                                </a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                This is an automated notification from Quickfix Admin System
                            </p>
                            <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 11px;">
                                © {datetime.now().year} Quickfix Admin Portal
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    def _generate_admin_resolution_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        category = complaint_data.get('category', 'General')
        solution = complaint_data.get('solution', 'Issue resolved')
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complaint Resolved - Admin</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="650" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center;">
                            <div style="font-size: 42px; margin-bottom: 10px;">✅</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Ticket Resolved Successfully
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #d1fae5; font-size: 14px;">
                                Admin Notification
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Ticket Info -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 50%;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">
                                            Ticket ID
                                        </p>
                                    </td>
                                    <td style="width: 50%; text-align: right;">
                                        <span style="display: inline-block; background-color: #10b981; color: #ffffff; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                                            RESOLVED
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Customer Info -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                            👤 Customer Details
                                        </h3>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Name:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{user_name}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Email:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{user_email}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Resolved On:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{timestamp}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Resolution Summary -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #065f46; font-size: 16px; font-weight: 600;">
                                    📋 Resolution Summary
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-bottom: 12px;">
                                            <p style="margin: 0 0 5px 0; color: #064e3b; font-size: 13px; font-weight: 600;">
                                                Category:
                                            </p>
                                            <p style="margin: 0; color: #065f46; font-size: 14px; line-height: 1.5;">
                                                {category}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 5px 0; color: #064e3b; font-size: 13px; font-weight: 600;">
                                                Solution Provided:
                                            </p>
                                            <p style="margin: 0; color: #065f46; font-size: 14px; line-height: 1.6;">
                                                {solution}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Action Button -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <a href="{self.app_url}" style="display: inline-block; background-color: #10b981; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 6px; font-weight: 600; font-size: 14px;">
                                View Full Details
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                Automated notification from Quickfix Admin System
                            </p>
                            <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 11px;">
                                © {datetime.now().year} Quickfix Admin Portal
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


# Initialize email service
email_service = EmailService()