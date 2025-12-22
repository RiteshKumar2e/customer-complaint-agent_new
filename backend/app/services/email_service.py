import os
import smtplib
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    """
    Service for sending emails via Gmail SMTP.
    Allows sending to ANY recipient (Admin & Users) without a verified domain.
    """
    
    def __init__(self):
        # Credentials from .env
        self.sender_email = os.getenv("SENDER_EMAIL", "riteshkumar90359@gmail.com")
        self.password = os.getenv("SENDER_PASSWORD")
        
        # Admin Configuration
        self.admin_email = "riteshkumar90359@gmail.com"
        
        if not self.password:
            print("⚠️ WARNING: GMAIL_APP_PASSWORD not set in .env file!")
            print("ℹ️  Generate one here: https://myaccount.google.com/apppasswords")

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        """Send confirmation email to the User and notification to Admin"""
        try:
            # 1. Send to USER
            subject = f"✅ Complaint Received - {user_name}"
            html_body = self._generate_confirmation_html(user_name, complaint_data)
            
            print(f"📧 Sending confirmation to User: {user_email}...")
            self._send_email_via_smtp(user_email, subject, html_body)
            print(f"✅ User confirmation sent.")

            # 2. Send to ADMIN (Internal Alert)
            self._send_admin_notification(user_name, user_email, complaint_data)
            
            return True

        except Exception as e:
            print(f"❌ Failed to send confirmation emails: {str(e)}")
            traceback.print_exc()
            return False

    def _send_admin_notification(self, user_name: str, user_email: str, complaint_data: dict):
        """Helper to send the internal admin alert"""
        try:
            subject = f"🚨 NEW: {user_name} - {complaint_data.get('category', 'General')}"
            html_body = self._generate_admin_notification_html(user_name, user_email, complaint_data)
            
            print(f"📧 Sending notification to Admin...")
            self._send_email_via_smtp(self.admin_email, subject, html_body)
            print(f"✅ Admin alert sent.")
        except Exception as e:
            print(f"⚠️ Failed to send admin notification: {e}")

    def send_resolution_email(self, user_name: str, user_email: str, complaint_data: dict):
        """Send resolution email when complaint is solved"""
        try:
            subject = f"✅ RESOLVED - {user_name}'s Complaint"
            html_body = self._generate_resolution_html(user_name, complaint_data)
            
            print(f"📧 Sending resolution to User: {user_email}...")
            self._send_email_via_smtp(user_email, subject, html_body)
            print(f"✅ Resolution email sent.")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send resolution email: {str(e)}")
            traceback.print_exc()
            return False

    def _send_email_via_smtp(self, to_email: str, subject: str, html_body: str):
        """Core function to send email using Gmail SMTP"""
        if not self.password:
            raise Exception("Gmail App Password is missing in .env!")

        # Create the email object
        msg = MIMEMultipart()
        msg['From'] = f"Quickfix Support <{self.sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach HTML content
        msg.attach(MIMEText(html_body, 'html'))

        try:
            # Connect to Gmail SMTP Server (Port 587 for TLS)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()  # Secure the connection
            
            # Login
            server.login(self.sender_email, self.password)
            
            # Send
            server.sendmail(self.sender_email, to_email, msg.as_string())
            
            # Close connection
            server.quit()
            
        except smtplib.SMTPAuthenticationError:
            raise Exception("❌ Authentication Failed! Check your GMAIL_USER and GMAIL_APP_PASSWORD.")
        except Exception as e:
            raise Exception(f"❌ SMTP Error: {str(e)}")

    # ------------------------------------------------------------------
    # HTML TEMPLATES (Professional Design)
    # ------------------------------------------------------------------

    def _generate_confirmation_html(self, user_name: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; text-align: center; }}
                    .content {{ padding: 30px; color: #333; }}
                    .info-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ background: #eee; text-align: center; padding: 15px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0; font-size:24px;">Complaint Received</h1>
                    </div>
                    <div class="content">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>We have received your complaint. Our AI system is analyzing it now.</p>
                        
                        <div class="info-box">
                            <p><strong>Category:</strong> {complaint_data.get('category', 'General')}</p>
                            <p><strong>Priority:</strong> {complaint_data.get('priority', 'Medium')}</p>
                            <p><strong>Description:</strong> {complaint_data.get('complaint_text', '')}</p>
                        </div>

                        <p><strong>AI Initial Analysis:</strong><br>
                        {complaint_data.get('response', 'Processing...')}</p>
                        
                        <p style="margin-top:20px;">We will update you shortly.</p>
                    </div>
                    <div class="footer">
                        &copy; {datetime.now().year} Quickfix Support
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_resolution_html(self, user_name: str, complaint_data: dict) -> str:
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 25px; text-align: center; }}
                    .content {{ padding: 30px; color: #333; }}
                    .success-box {{ background: #f0fff4; padding: 20px; border-left: 4px solid #38ef7d; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ background: #eee; text-align: center; padding: 15px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0; font-size:24px;">✅ Issue Resolved</h1>
                    </div>
                    <div class="content">
                        <p>Hi <strong>{user_name}</strong>,</p>
                        <p>Good news! Your complaint has been successfully resolved.</p>
                        
                        <div class="success-box">
                            <h3 style="margin-top:0; color:#11998e;">Solution Provided:</h3>
                            <p>{complaint_data.get('solution', 'Check your dashboard for details.')}</p>
                        </div>

                        <p>Thank you for using Quickfix!</p>
                    </div>
                    <div class="footer">
                        &copy; {datetime.now().year} Quickfix Support
                    </div>
                </div>
            </body>
        </html>
        """

    def _generate_admin_notification_html(self, user_name: str, user_email: str, complaint_data: dict) -> str:
        priority = complaint_data.get('priority', 'Medium')
        color = "#ff4444" if priority == "High" else "#ff9900"
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; border-top: 5px solid {color};">
                    <h2 style="color: {color}; margin-top:0;">🚨 New Complaint Alert</h2>
                    
                    <table style="width:100%; border-collapse: collapse; margin-top: 15px;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>User:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{user_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Email:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{user_email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Category:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{complaint_data.get('category')}</td>
                        </tr>
                         <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Priority:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {color}; font-weight:bold;">{priority}</td>
                        </tr>
                    </table>

                    <div style="background: #f9f9f9; padding: 15px; margin-top: 15px; border-radius: 4px;">
                        <strong>Complaint:</strong><br>
                        {complaint_data.get('complaint_text')}
                    </div>

                    <p style="font-size: 12px; color: #888; margin-top: 20px;">Sent from Quickfix System</p>
                </div>
            </body>
        </html>
        """

# Initialize singleton
email_service = EmailService()