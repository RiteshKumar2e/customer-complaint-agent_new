"""
Authentication emails: OTP codes and security notices.

The OTP appears exactly once, in the message body (never in the subject line,
which lock screens, mail logs and the provider's dashboard show widely).
No email ever contains a password.
"""
from __future__ import annotations

import html

from app.core.config import get_settings
from app.services import email_transport

_PURPOSE_COPY = {
    "registration": ("Verify your email address",
                     "Enter this code to finish creating your account."),
    "verify_email": ("Verify your email address",
                     "Enter this code to confirm your email address and activate your account."),
    "login": ("Your sign-in code",
              "Enter this code to sign in to your account."),
    "password_reset": ("Reset your password",
                       "Enter this code to reset your password. If you didn't ask for this, you can ignore "
                       "this email; your password has not been changed."),
}

_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


def _otp_html(code: str, heading: str, intro: str, name: str, minutes: int, company: str, app_url: str) -> str:
    e = html.escape
    greeting = f"Hi {e(name)}," if name else "Hello,"
    year_line = f"&copy; {e(company)}"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light">
<title>{e(heading)}</title>
<style>
  @media (max-width:520px) {{ .qf-card {{ padding:24px 20px 28px 20px !important; }} .qf-pad {{ padding-left:20px !important; padding-right:20px !important; }} .qf-outer {{ padding:20px 10px !important; }} .qf-code {{ font-size:30px !important; letter-spacing:8px !important; }} }}
</style>
</head>
<body style="margin:0;padding:0;background:#f4f5f7;-webkit-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">{e(heading)} &ndash; this code expires in {minutes} minutes.&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;">
  <tr><td align="center" class="qf-outer" style="padding:40px 16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;">
      <tr><td style="height:4px;background:#2563eb;line-height:4px;font-size:0;">&nbsp;</td></tr>
      <tr><td class="qf-pad" style="padding:28px 40px 0 40px;">
        <img src="{e(app_url)}/logo-email.png" alt="{e(company)}" height="32" style="display:block;height:32px;width:auto;border:0;font:700 18px {_FONT};color:#111827;">
      </td></tr>
      <tr><td class="qf-card" style="padding:28px 40px 36px 40px;font-family:{_FONT};color:#374151;">
        <h1 style="margin:0 0 16px 0;font-size:22px;line-height:30px;font-weight:700;color:#111827;">{e(heading)}</h1>
        <p style="margin:0 0 8px 0;font-size:15px;line-height:24px;">{greeting}</p>
        <p style="margin:0 0 28px 0;font-size:15px;line-height:24px;">{e(intro)}</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr><td align="center" style="background:#f3f6fd;border:1px solid #dbe4fb;border-radius:10px;padding:22px 12px;">
            <div style="font-size:12px;line-height:16px;letter-spacing:1.5px;text-transform:uppercase;color:#6b7280;margin-bottom:8px;">Verification code</div>
            <div class="qf-code" style="font-family:'SFMono-Regular',Menlo,Consolas,'Courier New',monospace;font-size:36px;line-height:44px;font-weight:700;letter-spacing:12px;color:#111827;padding-left:12px;">{e(code)}</div>
          </td></tr>
        </table>
        <p style="margin:24px 0 0 0;font-size:14px;line-height:22px;color:#4b5563;">
          This code expires in <strong style="color:#111827;">{minutes} minutes</strong> and can be used only once.
        </p>
        <p style="margin:12px 0 0 0;font-size:14px;line-height:22px;color:#4b5563;">
          For your security, never share this code with anyone. {e(company)} will never ask you for it.
        </p>
      </td></tr>
      <tr><td class="qf-pad" style="padding:20px 40px;border-top:1px solid #f0f1f3;font-family:{_FONT};font-size:12px;line-height:18px;color:#9ca3af;">
        Didn't request this? You can safely ignore this email &ndash; someone may have entered your address by mistake.<br>
        {year_line} &middot; This is an automated message, please don't reply.
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def _otp_text(code: str, heading: str, intro: str, name: str, minutes: int, company: str) -> str:
    return (
        f"{heading}\n\n"
        f"{('Hi ' + name + ',') if name else 'Hello,'}\n\n"
        f"{intro}\n\n"
        f"    {code}\n\n"
        f"This code expires in {minutes} minutes and can be used only once.\n"
        f"For your security, never share this code with anyone. {company} will never ask you for it.\n\n"
        f"Didn't request this? You can safely ignore this email.\n"
        f"-- {company} (automated message, please don't reply)\n"
    )


def render_otp_email(code: str, purpose: str, name: str = "") -> tuple:
    s = get_settings()
    heading, intro = _PURPOSE_COPY.get(purpose, _PURPOSE_COPY["verify_email"])
    minutes = max(1, s.otp_ttl_seconds // 60)
    subject = f"Your {s.company_name} verification code" if purpose != "password_reset" \
        else f"Reset your {s.company_name} password"
    return (subject,
            _otp_html(code, heading, intro, name, minutes, s.company_name, s.app_url),
            _otp_text(code, heading, intro, name, minutes, s.company_name))


def send_otp_email(to: str, code: str, purpose: str, name: str = "") -> None:
    """Synchronous: raises EmailDeliveryError so callers never treat a failed send as success."""
    subject, html_body, text_body = render_otp_email(code, purpose, name)
    email_transport.send(to, subject, html_body, text_body, category=f"otp:{purpose}", retries=1)


def send_password_changed_notice(to: str, name: str = "") -> None:
    s = get_settings()
    subject = f"Your {s.company_name} password was changed"
    text_body = (
        f"{('Hi ' + name + ',') if name else 'Hello,'}\n\nThe password for your {s.company_name} account was just "
        f"changed and all other sessions were signed out.\n\nIf this wasn't you, reset your password immediately "
        f"and contact support.\n"
    )
    html_body = (
        f"<div style=\"font-family:{_FONT};font-size:15px;line-height:24px;color:#374151;max-width:520px\">"
        f"<p>{('Hi ' + html.escape(name) + ',') if name else 'Hello,'}</p><p>The password for your "
        f"{html.escape(s.company_name)} account was just changed and all other sessions were signed out.</p>"
        f"<p>If this wasn't you, reset your password immediately and contact support.</p></div>"
    )
    email_transport.send(to, subject, html_body, text_body, category="security:password_changed")
