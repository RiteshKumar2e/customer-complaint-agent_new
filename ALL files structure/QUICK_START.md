# 🚀 Quick Start Guide

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install/update dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 2. Frontend Setup

```bash
# In another terminal, navigate to frontend
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
VITE v7.2.5 ready in 123 ms

➜  Local:   http://localhost:5173/
```

### 3. Access the Application

Open your browser and go to: **http://localhost:5173**

## What You'll See

### Landing Page (Initially)
1. **Hero Section** - Professional headline with animated gradient
2. **6 Feature Cards** - Each showcasing an AI agent
3. **Stats Section** - Key metrics about the system
4. **Animated Background** - Floating gradient orbs

### After Clicking "Get Started"
1. **Complaint Form** - Text area to describe the issue
2. **AI Response** - Complete analysis with 8 outputs:
   - Category (Billing, Technical, Delivery, Service, Security)
   - Priority (High, Medium, Low)
   - Sentiment (Angry, Negative, Neutral, Positive)
   - Response (Recommended message for customer)
   - Solution (Intelligent solution)
   - Satisfaction (Predicted outcome: High/Medium/Low)
   - Action (Recommended next step)
   - Similar Issues (Related past complaints)

3. **Chat Bot** - Floating robot icon for additional questions

## Environment Variables

### Backend (.env file)
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/complaints_db
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Key Features

### 🎨 Professional UI/UX
- Smooth animations on page load
- Hover effects on all interactive elements
- Responsive design for mobile/tablet/desktop
- Dark theme with green accents
- Glassmorphic card design

### 🤖 6 AI Agents
1. **Classifier** - Categorizes complaints
2. **Priority Detector** - Assesses urgency
3. **Sentiment Analyzer** - Detects emotions
4. **Solution Suggester** - Generates solutions
5. **Satisfaction Predictor** - Predicts outcomes
6. **Complaint Matcher** - Finds patterns

### ⚙️ Backend Features
- Real-time AI processing
- Automatic database storage
- Error handling with fallbacks
- Multiple API endpoints
- Chat integration

## Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
rm -rf .pytest_cache

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Frontend Won't Start
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite

# Start fresh
npm run dev
```

### GEMINI API Errors
- Verify `GEMINI_API_KEY` is set in `.env`
- Check API quota and limits
- System will automatically fall back to rule-based responses if API fails

### Database Connection Errors
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` is correct
- Check credentials and database exists

## API Endpoints

### POST /complaint
Submit a complaint for AI analysis
```json
{
  "complaint": "I was charged twice for my order"
}
```

**Response:** (with all 8 AI agent outputs)
```json
{
  "category": "Billing",
  "priority": "High",
  "response": "...",
  "action": "Escalate to human support immediately",
  "sentiment": "Angry",
  "solution": "...",
  "satisfaction": "High",
  "similar_issues": "..."
}
```

### POST /agent/chat
Chat with AI about complaints
```json
{
  "message": "My delivery is late"
}
```

## Development Tips

### Add New Features
1. Backend agents: Create new file in `app/agents/`
2. Frontend components: Create new file in `src/components/`
3. Styling: Add CSS files in `src/styles/`
4. Update routers in `app/api/routes.py`

### Testing the API
```bash
# Using curl
curl -X POST http://localhost:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{"complaint": "Test complaint"}'

# Using Python
import requests
response = requests.post(
  "http://localhost:8000/complaint",
  json={"complaint": "Test complaint"}
)
print(response.json())
```

## Performance Tips

### Frontend
- Use browser DevTools to check animation performance
- Verify 60fps on animations (Performance tab)
- Check bundle size: `npm run build`

### Backend
- Monitor response times with print() statements
- Check database queries for slowness
- Verify Gemini API latency

## Next Steps

1. **Customize UI Colors** - Edit color variables in CSS files
2. **Add Database Persistence** - Implement storage for complaint history
3. **Deploy to Production** - Use Vercel (frontend) and Railway/Heroku (backend)
4. **Add User Authentication** - Implement login system
5. **Create Admin Dashboard** - View complaint analytics
6. **Add Email Notifications** - Notify customers of resolution

## Support

For issues or questions:
1. Check the error messages in console
2. Review the documentation files in the project root
3. Check backend logs in terminal
4. Verify all environment variables are set

## Success Indicators

✅ Landing page loads with smooth animations
✅ Can submit a complaint successfully
✅ AI response displays all 8 outputs
✅ Color-coded priority and sentiment visible
✅ Chat bot button appears and works
✅ Form validation prevents empty submissions
✅ All animations run at 60fps
✅ Responsive on mobile devices

Enjoy your AI-powered complaint resolution system! 🎉
