# ⚡ Quick Reference Guide

Fast reference for common tasks and commands in the Quickfix project.

---

## 🚀 Quick Start Commands

### Backend
```bash
# Setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py

# Run
python start_backend.py
# OR
uvicorn app.main:app --reload

# Test
pytest
pytest --cov=app

# Database
python check_db.py
python migrate_db.py
```

### Frontend
```bash
# Setup
cd frontend
npm install

# Run
npm run dev

# Build
npm run build

# Preview
npm run preview

# Lint
npm run lint
```

---

## 📡 API Endpoints

### Authentication
```http
POST   /auth/register              # Register new user
POST   /auth/login                 # Login with email/password
POST   /auth/google                # Google OAuth login
POST   /auth/google-verify-otp     # Verify OTP
POST   /auth/forgot-password        # Request password reset
POST   /auth/reset-password         # Reset password
GET    /auth/me                     # Get current user
```

### Complaints
```http
POST   /complaint                   # Submit complaint
GET    /complaints/user/{user_id}   # Get user complaints
GET    /complaint/{id}              # Get complaint by ID
PUT    /complaint/{id}              # Update complaint
DELETE /complaint/{id}              # Delete complaint
```

### Chat
```http
POST   /agent/chat?message=...      # Chat with AI assistant
```

### Feedback
```http
POST   /feedback/submit             # Submit user feedback
GET    /feedback/user/{user_id}     # Get user feedback
```

---

## 🔑 Environment Variables

### Backend (.env)
```env
# Required
GEMINI_API_KEY=your_key
DATABASE_URL=postgresql://user:pass@host/db
BREVO_API_KEY=your_key
SENDER_EMAIL=email@domain.com
ADMIN_EMAIL=admin@domain.com
SECRET_KEY=your-secret-key-32-chars-min

# Optional
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
HOST=0.0.0.0
PORT=10000
GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_id
```

---

## 🗄️ Database Commands

### PostgreSQL
```bash
# Connect
psql -U postgres

# Create database
CREATE DATABASE quickfix;

# List databases
\l

# Connect to database
\c quickfix

# List tables
\dt

# Describe table
\d users

# Query
SELECT * FROM users;

# Exit
\q
```

### SQLAlchemy (Python)
```python
from app.db.database import SessionLocal, engine
from app.db import models

# Create tables
models.Base.metadata.create_all(bind=engine)

# Get session
db = SessionLocal()

# Query
users = db.query(models.User).all()

# Create
user = models.User(email="test@test.com", full_name="Test User")
db.add(user)
db.commit()

# Update
user.full_name = "Updated Name"
db.commit()

# Delete
db.delete(user)
db.commit()

# Close
db.close()
```

---

## 🐛 Debugging

### Backend Logs
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Frontend Console
```javascript
console.log("Debug:", data);
console.error("Error:", error);
console.table(array);
console.time("Timer");
// ... code ...
console.timeEnd("Timer");
```

### Network Debugging
```bash
# Check backend health
curl http://localhost:8000/

# Test API endpoint
curl -X POST http://localhost:8000/complaint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"complaint": "Test", "user_id": 1}'

# Check CORS
curl -H "Origin: http://localhost:5174" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/complaint
```

---

## 🔧 Common Issues & Fixes

### Issue: "Module not found"
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### Issue: "Database connection failed"
```bash
# Check DATABASE_URL format
# Should be: postgresql://user:pass@host:port/db

# Test connection
psql $DATABASE_URL
```

### Issue: "CORS error"
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Port already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Issue: "Email not sending"
```bash
# Check environment variables
echo $BREVO_API_KEY
echo $SENDER_EMAIL

# Verify sender email in Brevo dashboard
# Check Brevo API logs
```

---

## 📦 Package Management

### Python
```bash
# Install package
pip install package-name

# Install specific version
pip install package-name==1.0.0

# Update package
pip install --upgrade package-name

# Uninstall package
pip uninstall package-name

# List installed
pip list

# Freeze requirements
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

### Node.js
```bash
# Install package
npm install package-name

# Install dev dependency
npm install --save-dev package-name

