"""
Authentication emails: OTP codes and security notices.

The OTP appears only in the message body (never in the subject line, which
mail clients and logs display widely). No email ever contains a password.
"""
from __future__ import annotations

import html

from app.core.config import get_settings
from app.services import email_transport

_PURPOSE_COPY = {
    "registration": ("Verify your email address",
                     "Use this code to finish creating your account."),
    "verify_email": ("Verify your email address",
                     "Use this code to confirm your email address and activate your account."),
    "login": ("Your sign-in code",
              "Use this code to sign in to your account."),
    "password_reset": ("Reset your password",
                       "Use this code to reset your password. If you did not ask for this, you can ignore "
                       "this email — your password has not been changed."),
}


def _otp_html(code: str, heading: str, intro: str, name: str, minutes: int, company: str) -> str:
    safe_name = html.escape(name) if name else "there"
    digits = "".join(
        f'<td style="padding:0 3px"><div style="width:40px;height:52px;line-height:52px;border:1px solid #d0d5dd;'
        f'border-radius:8px;font:700 26px/52px \'Segoe UI\',Arial,sans-serif;color:#101828;text-align:center;'
        f'background:#f9fafb">{d}</div></td>' for d in code
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{html.escape(heading)}</title>
<style>@media (max-width:480px){{.card{{padding:24px 18px!important}}.digits td div{{width:34px!important;height:46px!important;line-height:46px!important;font-size:22px!important}}}}</style>
</head>
<body style="margin:0;padding:0;background:#f2f4f7;font-family:'Segoe UI',Arial,sans-serif;color:#344054">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2f4f7;padding:32px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:12px;border:1px solid #eaecf0">
<tr><td style="padding:16px 32px;border-bottom:1px solid #eaecf0;font:700 16px 'Segoe UI',Arial,sans-serif;color:#101828"><img src="{html.escape(get_settings().app_url)}/logo-email.png" alt="{html.escape(company)}" height="36" style="display:block;height:36px;border:0"></td></tr>
<tr><td class="card" style="padding:32px">
<h1 style="margin:0 0 12px;font:700 22px 'Segoe UI',Arial,sans-serif;color:#101828">{html.escape(heading)}</h1>
<p style="margin:0 0 8px;font-size:15px;line-height:22px">Hi {safe_name},</p>
<p style="margin:0 0 24px;font-size:15px;line-height:22px">{html.escape(intro)}</p>
<table role="presentation" class="digits" cellpadding="0" cellspacing="0" align="center" style="margin:0 auto 12px"><tr>{digits}</tr></table>
<p style="margin:0 0 24px;text-align:center;font-size:13px;color:#667085">Code: <strong style="letter-spacing:2px;color:#101828">{code}</strong></p>
<p style="margin:0 0 8px;font-size:14px;line-height:21px">This code expires in <strong>{minutes} minutes</strong> and can be used only once.</p>
<p style="margin:0;font-size:14px;line-height:21px">Never share this code. Our team will never ask you for it.</p>
</td></tr>
<tr><td style="padding:16px 32px;border-top:1px solid #eaecf0;font-size:12px;line-height:18px;color:#98a2b3">
If you did not request this code, you can safely ignore this email. Someone may have typed your address by mistake.
</td></tr>
</table></td></tr></table></body></html>"""


def _otp_text(code: str, heading: str, intro: str, name: str, minutes: int, company: str) -> str:
    return (
        f"{company} - {heading}\n\n"
        f"Hi {name or 'there'},\n\n"
        f"{intro}\n\n"
        f"Your code: {code}\n\n"
        f"This code expires in {minutes} minutes and can be used only once.\n"
        f"Never share this code. Our team will never ask you for it.\n\n"
        f"If you did not request this code, you can ignore this email.\n"
    )


def render_otp_email(code: str, purpose: str, name: str = "") -> tuple:
    s = get_settings()
    heading, intro = _PURPOSE_COPY.get(purpose, _PURPOSE_COPY["verify_email"])
    minutes = max(1, s.otp_ttl_seconds // 60)
    subject = f"{heading} - {s.company_name}"
    return (subject, _otp_html(code, heading, intro, name, minutes, s.company_name),
            _otp_text(code, heading, intro, name, minutes, s.company_name))


def send_otp_email(to: str, code: str, purpose: str, name: str = "") -> None:
    """Synchronous: raises EmailDeliveryError so callers never treat a failed send as success."""
    subject, html_body, text_body = render_otp_email(code, purpose, name)
    email_transport.send(to, subject, html_body, text_body, category=f"otp:{purpose}", retries=1)


def send_password_changed_notice(to: str, name: str = "") -> None:
    s = get_settings()
    subject = f"Your password was changed - {s.company_name}"
    text_body = (
        f"Hi {name or 'there'},\n\nThe password for your {s.company_name} account was just changed and all "
        f"other sessions were signed out.\n\nIf this was not you, reset your password immediately and contact support.\n"
    )
    html_body = (
        f"<p>Hi {html.escape(name or 'there')},</p><p>The password for your {html.escape(s.company_name)} account "
        f"was just changed and all other sessions were signed out.</p><p>If this was not you, reset your password "
        f"immediately and contact support.</p>"
    )
    email_transport.send(to, subject, html_body, text_body, category="security:password_changed")
