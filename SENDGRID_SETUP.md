# SendGrid Setup Guide

SendGrid is a free email service that works on DigitalOcean (unlike SMTP which is blocked).

**Free tier:** 100 emails/day (plenty for daily deal emails)

---

## Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Click **"Start for Free"**
3. Fill out the form:
   - Email: `lukesward@gmail.com`
   - Password: (create one)
   - Company: "Personal" or "Flight Deals"
4. Verify your email (check inbox)

---

## Step 2: Complete Onboarding

After email verification:

1. **Tell us about yourself:**
   - Role: "Developer" or "Other"
   - Company size: "Just me"
   - Click "Get Started"

2. **Choose integration:**
   - Select "Web API"
   - Language: "Python"
   - Click "Next"

---

## Step 3: Create API Key

1. In SendGrid dashboard, go to **Settings** → **API Keys**
2. Click **"Create API Key"**
3. Name it: `flight-scraper`
4. Permissions: **"Full Access"** (or at minimum "Mail Send")
5. Click **"Create & View"**
6. **⚠️ IMPORTANT: Copy the API key NOW** (you can't see it again!)
   - It looks like: `SG.xxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy`

---

## Step 4: Verify Sender Email

SendGrid requires you to verify the email you'll send FROM:

1. Go to **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"**
3. Fill out form:
   - From Name: "Flight Deals" (or your name)
   - From Email: `lukesward@gmail.com`
   - Reply To: `lukesward@gmail.com`
   - Company: "Personal"
   - Address: (your address)
   - City, State, Zip: (your info)
4. Click **"Create"**
5. **Check your email** for verification link
6. Click the verification link

**✅ Once verified, you can send emails from `lukesward@gmail.com`**

---

## Step 5: Update Your Droplet

Once you have your API key, run these commands:

```bash
# SSH into droplet
ssh root@165.245.139.247

# Go to project
cd /root/explorer-scraper

# Pull latest code
git pull

# Install SendGrid
pip3 install sendgrid

# Update .env file
nano .env
```

**Add these lines to your `.env` file:**

```bash
# SendGrid (add these lines)
SENDGRID_API_KEY=SG.your_actual_api_key_here
FROM_EMAIL=lukesward@gmail.com
```

Save: `Ctrl+X`, `Y`, `Enter`

---

## Step 6: Test It!

```bash
# Test sending email via SendGrid
python3 send_daily_deals_sendgrid.py --num-deals 5

# If it works, you should get an email in ~10 seconds!
```

---

## Step 7: Update Daily Pipeline

Update `run_daily_pipeline.sh` to use SendGrid instead of SMTP.

I'll do this automatically once you confirm SendGrid is working!

---

## Troubleshooting

### "SendGrid library not installed"
```bash
pip3 install sendgrid
```

### "Sender email not verified"
- Go to SendGrid dashboard → Settings → Sender Authentication
- Make sure `lukesward@gmail.com` shows as "Verified"
- If not, click "Resend Verification Email"

### "API key invalid"
- Make sure you copied the full API key (starts with `SG.`)
- No spaces before/after the key in `.env`
- Try creating a new API key if needed

### "403 Forbidden"
- Your API key needs "Mail Send" permission
- Go to Settings → API Keys → Edit your key → Set to "Full Access"

---

## Quick Reference

**SendGrid Dashboard:** https://app.sendgrid.com/

**API Keys:** Settings → API Keys

**Sender Verification:** Settings → Sender Authentication

**Email Activity:** Activity → Email Activity (see sent emails)

---

## Next Steps

Once SendGrid is working:

1. ✅ Update `run_daily_pipeline.sh` to use SendGrid
2. ✅ Set up cron job on droplet
3. ✅ Enjoy automated daily deal emails!

**Your scraper will run every day at 6 AM and email you the best deals! 📧✈️**

