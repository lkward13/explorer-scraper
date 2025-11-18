# Quick Deploy to Railway

## Step 1: Create GitHub Repo

Go to: https://github.com/new

- **Repository name**: `explorer-scraper`
- **Description**: Google Travel Explore flight deal scraper
- **Visibility**: ⚠️ **Private** (important!)
- Click "Create repository"

## Step 2: Push Your Code

```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Explorer Scraper for Railway"

# Link to your new repo
git remote add origin https://github.com/lkward13/explorer-scraper.git

# Push
git branch -M main
git push -u origin main
```

You'll be prompted for GitHub credentials. Use your GitHub personal access token (not password).

## Step 3: Deploy to Railway

1. Go to Railway dashboard: https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. If prompted, click "Configure GitHub App" and give Railway access to `explorer-scraper`
5. Select `lkward13/explorer-scraper`
6. Railway will automatically:
   - Detect Python project
   - Install requirements
   - Install Playwright & Chromium
   - Start building (takes ~5-10 min first time)

## Step 4: Monitor Build

Watch the logs in Railway. You should see:

```
Installing dependencies...
Installing Playwright browsers...
✓ Chromium installed
Build complete!
```

## Step 5: Test

Once deployed, check the logs to confirm it's working. You can manually trigger by clicking "Redeploy".

## Troubleshooting

**If build fails**: Check Railway logs for errors
**If Playwright fails**: Make sure `nixpacks.toml` was committed
**If out of memory**: Upgrade to Hobby plan ($20/month)

Done! Your scraper is now deployed and will run automatically.
