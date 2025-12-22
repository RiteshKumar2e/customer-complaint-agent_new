# 📧 Email Setup Guide - Quickfix

Complete guide to set up email notifications for the Quickfix complaint management system.

## Quick Start

### 1️⃣ Enable Gmail 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **"2-Step Verification"** in the left menu
3. Follow the setup wizard to enable 2FA
4. Complete the verification process

### 2️⃣ Generate Gmail App Password

1. Visit [App Passwords](https://myaccount.google.com/apppasswordsa)
2. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or your device)
3. Google will generate a **16-character password**
4. Copy the password (it looks like: `xxxx xxxx xxxx xxxx`)

### 3️⃣ Update Environment Variables

Edit `.env` file in the `backend` directory:

```env
SENDER_EMAIL=your-actual-gmail@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
```

**Example:**
```env
SENDER_EMAIL=riteshkumar90359@gmail.com
SENDER_PASSWORD=svit ekgh ksho tloo
```

### 4️⃣ Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5️⃣ Restart Backend Server

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## How Email Works

### When User Submits Complaint

```
User fills form (name, email, complaint)
         ↓
AI agents analyze complaint
         ↓
Data saved to database
         ↓
📧 Email sent to user (confirmation)
📧 Email sent to admin (alert)
         ↓
Success notification on frontend
```

### User Email

**Subject:** `Complaint Received - Quickfix Support Team`

Contains:
- ✅ Complaint confirmation
- 📋 Complaint details
- 🤖 AI analysis results
- ⏱️ Expected resolution time
- 🔗 Dashboard link

### Admin Email

**Subject:** `🚨 New Complaint from [Name] - [Category]`

Contains:
- 👤 Customer information
- 📋 Full complaint details
- 🎯 Priority level (color-coded)
- 🤖 AI analysis results
- ⚡ Recommended next steps
- 🔗 Dashboard link to manage complaint

---

## Troubleshooting

### ❌ Error: "Username and Password not accepted"

**Problem:** Wrong email or app password

**Solution:**
1. Verify your Gmail address is correct
2. Generate a NEW app password from [App Passwords](https://myaccount.google.com/apppasswords)
3. **Important:** Use the App Password, NOT your regular Gmail password
4. Update `.env` file with new credentials
5. Restart backend server

### ❌ Error: "2-Step Verification not enabled"

**Problem:** Gmail 2FA is required for app passwords

**Solution:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Then generate app password

### ❌ Error: "SMTP connection failed"

**Problem:** Network or firewall issue

**Solution:**
1. Check internet connection
2. Try using a VPN if blocked by firewall
3. Verify SMTP settings:
   - Server: `smtp.gmail.com`
   - Port: `587`
   - Security: `STARTTLS`

### ❌ Emails not being sent but no error message

**Problem:** Email service might be disabled or not initialized

**Solution:**
1. Check backend console for email errors
2. Verify `.env` file has correct credentials
3. Make sure `email_service.py` is in `app/services/` directory
4. Restart backend server

---

## Security Best Practices

⚠️ **IMPORTANT SECURITY NOTES:**

1. **Never use your main Gmail password** - Always use an App Password
2. **App Passwords are app-specific** - They only work with this application
3. **Revoke anytime** - If compromised, delete the app password from your Google Account
4. **Don't commit .env to Git** - Keep `.env` file local and in `.gitignore`
5. **Enable 2FA** - Required for app passwords to work

### Revoking App Password

If you think the password is compromised:

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select the app password you created
3. Click delete/revoke
4. Generate a new one if needed

---

## Email Templates

### Confirmation Email Structure

```
Header (Company branding)
├── Greeting
├── Thank you message
├── Complaint details (category, priority, description)
├── AI analysis results
│   ├── Sentiment
│   ├── Response
│   ├── Solution
│   └── Action
├── Expected resolution time
├── Dashboard link
└── Footer (Contact info)
```

### Admin Alert Structure

```
Header (Alert styling)
├── Greeting (Hi Admin)
├── Customer information
│   ├── Name
│   └── Email
├── Complaint details
│   ├── Category
│   ├── Priority (color-coded)
│   └── Description
├── AI analysis results
├── Action items
├── Dashboard link
└── Footer (Admin panel)
```

---

## Testing

### Test Email Manually

1. Submit a complaint through the form
2. Check your email inbox (user email)
3. Check admin inbox (`riteshkumar90359@gmail.com`)
4. Verify both emails received successfully

### Backend Console Output

When email is sent, you'll see:

```
📧 Confirmation email sent to user@example.com
📧 Admin notification sent to riteshkumar90359@gmail.com
```

### Common Issues in Console

```
✅ Success:
  ✅ Complaint saved successfully!
  📧 Confirmation email sent to...
  📧 Admin notification sent to...

❌ Failure:
  ❌ Failed to send confirmation email: [error message]
```

---

## Configuration Details

### Email Service Location
`backend/app/services/email_service.py`

### Key Functions
- `send_complaint_confirmation()` - Sends email to user
- `send_resolution_email()` - For future use (sends resolution details)
- `_generate_confirmation_html()` - User email template
- `_generate_admin_notification_html()` - Admin email template

### Email Service Class
```python
class EmailService:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    def send_complaint_confirmation(user_name, user_email, complaint_data)
    def send_resolution_email(user_name, user_email, complaint_data)
```

---

## Next Steps

- ✅ Set up Gmail 2FA
- ✅ Generate app password
- ✅ Update `.env` file
- ✅ Install requirements
- ✅ Restart backend
- ✅ Test by submitting complaint
- ✅ Verify emails received

---

## Contact & Support

- **Developer:** Ritesh Kumar
- **Email:** riteshkumar90359@gmail.com
- **Phone:** +91 62062 69895
- **GitHub:** https://github.com/RiteshKumar2e
- **LinkedIn:** https://www.linkedin.com/in/ritesh-kumar-b3a654253

---

## FAQ

**Q: Can I use a different email provider?**
A: Yes, but you'll need to update SMTP settings in `email_service.py`

**Q: Are emails encrypted?**
A: Yes, using STARTTLS encryption on port 587

**Q: Will emails be sent if AI fails?**
A: No, emails are only sent after successful database save and analysis

**Q: Can I customize email templates?**
A: Yes, edit the HTML templates in `_generate_confirmation_html()` and `_generate_admin_notification_html()` methods

**Q: How often can I send emails?**
A: Gmail free tier allows ~500 emails/day

---

Last Updated: December 21, 2025
Version: 1.0
