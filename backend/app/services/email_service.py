import os
from datetime import datetime
import requests

class EmailService:
    """Service for sending emails via Resend API - No SMTP network issues!"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.sender_email = "noreply@quickfix.com"  # Your verified domain # Resend's testing sender
        self.admin_email = "riteshkumar90359@gmail.com"
        self.company_name = "Quickfix"
        
        if not self.api_key:
            print("⚠️ WARNING: RESEND_API_KEY not set!")
            print("📝 Get your key from: https://resend.com/api-keys")
            print("   Then set: export RESEND_API_KEY='re_xxxxx'")
    
    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email when complaint is submitted"""
        try:
            # In testing mode, all emails go to verified email (admin)
            # Subject shows intended recipient
            
            # Send USER confirmation (to admin in testing mode)
            subject = f"✅ Complaint Received - {user_name}"
            if user_email != self.admin_email:
                subject = f"[TO: {user_email}] " + subject
            
            html_body = self._generate_confirmation_html(user_name, complaint_data, user_email)
            self._send_email(user_email if os.getenv("EMAIL_MODE") == "production" else self.admin_email,subject,html_body)
            print(f"✅ User confirmation sent (intended for: {user_email})")
            
            # Send ADMIN notification
            admin_subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
            admin_html = self._generate_admin_notification_html(user_name, user_email, complaint_data)
            self._send_email(self.admin_email, admin_subject, admin_html)
            print(f"✅ Admin notification sent")
            
            print(f"\n💡 TIP: To send to actual user emails, verify domain at: https://resend.com/domains")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send emails: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email when complaint is solved"""
        try:
            subject = f"✅ RESOLVED - {user_name}'s Complaint"
            if user_email != self.admin_email:
                subject = f"[TO: {user_email}] " + subject
            
            html_body = self._generate_resolution_html(user_name, complaint_data, user_email)
            self._send_email(self.admin_email, subject, html_body)
            print(f"✅ Resolution email sent (intended for: {user_email})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send resolution email: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Internal method to send email via Resend API"""
        if not self.api_key:
            raise Exception(
                "Resend API key not configured!\n"
                "Get it from: https://resend.com/api-keys\n"
                "Then set: RESEND_API_KEY environment variable"
            )
        email_mode = os.getenv("EMAIL_MODE", "testing")
        final_recipient = (
            self.admin_email if email_mode == "testing" else to_email
        )

        payload = {
            "from": self.sender_email,
            "to": [final_recipient],
            "subject": subject,
            "html": html_body
        }
        url = "https://api.resend.com/emails"
        
        response = requests.post(
        "https://api.resend.com/emails",
         headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        },
        
        json=payload,
        timeout=10
    )
        

        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 403:
                error_data = response.json()
                if "testing emails" in error_data.get("message", "").lower():
                    raise Exception(
                        f"Resend Testing Mode Active!\n"
                        f"Can only send to: {self.admin_email}\n"
                        f"To send to other emails:\n"
                        f"1. Verify domain at: https://resend.com/domains\n"
                        f"2. Update sender_email to: noreply@yourdomain.com"
                    )
                raise Exception(f"403 Forbidden: {error_data.get('message', 'Unknown error')}")
            
            if response.status_code != 200:
                raise Exception(f"Email failed: {response.status_code} {response.text}")

            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def _generate_confirmation_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        """Generate HTML for confirmation email"""
        testing_notice = ""
        if user_email and user_email != self.admin_email:
            testing_notice = f"""
            <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
                <strong style="font-size: 18px;">⚠️ TESTING MODE</strong><br>
                <p style="margin: 10px 0 0 0;">This email is intended for: <strong style="color: #ff6b6b;">{user_email}</strong></p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">In production, this will be sent directly to the user.</p>
            </div>
            """
        
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
                    {testing_notice}
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
        testing_notice = ""
        if user_email and user_email != self.admin_email:
            testing_notice = f"""
            <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
                <strong style="font-size: 18px;">⚠️ TESTING MODE</strong><br>
                <p style="margin: 10px 0 0 0;">This email is intended for: <strong style="color: #ff6b6b;">{user_email}</strong></p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">In production, this will be sent directly to the user.</p>
            </div>
            """
        
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
                    {testing_notice}
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

# Initialize email service
email_service = EmailService()