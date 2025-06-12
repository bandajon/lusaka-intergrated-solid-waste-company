# LISWMC Analytics Dashboard Deployment Guide

## 🚀 Deploy to Render.com (Recommended - FREE)

### Prerequisites
1. GitHub account
2. Render.com account (free)

### Step-by-Step Deployment

#### 1. **Prepare Repository**
```bash
# Navigate to analytics folder
cd /path/to/lusaka-intergrated-solid-waste-management-company/analytics

# Initialize git if not already done
git init
git add .
git commit -m "Add analytics dashboard for deployment"

# Push to GitHub (create repo first on GitHub)
git remote add origin https://github.com/yourusername/liswmc-analytics.git
git push -u origin main
```

#### 2. **Deploy on Render**
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Name**: `liswmc-analytics`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:server`

#### 3. **Set Environment Variables**
In Render dashboard, add these environment variables:
```
DB_HOST=agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com
DB_NAME=users
DB_USER=agripredict
DB_PASSWORD=Wee8fdm0k2!!
DB_PORT=5432
DEBUG=false
```

#### 4. **Deploy**
- Click "Create Web Service"
- Render will automatically build and deploy
- Get your URL: `https://liswmc-analytics.onrender.com`

### 🔄 **Auto-Deployment**
- Every `git push` to main branch automatically redeploys
- No manual intervention needed

---

## 🌐 Alternative Deployment Options

### **Railway.app** ($5/month)
1. Connect GitHub repo
2. Add environment variables
3. Deploy with one click

### **Google Cloud Run** (Pay-per-use)
```bash
# Build Docker image
docker build -t liswmc-analytics .

# Deploy to Cloud Run
gcloud run deploy --image gcr.io/PROJECT-ID/liswmc-analytics
```

### **DigitalOcean App Platform** ($5/month)
1. Connect GitHub repo
2. Configure build settings
3. Deploy

---

## 📋 **Production Checklist**

- ✅ Environment variables configured
- ✅ Database connection secured
- ✅ Auto-refresh working
- ✅ Filter preservation enabled
- ✅ Auto-close sessions functional
- ✅ HTTPS enabled (automatic on Render)

---

## 🔧 **Local Testing Before Deployment**

```bash
# Test production setup locally
export DB_HOST=your-db-host
export DB_NAME=your-db-name
export DB_USER=your-db-user
export DB_PASSWORD=your-db-password
export PORT=8050

# Run with gunicorn (production server)
gunicorn --bind 0.0.0.0:8050 wsgi:server

# Access at http://localhost:8050
```

---

## 🎯 **Recommended: Start with Render**

**Why Render?**
- ✅ **FREE** 750 hours/month
- ✅ Automatic HTTPS
- ✅ Auto-deployment from GitHub
- ✅ Built-in database support
- ✅ Easy environment variable management
- ✅ No credit card required for free tier

**Free Tier Limits:**
- 750 hours/month (enough for 24/7 operation)
- Sleeps after 15 minutes of inactivity
- Wakes up automatically on first request

Perfect for your waste collection analytics dashboard!