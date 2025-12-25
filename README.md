<div align="center">

# 🚀 Quickfix - AI-Powered Customer Complaint Resolution System

<img src="https://img.shields.io/badge/Status-Live-success?style=for-the-badge" alt="Status">
<img src="https://img.shields.io/badge/Version-2.0.0-blue?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">

### 🌟 Transform Customer Complaints into Opportunities with AI

[🎯 Live Demo](https://customer-complaint-agent-new.vercel.app) • [📚 Documentation](#-documentation) • [🚀 Quick Start](#-quick-start) • [💡 Features](#-key-features)

---

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2.0-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Google_Gemini-AI-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Vite-7.2.5-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite">
</p>

</div>

---

## 📖 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [🔧 Installation](#-installation)
- [🌐 Deployment](#-deployment)
- [📡 API Documentation](#-api-documentation)
- [🤖 AI Agent System](#-ai-agent-system)
- [🔐 Authentication Flow](#-authentication-flow)
- [📊 Tech Stack](#-tech-stack)
- [🎨 Screenshots](#-screenshots)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [👨‍💻 Author](#-author)

---

## 🎯 Overview

**Quickfix** is an enterprise-grade, AI-powered customer complaint resolution platform that revolutionizes how businesses handle customer feedback. Built with cutting-edge technologies including **Google Gemini AI**, **FastAPI**, and **React**, it provides intelligent, automated complaint analysis and resolution recommendations.

### 🎬 Live Demo

🌐 **Production URL**: [https://customer-complaint-agent-new.vercel.app](https://customer-complaint-agent-new.vercel.app)

### 🎥 Demo Video

> Experience the power of AI-driven complaint resolution in action!

---

## ✨ Key Features

### 🧠 **Intelligent AI Agents**

Our system employs **14 specialized AI agents** working in harmony:

| Agent | Purpose | Technology |
|-------|---------|------------|
| 🎯 **Classifier** | Categorizes complaints into departments | Google Gemini AI |
| ⚡ **Priority Agent** | Assigns urgency levels (Low/Medium/High) | ML-based scoring |
| 😊 **Sentiment Analyzer** | Analyzes customer emotions and tone | NLP + Gemini |
| 📝 **Responder** | Generates professional, empathetic responses | GPT-style generation |
| 💡 **Solution Suggester** | Recommends specific solutions | Knowledge base + AI |
| 🎬 **Action Recommender** | Suggests next steps for resolution | Rule-based + AI |
| 🔄 **Re-evaluator** | Reassesses urgency after analysis | Adaptive algorithms |
| 📊 **Satisfaction Predictor** | Predicts customer satisfaction outcomes | Predictive ML |
| 🔍 **Complaint Matcher** | Finds similar past complaints | Vector similarity |
| 💬 **Chat Agent** | Handles real-time user queries | Conversational AI |
| ⚡ **Cache Layer** | Optimizes response times | Redis caching |
| ✅ **Response Validator** | Ensures quality responses | Validation rules |
| 🎯 **Orchestrator** | Coordinates all agents | Central controller |
| 🔌 **Gemini Client** | Manages AI API interactions | Google Gemini API |

### 🔐 **Advanced Authentication**

- **Google OAuth 2.0** integration
- **Email OTP verification** for enhanced security
- **JWT token-based** session management
- **Password reset** functionality
- **Secure user profiles** with data persistence

### 💼 **User Management**

- ✅ User registration and login
- ✅ Profile management with avatar support
- ✅ Complaint history tracking
- ✅ Dashboard analytics
- ✅ Notification center
- ✅ Feedback system

### 📧 **Email Notifications**

- **User confirmation emails** with AI analysis results
- **Admin alert emails** for high-priority complaints
- **OTP verification emails** with beautiful HTML templates
- **Password reset emails** with secure tokens
- Powered by **Brevo API** for reliable delivery

### 🎨 **Modern UI/UX**

- 🌓 **Dark/Light mode** toggle
- 🎯 **Custom cursor** animations
- 📱 **Fully responsive** design
- ✨ **Smooth animations** with Framer Motion
- 🎊 **Confetti celebrations** for successful actions
- 🎨 **Professional glassmorphism** design

### 📊 **Analytics & Insights**

- Real-time complaint statistics
- Sentiment analysis visualization
- Priority distribution charts
- Response time tracking
- User satisfaction metrics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │────────▶│   Backend    │────────▶│   Database   │
│  React+Vite  │  HTTPS  │   FastAPI    │   ORM   │  PostgreSQL  │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       │                        │                        │
       ▼                        ▼                        ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Vercel     │         │  AI Agents   │         │    Redis     │
│  (Hosting)   │         │ Orchestrator │         │   (Cache)    │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Google Gemini│
                         │     API      │
                         └──────────────┘
```

### 📁 Project Structure

```
customer-complaint-agent_new/
│
├── 📂 frontend/                    # React Frontend
│   ├── 📂 src/
│   │   ├── 📂 components/          # React Components
│   │   │   ├── Landing.jsx         # Landing page
│   │   │   ├── Login.jsx           # Login page
│   │   │   ├── Signup.jsx          # Registration page
│   │   │   ├── Dashboard.jsx       # User dashboard
│   │   │   ├── Profile.jsx         # User profile
│   │   │   ├── ComplaintForm.jsx   # Complaint submission
│   │   │   ├── ComplaintList.jsx   # Complaint history
│   │   │   ├── ComplaintCard.jsx   # AI results display
│   │   │   ├── SideChatBot.jsx     # AI assistant
│   │   │   ├── Feedback.jsx        # User feedback
│   │   │   ├── NotificationCenter.jsx  # Notifications
│   │   │   ├── CustomCursor.jsx    # Custom cursor
│   │   │   ├── OTPModal.jsx        # OTP verification
│   │   │   ├── ForgotPassword.jsx  # Password recovery
│   │   │   └── ResetPassword.jsx   # Password reset
│   │   │
│   │   ├── 📂 styles/              # CSS Modules
│   │   │   ├── Landing.css
│   │   │   ├── Login.css
│   │   │   ├── Dashboard.css
│   │   │   ├── Profile.css
│   │   │   └── ... (component styles)
│   │   │
│   │   ├── App.jsx                 # Main app component
│   │   ├── api.js                  # API client
│   │   └── main.jsx                # Entry point
│   │
│   ├── package.json                # Dependencies
│   ├── vite.config.js              # Vite configuration
│   └── Dockerfile                  # Docker config
│
├── 📂 backend/                     # FastAPI Backend
│   ├── 📂 app/
│   │   ├── 📂 agents/              # AI Agent System
│   │   │   ├── orchestrator.py     # Main coordinator
│   │   │   ├── classifier.py       # Complaint categorization
│   │   │   ├── priority.py         # Priority assignment
│   │   │   ├── sentiment_analyzer.py  # Sentiment analysis
│   │   │   ├── responder.py        # Response generation
│   │   │   ├── solution_suggester.py  # Solution recommendations
│   │   │   ├── action_recommender.py  # Action suggestions
│   │   │   ├── reevaluator.py      # Urgency reassessment
│   │   │   ├── satisfaction_predictor.py  # Satisfaction prediction
│   │   │   ├── complaint_matcher.py  # Similar complaint matching
│   │   │   ├── chat_agent.py       # Chatbot handler
│   │   │   ├── gemini_client.py    # Gemini API client
│   │   │   ├── cache_layer.py      # Caching system
│   │   │   └── response_validation.py  # Response validation
│   │   │
│   │   ├── 📂 routes/              # API Routes
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   └── feedback.py         # Feedback endpoints
│   │   │
│   │   ├── 📂 api/                 # Additional APIs
│   │   │   ├── routes.py           # Complaint endpoints
│   │   │   └── chat.py             # Chat endpoints
│   │   │
│   │   ├── 📂 db/                  # Database
│   │   │   ├── database.py         # DB connection
│   │   │   └── models.py           # SQLAlchemy models
│   │   │
│   │   ├── 📂 services/            # Business Logic
│   │   │   ├── email_service.py    # Email handling
│   │   │   └── auth_service.py     # Auth logic
│   │   │
│   │   ├── 📂 schemas/             # Pydantic Schemas
│   │   │   ├── complaint.py
│   │   │   ├── user.py
│   │   │   └── feedback.py
│   │   │
│   │   └── main.py                 # FastAPI app
│   │
│   ├── requirements.txt            # Python dependencies
│   ├── start_backend.py            # Startup script
│   ├── init_db.py                  # Database initialization
│   └── Dockerfile                  # Docker config
│
├── 📂 ALL files structure/         # Documentation
│   ├── AUTHENTICATION_FLOW.md      # Auth documentation
│   ├── DATABASE_SETUP.md           # DB setup guide
│   ├── EMAIL_SETUP.md              # Email configuration
│   ├── QUICK_START.md              # Quick start guide
│   └── ... (additional docs)
│
├── docker-compose.yml              # Docker Compose config
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.10+
- **PostgreSQL** 15+ (or use Render's managed database)
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **Brevo API Key** ([Sign up here](https://www.brevo.com/))

### ⚡ Fast Setup (5 minutes)

```bash
# 1️⃣ Clone the repository
git clone https://github.com/RiteshKumar2e/customer-complaint-agent_new.git
cd customer-complaint-agent_new

# 2️⃣ Backend Setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Create .env file
echo GEMINI_API_KEY=your_gemini_api_key > .env
echo DATABASE_URL=postgresql://user:pass@host:port/dbname >> .env
echo BREVO_API_KEY=your_brevo_api_key >> .env
echo SENDER_EMAIL=your-verified-email@domain.com >> .env
echo ADMIN_EMAIL=admin@yourdomain.com >> .env
echo SECRET_KEY=your-secret-key-here >> .env

# Initialize database
python init_db.py

# Start backend
python start_backend.py

# 3️⃣ Frontend Setup (new terminal)
cd ../frontend
npm install
npm run dev
```

🎉 **Done!** Open [http://localhost:5174](http://localhost:5174)

---

## 🔧 Installation

### Detailed Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with all required variables
cat > .env << EOL
# Google Gemini AI
GEMINI_API_KEY=your_google_gemini_api_key

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Email Service (Brevo)
BREVO_API_KEY=your_brevo_api_key
SENDER_EMAIL=your-verified-sender@domain.com
ADMIN_EMAIL=admin@yourdomain.com

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Server Configuration
HOST=0.0.0.0
PORT=10000

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
EOL

# Initialize database
python init_db.py

# Verify database
python check_db.py

# Start server
python start_backend.py
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Detailed Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (optional)
echo VITE_API_URL=http://localhost:8000 > .env
echo VITE_GOOGLE_CLIENT_ID=your_google_client_id >> .env

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🌐 Deployment

### 🚀 Vercel Deployment (Frontend)

#### Option 1: Deploy via Vercel Dashboard

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Vite
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`

3. **Environment Variables**
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   VITE_GOOGLE_CLIENT_ID=your_google_client_id
   ```

4. **Deploy** 🎉

#### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod
```

### 🔧 Render Deployment (Backend)

#### 1. Database Setup

1. **Create PostgreSQL Database**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **New +** → **PostgreSQL**
   - Name: `quickfix-db`
   - Region: Choose closest to your users
   - Plan: Free or Starter
   - Click **Create Database**

2. **Copy Database URL**
   - Copy the **Internal Database URL**
   - Format: `postgresql://user:pass@host/db`

#### 2. Web Service Setup

1. **Create Web Service**
   - Click **New +** → **Web Service**
   - Connect your GitHub repository
   - Configure:
     - **Name**: `quickfix-backend`
     - **Region**: Same as database
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python start_backend.py`

2. **Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_api_key
   DATABASE_URL=postgresql://user:pass@host/db
   BREVO_API_KEY=your_brevo_api_key
   SENDER_EMAIL=your-verified-email@domain.com
   ADMIN_EMAIL=admin@yourdomain.com
   SECRET_KEY=your-super-secret-jwt-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=10080
   HOST=0.0.0.0
   PORT=10000
   ```

3. **Deploy** 🚀

#### 3. Update Frontend

Update `frontend/src/api.js` with your Render backend URL:
```javascript
const API_URL = 'https://your-backend-url.onrender.com';
```

Redeploy frontend on Vercel.

### 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📡 API Documentation

### 🔐 Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}

Response: 201 Created
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-12-25T10:00:00"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### Google OAuth
```http
POST /auth/google
Content-Type: application/json

{
  "token": "user@gmail.com",
  "name": "John Doe"
}

Response: 200 OK
{
  "message": "OTP sent to your Google email",
  "email": "user@gmail.com",
  "requires_otp": true
}
```

#### Verify OTP
```http
POST /auth/google-verify-otp
Content-Type: application/json

{
  "email": "user@gmail.com",
  "otp": "123456"
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

### 📝 Complaint Endpoints

#### Submit Complaint
```http
POST /complaint
Authorization: Bearer <token>
Content-Type: application/json

{
  "complaint": "My refund has been delayed for over 2 weeks",
  "user_id": 1
}

Response: 200 OK
{
  "id": 1,
  "complaint": "My refund has been delayed for over 2 weeks",
  "category": "Billing",
  "priority": "High",
  "sentiment": "Negative",
  "satisfaction_score": 0.35,
  "response": "We sincerely apologize for the delay...",
  "action": "Escalate to finance team within 24 hours",
  "solution": "Initiate immediate refund processing",
  "similar_complaints": [...],
  "created_at": "2025-12-25T10:00:00"
}
```

#### Get User Complaints
```http
GET /complaints/user/{user_id}
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "complaint": "...",
    "category": "Billing",
    "priority": "High",
    "status": "pending",
    "created_at": "2025-12-25T10:00:00"
  },
  ...
]
```

### 💬 Chat Endpoint

```http
POST /agent/chat?message=What%20does%20this%20system%20do
Authorization: Bearer <token>

Response: 200 OK
{
  "response": "Quickfix is an AI-powered customer complaint management system..."
}
```

### 📊 Feedback Endpoint

```http
POST /feedback/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 1,
  "rating": 5,
  "comment": "Excellent service!",
  "recommendation": 10
}

Response: 200 OK
{
  "message": "Thank you for your feedback!"
}
```

### 📖 Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤖 AI Agent System

### Agent Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT PIPELINE                          │
└─────────────────────────────────────────────────────────────────┘

User Submits Complaint
        │
        ▼
┌──────────────────┐
│  Orchestrator    │ ◄─── Coordinates all agents
└────────┬─────────┘
         │
         ├─────────────────────────────────────────────────┐
         │                                                  │
         ▼                                                  ▼
┌──────────────────┐                              ┌──────────────────┐
│   Classifier     │ ─── Categorizes complaint    │  Cache Layer     │
│   (Gemini AI)    │     (Billing, Support, etc)  │  (Redis)         │
└────────┬─────────┘                              └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Sentiment        │ ─── Analyzes emotions
│ Analyzer         │     (Positive/Negative/Neutral)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Priority Agent   │ ─── Assigns urgency
│                  │     (Low/Medium/High)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Complaint        │ ─── Finds similar cases
│ Matcher          │     (Vector similarity)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Responder        │ ─── Generates professional
│ (Gemini AI)      │     empathetic response
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Solution         │ ─── Recommends specific
│ Suggester        │     solutions
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Action           │ ─── Suggests next steps
│ Recommender      │     (Escalate, Refund, etc)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Satisfaction     │ ─── Predicts customer
│ Predictor        │     satisfaction score
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Re-evaluator     │ ─── Adjusts priority if
│                  │     needed based on analysis
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Response         │ ─── Validates quality
│ Validator        │     of generated response
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Database         │ ─── Stores complaint
│ (PostgreSQL)     │     and AI analysis
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Email Service    │ ─── Sends notifications
│ (Brevo)          │     to user and admin
└──────────────────┘
```

### Agent Details

| Agent | Input | Output | AI Model |
|-------|-------|--------|----------|
| **Classifier** | Complaint text | Category (Billing, Technical, etc.) | Gemini 1.5 Flash |
| **Sentiment Analyzer** | Complaint text | Sentiment (Positive/Negative/Neutral) | Gemini + NLP |
| **Priority Agent** | Complaint + Sentiment | Priority (Low/Medium/High) | Rule-based + ML |
| **Complaint Matcher** | Complaint text | Similar complaints | Vector embeddings |
| **Responder** | Complaint + Context | Professional response | Gemini 1.5 Pro |
| **Solution Suggester** | Category + Complaint | Specific solutions | Knowledge base + AI |
| **Action Recommender** | Priority + Category | Action items | Rule-based logic |
| **Satisfaction Predictor** | All analysis | Satisfaction score (0-1) | Predictive model |
| **Re-evaluator** | Initial + Response | Adjusted priority | Adaptive algorithm |
| **Response Validator** | Generated response | Validation result | Quality checks |

---

## 🔐 Authentication Flow

For detailed authentication documentation, see [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md)

### Quick Overview

```
User Journey:
1. User clicks "Launch AI" → Redirected to Login
2. User clicks "Sync with Google" → Google OAuth popup
3. User selects Google account → Google authenticates
4. Backend generates 6-digit OTP → Sent via email
5. User enters OTP in modal → Backend verifies
6. JWT token generated → User logged in
7. Redirected to Dashboard → Full access granted

Security Layers:
✅ Google OAuth 2.0
✅ Email OTP verification (10-min expiry)
✅ JWT token authentication (7-day expiry)
✅ CORS protection
✅ Password hashing (bcrypt)
✅ Secure session management
```

---

## 📊 Tech Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2.0 | UI framework |
| **Vite** | 7.2.5 | Build tool & dev server |
| **Framer Motion** | 12.23.26 | Animations |
| **Axios** | 1.13.2 | HTTP client |
| **React OAuth Google** | 0.13.4 | Google authentication |
| **Canvas Confetti** | 1.9.4 | Celebration effects |
| **Lodash** | 4.17.21 | Utility functions |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Programming language |
| **FastAPI** | 0.110.0 | Web framework |
| **Google Gemini** | 0.3.2 | AI language model |
| **SQLAlchemy** | 2.0.45 | ORM |
| **PostgreSQL** | 15+ | Database |
| **Pydantic** | 2.6.4 | Data validation |
| **Redis** | 5.0.3 | Caching |
| **PyJWT** | 3.3.0 | JWT authentication |
| **Passlib** | 1.7.4 | Password hashing |
| **Uvicorn** | 0.29.0 | ASGI server |

### DevOps & Deployment

| Technology | Purpose |
|------------|---------|
| **Vercel** | Frontend hosting |
| **Render** | Backend hosting |
| **Docker** | Containerization |
| **GitHub Actions** | CI/CD (optional) |
| **Brevo** | Email service |

---

## 🎨 Screenshots

### 🏠 Landing Page
> Modern, responsive landing page with smooth animations

### 🔐 Authentication
> Secure login with Google OAuth and OTP verification

### 📊 Dashboard
> Comprehensive dashboard with analytics and insights

### 📝 Complaint Submission
> Intuitive form with real-time AI analysis

### 💬 AI Chat Assistant
> Side-panel chatbot for instant help

### 👤 User Profile
> Personalized profile with complaint history

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 1️⃣ Fork the Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/customer-complaint-agent_new.git
cd customer-complaint-agent_new
```

### 2️⃣ Create a Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### 3️⃣ Make Your Changes

- Follow existing code style
- Add comments for complex logic
- Update documentation if needed
- Test thoroughly

### 4️⃣ Commit Your Changes

```bash
git add .
git commit -m "✨ Add amazing feature"
```

### 5️⃣ Push and Create Pull Request

```bash
git push origin feature/amazing-feature
```

Then create a Pull Request on GitHub.

### 📋 Contribution Guidelines

- **Code Quality**: Follow PEP 8 (Python) and ESLint rules (JavaScript)
- **Testing**: Add tests for new features
- **Documentation**: Update README and inline comments
- **Commits**: Use conventional commit messages
- **Issues**: Check existing issues before creating new ones

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Ritesh Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the [LICENSE](LICENSE) file for full details.

---

## 👨‍💻 Author

<div align="center">

### **Ritesh Kumar**

[![GitHub](https://img.shields.io/badge/GitHub-RiteshKumar2e-181717?style=for-the-badge&logo=github)](https://github.com/RiteshKumar2e)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ritesh_Kumar-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/ritesh-kumar-b3a654253)
[![Email](https://img.shields.io/badge/Email-riteshkumar90359@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:riteshkumar90359@gmail.com)
[![Phone](https://img.shields.io/badge/Phone-+91_6206269895-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](tel:+916206269895)

</div>

---

## 🌟 Show Your Support

If you find this project helpful, please consider:

- ⭐ **Starring** the repository
- 🍴 **Forking** for your own projects
- 📢 **Sharing** with others
- 🐛 **Reporting** bugs and issues
- 💡 **Suggesting** new features

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/RiteshKumar2e/customer-complaint-agent_new?style=social)](https://github.com/RiteshKumar2e/customer-complaint-agent_new)
[![GitHub forks](https://img.shields.io/github/forks/RiteshKumar2e/customer-complaint-agent_new?style=social)](https://github.com/RiteshKumar2e/customer-complaint-agent_new/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/RiteshKumar2e/customer-complaint-agent_new?style=social)](https://github.com/RiteshKumar2e/customer-complaint-agent_new)

</div>

---

## 🙏 Acknowledgments

- **Google Gemini Team** - For the powerful AI API
- **FastAPI Community** - For excellent documentation
- **React Team** - For the amazing framework
- **Vercel** - For seamless deployment
- **Render** - For reliable backend hosting
- **Brevo** - For email service
- **Open Source Community** - For inspiration and support

---

## 📚 Additional Resources

- 📖 [Full Documentation](./ALL%20files%20structure/)
- 🔐 [Authentication Guide](./AUTHENTICATION_FLOW.md)
- 🗄️ [Database Setup](./ALL%20files%20structure/DATABASE_SETUP.md)
- 📧 [Email Configuration](./ALL%20files%20structure/EMAIL_SETUP.md)
- 🚀 [Quick Start Guide](./ALL%20files%20structure/QUICK_START.md)
- 🎨 [Visual Design Guide](./ALL%20files%20structure/VISUAL_DESIGN_GUIDE.md)

---

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Voice complaint submission
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Slack/Teams integration
- [ ] Custom AI model training
- [ ] Real-time collaboration
- [ ] API rate limiting
- [ ] Webhook support
- [ ] Export reports (PDF/Excel)

---

## 📞 Support

Need help? Reach out:

- 📧 **Email**: [riteshkumar90359@gmail.com](mailto:riteshkumar90359@gmail.com)
- 💬 **GitHub Issues**: [Create an issue](https://github.com/RiteshKumar2e/customer-complaint-agent_new/issues)
- 📱 **Phone**: +91 6206269895

---

<div align="center">

### ⚡ Built with ❤️ by Ritesh Kumar

**Transforming Customer Service with AI**

[🚀 Live Demo](https://customer-complaint-agent-new.vercel.app) • [📖 Docs](#-documentation) • [💻 GitHub](https://github.com/RiteshKumar2e/customer-complaint-agent_new)

---

**© 2025 Quickfix. All rights reserved.**

</div>
