# 🤖 Quickfix – AI Complaint Resolver

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)

Quickfix is an **enterprise-grade agentic AI platform** that intelligently handles customer complaints through **multi-step reasoning, persistent memory, and conditional decision-making**. Built with **Google Gemini AI**, **FastAPI**, and **React.js**, it automates complaint classification, prioritization, response generation, and actionable recommendations.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Agent Workflow](#-agent-workflow)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## ✨ Key Features

### 🧠 Agentic AI Capabilities

ComplaintAI operates as an **autonomous AI agent**, not just a simple chatbot:

- **Intelligent Classification** – Automatically categorizes complaints into relevant departments
- **Dynamic Prioritization** – Assigns urgency levels (Low/Medium/High) based on context
- **Sentiment Analysis** – Analyzes customer emotions and tone
- **Satisfaction Prediction** – Predicts customer satisfaction outcomes
- **Professional Response Generation** – Drafts empathetic, context-aware response templates
- **Solution Suggestions** – Recommends specific solutions based on complaint type
- **Smart Action Recommendations** – Suggests next steps for resolution
- **Complaint Matching** – Identifies similar past complaints for faster resolution
- **Adaptive Re-evaluation** – Reassesses urgency after initial response drafting
- **Email Notifications** – Automated confirmation emails to users and alert emails to admins
- **Persistent Memory** – Redis-based memory for high-priority complaint tracking
- **Database Integration** – SQLite database for complaint history and analytics
- **Conditional Workflows** – Executes different flows based on complaint severity

### 💬 Integrated AI Assistant

- **Side-Panel Chatbot** – Always accessible for real-time help
- **Contextual Guidance** – Answers questions about complaint workflow and AI decisions
- **Gemini-Powered** – Leverages Google's advanced language model
- **Graceful Fallbacks** – Rule-based logic ensures reliability

### 🖥️ Modern Frontend

- **Responsive Design** – Works seamlessly across devices
- **Intuitive Interface** – Clean, user-friendly complaint submission flow
- **Real-Time Feedback** – Instant AI analysis results
- **Dashboard View** – Admin dashboard for complaint management
- **Complaint List** – View and track all submitted complaints
- **Component Architecture** – Modular React components for maintainability
- **Professional Styling** – Production-ready CSS modules for each component

### ⚙️ Robust Backend

- **Modular Agent System** – 11 specialized AI agents for comprehensive complaint handling
- **RESTful API** – Clean, documented endpoints
- **Database Integration** – SQLite database with SQLAlchemy ORM
- **Redis Memory Store** – Fast, persistent memory for agent state
- **Error Handling** – Comprehensive exception management
- **CORS Support** – Configured for frontend integration
- **Secure Configuration** – Environment-based secrets management
- **Startup Scripts** – Easy initialization and database setup
- **Scalable Architecture** – Ready for production deployment

---

## 🏗️ System Architecture

```
customer-complaint-agent/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── action_recommender.py    # Action suggestion engine
│   │   │   ├── chat_agent.py            # Chatbot conversation handler
│   │   │   ├── classifier.py            # Complaint categorization
│   │   │   ├── complaint_matcher.py     # Complaint matching logic
│   │   │   ├── gemini_client.py         # Gemini API abstraction
│   │   │   ├── orchestrator.py          # Main agent coordinator
│   │   │   ├── priority.py              # Priority assignment logic
│   │   │   ├── reevaluator.py           # Urgency reassessment
│   │   │   ├── responder.py             # Response template generation
│   │   │   ├── satisfaction_predictor.py # Customer satisfaction prediction
│   │   │   ├── sentiment_analyzer.py    # Sentiment analysis engine
│   │   │   └── solution_suggester.py    # Solution recommendation system
│   │   ├── api/
│   │   │   ├── chat.py                  # Chatbot API endpoints
│   │   │   └── routes.py                # Complaint submission endpoints
│   │   ├── db/
│   │   │   ├── database.py              # Database connection & setup
│   │   │   └── models.py                # SQLAlchemy models
│   │   ├── memory/
│   │   │   └── redis_store.py           # Redis-based memory management
│   │   ├── models/
│   │   │   └── complaint.py             # Complaint data model
│   │   └── schemas/
│   │       ├── init_.py                 # Schema initialization
│   │       └── complaint.py             # Pydantic schemas
│   ├── .env
    ├── email_services.py                   # Environment variables
│   ├── check_db.py                      # Database verification script
│   ├── complaints.db                    # SQLite database
│   ├── init_db.py                       # Database initialization
│   ├── requirements.txt                 # Python dependencies
│   ├── requirements.lock.txt            # Locked dependencies
│   └── start_backend.py                 # Backend startup script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ComplaintCard.jsx        # AI result display
│   │   │   ├── ComplaintForm.jsx        # Complaint submission form
│   │   │   ├── ComplaintList.jsx        # List of complaints
│   │   │   ├── Dashboard.jsx            # Admin dashboard
│   │   │   ├── Landing.jsx              # Landing page component
│   │   │   └── SideChatBot.jsx          # Integrated chat assistant
│   │   ├── styles/
│   │   │   ├── ComplaintCard.css        # Card styling
│   │   │   ├── ComplaintForm.css        # Form styling
│   │   │   ├── ComplaintList.css        # List styling
│   │   │   ├── Dashboard.css            # Dashboard styling
│   │   │   ├── Landing.css              # Landing page styling
│   │   │   └── SideChatBot.css          # Chatbot styling
│   │   ├── api.js                       # API client configuration
│   │   ├── App.css                      # Global app styles
│   │   ├── App.jsx                      # Main application component
│   │   ├── index.css                    # Base CSS styles
│   │   └── main.jsx                     # React entry point
│   ├── .gitignore                       # Frontend git ignore
│   ├── eslint.config.js                 # ESLint configuration
│   ├── index.html                       # HTML template
│   ├── package.json                     # NPM dependencies
│   ├── package-lock.json                # NPM lock file
│   ├── vite.config.js                   # Vite configuration
│   └── start_backend.py                 # Backend startup helper
│
├── .gitignore                           # Git ignore rules
└── README.md                            # Project documentation
```

---

## 🔑 Technology Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core programming language |
| **FastAPI** | High-performance web framework |
| **Google Gemini API** | Advanced language model |
| **Pydantic** | Data validation and serialization |
| **SQLAlchemy** | SQL toolkit and ORM |
| **SQLite** | Lightweight database |
| **Redis** | In-memory data store for agent memory |
| **SMTP (Gmail)** | Email notification service |
| **Uvicorn** | ASGI server |

### Frontend

| Technology | Purpose |
|------------|---------|
| **React.js** | UI component framework |
| **Vite** | Fast build tool and dev server |
| **Axios** | HTTP client for API calls |
| **CSS Modules** | Scoped component styling |

### AI & Agent Framework

- **Google Gemini** – Natural language understanding and generation
- **Multi-Agent Pipeline** – 11 specialized agents working in coordination:
  - **Orchestrator** – Coordinates all agents
  - **Classifier** – Categorizes complaints
  - **Priority Agent** – Assigns urgency levels
  - **Sentiment Analyzer** – Analyzes emotional tone
  - **Responder** – Generates professional responses
  - **Action Recommender** – Suggests next steps
  - **Solution Suggester** – Recommends specific solutions
  - **Re-evaluator** – Reassesses complaint urgency
  - **Satisfaction Predictor** – Predicts customer satisfaction
  - **Complaint Matcher** – Finds similar past complaints
  - **Chat Agent** – Handles conversational queries
- **Redis-Based Memory** – Persistent state management across sessions
- **SQLite Database** – Historical data and analytics
- **Rule-Based Fallbacks** – Ensures reliability when AI is unavailable

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.10+
- **Redis** (optional, for memory store)
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/RiteshKumar2e/customer-complaint-agent.git
cd customer-complaint-agent
```

#### 2. Backend Setup

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

# Initialize the database
python init_db.py

# Create .env file
echo "GEMINI_API_KEY=your_google_gemini_api_key" > .env
```

#### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

### Running the Application

#### Start Backend Server

```bash
cd backend

# Using the startup script
python start_backend.py

# Or manually with uvicorn
uvicorn app.main:app --reload
```

Backend will be available at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

#### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5174**

---

## 📡 API Documentation

### Submit Complaint

**Endpoint:** `POST /complaint`

**Request Body:**
```json
{
  "complaint": "My refund has been delayed for over 2 weeks"
}
```

**Response:**
```json
{
  "category": "Billing",
  "priority": "High",
  "sentiment": "Negative",
  "satisfaction_score": 0.35,
  "response": "We sincerely apologize for the delay in processing your refund. We understand how frustrating this must be. Our finance team has been notified and will prioritize your case immediately.",
  "action": "Escalate to finance team within 24 hours",
  "solution": "Initiate immediate refund processing and provide tracking number"
}
```

### Agent Chat

**Endpoint:** `POST /agent/chat`

**Query Parameters:**
- `message` (string, required) – User's question

**Example:**
```
POST /agent/chat?message=What%20does%20this%20website%20do
```

**Response:**
```json
{
  "response": "ComplaintAI is an intelligent customer complaint management system that uses AI to automatically categorize, prioritize, and draft responses to customer complaints. It helps businesses handle customer issues more efficiently."
}
```

---

## 🔄 Agent Workflow

ComplaintAI uses a **multi-stage agent pipeline** for intelligent complaint processing:

```
┌─────────────────────┐
│  Complaint Received │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Classify Category   │  ← Classifier Agent
│ (Billing, Support,  │
│  Technical, etc.)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Analyze Sentiment   │  ← Sentiment Analyzer
│ (Positive, Negative,│
│  Neutral)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Assign Priority     │  ← Priority Agent
│ (Low/Medium/High)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Match Similar       │  ← Complaint Matcher
│ Complaints          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Draft Response      │  ← Responder Agent
│ (Professional,      │
│  Empathetic)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Suggest Solutions   │  ← Solution Suggester
│ (Specific fixes,    │
│  workarounds)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Recommend Actions   │  ← Action Recommender
│ (Escalate, Refund,  │
│  Investigation)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Predict Satisfaction│  ← Satisfaction Predictor
│ (Expected outcome)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Re-evaluate Urgency │  ← Re-evaluator Agent
│ (Adjust priority if │
│  needed)            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Store in Database   │  ← SQLite Database
│ & Update Memory     │     Redis Store
│ (Track high-priority│
│  complaints)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Send Email          │  ← Email Service
│ Notifications       │     (User + Admin)
│ (Confirmation +     │
│  Alert)             │
└─────────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_google_gemini_api_key

# Email Configuration (Gmail)
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=your-gmail-app-password

# Database Configuration
DATABASE_URL=sqlite:///./complaints.db

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000

# CORS Settings (optional)
ALLOWED_ORIGINS=http://localhost:5174,http://localhost:3000
```

### Email Setup (Gmail)

ComplaintAI sends automated email notifications to users and admins. Follow these steps to configure:

#### 1. Enable Gmail 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **"2-Step Verification"** and enable it
3. Complete the verification process

#### 2. Generate Gmail App Password

1. Visit [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **App: Mail** and **Device: Windows Computer**
3. Copy the generated 16-character password (format: `xxxx xxxx xxxx xxxx`)

#### 3. Update .env File

```env
SENDER_EMAIL=your-actual-gmail@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
```

**Important:** Use the App Password, NOT your regular Gmail password!

#### Email Features

- **User Confirmation Email** - Sent immediately after complaint submission with AI analysis results
- **Admin Alert Email** - Notifies admin team about new high-priority complaints
- **Professional Templates** - HTML-formatted emails with branding and detailed information

#### Troubleshooting Emails

**"Username and Password not accepted"**
- Verify Gmail address is correct
- Generate a NEW app password from Google Account
- Use App Password, not regular password
- Restart backend server

**"2-Step Verification not enabled"**
- Enable 2FA in Google Account Security settings
- Then generate app password

**SMTP Connection Failed**
- Check internet connection
- Verify firewall settings
- Try using VPN if corporate network blocks SMTP

### Customization

Modify agent behavior in `backend/app/agents/`:
- **classifier.py** – Add new complaint categories
- **priority.py** – Adjust priority thresholds
- **sentiment_analyzer.py** – Customize sentiment detection
- **responder.py** – Customize response templates
- **solution_suggester.py** – Add domain-specific solutions
- **action_recommender.py** – Define action rules
- **satisfaction_predictor.py** – Adjust satisfaction metrics

### Database Management

```bash
# Initialize/reset database
python init_db.py

# Check database contents
python check_db.py
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Ritesh Kumar

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

---

---

## 📞 Contact

**Ritesh Kumar**

- 🌐 GitHub: [@RiteshKumar2e](https://github.com/RiteshKumar2e)
- 💼 LinkedIn: [Ritesh Kumar](https://www.linkedin.com/in/ritesh-kumar-b3a654253)
- 📧 Email: riteshkumar90359@gmail.com
- 📱 Phone: +91 6206269895

---

## ⭐ Show Your Support

If you find this project helpful, please consider giving it a star on GitHub! Your support helps others discover this tool.

[![GitHub stars](https://img.shields.io/github/stars/RiteshKumar2e/customer-complaint-agent?style=social)](https://github.com/RiteshKumar2e/customer-complaint-agent)

---

## 🙏 Acknowledgments

- Google Gemini team for the powerful AI API
- FastAPI community for excellent documentation
- React and Vite teams for modern development tools

---

**Made with ❤️ by Ritesh Kumar**
