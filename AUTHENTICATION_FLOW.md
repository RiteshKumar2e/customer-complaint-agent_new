# 🔐 Google Sign-In with OTP - Complete Flow

## 📊 Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                                 │
└─────────────────────────────────────────────────────────────────────┘

Step 1: User Opens Application
┌──────────────┐
│   Browser    │
│  (Vercel)    │ ──► User clicks "Launch AI" button
└──────────────┘
       │
       ▼
┌──────────────┐
│ Login Page   │ ──► Shows login form with "Sync with Google" button
└──────────────┘


Step 2: User Clicks "Sync with Google"
┌──────────────┐
│ Login Page   │ ──► User clicks "Sync with Google"
└──────────────┘
       │
       ▼
┌──────────────────────┐
│  Google OAuth Popup  │ ──► Google authentication window opens
│  (Google's Server)   │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  User Selects        │ ──► User chooses their Google account
│  Google Account      │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Google Returns      │ ──► Access token + user info returned
│  User Info           │     (email, name, profile)
└──────────────────────┘


Step 3: Frontend Sends Request to Backend
┌──────────────┐
│  Frontend    │ ──► POST /auth/google
│  (React)     │     { email: "user@gmail.com", name: "User Name" }
└──────────────┘
       │
       ▼
┌──────────────┐
│  Backend     │ ──► 1. Check if user exists in database
│  (FastAPI)   │     2. Create user if new
│              │     3. Generate 6-digit OTP
│              │     4. Save OTP to database (expires in 10 min)
│              │     5. Send OTP via Brevo email service
└──────────────┘
       │
       ▼
┌──────────────┐
│ Email Service│ ──► Sends beautiful HTML email with OTP
│  (Brevo API) │     To: user@gmail.com
└──────────────┘


Step 4: User Receives OTP
┌──────────────┐
│ User's Email │ ──► 📧 "Your verification code is: 123456"
│  Inbox       │
└──────────────┘


Step 5: OTP Modal Appears
┌──────────────┐
│  Frontend    │ ──► Shows OTP input modal
│ (OTP Modal)  │     6 input boxes for digits
└──────────────┘
       │
       ▼
┌──────────────┐
│  User Enters │ ──► Types: 1 2 3 4 5 6
│  OTP Code    │
└──────────────┘


Step 6: Verify OTP
┌──────────────┐
│  Frontend    │ ──► POST /auth/google-verify-otp
│  (React)     │     { email: "user@gmail.com", otp: "123456" }
└──────────────┘
       │
       ▼
┌──────────────┐
│  Backend     │ ──► 1. Check if OTP matches
│  (FastAPI)   │     2. Check if OTP not expired
│              │     3. Clear OTP from database
│              │     4. Generate JWT token
│              │     5. Return token + user data
└──────────────┘
       │
       ▼
┌──────────────┐
│  Frontend    │ ──► 1. Save token to localStorage
│  (React)     │     2. Save user data to localStorage
│              │     3. Close OTP modal
│              │     4. Redirect to dashboard
└──────────────┘


Step 7: User Logged In! 🎉
┌──────────────┐
│  Dashboard   │ ──► User can now access the application
│   (Logged)   │
└──────────────┘
```

---

## 🔄 Technical Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TECHNICAL ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────┘

Frontend (React + Vite)
├── Login.jsx
│   ├── useGoogleLogin() hook
│   │   └── Opens Google OAuth popup
│   ├── handleGoogleLogin()
│   │   ├── Fetches user info from Google API
│   │   └── Calls backend /auth/google
│   └── handleOTPVerify()
│       └── Calls backend /auth/google-verify-otp
│
└── OTPModal.jsx
    ├── 6-digit input fields
    ├── Auto-focus & paste support
    └── Error handling

Backend (FastAPI + Python)
├── /auth/google
│   ├── Receives: { email, name }
│   ├── Creates/finds user in database
│   ├── Generates 6-digit OTP
│   ├── Saves OTP with 10-min expiry
│   ├── Sends email via Brevo
│   └── Returns: { requires_otp: true, email }
│
└── /auth/google-verify-otp
    ├── Receives: { email, otp }
    ├── Validates OTP
    ├── Checks expiry
    ├── Clears OTP
    ├── Generates JWT token
    └── Returns: { access_token, user }

Database (MySQL)
├── users table
│   ├── id
│   ├── email
│   ├── full_name
│   ├── otp (nullable)
│   ├── otp_expiry (nullable)
│   └── created_at

Email Service (Brevo)
├── SMTP API
├── HTML email templates
└── Delivery tracking
```

---

## 🔐 Security Features

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                               │
└─────────────────────────────────────────────────────────────────────┘

Layer 1: Google OAuth
├── ✅ User authenticates with Google
├── ✅ Google verifies identity
├── ✅ Access token from Google
└── ✅ User info from trusted source

Layer 2: Email OTP
├── ✅ 6-digit random code
├── ✅ Sent to verified email
├── ✅ 10-minute expiry
├── ✅ One-time use only
└── ✅ Cleared after verification

Layer 3: JWT Token
├── ✅ Signed with secret key
├── ✅ 7-day expiry
├── ✅ Stored in localStorage
└── ✅ Sent with each API request

Layer 4: CORS Protection
├── ✅ Only allowed origins
├── ✅ Vercel domain whitelisted
└── ✅ Localhost whitelisted
```

---

## 📱 User Experience Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          UX TIMELINE                                 │
└─────────────────────────────────────────────────────────────────────┘

0:00 ──► User clicks "Sync with Google"
         └─► Button shows loading state

0:01 ──► Google popup opens
         └─► User sees their Google accounts

0:03 ──► User selects account
         └─► Google authenticates

0:04 ──► Popup closes
         └─► Frontend receives user info

0:05 ──► Backend generates & sends OTP
         └─► OTP modal appears on screen

0:06 ──► User checks email
         └─► Receives OTP: "123456"

0:10 ──► User enters OTP in modal
         └─► Auto-focuses next input

0:12 ──► User clicks "Verify OTP"
         └─► Button shows "Verifying..."

0:13 ──► Backend validates OTP
         └─► Generates JWT token

0:14 ──► Success! User logged in
         └─► Redirected to dashboard

Total Time: ~14 seconds
```

---

## 🎨 Component Interaction

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPONENT HIERARCHY                               │
└─────────────────────────────────────────────────────────────────────┘

App.jsx
└── Login.jsx
    ├── State Management
    │   ├── email
    │   ├── loading
    │   ├── showOTPModal
    │   ├── otpEmail
    │   └── otpLoading
    │
    ├── Google OAuth Button
    │   └── onClick: handleGoogleLogin()
    │       ├── Opens Google popup
    │       ├── Gets user info
    │       ├── Calls API
    │       └── Shows OTP modal
    │
    └── OTPModal.jsx
        ├── Props
        │   ├── isOpen
        │   ├── email
        │   ├── onVerify
        │   ├── onClose
        │   └── loading
        │
        └── Features
            ├── 6 input fields
            ├── Auto-focus
            ├── Paste support
            ├── Error display
            └── Submit button
```

---

## 🌐 API Endpoints

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API ROUTES                                   │
└─────────────────────────────────────────────────────────────────────┘

POST /auth/google
├── Request:
│   {
│     "token": "user@gmail.com",
│     "name": "User Name"
│   }
│
└── Response:
    {
      "message": "OTP sent to your Google email",
      "email": "user@gmail.com",
      "requires_otp": true
    }

POST /auth/google-verify-otp
├── Request:
│   {
│     "email": "user@gmail.com",
│     "otp": "123456"
│   }
│
└── Response:
    {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer",
      "user": {
        "id": 1,
        "email": "user@gmail.com",
        "full_name": "User Name",
        "is_active": true,
        "created_at": "2025-12-24T20:00:00"
      }
    }
```

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA TRANSFORMATION                             │
└─────────────────────────────────────────────────────────────────────┘

Google OAuth Response
{
  "access_token": "ya29.a0AfH6...",
  "email": "user@gmail.com",
  "name": "User Name",
  "picture": "https://..."
}
       │
       ▼
Frontend Extracts
{
  "email": "user@gmail.com",
  "name": "User Name"
}
       │
       ▼
Backend Creates/Updates User
{
  "id": 1,
  "email": "user@gmail.com",
  "full_name": "User Name",
  "otp": "123456",
  "otp_expiry": "2025-12-24T20:10:00"
}
       │
       ▼
Email Sent
Subject: "🔐 123456 is your Quickfix Verification Code"
Body: [Beautiful HTML template]
       │
       ▼
User Enters OTP
{
  "email": "user@gmail.com",
  "otp": "123456"
}
       │
       ▼
Backend Verifies & Returns JWT
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
       │
       ▼
Frontend Stores
localStorage.setItem("token", "eyJhbGciOiJIUzI1NiIs...")
localStorage.setItem("user", JSON.stringify(user))
```

---

## ✅ Success Criteria

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VERIFICATION CHECKLIST                            │
└─────────────────────────────────────────────────────────────────────┘

Frontend:
├── ✅ Google button triggers OAuth popup
├── ✅ Popup shows Google accounts
├── ✅ After selection, popup closes
├── ✅ OTP modal appears
├── ✅ 6 input fields visible
├── ✅ Can enter digits
├── ✅ Can paste OTP
└── ✅ Submit button works

Backend:
├── ✅ Receives Google auth request
├── ✅ Creates/finds user
├── ✅ Generates OTP
├── ✅ Saves to database
├── ✅ Sends email
├── ✅ Validates OTP
├── ✅ Checks expiry
└── ✅ Returns JWT

Email:
├── ✅ Received in inbox
├── ✅ Contains 6-digit code
├── ✅ Professional design
└── ✅ Within 10 seconds

Database:
├── ✅ User created/updated
├── ✅ OTP stored
├── ✅ Expiry set
└── ✅ OTP cleared after use

Authentication:
├── ✅ JWT token generated
├── ✅ Token stored in localStorage
├── ✅ User data stored
└── ✅ Redirected to dashboard
```

---

**This flow ensures maximum security with excellent user experience!**
