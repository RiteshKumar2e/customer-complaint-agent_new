# 🚀 Vercel Deployment Guide

Complete guide for deploying the Quickfix application on Vercel (Frontend) and Render (Backend).

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Environment Variables](#environment-variables)
- [Custom Domain Setup](#custom-domain-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- ✅ GitHub account
- ✅ Vercel account ([Sign up](https://vercel.com/signup))
- ✅ Render account ([Sign up](https://render.com/register))
- ✅ Google Gemini API key ([Get one](https://makersuite.google.com/app/apikey))
- ✅ Brevo API key ([Sign up](https://www.brevo.com/))
- ✅ Code pushed to GitHub repository

---

## Backend Deployment (Render)

### Step 1: Create PostgreSQL Database

1. **Login to Render Dashboard**
   - Go to [https://dashboard.render.com](https://dashboard.render.com)

2. **Create New PostgreSQL Database**
   - Click **New +** → **PostgreSQL**
   - Fill in details:
     - **Name**: `quickfix-db`
     - **Database**: `quickfix`
     - **User**: `quickfix_user`
     - **Region**: Choose closest to your users (e.g., Oregon, Frankfurt)
     - **PostgreSQL Version**: 15
     - **Plan**: Free (for testing) or Starter (for production)

3. **Create Database**
   - Click **Create Database**
   - Wait for provisioning (1-2 minutes)

4. **Copy Database URL**
   - Go to database dashboard
   - Copy **Internal Database URL**
   - Format: `postgresql://user:password@host/database`
   - Save this for later

### Step 2: Create Web Service

1. **Create New Web Service**
   - Click **New +** → **Web Service**

2. **Connect Repository**
   - Click **Connect GitHub**
   - Select your repository: `customer-complaint-agent_new`
   - Click **Connect**

3. **Configure Service**
   - **Name**: `quickfix-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_backend.py`

4. **Select Plan**
   - **Free** (for testing) or **Starter** (for production)
   - Click **Create Web Service**

### Step 3: Configure Environment Variables

In the Render dashboard, go to **Environment** tab and add:

```env
# Google Gemini AI
GEMINI_API_KEY=your_google_gemini_api_key_here

# Database (Use Internal Database URL from Step 1)
DATABASE_URL=postgresql://quickfix_user:password@host/quickfix

# Email Service (Brevo)
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=your-verified-sender@domain.com
ADMIN_EMAIL=admin@yourdomain.com

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Server Configuration
HOST=0.0.0.0
PORT=10000

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**Important Notes:**
- Replace all placeholder values with your actual credentials
- `SECRET_KEY` should be at least 32 characters long
- `SENDER_EMAIL` must be verified in Brevo
- Save changes after adding all variables

### Step 4: Deploy

1. **Trigger Deployment**
   - Click **Manual Deploy** → **Deploy latest commit**
   - Or push to GitHub (auto-deploy if enabled)

2. **Monitor Deployment**
   - Watch the build logs
   - Wait for "Live" status (3-5 minutes)

3. **Get Backend URL**
   - Copy your backend URL: `https://quickfix-backend.onrender.com`
   - Test it: `https://quickfix-backend.onrender.com/` should return `{"status": "Quickfix Backend Running"}`

---

## Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

1. **Update API URL**
   
   Edit `frontend/src/api.js`:
   ```javascript
   const API_URL = 'https://quickfix-backend.onrender.com';
   ```

2. **Commit Changes**
   ```bash
   git add frontend/src/api.js
   git commit -m "🚀 Update API URL for production"
   git push origin main
   ```

### Step 2: Deploy to Vercel

#### Option A: Vercel Dashboard (Recommended)

1. **Login to Vercel**
   - Go to [https://vercel.com/login](https://vercel.com/login)
   - Sign in with GitHub

2. **Import Project**
   - Click **Add New...** → **Project**
   - Select your repository: `customer-complaint-agent_new`
   - Click **Import**

3. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

4. **Environment Variables**
   
   Add these variables:
   ```env
   VITE_API_URL=https://quickfix-backend.onrender.com
   VITE_GOOGLE_CLIENT_ID=your_google_client_id
   ```

5. **Deploy**
   - Click **Deploy**
   - Wait for deployment (1-2 minutes)
   - Get your URL: `https://customer-complaint-agent-new.vercel.app`

#### Option B: Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   cd frontend
   vercel --prod
   ```

4. **Follow Prompts**
   - Set up and deploy: **Y**
   - Scope: Select your account
   - Link to existing project: **N**
   - Project name: `customer-complaint-agent-new`
   - Directory: `./`
   - Override settings: **N**

### Step 3: Update Backend CORS

1. **Update Backend CORS Settings**
   
   Edit `backend/app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://customer-complaint-agent-new.vercel.app",  # Your Vercel URL
           "http://localhost:5173",
           "http://localhost:5174",
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Commit and Push**
   ```bash
   git add backend/app/main.py
   git commit -m "🔧 Update CORS for Vercel deployment"
   git push origin main
   ```

3. **Render Auto-Deploy**
   - Render will automatically redeploy
   - Wait for deployment to complete

### Step 4: Test Deployment

1. **Open Frontend**
   - Visit: `https://customer-complaint-agent-new.vercel.app`

2. **Test Features**
   - ✅ Landing page loads
   - ✅ Login/Signup works
   - ✅ Google OAuth works
   - ✅ OTP verification works
   - ✅ Complaint submission works
   - ✅ Dashboard displays data
   - ✅ Chat assistant responds

3. **Check Browser Console**
   - No CORS errors
   - No 404 errors
   - API calls successful

---

## Environment Variables

### Backend (Render)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key | `AIzaSy...` |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `BREVO_API_KEY` | ✅ Yes | Brevo email service API key | `xkeysib-...` |
| `SENDER_EMAIL` | ✅ Yes | Verified sender email | `noreply@yourdomain.com` |
| `ADMIN_EMAIL` | ✅ Yes | Admin notification email | `admin@yourdomain.com` |
| `SECRET_KEY` | ✅ Yes | JWT secret key (32+ chars) | `super-secret-key-change-this` |
| `ALGORITHM` | ✅ Yes | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ Yes | Token expiry (7 days = 10080) | `10080` |
| `HOST` | ✅ Yes | Server host | `0.0.0.0` |
| `PORT` | ✅ Yes | Server port | `10000` |
| `GOOGLE_CLIENT_ID` | ❌ No | Google OAuth client ID | `123456789...` |
| `GOOGLE_CLIENT_SECRET` | ❌ No | Google OAuth client secret | `GOCSPX-...` |

### Frontend (Vercel)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✅ Yes | Backend API URL | `https://quickfix-backend.onrender.com` |
| `VITE_GOOGLE_CLIENT_ID` | ❌ No | Google OAuth client ID | `123456789...` |

---

## Custom Domain Setup

### Vercel (Frontend)

1. **Add Domain**
   - Go to project settings
   - Click **Domains**
   - Add your domain: `quickfix.yourdomain.com`

2. **Configure DNS**
   - Add CNAME record:
     - **Name**: `quickfix`
     - **Value**: `cname.vercel-dns.com`

3. **Wait for Verification**
   - Usually takes 5-10 minutes
   - Vercel auto-configures SSL

### Render (Backend)

1. **Add Custom Domain**
   - Go to service settings
   - Click **Custom Domains**
   - Add: `api.yourdomain.com`

2. **Configure DNS**
   - Add CNAME record:
     - **Name**: `api`
     - **Value**: Provided by Render

3. **Update Frontend**
   - Update `VITE_API_URL` in Vercel
   - Redeploy frontend

---

## Troubleshooting

### Backend Issues

#### ❌ "Application failed to start"

**Solution:**
```bash
# Check Render logs
# Ensure all environment variables are set
# Verify DATABASE_URL format
# Check requirements.txt is complete
```

#### ❌ "Database connection failed"

**Solution:**
```bash
# Use Internal Database URL (not External)
# Format: postgresql://user:pass@host/db
# Ensure database is in same region
# Check database is running
```

#### ❌ "Email sending failed"

**Solution:**
```bash
# Verify BREVO_API_KEY is correct
# Ensure SENDER_EMAIL is verified in Brevo
# Check Brevo account is active
# Review Brevo logs
```

### Frontend Issues

#### ❌ "CORS error"

**Solution:**
```javascript
// Update backend/app/main.py
allow_origins=[
    "https://your-vercel-url.vercel.app",
    "http://localhost:5173",
]
// Commit and push to trigger redeploy
```

#### ❌ "API calls failing"

**Solution:**
```javascript
// Check VITE_API_URL in Vercel environment variables
// Ensure backend is running
// Test backend URL directly
// Check browser console for errors
```

#### ❌ "Build failed"

**Solution:**
```bash
# Check build logs in Vercel
# Ensure all dependencies in package.json
# Test build locally: npm run build
# Check for TypeScript/ESLint errors
```

### Common Issues

#### ❌ "Google OAuth not working"

**Solution:**
```bash
# Add Vercel URL to Google Cloud Console
# Authorized JavaScript origins: https://your-app.vercel.app
# Authorized redirect URIs: https://your-app.vercel.app
# Update VITE_GOOGLE_CLIENT_ID
```

#### ❌ "OTP not received"

**Solution:**
```bash
# Check spam folder
# Verify SENDER_EMAIL in Brevo
# Check Brevo sending limits
# Review backend logs for email errors
```

#### ❌ "Slow backend response"

**Solution:**
```bash
# Render free tier has cold starts (30s)
# Upgrade to paid plan for always-on
# Implement Redis caching
# Optimize database queries
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code tested locally
- [ ] All environment variables documented
- [ ] Database migrations ready
- [ ] API endpoints tested
- [ ] CORS configured correctly
- [ ] Error handling implemented
- [ ] Logging configured

### Backend Deployment

- [ ] PostgreSQL database created
- [ ] Environment variables set
- [ ] Build command configured
- [ ] Start command configured
- [ ] Deployment successful
- [ ] Health check passing
- [ ] Database connected
- [ ] Email service working

### Frontend Deployment

- [ ] API URL updated
- [ ] Environment variables set
- [ ] Build successful
- [ ] Deployment successful
- [ ] CORS working
- [ ] Google OAuth working
- [ ] All features tested

### Post-Deployment

- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring setup
- [ ] Error tracking configured
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Team notified

---

## Monitoring & Maintenance

### Render Monitoring

- **Logs**: View real-time logs in dashboard
- **Metrics**: CPU, memory, response time
- **Alerts**: Set up email/Slack alerts
- **Health Checks**: Auto-configured

### Vercel Monitoring

- **Analytics**: Built-in analytics
- **Logs**: Function logs and build logs
- **Performance**: Core Web Vitals
- **Errors**: Error tracking

### Recommended Tools

- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Uptime Robot**: Uptime monitoring
- **Google Analytics**: User analytics

---

## Scaling

### Backend Scaling (Render)

1. **Vertical Scaling**
   - Upgrade to larger instance
   - More CPU/RAM

2. **Horizontal Scaling**
   - Add more instances
   - Load balancer (paid plans)

3. **Database Scaling**
   - Upgrade database plan
   - Connection pooling
   - Read replicas

### Frontend Scaling (Vercel)

- **Automatic**: Vercel auto-scales
- **CDN**: Global edge network
- **Caching**: Automatic caching
- **Serverless**: Infinite scalability

---

## Cost Estimation

### Free Tier (Testing)

| Service | Plan | Cost | Limits |
|---------|------|------|--------|
| Vercel | Hobby | $0 | 100GB bandwidth/month |
| Render | Free | $0 | 750 hours/month, sleeps after 15min |
| PostgreSQL | Free | $0 | 1GB storage, 97 connection hours/month |
| **Total** | | **$0/month** | |

### Production Tier

| Service | Plan | Cost | Features |
|---------|------|------|----------|
| Vercel | Pro | $20/month | Unlimited bandwidth, analytics |
| Render | Starter | $7/month | Always-on, 512MB RAM |
| PostgreSQL | Starter | $7/month | 10GB storage, always-on |
| **Total** | | **$34/month** | |

---

## Support

- 📧 **Email**: [riteshkumar90359@gmail.com](mailto:riteshkumar90359@gmail.com)
- 💬 **GitHub Issues**: [Report an issue](https://github.com/RiteshKumar2e/customer-complaint-agent_new/issues)
- 📚 **Documentation**: [README.md](./README.md)

---

**Happy Deploying! 🚀**
