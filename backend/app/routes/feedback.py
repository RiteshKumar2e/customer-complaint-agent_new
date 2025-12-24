from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import email_service
import os

router = APIRouter()

class FeedbackRequest(BaseModel):
    name: str
    email: EmailStr
    rating: int  # Overall Satisfaction (1-5)
    recommendation: int = 8  # NPS Score (0-10), default to 8
    message: str

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback and send professional email to administrative team
    """
    try:
        # Get admin email from configuration
        admin_email = "riteshkumar90359@gmail.com"
        
        # Create feedback email subject with high visibility
        subject = f"🌟 NEW FEEDBACK - {feedback.name} ({feedback.rating}/5 ⭐)"
        
        # NPS Color Logic
        nps_color = "#ef4444" # Detractor
        if feedback.recommendation >= 9:
            nps_color = "#10b981" # Promoter
        elif feedback.recommendation >= 7:
            nps_color = "#f59e0b" # Passive

        # Create detailed HTML email body
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Feedback Received</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">📥</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                New User Feedback
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #ede9fe; font-size: 14px; font-weight: 500;">
                                Real-time customer insight from QuickFix AI
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Scoring Section -->
                    <tr>
                        <td style="padding: 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 50%; padding-right: 15px;">
                                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                                                Satisfaction
                                            </p>
                                            <div style="font-size: 32px; font-weight: 800; color: #1e293b;">
                                                {feedback.rating}/5
                                            </div>
                                            <div style="color: #f59e0b; font-size: 14px; margin-top: 5px;">
                                                {"⭐" * feedback.rating}
                                            </div>
                                        </div>
                                    </td>
                                    <td style="width: 50%; padding-left: 15px;">
                                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                                                NPS Score
                                            </p>
                                            <div style="font-size: 32px; font-weight: 800; color: {nps_color};">
                                                {feedback.recommendation}/10
                                            </div>
                                            <div style="font-size: 12px; color: #64748b; margin-top: 5px; font-weight: 600;">
                                                {'Promoter' if feedback.recommendation >= 9 else 'Passive' if feedback.recommendation >= 7 else 'Detractor'}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Messages Section -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background-color: #f1f5f9; border-radius: 12px; padding: 25px;">
                                <h3 style="margin: 0 0 15px 0; color: #0f172a; font-size: 16px; font-weight: 700; display: flex; align-items: center;">
                                    <span style="margin-right: 8px;">📝</span> Detailed Thoughts
                                </h3>
                                <p style="margin: 0; color: #334155; font-size: 15px; line-height: 1.6; white-space: pre-wrap; font-style: italic;">
"{feedback.message}"
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- User Details -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="border-top: 1px solid #f1f5f9; padding-top: 25px;">
                                <tr>
                                    <td>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding-bottom: 20px;">
                                                    <p style="margin: 0; color: #64748b; font-size: 12px; font-weight: 600;">SUBMITTED BY</p>
                                                    <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 15px; font-weight: 700;">{feedback.name}</p>
                                                </td>
                                                <td style="padding-bottom: 20px; text-align: right;">
                                                    <p style="margin: 0; color: #64748b; font-size: 12px; font-weight: 600;">CONTACT EMAIL</p>
                                                    <p style="margin: 4px 0 0 0; color: #8b5cf6; font-size: 15px; font-weight: 700;">{feedback.email}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 25px; text-align: center;">
                            <p style="margin: 0; color: #94a3b8; font-size: 12px; font-weight: 500;">
                                This is an automated report generated by the QuickFix AI Feedback Engine.
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
        
        # Send email using dispatcher
        print(f"📧 Sending feedback report to: {admin_email}")
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
