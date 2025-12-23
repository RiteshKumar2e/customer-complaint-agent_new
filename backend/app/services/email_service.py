import os
from datetime import datetime
import requests
import traceback

class EmailService:
    """Service for sending emails via Resend API - Fixed & Optimized"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        
        # ✅ Using Resend's default testing domain (no verification needed)
        # For production, add your own verified domain at https://resend.com/domains
        self.sender_email = "onboarding@resend.dev"
        
        self.admin_email = "riteshkumar90359@gmail.com"
        self.company_name = "Quickfix"
        
        if not self.api_key:
            print("⚠️ CRITICAL: RESEND_API_KEY not set!")
            print("📝 Get your key from: https://resend.com/api-keys")
            print("❌ EMAILS WILL NOT BE SENT WITHOUT THIS KEY")

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email when complaint is submitted - sends to BOTH user and admin"""
        # Flag to track partial success
        emails_sent = False

        # 1. Send to User Email (Might fail in test mode if not verified)
        try:
            # Validate API key first
            if not self.api_key:
                print("⚠️ RESEND_API_KEY not set. Skipping emails.")
                return False

            subject = f"✅ Complaint Received - {user_name}"
            html_body = self._generate_confirmation_html(user_name, complaint_data, user_email)
            print(f"📧 Sending confirmation to USER: {user_email}...")
            
            self._send_email(user_email, subject, html_body)
            print(f"✅ User confirmation email sent successfully to {user_email}.")
            emails_sent = True
        except Exception as e:
            print(f"⚠️ Could not send email to User ({user_email}).")
            print(f"   Reason: {str(e)}")
            if "domain" in str(e).lower() or "verified" in str(e).lower():
                print("   ℹ️ NOTE: In 'onboarding@resend.dev' mode, you can ONLY send to your own registered email.")
        
        # 2. Send to Admin Email (Critical - should always try to send)
        try:
            self._send_admin_notification(user_name, user_email, complaint_data)
            emails_sent = True
        except Exception as e:
            print(f"❌ Failed to send Admin notification: {str(e)}")
            
        return emails_sent

    def _send_admin_notification(self, user_name: str, user_email: str, complaint_data: dict):
        """Helper to send the internal admin alert"""
        try:
            admin_subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
            admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
            self._send_email(self.admin_email, admin_subject, admin_html)
            print(f"✅ Admin notification sent.")
        except Exception as e:
            print(f"⚠️ Failed to send admin notification: {e}")

    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email when complaint is solved - sends to BOTH user and admin"""
        # Flag to track partial success
        emails_sent = False

        # 1. Send to User Email
        try:
            # Validate API key first
            if not self.api_key:
                print("⚠️ RESEND_API_KEY not set. Skipping emails.")
                return False

            subject = f"✅ RESOLVED - {user_name}'s Complaint"
            html_body = self._generate_resolution_html(user_name, complaint_data, user_email)
            
            print(f"📧 Sending resolution to USER: {user_email}...")
            self._send_email(user_email, subject, html_body)
            print(f"✅ Resolution email sent successfully to {user_email}")
            emails_sent = True
        except Exception as e:
            print(f"⚠️ Could not send resolution to User ({user_email}).")
            print(f"   Reason: {str(e)}")

        # 2. Send Admin Notification (Critical)
        try:
            print(f"📧 Sending resolution notification to ADMIN: {self.admin_email}...")
            admin_subject = f"✅ RESOLVED: {user_name} - {complaint_data.get('category', 'General')}"
            admin_html = self._generate_admin_resolution_html(user_name, user_email, complaint_data)
            self._send_email(self.admin_email, admin_subject, admin_html)
            print(f"✅ Admin resolution notification sent.")
            emails_sent = True
        except Exception as e:
            print(f"❌ Failed to send Admin resolution status: {str(e)}")

        return emails_sent

    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Internal method to send email via Resend API"""
        if not self.api_key:
            raise Exception("Resend API key not configured!")

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
            # Send request with longer timeout and better error handling
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Handle Specific Resend Errors
            if response.status_code == 403:
                error_data = response.json()
                msg = error_data.get("message", "").lower()
                if "domain" in msg or "verified" in msg:
                    raise Exception(
                        f"⛔ DOMAIN ERROR: Resend rejected email from '{self.sender_email}'.\n"
                        f"Using default domain 'resend.dev' which should work without verification.\n"
                        f"For production, verify your domain at https://resend.com/domains"
                    )
                if "testing" in msg:
                    raise Exception(
                        f"⛔ TESTING MODE RESTRICTION: You cannot send to {to_email}.\n"
                        f"In testing, you can only send to yourself ({self.admin_email})."
                    )

            if response.status_code not in [200, 201, 202]:
                raise Exception(f"Email failed: {response.status_code} {response.text}")

            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception(f"⚠️ Network timeout: Email service took too long to respond. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"⚠️ Connection error: Cannot reach email service. Check your internet connection and firewall settings.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"⚠️ Network error: {str(e)}. Please check your internet connection.")

    # ------------------------------------------------------------------
    # HTML GENERATION METHODS (Preserved from your original code)
    # ------------------------------------------------------------------

    def _generate_confirmation_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        """Generate HTML for confirmation email"""
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
                    .info-box p {{ margin: 8px 0; font-size: 14px; }}
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
                            <p><strong>Description:</strong> {complaint_data.get('complaint_text', 'N/A')[:150]}{"..." if len(complaint_data.get('complaint_text', '')) > 150 else ''}</p>
                        </div>
                        
                        <div class="info-box">
                            <h3>🤖 AI Analysis Results</h3>
                            <p><strong>Sentiment:</strong> {complaint_data.get('sentiment', 'Analyzing...')}</p>
                            <p><strong>Our Response:</strong> {complaint_data.get('response', 'Processing...')}</p>
                            <p><strong>Proposed Solution:</strong> {complaint_data.get('solution', 'Generating solution...')}</p>
                        </div>
                        
                        <p style="background: #fff9e6; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px; margin: 20px 0;">
                            <strong>⏱️ Expected Resolution:</strong> We typically resolve {complaint_data.get('priority', 'Medium')} priority complaints within 24-48 hours.
                        </p>
                        
                        <center>
                            <a href="http://localhost:5173/dashboard" class="button">📊 View Dashboard</a>
                        </center>
                        
                        <p style="margin-top: 30px;">Need help? Contact us directly.</p>
                        
                        <p style="margin-top: 20px;">Best regards,<br><strong style="color: #667eea;">The Quickfix Support Team</strong></p>
                    </div>
                    <div class="footer">
                        <p style="margin: 5px 0;"><strong>Quickfix</strong> - AI-Powered Complaint Resolution</p>
                        <p style="margin: 5px 0;">📧 riteshkumar90359@gmail.com | 📱 +91 62062 69895</p>
                        <p style="margin: 10px 0 5px 0; color: #999;">© {datetime.now().year} Quickfix. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_resolution_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        """Generate HTML for resolution email"""
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .success-box {{ background: #f0fff4; padding: 20px; margin: 20px 0; border-left: 4px solid #38ef7d; border-radius: 6px; }}
                    .success-box h3 {{ margin: 0 0 15px 0; color: #11998e; font-size: 16px; }}
                    .button {{ display: inline-block; background: #38ef7d; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                    .footer {{ background: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Complaint Resolved Successfully!</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Your issue has been addressed</p>
                    </div>
                    <div class="content">
                        <div style="font-size: 48px; color: #38ef7d; text-align: center; margin: 20px 0;">✓</div>
                        
                        <p>Hi <strong>{user_name}</strong>,</p>
                        
                        <p>Great news! Our AI system has successfully analyzed and resolved your complaint.</p>
                        
                        <div class="success-box">
                            <h3>📋 Complaint Summary</h3>
                            <p><strong>Category:</strong> {complaint_data.get('category', 'N/A')}</p>
                            <p><strong>Status:</strong> <span style="color: #38ef7d; font-weight: 600;">✅ RESOLVED</span></p>
                        </div>
                        
                        <div class="success-box">
                            <h3>🎯 Solution Provided</h3>
                            <p>{complaint_data.get('solution', 'Check dashboard for details')}</p>
                        </div>
                        
                        <center>
                            <a href="http://localhost:5173/dashboard" class="button">📊 View Full Details</a>
                        </center>
                        
                        <p style="margin-top: 30px;">Thank you for choosing Quickfix!</p>
                        
                        <p style="margin-top: 20px;">Best regards,<br><strong style="color: #11998e;">The Quickfix Support Team</strong></p>
                    </div>
                    <div class="footer">
                        <p style="margin: 5px 0;"><strong>Quickfix</strong> - AI-Powered Complaint Resolution</p>
                        <p style="margin: 5px 0;">📧 riteshkumar90359@gmail.com | 📱 +91 62062 69895</p>
                        <p style="margin: 10px 0 5px 0; color: #999;">© {datetime.now().year} Quickfix. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_notification_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        """Generate HTML for admin notification email"""
        priority_colors = {"High": "#ff4444", "Medium": "#ff9900", "Low": "#00cc66"}
        priority = complaint_data.get('priority', 'Medium')
        color = priority_colors.get(priority, "#0066cc")
        
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
                    .container {{ max-width: 700px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ padding: 30px; }}
                    .priority-badge {{ background: {color}; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; }}
                    .section {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    table td {{ padding: 12px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; }}
                    table td:first-child {{ font-weight: 600; width: 35%; background: #f8f9fa; }}
                    .footer {{ background: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">🚨 New Complaint Alert</h1>
                        <p style="margin: 10px 0 0 0;">Immediate attention required</p>
                    </div>
                    <div class="content">
                        <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center;">
                            Priority: <span class="priority-badge">{priority}</span>
                        </div>
                        
                        <div class="section">
                            <h3 style="margin: 0 0 15px 0;">👤 Customer Information</h3>
                            <table>
                                <tr><td>Name:</td><td><strong>{user_name}</strong></td></tr>
                                <tr><td>Email:</td><td><strong>{user_email}</strong></td></tr>
                                <tr><td>Time:</td><td>{datetime.now().strftime('%d %B %Y, %I:%M %p')}</td></tr>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h3 style="margin: 0 0 15px 0;">📋 Complaint Details</h3>
                            <table>
                                <tr><td>Category:</td><td><strong>{complaint_data.get('category', 'N/A')}</strong></td></tr>
                                <tr><td>Priority:</td><td><span class="priority-badge">{priority}</span></td></tr>
                                <tr><td>Description:</td><td>{complaint_data.get('complaint_text', 'N/A')}</td></tr>
                            </table>
                        </div>
                        
                        <div class="section" style="border-left-color: #38ef7d;">
                            <h3 style="margin: 0 0 15px 0;">🤖 AI Analysis</h3>
                            <table>
                                <tr><td>Sentiment:</td><td>{complaint_data.get('sentiment', 'N/A')}</td></tr>
                                <tr><td>Response:</td><td>{complaint_data.get('response', 'Processing...')}</td></tr>
                                <tr><td>Solution:</td><td>{complaint_data.get('solution', 'Generating...')}</td></tr>
                            </table>
                        </div>
                    </div>
                    <div class="footer">
                        <p style="margin: 5px 0;"><strong>Quickfix Admin Panel</strong></p>
                        <p style="margin: 5px 0; color: #999;">© {datetime.now().year} Quickfix</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_resolution_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        """Generate HTML for admin resolution notification email"""
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
                    .container {{ max-width: 700px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ padding: 30px; }}
                    .success-badge {{ background: #38ef7d; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; }}
                    .section {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #38ef7d; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    table td {{ padding: 12px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; }}
                    table td:first-child {{ font-weight: 600; width: 35%; background: #f8f9fa; }}
                    .footer {{ background: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">✅ Complaint Resolved</h1>
                        <p style="margin: 10px 0 0 0;">Customer issue has been resolved</p>
                    </div>
                    <div class="content">
                        <div style="text-align: center; margin: 20px 0;">
                            <div style="font-size: 48px; color: #38ef7d;">✓</div>
                            <span class="success-badge">RESOLVED</span>
                        </div>
                        
                        <div class="section">
                            <h3 style="margin: 0 0 15px 0;">👤 Customer Information</h3>
                            <table>
                                <tr><td>Name:</td><td><strong>{user_name}</strong></td></tr>
                                <tr><td>Email:</td><td><strong>{user_email}</strong></td></tr>
                                <tr><td>Resolution Time:</td><td>{datetime.now().strftime('%d %B %Y, %I:%M %p')}</td></tr>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h3 style="margin: 0 0 15px 0;">📋 Complaint Details</h3>
                            <table>
                                <tr><td>Category:</td><td><strong>{complaint_data.get('category', 'N/A')}</strong></td></tr>
                                <tr><td>Status:</td><td><span class="success-badge">RESOLVED</span></td></tr>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h3 style="margin: 0 0 15px 0;">💡 Solution Provided</h3>
                            <p>{complaint_data.get('solution', 'Check dashboard for details')}</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p style="margin: 5px 0;"><strong>Quickfix Admin Panel</strong></p>
                        <p style="margin: 5px 0; color: #999;">© {datetime.now().year} Quickfix</p>
                    </div>
                </div>
            </body>
        </html>
        """

# Initialize email service
email_service = EmailService()