# Install specific version
npm install package-name@1.0.0

# Update package
npm update package-name

# Uninstall package
npm uninstall package-name

# List installed
npm list

# Check outdated
npm outdated

# Update all
npm update
```

---

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_classifier

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Frontend Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test -- ComplaintForm.test.jsx

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Update snapshots
npm test -- -u
```

---

## 🚀 Deployment

### Vercel (Frontend)
```bash
# Install CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod

# Set environment variable
vercel env add VITE_API_URL production
```

### Render (Backend)
```bash
# Push to GitHub
git add .
git commit -m "Deploy to production"
git push origin main

# Render auto-deploys on push
# Check logs in Render dashboard
```

### Docker
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and run
docker-compose up -d --build
```

---

## 🔐 Security

### Generate Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Hash Password
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("password123")
print(hashed)
```

### Verify Password
```python
is_valid = pwd_context.verify("password123", hashed)
print(is_valid)
```

### Generate JWT Token
```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

data = {"sub": "user@example.com"}
expires = datetime.utcnow() + timedelta(days=7)
token = jwt.encode({**data, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)
print(token)
```

---

## 📊 Monitoring

### Check Backend Health
```bash
curl http://localhost:8000/
# Should return: {"status": "Quickfix Backend Running"}
```

### Check Database
```bash
python backend/check_db.py
```

### Check Frontend Build
```bash
cd frontend
npm run build
# Check dist/ folder
```

### Performance Testing
```bash
# Install Apache Bench
# Windows: Download from Apache website
# Linux: apt-get install apache2-utils
# Mac: brew install ab

# Test API endpoint
ab -n 1000 -c 10 http://localhost:8000/
```

---

## 🎨 Code Formatting

### Python (Black)
```bash
# Format all files
black .

# Check without formatting
black --check .

# Format specific file
black backend/app/main.py
```

### JavaScript (Prettier)
```bash
# Install
npm install --save-dev prettier

# Format all files
npx prettier --write .

# Check without formatting
npx prettier --check .

# Format specific file
npx prettier --write src/App.jsx
```

---

## 📝 Git Commands

### Common Workflow
```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "feat: add new feature"

# Push
git push origin main

# Pull
git pull origin main

# Create branch
git checkout -b feature/new-feature

# Switch branch
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### Undo Changes
```bash
# Discard changes in file
git checkout -- file.js

# Unstage file
git reset HEAD file.js

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

---

## 🔍 Useful Links

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Google Gemini Docs](https://ai.google.dev/docs)

### Tools
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Render Dashboard](https://dashboard.render.com/)
- [Brevo Dashboard](https://app.brevo.com/)
- [Google Cloud Console](https://console.cloud.google.com/)

### Resources
- [GitHub Repo](https://github.com/RiteshKumar2e/customer-complaint-agent_new)
- [Live Demo](https://customer-complaint-agent-new.vercel.app)
- [API Docs](http://localhost:8000/docs)

---

## 💡 Tips & Tricks

### Backend
```python
# Use type hints
def process_complaint(text: str) -> dict:
    pass

# Use async/await for I/O operations
async def get_user(user_id: int):
    return await db.query(User).filter(User.id == user_id).first()

# Use dependency injection
from fastapi import Depends
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use Pydantic for validation
from pydantic import BaseModel, EmailStr
class UserCreate(BaseModel):
    email: EmailStr
    password: str
```

### Frontend
```javascript
// Use hooks
const [state, setState] = useState(initialState);
useEffect(() => {
  // Side effects
}, [dependencies]);

// Use async/await
const fetchData = async () => {
  try {
    const response = await api.get('/endpoint');
    setData(response.data);
  } catch (error) {
    console.error(error);
  }
};

// Use destructuring
const { name, email } = user;

// Use template literals
const message = `Hello, ${name}!`;

// Use optional chaining
const value = user?.profile?.avatar;
```

---

## 📞 Support

- 📧 Email: riteshkumar90359@gmail.com
- 💬 GitHub: [@RiteshKumar2e](https://github.com/RiteshKumar2e)
- 📱 Phone: +91 6206269895

---

**Last Updated**: December 25, 2025
