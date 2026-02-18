"""
Agent Resolution Email Extension for Email Service
Add this method to the EmailService class in email_service.py
"""

# Add this method to the EmailService class after send_resolution_feedback_to_admin:

def send_agent_resolution(self, user_email: str, user_name: str, ticket_id: str, 
                         complaint_subject: str, agent_solution: str, agent_name: str):
    """Send agent-verified resolution to user in background"""
    import threading
    thread = threading.Thread(
        target=self._worker_send_agent_resolution,
        args=(user_email, user_name, ticket_id, complaint_subject, agent_solution, agent_name)
    )
    thread.daemon = True
    thread.start()
    return True

# Add this worker method after _worker_send_resolution_feedback:

def _worker_send_agent_resolution(self, user_email: str, user_name: str, ticket_id: str,
                                  complaint_subject: str, agent_solution: str, agent_name: str):
    """Background logic to send agent-verified resolution to user"""
    try:
        subject = f"✅ Agent Resolution: Ticket #{ticket_id} - Quickfix"
        html_body = self._generate_agent_resolution_html(
            user_name, ticket_id, complaint_subject, agent_solution, agent_name
        )
        print(f"📧 Sending agent resolution to USER: {user_email}...")
        self._dispatch_api(user_email, subject, html_body)
        
        # Also notify admin
        admin_subject = f"📤 Agent Resolution Sent: Ticket #{ticket_id} - {agent_name}"
        admin_html = self._generate_admin_agent_resolution_html(
            user_name, user_email, ticket_id, complaint_subject, agent_solution, agent_name
        )
        print(f"📧 Sending agent resolution notification to ADMIN...")
        self._dispatch_api(self.admin_email, admin_subject, admin_html)
        
    except Exception as e:
        print(f"❌ Agent Resolution Email Error: {str(e)}") 
        import traceback
        traceback.print_exc()

# Add these HTML template methods after the existing template methods:

def _generate_agent_resolution_html(self, user_name: str, ticket_id: str, 
                                   complaint_subject: str, agent_solution: str, 
                                   agent_name: str) -> str:
    """Generate HTML email for agent-verified resolution sent to user"""
    from app.db.database import get_ist_time
    timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Resolution - Quickfix</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 56px; margin-bottom: 15px;">👨‍💼</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                Human-Verified Solution
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 15px; font-weight: 500;">
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
                                Great news! Your complaint has been personally reviewed by our expert support agent <strong>{agent_name}</strong>, who has prepared a comprehensive solution for you.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Issue Summary -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background-color: #f9fafb; border-radius: 12px; padding: 20px; border-left: 4px solid #6366f1;">
                                <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">
                                    Your Issue
                                </p>
                                <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600; line-height: 1.5;">
                                    {complaint_subject}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Agent Badge -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; text-align: center; border: 2px solid #f59e0b;">
                                <p style="margin: 0 0 8px 0; color: #92400e; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                    ✅ Multi-Model AI Validated
                                </p>
                                <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.6;">
                                    This solution has been validated by 5-10 advanced AI models and personally verified by {agent_name} to ensure accuracy, safety, and effectiveness.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Solution Details -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; padding: 25px; border: 2px solid #6366f1;">
                                <h3 style="margin: 0 0 15px 0; color: #1e40af; font-size: 18px; font-weight: 700; display: flex; align-items: center;">
                                    <span style="font-size: 24px; margin-right: 10px;">💡</span>
                                    Expert Solution
                                </h3>
                                <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; margin-top: 15px;">
                                    <p style="margin: 0; color: #1e40af; font-size: 15px; line-height: 1.8; white-space: pre-wrap;">
{agent_solution}
                                    </p>
                                </div>
                                <p style="margin: 15px 0 0 0; color: #3b82f6; font-size: 13px; font-weight: 600;">
                                    <span style="font-size: 16px; margin-right: 5px;">📅</span>
                                    Verified on {timestamp} by {agent_name}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Thank You Message -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 12px; padding: 25px; text-align: center; border: 2px solid #10b981;">
                                <h3 style="margin: 0 0 12px 0; color: #065f46; font-size: 20px; font-weight: 700;">
                                    🙏 Thank You for Your Trust!
                                </h3>
                                <p style="margin: 0; color: #047857; font-size: 15px; line-height: 1.7;">
                                    We're committed to providing you with the highest quality support. If you have any questions about this solution or need further assistance, please don't hesitate to reach out.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Feedback Request -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #fef3c7; border-radius: 12px; padding: 25px; text-align: center;">
                                <h4 style="margin: 0 0 12px 0; color: #92400e; font-size: 17px; font-weight: 600;">
                                    📊 How Was Your Experience?
                                </h4>
                                <p style="margin: 0 0 20px 0; color: #78350f; font-size: 14px; line-height: 1.6;">
                                    Your feedback helps us improve our service quality.
                                </p>
                                <a href="{self.app_url}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);">
                                    Rate This Solution
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
                                    Reply to this email or visit our <a href="mailto:{self.admin_email}?subject=Help%20Request" style="color: #6366f1; text-decoration: none; font-weight: 600;">Help Center</a>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; color: #6366f1; font-size: 14px; font-weight: 600;">
                                Thank you for choosing Quickfix! 🎉
                            </p>
                            <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 13px; line-height: 1.6;">
                                Expert human support powered by advanced AI validation.
                            </p>
                            <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 12px;">
                                © {get_ist_time().year} Quickfix. All rights reserved.
                            </p>
                            <div style="margin-top: 15px;">
                                <a href="mailto:{self.admin_email}?subject=Help%20Request" style="color: #6366f1; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Help Center</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="{self.app_url}" style="color: #6366f1; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Privacy Policy</a>
                                <span style="color: #d1d5db;">|</span>
                                <a href="mailto:{self.admin_email}?subject=Contact%20Request" style="color: #6366f1; text-decoration: none; margin: 0 10px; font-size: 12px; font-weight: 500;">Contact Us</a>
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

def _generate_admin_agent_resolution_html(self, user_name: str, user_email: str, 
                                          ticket_id: str, complaint_subject: str,
                                          agent_solution: str, agent_name: str) -> str:
    """Generate HTML email for admin notification of agent resolution"""
    from app.db.database import get_ist_time
    timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Resolution Sent</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center;">
                            <div style="font-size: 42px; margin-bottom: 10px;">📤</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Agent Resolution Sent
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #d1fae5; font-size: 14px;">
                                Ticket #{ticket_id}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Agent Info -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <div style="background-color: #eff6ff; border-radius: 8px; padding: 20px; border-left: 4px solid #3b82f6;">
                                <p style="margin: 0 0 5px 0; color: #1e40af; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                                    Agent
                                </p>
                                <p style="margin: 0; color: #1e3a8a; font-size: 16px; font-weight: 600;">
                                    {agent_name}
                                </p>
                            </div>
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
                                        <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;"><strong>Name:</strong> {user_name}</p>
                                        <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;"><strong>Email:</strong> {user_email}</p>
                                        <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;"><strong>Subject:</strong> {complaint_subject}</p>
                                        <p style="margin: 0; color: #6b7280; font-size: 13px;"><strong>Sent:</strong> {timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Solution Preview -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                    💡 Solution Sent to User
                                </h3>
                                <p style="margin: 0; color: #4b5563; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
{agent_solution[:300]}{"..." if len(agent_solution) > 300 else ""}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                © {get_ist_time().year} Quickfix Admin Panel
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
