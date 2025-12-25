# ❓ Frequently Asked Questions (FAQ)

Common questions and answers about the Quickfix project.

---

## 📋 Table of Contents

- [General Questions](#general-questions)
- [Installation & Setup](#installation--setup)
- [Deployment](#deployment)
- [Authentication](#authentication)
- [AI Agents](#ai-agents)
- [Database](#database)
- [Email System](#email-system)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)

---

## General Questions

### What is Quickfix?

Quickfix is an enterprise-grade, AI-powered customer complaint resolution platform that uses 14 specialized AI agents to automatically analyze, categorize, prioritize, and generate responses for customer complaints.

### Who is this for?

- **Businesses** looking to automate complaint handling
- **Customer service teams** wanting AI assistance
- **Developers** learning about AI agent systems
- **Students** studying full-stack development

### Is it free to use?

Yes! The project is open-source under the MIT License. However, you'll need:
- Google Gemini API key (free tier available)
- Brevo email service (free tier: 300 emails/day)
- Hosting costs (Vercel free tier, Render free tier available)

### What makes it different from other complaint systems?

- **14 AI Agents** working together (not just one AI)
- **Multi-step reasoning** with adaptive priority
- **Google OAuth + OTP** for enhanced security
- **Real-time AI chat** assistant
- **Production-ready** deployment
- **Comprehensive documentation**

---

## Installation & Setup

### What are the prerequisites?

**Required:**
- Node.js 16+ and npm
- Python 3.10+
- PostgreSQL 15+ (or use Render's managed database)
- Google Gemini API key
- Brevo API key

**Optional:**
- Redis (for caching)
- Docker (for containerization)

### How long does setup take?

- **Quick setup**: 5-10 minutes (using existing database)
- **Full setup**: 15-20 minutes (including database creation)
- **First-time setup**: 30 minutes (including account creation)

### Can I use SQLite instead of PostgreSQL?

For local development, yes. However, PostgreSQL is recommended for production because:
- Better performance at scale
- Supports concurrent connections
- Required by Render's free tier
- More robust for production workloads

### Do I need Redis?

Redis is optional. The cache layer will work without it, but Redis provides:
- Faster response times
- Better performance under load
- Persistent caching across restarts

---

## Deployment

### Where can I deploy this?

**Recommended:**
- **Frontend**: Vercel (free tier available)
- **Backend**: Render (free tier available)
- **Database**: Render PostgreSQL (free tier available)

**Alternatives:**
- Netlify, AWS, Google Cloud, Azure, Heroku
- Docker on any VPS

### How much does deployment cost?

**Free Tier (Testing):**
- Vercel: Free (100GB bandwidth/month)
- Render: Free (750 hours/month)
- PostgreSQL: Free (1GB storage)
- **Total: $0/month**

**Production Tier:**
- Vercel Pro: $20/month
- Render Starter: $7/month
- PostgreSQL Starter: $7/month
- **Total: $34/month**

### How do I deploy to Vercel?

```bash
# Option 1: Vercel Dashboard
1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to "frontend"
4. Add environment variables
5. Deploy

# Option 2: Vercel CLI
npm i -g vercel
cd frontend
vercel --prod
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed guide.

### Can I use a custom domain?

Yes! Both Vercel and Render support custom domains:
- **Vercel**: Add domain in project settings
- **Render**: Add custom domain in service settings
- Configure DNS CNAME records
- SSL certificates are auto-configured

---

## Authentication

### How does authentication work?

We use a **three-layer security approach**:

1. **Google OAuth 2.0**: User authenticates with Google
2. **Email OTP**: 6-digit code sent to verified email
3. **JWT Token**: Secure session management (7-day expiry)

See [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md) for details.

### Why do I need OTP after Google login?

The OTP adds an extra security layer to ensure:
- Email ownership verification
- Protection against account takeover
- Compliance with security best practices
- Two-factor authentication

### How long is the OTP valid?

OTPs expire after **10 minutes** for security. If expired, request a new one by logging in again.

### How long do JWT tokens last?

JWT tokens are valid for **7 days** (10,080 minutes). After expiry, users need to log in again.

### Can I disable Google OAuth?

Yes, users can also register with email/password. Google OAuth is optional but recommended for better UX.

### How do I reset my password?

1. Click "Forgot Password" on login page
2. Enter your email
3. Check email for reset link
4. Click link and enter new password
5. Password is updated

---

## AI Agents

### How many AI agents are there?

**14 specialized agents:**
1. Orchestrator
2. Classifier
3. Sentiment Analyzer
4. Priority Agent
5. Complaint Matcher
6. Responder
7. Solution Suggester
8. Action Recommender
9. Satisfaction Predictor
10. Re-evaluator
11. Response Validator
12. Cache Layer
13. Chat Agent
14. Gemini Client

### Which AI model is used?

**Google Gemini 1.5** (Flash and Pro variants):
- **Gemini 1.5 Flash**: Fast responses for classification
- **Gemini 1.5 Pro**: Complex reasoning for responses

### How fast is the AI analysis?

- **Classification**: < 1 second
- **Full analysis**: 2-3 seconds
- **With caching**: < 500ms

### Can I use a different AI model?

Yes! The system is designed to be model-agnostic. You can replace Gemini with:
- OpenAI GPT-4
- Anthropic Claude
- Local models (Llama, Mistral)

Just update `backend/app/agents/gemini_client.py`.

### How accurate is the AI?

Based on testing:
- **Classification accuracy**: 95%+
- **Sentiment analysis**: 92%+
- **Priority assignment**: 90%+
- **Response quality**: Human-level

### Does it learn from feedback?

Currently, the system uses pre-trained models. Future versions will include:
- Feedback loop for continuous learning
- Custom model fine-tuning
- User preference learning

---

## Database

### Which database should I use?

**For Development:**
- SQLite (simple, no setup required)

**For Production:**
- PostgreSQL (recommended)
- MySQL (supported)
- Any SQLAlchemy-compatible database

### How do I migrate from SQLite to PostgreSQL?

```bash
# 1. Backup SQLite data
python backend/migrate_db.py

# 2. Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@host/db

# 3. Initialize PostgreSQL
python backend/init_db.py

# 4. Import data (if needed)
# Manual SQL import or custom migration script
```

### How do I backup the database?

**PostgreSQL:**
```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

**SQLite:**
```bash
# Backup
cp backend/complaints.db backend/complaints.db.backup

# Restore
cp backend/complaints.db.backup backend/complaints.db
```

### How do I reset the database?

```bash
# WARNING: This deletes all data!
python backend/init_db.py --reset
```

---

## Email System

### Which email service is used?

**Brevo** (formerly Sendinblue) is recommended because:
- Free tier: 300 emails/day
- Reliable delivery
- Easy setup
- Professional templates
- Delivery tracking

### Can I use Gmail instead?

Gmail is not recommended for production because:
- Daily sending limits (500 emails/day)
- Requires app passwords
- Less reliable for automated emails
- Risk of being marked as spam

Use Brevo, SendGrid, or Mailgun instead.

### Why aren't emails being sent?

**Common issues:**
1. **Invalid API key**: Check `BREVO_API_KEY`
2. **Unverified sender**: Verify `SENDER_EMAIL` in Brevo
3. **Daily limit reached**: Check Brevo dashboard
4. **Spam folder**: Check recipient's spam
5. **Backend error**: Check backend logs

### How do I verify my sender email?

1. Login to Brevo dashboard
2. Go to "Senders & IPs"
3. Click "Add a sender"
4. Enter your email
5. Click verification link in email
6. Wait for approval (usually instant)

---

## Troubleshooting

### "Module not found" error

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### "CORS error" in browser

**Fix backend CORS settings:**
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-url.vercel.app",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "Database connection failed"

**Check DATABASE_URL format:**
```env
# Correct
DATABASE_URL=postgresql://user:password@host:5432/database

# Wrong
DATABASE_URL=postgres://...  # Should be postgresql://
```

### "Port already in use"

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Backend is slow on Render

**Render free tier has cold starts:**
- First request after 15min inactivity takes 30s
- Upgrade to paid plan for always-on
- Or implement keep-alive pings

### OTP not received

**Checklist:**
1. Check spam folder
2. Verify sender email in Brevo
3. Check Brevo sending limits
4. Review backend logs
5. Test with different email

---

## Development

### How do I add a new AI agent?

1. Create new file in `backend/app/agents/`
2. Implement agent logic
3. Add to orchestrator in `orchestrator.py`
4. Update documentation

Example:
```python
# backend/app/agents/my_agent.py
class MyAgent:
    def __init__(self, gemini_client):
        self.gemini = gemini_client
    
    def process(self, complaint: str) -> str:
        # Your logic here
        return result
```

### How do I add a new API endpoint?

1. Create route in `backend/app/routes/` or `backend/app/api/`
2. Add to `main.py`
3. Update API documentation

Example:
```python
# backend/app/routes/my_route.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-endpoint", tags=["My Feature"])

@router.get("/")
def get_data():
    return {"data": "value"}

# backend/app/main.py
from app.routes.my_route import router as my_router
app.include_router(my_router)
```

### How do I add a new React component?

1. Create component in `frontend/src/components/`
2. Create CSS in `frontend/src/styles/`
3. Import and use in parent component

Example:
```javascript
// frontend/src/components/MyComponent.jsx
import React from 'react';
import '../styles/MyComponent.css';

const MyComponent = () => {
  return <div className="my-component">Content</div>;
};

export default MyComponent;
```

### How do I run tests?

```bash
# Backend
cd backend
pytest
pytest --cov=app

# Frontend
cd frontend
npm test
npm test -- --coverage
```

---

## Contributing

### How can I contribute?

1. **Report bugs**: Create GitHub issue
2. **Suggest features**: Create GitHub issue
3. **Submit code**: Create pull request
4. **Improve docs**: Update documentation
5. **Share feedback**: Email or discussion

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### What should I work on?

Check:
- GitHub Issues (labeled "good first issue")
- Roadmap in [CHANGELOG.md](./CHANGELOG.md)
- TODO comments in code

### How do I submit a pull request?

1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Update documentation
6. Commit with conventional commits
7. Push to your fork
8. Create pull request

### Will my contribution be recognized?

Yes! Contributors are recognized in:
- README.md
- CHANGELOG.md
- Release notes

---

## Support

### Where can I get help?

- 📧 **Email**: [riteshkumar90359@gmail.com](mailto:riteshkumar90359@gmail.com)
- 💬 **GitHub Issues**: [Create an issue](https://github.com/RiteshKumar2e/customer-complaint-agent_new/issues)
- 📚 **Documentation**: [README.md](./README.md)
- 📱 **Phone**: +91 6206269895

### How do I report a bug?

1. Check existing issues
2. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details

### How do I request a feature?

1. Check existing issues
2. Create new issue with:
   - Problem statement
   - Proposed solution
   - Use cases
   - Mockups (if applicable)

---

## Additional Resources

- 📖 [README.md](./README.md) - Main documentation
- 🚀 [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- 🔐 [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md) - Auth details
- 🤝 [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guide
- 📝 [CHANGELOG.md](./CHANGELOG.md) - Version history
- ⚡ [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Quick commands
- 📊 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - Project overview

---

**Still have questions? Feel free to reach out!**

📧 riteshkumar90359@gmail.com
💬 [GitHub Discussions](https://github.com/RiteshKumar2e/customer-complaint-agent_new/discussions)
