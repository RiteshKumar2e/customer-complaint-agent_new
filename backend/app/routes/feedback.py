from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import email_service
import os

router = APIRouter()

class FeedbackRequest(BaseModel):
    name: str
    email: EmailStr
    rating: int
    category: str
    message: str

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback and send email to admin
    """
    try:
        # Get admin email from environment or use default
        admin_email = os.getenv("ADMIN_EMAIL", "riteshkumar90359@gmail.com")
        
        # Create feedback email subject
        subject = f"🌟 Quickfix Feedback - {feedback.category} ({feedback.rating}⭐)"
        
        # Create detailed HTML email body
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Feedback</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <div style="font-size: 42px; margin-bottom: 10px;">💬</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                New Feedback Received
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 14px;">
                                From Quickfix Platform
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Rating -->
                    <tr>
                        <td style="padding: 25px 30px; text-align: center;">
                            <div style="background-color: #f9fafb; border-radius: 12px; padding: 20px; display: inline-block;">
                                <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase;">
                                    User Rating
                                </p>
                                <div style="font-size: 48px; color: #f59e0b;">
                                    {"⭐" * feedback.rating}
                                </div>
                                <p style="margin: 10px 0 0 0; color: #1f2937; font-size: 24px; font-weight: 700;">
                                    {feedback.rating}/5
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- User Information -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                                            👤 User Information
                                        </h3>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Name:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{feedback.name}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Email:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{feedback.email}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 13px; font-weight: 600;">Category:</p>
                                                    <p style="margin: 5px 0 0 0; color: #1f2937; font-size: 15px;">{feedback.category}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Feedback Message -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #1e40af; font-size: 16px; font-weight: 600;">
                                    📝 Feedback Message
                                </h3>
                                <p style="margin: 0; color: #1e3a8a; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
{feedback.message}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                This feedback was submitted through Quickfix Platform
                            </p>
                            <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 11px;">
                                © 2025 Quickfix. All rights reserved.
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
        
        # Send email using the existing email service
        email_service._dispatch_api(admin_email, subject, html_body)
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully! Thank you for your input."
        }
        
    except Exception as e:
        print(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback. Please try again later."
        )
