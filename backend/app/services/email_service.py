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
        self.app_url = os.getenv("APP_URL", "https://riteshkr.online")
        
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
    
    def send_resolution_email(self, name: str, email: str, ticket_id: str, subject: str, solution: str):
        """Send resolution email to BOTH User and Admin in background"""
        complaint_data = {
            'ticket_id': ticket_id,
            'subject': subject,
            'solution': solution,
            'category': 'Resolved'
        }
        thread = threading.Thread(
            target=self._worker_send_notification,
            args=("resolution", name, email, complaint_data)
        )
        thread.daemon = True
        thread.start()
        return True

    def send_otp(self, user_email: str, otp: str):
        """Send OTP to user with INSTANT priority - Non-blocking for speed"""
        # 🚀 INSTANT SEND: Fire-and-forget for maximum speed
        thread = threading.Thread(
            target=self._worker_send_otp,
            args=(user_email, otp),
            name="OTP-Instant-Delivery"  # Named thread for debugging
        )
        thread.daemon = False  # Non-daemon ensures completion even if main thread exits
        thread.start()
        # No blocking - return immediately for fastest API response
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
    
    def send_resolution_feedback_to_admin(self, user_name: str, user_email: str, ticket_id: str, 
                                         subject: str, is_actually_resolved: bool, 
                                         user_comment: str, original_solution: str):
        """Send user's resolution feedback to admin"""
        thread = threading.Thread(
            target=self._worker_send_resolution_feedback,
            args=(user_name, user_email, ticket_id, subject, is_actually_resolved, user_comment, original_solution)
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
        """INSTANT OTP delivery with priority handling"""
        try:
            subject = f"🔐 {otp} is your Quickfix Verification Code"
            html_body = self._generate_otp_html(otp)
            print(f"⚡ [PRIORITY] Sending OTP to: {user_email}...")
            # Use priority dispatch for OTP (faster timeout)
            self._dispatch_api(user_email, subject, html_body, priority=True)
            print(f"✅ OTP sent successfully to {user_email}")
        except Exception as e:
            print(f"❌ CRITICAL: OTP Email Failed for {user_email}")
            print(f"   Error: {str(e)}")
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
    
    def _worker_send_resolution_feedback(self, user_name: str, user_email: str, ticket_id: str,
                                        subject: str, is_actually_resolved: bool, 
                                        user_comment: str, original_solution: str):
        """Background logic to send resolution feedback to admin"""
        try:
            status_text = "RESOLVED ✅" if is_actually_resolved else "NOT RESOLVED ❌"
            email_subject = f"📊 User Feedback: Ticket #{ticket_id} - {status_text}"
            html_body = self._generate_resolution_feedback_html(
                user_name, user_email, ticket_id, subject, 
                is_actually_resolved, user_comment, original_solution
            )
            print(f"📧 Sending resolution feedback to ADMIN for ticket {ticket_id}...")
            self._dispatch_api(self.admin_email, email_subject, html_body)
        except Exception as e:
            print(f"❌ Resolution Feedback Email Error: {str(e)}")
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

    def _dispatch_api(self, to_email: str, subject: str, html_body: str, priority: bool = False):
        """Internal dispatcher using Brevo HTTPS API with priority support"""
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
        
        # 🚀 PRIORITY: Faster timeout for OTP emails (3s vs 12s)
        timeout_duration = 3 if priority else 10
        
        try:
            priority_label = "[PRIORITY OTP]" if priority else ""
            print(f"🚀 {priority_label} Dispatching via Brevo... To: {to_email}")
            
            response = requests.post(url, headers=headers, json=data, timeout=timeout_duration)
            
            if response.status_code in [200, 201, 202]:
                msg_id = response.json().get('messageId', 'N/A')
                print(f"✅ {priority_label} Email delivered to {to_email} (ID: {msg_id})")
            else:
                print(f"⚠️ Brevo API Failure - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT: Email to {to_email} took longer than {timeout_duration}s")
            print(f"   This may indicate network issues or Brevo API slowness")
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {str(e)}")
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
        
        # Enhanced color schemes with backgrounds
        priority_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
        priority_bg = {"High": "#fee2e2", "Medium": "#fef3c7", "Low": "#d1fae5"}
        priority_color = priority_colors.get(priority, "#3b82f6")
        priority_bg_color = priority_bg.get(priority, "#dbeafe")
        
        # Category icons and colors
        category_data = {
            "Billing": {"icon": "💳", "color": "#3b82f6", "bg": "#dbeafe"},
            "Technical": {"icon": "🔧", "color": "#8b5cf6", "bg": "#ede9fe"},
            "Delivery": {"icon": "📦", "color": "#f59e0b", "bg": "#fef3c7"},
            "Service": {"icon": "🛎️", "color": "#10b981", "bg": "#d1fae5"},
            "Security": {"icon": "🔒", "color": "#ef4444", "bg": "#fee2e2"},
            "Other": {"icon": "📋", "color": "#6b7280", "bg": "#f3f4f6"}
        }
        cat_info = category_data.get(category, category_data["Other"])
        category_icon = cat_info["icon"]
        category_color = cat_info["color"]
        category_bg = cat_info["bg"]
        
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
                                     <td style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
                                         <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                             Subject
                                         </p>
                                         <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 700;">
                                             {complaint_data.get('subject', 'No Subject')}
                                         </p>
                                     </td>
                                 </tr>
                                 <tr>
                                     <td style="padding: 20px;">
                                         <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                             Detailed Description
                                         </p>
                                         <p style="margin: 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                             {complaint_data.get('description', 'No Description')}
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
                                © {get_ist_time().year} Quickfix. All rights reserved.
                            </p>
                            <div style="margin-top: 15px;">
                                <a href="mailto:{self.admin_email}?subject=Help%20Request" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Help Center</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="{self.app_url}" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Privacy Policy</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="mailto:{self.admin_email}?subject=Contact%20Request" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Contact Us</a>
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
        ticket_id = complaint_data.get('ticket_id', 'N/A')
        subject = complaint_data.get('subject', 'Your Issue')
        solution = complaint_data.get('solution', 'Your issue has been resolved.')
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Issue Resolved - Quickfix</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Success Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 56px; margin-bottom: 15px;">✅</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                Issue Resolved!
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #d1fae5; font-size: 15px; font-weight: 500;">
                                Ticket #{ticket_id}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 40px 30px 20px 30px;">
                            <h2 style="margin: 0 0 15px 0; color: #1f2937; font-size: 22px; font-weight: 600;">
                                Dear {user_name},
                            </h2>
                            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                We're delighted to inform you that your issue has been successfully resolved! Our team has carefully reviewed your complaint and implemented a comprehensive solution.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Issue Summary -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #f9fafb; border-radius: 12px; padding: 20px; border-left: 4px solid #10b981;">
                                <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                    Your Issue
                                </p>
                                <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600; line-height: 1.5;">
                                    {subject}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Solution Details -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius: 12px; padding: 25px; border: 2px solid #10b981;">
                                <h3 style="margin: 0 0 15px 0; color: #065f46; font-size: 18px; font-weight: 700; display: flex; align-items: center;">
                                    <span style="font-size: 24px; margin-right: 10px;">💡</span>
                                    Solution Implemented
                                </h3>
                                <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; margin-top: 15px;">
                                    <p style="margin: 0; color: #047857; font-size: 15px; line-height: 1.8; white-space: pre-wrap;">
{solution}
                                    </p>
                                </div>
                                <p style="margin: 15px 0 0 0; color: #059669; font-size: 13px; font-weight: 600;">
                                    <span style="font-size: 16px; margin-right: 5px;">📅</span>
                                    Resolved on {timestamp}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Thank You Message -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 25px; text-align: center; border: 2px solid #f59e0b;">
                                <h3 style="margin: 0 0 12px 0; color: #92400e; font-size: 20px; font-weight: 700;">
                                    🙏 Thank You for Your Patience!
                                </h3>
                                <p style="margin: 0; color: #78350f; font-size: 15px; line-height: 1.7;">
                                    We truly appreciate your trust in Quickfix. Your feedback helps us improve our services and serve you better. We're committed to providing you with the best possible experience.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Feedback Request -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #eff6ff; border-radius: 12px; padding: 25px; text-align: center;">
                                <h4 style="margin: 0 0 12px 0; color: #1e40af; font-size: 17px; font-weight: 600;">
                                    📊 How Was Your Experience?
                                </h4>
                                <p style="margin: 0 0 20px 0; color: #1e3a8a; font-size: 14px; line-height: 1.6;">
                                    Your feedback is invaluable to us. Please take a moment to share your experience.
                                </p>
                                <a href="{self.app_url}" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                                    Rate Your Experience
                                </a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Need Help Section -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; text-align: center;">
                                <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                    Still have questions or need further assistance?
                                </p>
                                <p style="margin: 0; color: #6b7280; font-size: 13px;">
                                    Reply to this email or visit our <a href="mailto:{self.admin_email}?subject=Help%20Request" style="color: #10b981; text-decoration: none; font-weight: 600;">Help Center</a>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; color: #059669; font-size: 14px; font-weight: 600;">
                                Thank you for choosing Quickfix! 🎉
                            </p>
                            <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 13px; line-height: 1.6;">
                                We're always here to help you with exceptional AI-powered support.
                            </p>
                            <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 12px;">
                                © {get_ist_time().year} Quickfix. All rights reserved.
                            </p>
                            <div style="margin-top: 15px;">
                                <a href="mailto:{self.admin_email}?subject=Help%20Request" style="color: #10b981; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Help Center</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="{self.app_url}" style="color: #10b981; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Privacy Policy</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="mailto:{self.admin_email}?subject=Contact%20Request" style="color: #10b981; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Contact Us</a>
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
                                                 Subject:
                                             </p>
                                             <p style="margin: 0; color: #991b1b; font-size: 15px; font-weight: 700;">
                                                 {complaint_data.get('subject', 'No Subject')}
                                             </p>
                                         </td>
                                     </tr>
                                     <tr>
                                         <td>
                                             <p style="margin: 0 0 5px 0; color: #7f1d1d; font-size: 13px; font-weight: 600;">
                                                 Detailed Description:
                                             </p>
                                             <p style="margin: 0; color: #991b1b; font-size: 14px; line-height: 1.6;">
                                                 {complaint_data.get('description', 'No Description')}
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
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
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


    def _generate_resolution_feedback_html(self, user_name: str, user_email: str, ticket_id: str,
                                           subject: str, is_actually_resolved: bool,
                                           user_comment: str, original_solution: str) -> str:
        """Generate HTML email for admin notification about user's resolution feedback"""
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        status_color = "#10b981" if is_actually_resolved else "#ef4444"
        status_bg = "#d1fae5" if is_actually_resolved else "#fee2e2"
        status_text = "Issue Resolved" if is_actually_resolved else "Issue NOT Resolved"
        status_icon = "✅" if is_actually_resolved else "❌"
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Resolution Feedback</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="650" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px; text-align: center;">
                            <div style="font-size: 42px; margin-bottom: 10px;">📊</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                User Resolution Feedback
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #dbeafe; font-size: 14px;">
                                Customer Satisfaction Report
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Status Badge -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <div style="display: inline-block; background-color: {status_bg}; border: 2px solid {status_color}; border-radius: 50px; padding: 12px 30px;">
                                <span style="font-size: 24px; margin-right: 10px;">{status_icon}</span>
                                <span style="color: {status_color}; font-size: 18px; font-weight: 700;">{status_text}</span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Ticket Info -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                            🎫 Ticket Information
                                        </h3>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Ticket ID:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px; font-weight: 700;">{ticket_id}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Subject:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{subject}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Customer:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{user_name} ({user_email})</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Feedback Submitted:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{timestamp}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Original Solution -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #1e40af; font-size: 16px; font-weight: 600;">
                                    💡 Original Solution Provided
                                </h3>
                                <p style="margin: 0; color: #1e3a8a; font-size: 14px; line-height: 1.6;">
                                    {original_solution}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- User Comment -->
                    {f'''
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #92400e; font-size: 16px; font-weight: 600;">
                                    💬 User's Additional Comments
                                </h3>
                                <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.6; font-style: italic;">
                                    "{user_comment}"
                                </p>
                            </div>
                        </td>
                    </tr>
                    ''' if user_comment else ''}
                    
                    <!-- Action Required (if not resolved) -->
                    {f'''
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #fee2e2; border: 2px solid #ef4444; border-radius: 12px; padding: 25px; text-align: center;">
                                <h3 style="margin: 0 0 12px 0; color: #991b1b; font-size: 18px; font-weight: 700;">
                                    ⚠️ Action Required
                                </h3>
                                <p style="margin: 0; color: #7f1d1d; font-size: 15px; line-height: 1.6;">
                                    The customer has reported that their issue is <strong>NOT RESOLVED</strong>. 
                                    Please review this ticket and take appropriate action to address their concerns.
                                </p>
                            </div>
                        </td>
                    </tr>
                    ''' if not is_actually_resolved else f'''
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #d1fae5; border: 2px solid #10b981; border-radius: 12px; padding: 25px; text-align: center;">
                                <h3 style="margin: 0 0 12px 0; color: #065f46; font-size: 18px; font-weight: 700;">
                                    🎉 Great News!
                                </h3>
                                <p style="margin: 0; color: #064e3b; font-size: 15px; line-height: 1.6;">
                                    The customer has confirmed that their issue has been successfully resolved. 
                                    Excellent work by the team!
                                </p>
                            </div>
                        </td>
                    </tr>
                    '''}
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <a href="{self.app_url}" style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);">
                                View in Admin Panel
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;">
                                Automated notification from Quickfix Admin System
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                                © {get_ist_time().year} Quickfix Admin Portal
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
