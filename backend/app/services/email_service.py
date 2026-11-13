"""
Customer and staff notification emails (complaint received, resolved, agent
resolution, feedback). Authentication emails (OTP) live in auth_emails.py.

Delivery goes through app.services.email_transport (SMTP by default). These
notifications are not security-critical, so they are sent on a small background
worker pool and failures are logged instead of failing the request.

Every user-supplied value is HTML-escaped before it reaches a template.
"""
import html
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import get_ist_time
from app.services import email_transport

logger = get_logger("app.email.notifications")

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="email")


def _esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _esc_dict(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {k: (_esc(v) if isinstance(v, str) else v) for k, v in (data or {}).items()}


def _esc_list(items: Optional[List[Any]]) -> Optional[List[str]]:
    return [_esc(i) for i in items] if items else items


def html_to_text(markup: str) -> str:
    """Plain-text fallback derived from the HTML body."""
    text = re.sub(r"(?is)<(script|style|head).*?</\1>", "", markup)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</h[1-6]>|</li>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


class EmailService:
    """Notification emails. Public methods return immediately; delivery is backgrounded."""

    def __init__(self):
        s = get_settings()
        self.company_name = s.company_name
        self.app_url = s.app_url
        # Address staff notifications go to; nothing is sent to staff if unset.
        self.admin_email = s.admin_notification_email or s.smtp_from_email
        self.notify_admin = bool(s.admin_notification_email)

    # ------------------------------------------------------------------
    # PUBLIC METHODS
    # ------------------------------------------------------------------

    def send_complaint_confirmation(self, user_name: str, user_email: str, complaint_data: dict):
        _executor.submit(self._worker_send_notification, "complaint", _esc(user_name), user_email,
                         _esc_dict(complaint_data))
        return True

    def send_resolution_email(self, name: str, email: str, ticket_id: str, subject: str, solution: str):
        complaint_data = {"ticket_id": ticket_id, "subject": subject, "solution": solution, "category": "Resolved"}
        _executor.submit(self._worker_send_notification, "resolution", _esc(name), email, _esc_dict(complaint_data))
        return True

    def send_resolution_feedback_to_admin(self, user_name: str, user_email: str, ticket_id: str,
                                          subject: str, is_actually_resolved: bool,
                                          user_comment: str, original_solution: str):
        _executor.submit(self._worker_send_resolution_feedback, _esc(user_name), _esc(user_email), _esc(ticket_id),
                         _esc(subject), is_actually_resolved, _esc(user_comment), _esc(original_solution))
        return True

    def send_agent_resolution(self, user_email: str, user_name: str, ticket_id: str,
                              complaint_subject: str, agent_solution: str, agent_name: str,
                              agent_steps: list = None):
        _executor.submit(self._worker_send_agent_resolution, user_email, _esc(user_name), _esc(ticket_id),
                         _esc(complaint_subject), _esc(agent_solution), _esc(agent_name), _esc_list(agent_steps))
        return True

    def send_raw_to_admin(self, subject: str, html_body: str) -> bool:
        """For callers that build their own (already escaped) HTML, e.g. feedback."""
        if not self.notify_admin:
            logger.info("Admin notification skipped: ADMIN_NOTIFICATION_EMAIL not set")
            return False
        _executor.submit(self._deliver, self.admin_email, subject, html_body, "admin")
        return True

    # ------------------------------------------------------------------
    # WORKERS
    # ------------------------------------------------------------------

    def _deliver(self, to_email: str, subject: str, html_body: str, category: str = "notification") -> bool:
        try:
            email_transport.send(to_email, subject, html_body, html_to_text(html_body), category=category, retries=1)
            return True
        except email_transport.EmailDeliveryError:
            logger.warning("Notification email not delivered (category=%s)", category)
            return False
        except Exception:
            logger.exception("Unexpected error while sending %s email", category)
            return False

    def _to_admin(self, subject: str, html_body: str) -> None:
        if self.notify_admin:
            self._deliver(self.admin_email, subject, html_body, "admin")

    def _worker_send_notification(self, type: str, user_name: str, user_email: str, complaint_data: dict):
        ticket = complaint_data.get("ticket_id", "N/A")
        if type == "complaint":
            self._deliver(user_email, f"Complaint received - Ticket #{ticket}",
                          self._generate_confirmation_html(user_name, complaint_data, user_email), "complaint")
            self._to_admin(f"New ticket #{ticket} - {complaint_data.get('category', 'General')}",
                           self._generate_admin_notification_html(user_name, user_email, complaint_data))
        elif type == "resolution":
            self._deliver(user_email, f"Ticket #{ticket} resolved - {self.company_name}",
                          self._generate_resolution_html(user_name, complaint_data, user_email), "resolution")
            self._to_admin(f"Resolved: ticket #{ticket} - {user_name}",
                           self._generate_admin_resolution_html(user_name, user_email, complaint_data))

    def _worker_send_resolution_feedback(self, user_name: str, user_email: str, ticket_id: str,
                                         subject: str, is_actually_resolved: bool,
                                         user_comment: str, original_solution: str):
        status_text = "RESOLVED" if is_actually_resolved else "NOT RESOLVED"
        self._to_admin(
            f"Customer feedback: ticket #{ticket_id} - {status_text}",
            self._generate_resolution_feedback_html(user_name, user_email, ticket_id, subject,
                                                    is_actually_resolved, user_comment, original_solution),
        )

    def _worker_send_agent_resolution(self, user_email: str, user_name: str, ticket_id: str,
                                      complaint_subject: str, agent_solution: str, agent_name: str,
                                      agent_steps: list = None):
        self._deliver(user_email, f"Resolution for ticket #{ticket_id} - {self.company_name}",
                      self._generate_agent_resolution_html(user_name, ticket_id, complaint_subject,
                                                           agent_solution, agent_name, agent_steps),
                      "agent_resolution")
        self._to_admin(f"Resolution sent: ticket #{ticket_id} - {agent_name}",
                       self._generate_admin_agent_resolution_html(user_name, user_email, ticket_id,
                                                                  complaint_subject, agent_solution,
                                                                  agent_name, agent_steps))

    # ------------------------------------------------------------------
    # ADVANCED PROFESSIONAL HTML TEMPLATES
    # ------------------------------------------------------------------
    
    def _generate_confirmation_html(self, user_name: str, complaint_data: dict, user_email: str = None) -> str:
        ticket_id = complaint_data.get('ticket_id', 'N/A')
        category = complaint_data.get('category', 'General')
        priority = complaint_data.get('priority', 'Medium')
        complaint_data.get('complaint_text', 'N/A')
        sentiment = complaint_data.get('sentiment', 'Analyzing...')
        response = complaint_data.get('response', 'Processing your request...')
        solution = complaint_data.get('solution', 'Generating solution...')
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
        # Enhanced color schemes with backgrounds
        priority_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
        priority_bg = {"High": "#fee2e2", "Medium": "#fef3c7", "Low": "#d1fae5"}
        priority_color = priority_colors.get(priority, "#3b82f6")
        priority_bg.get(priority, "#dbeafe")
        
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
        cat_info["icon"]
        cat_info["color"]
        cat_info["bg"]
        
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
        complaint_data.get('category', 'General')
        priority = complaint_data.get('priority', 'Medium')
        complaint_data.get('complaint_text', 'N/A')
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
                    {'''
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
                    ''' if not is_actually_resolved else '''
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

    def _generate_agent_resolution_html(self, user_name: str, ticket_id: str, 
                                       complaint_subject: str, agent_solution: str, 
                                       agent_name: str, agent_steps: list = None) -> str:
        """Generate HTML email for agent-verified resolution sent to user"""
        timestamp = get_ist_time().strftime("%B %d, %Y at %I:%M %p")
        
        steps_html = ""
        if agent_steps:
            steps_items = "".join([f'<li style="margin-bottom: 10px; color: #1e3a8a;">{step}</li>' for step in agent_steps])
            steps_html = f"""
                    <!-- Actionable Steps -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #eff6ff; border-radius: 12px; padding: 25px; border-left: 4px solid #3b82f6;">
                                <h3 style="margin: 0 0 15px 0; color: #1e40af; font-size: 17px; font-weight: 700;">
                                    📌 Actionable Next Steps
                                </h3>
                                <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
                                    {steps_items}
                                </ul>
                            </div>
                        </td>
                    </tr>
            """
        
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
                    
                    {steps_html}
                    
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
                                              agent_solution: str, agent_name: str,
                                              agent_steps: list = None) -> str:
        """Generate HTML email for admin notification of agent resolution"""
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



# Initialize email service
email_service = EmailService()
