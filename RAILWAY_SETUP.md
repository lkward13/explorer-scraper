# Railway.app Setup Guide for Explorer Scraper

Railway is the easiest deployment option - just push your code and it runs automatically.

## Step 1: Prepare Your Code for Railway

First, let's create the necessary Railway configuration files.

### 1. Create `railway.toml` (Railway config)

Already done! This tells Railway how to run your app.

### 2. Create `Procfile` (tells Railway what commands to run)

Already done! This defines your cron job.

### 3. Update `.gitignore` (if you don't have one)

Make sure you're not committing unnecessary files.

## Step 2: Push Your Code to GitHub

Railway deploys from GitHub, so we need your code there first.

```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for Railway deployment"

# Create a new PRIVATE repo on GitHub at: https://github.com/new
# Name it: explorer-scraper
# Keep it PRIVATE (important - has your scraping logic)

# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/explorer-scraper.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Railway

1. **Go to Railway dashboard**: https://railway.app/dashboard (you're already there!)

2. **Click "New Project"**

3. **Select "Deploy from GitHub repo"**

4. **Connect GitHub** (if not already connected):
   - Click "Configure GitHub App"
   - Select your repositories
   - Give Railway access to `explorer-scraper` repo

5. **Select your `explorer-scraper` repository**

6. **Railway will automatically**:
   - Detect it's a Python project
   - Install dependencies from `requirements.txt`
   - Install Playwright browsers
   - Start building

## Step 4: Configure Environment (if needed)

Railway should auto-detect everything, but if you need to set variables:

1. Click on your deployed service
2. Go to "Variables" tab
3. Add any environment variables (none needed for now)

## Step 5: Set Up the Cron Job

Railway doesn't have built-in cron, so we have two options:

### Option A: Use Railway Cron (Recommended)

1. In your Railway project, click **"New"** → **"Cron Job"**
2. Set schedule: `0 6 * * *` (daily at 6 AM UTC)
3. Set command: `python worker/run_daily.py`
4. Click "Deploy"

### Option B: Use External Cron Service (Free alternative)

Use **cron-job.org** to ping a Railway endpoint:

1. Create a new service in Railway that runs: `python worker/run_daily.py`
2. Expose it via Railway's generated URL
3. Set up cron-job.org to hit that URL daily

## Step 6: Monitor Your Deployment

1. **View Logs**:
   - Click on your service in Railway
   - Click "Deployments"
   - Click the latest deployment
   - See real-time logs

2. **Check Build Status**:
   - Green checkmark = Success
   - Red X = Failed (click to see error logs)

## Step 7: Test Your Deployment

Once deployed, Railway will show you the logs. You should see:

```
Installing Playwright browsers...
✓ Chromium installed
Running test...
```

To manually trigger a test:

1. Go to your service settings
2. Click "Deploy" → "Redeploy"
3. Or push a new commit to GitHub (auto-deploys)

## Troubleshooting

### Build fails with "Playwright not found"

Railway should auto-install Playwright browsers. If not, add this to your deployment:

1. Go to Settings → Start Command
2. Set to: `playwright install chromium && python worker/test_parallel.py --phase 1`

### Out of memory errors

Railway free tier has limited RAM. Upgrade to:
- **Developer Plan**: $5/month (512MB RAM) - too small
- **Hobby Plan**: $20/month (8GB RAM) - perfect for your needs

### Builds are slow

First build takes 5-10 minutes (installing Chromium). Subsequent builds are faster (cached).

## Railway Pricing

**Free Trial**: 
- Ended (as shown in your dashboard)
- Need to upgrade to continue

**Hobby Plan** ($20/month):
- 8GB RAM
- 8 vCPU
- $5 included credits/month
- Suitable for your scraper

**Pro Plan** ($50/month):
- 32GB RAM
- 32 vCPU
- $20 included credits/month
- Overkill for your needs

## Cost Comparison

| Provider | Cost/month | RAM | Setup Difficulty |
|----------|-----------|-----|------------------|
| Railway Hobby | $20 | 8GB | ⭐ Easiest |
| Hetzner CX31 | $9 | 8GB | ⭐⭐ Medium |
| DigitalOcean | $12 | 4GB | ⭐⭐ Medium |

**Railway Pros:**
- ✅ Easiest deployment (Git push = deploy)
- ✅ No SSH, no server management
- ✅ Built-in logging and monitoring
- ✅ Auto-restarts if crashes

**Railway Cons:**
- ❌ More expensive ($20 vs $9-12)
- ❌ Less control over server
- ❌ Cron jobs require workaround

## My Recommendation

**If you're comfortable spending $20/month**: Use Railway
- Worth it for the simplicity
- Perfect for testing and small-scale

**If you want to save money ($9/month)**: Use Hetzner
- More setup work (30 min one-time)
- Better value long-term
- Full control

**For production at scale (100 origins)**: Hetzner is better
- Railway could cost $30-50/month with high usage
- Hetzner stays at $9-17/month regardless

## Next Steps

1. **Push your code to GitHub** (see Step 2 above)
2. **Deploy to Railway** (see Step 3)
3. **Test Phase 1** to confirm Chromium works
4. **Set up cron job** for daily runs
5. **Monitor for a few days**
6. **Consider switching to Hetzner** if Railway costs too much

Need help with any step? Let me know!

