# Email Setup Guide

## Quick Setup (2 minutes)

### Step 1: Create .env file
```bash
cp env.example .env
```

### Step 2: Edit .env with your credentials
```bash
# Open in your editor
nano .env
# or
code .env
```

Fill in:
```bash
# Database (already working)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flight_deals
DB_USER=lukeward
DB_PASSWORD=your_db_password

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_16_char_app_password
RECIPIENT_EMAIL=your_email@gmail.com
```

### Step 3: Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Click "Select app" → Choose "Mail"
4. Click "Select device" → Choose "Other" → Type "Flight Deals"
5. Click "Generate"
6. Copy the 16-character password (no spaces)
7. Paste into `.env` as `SMTP_PASS`

### Step 4: Test it!
```bash
# Dry run (preview only)
python3 send_test_email.py --dry-run

# Send actual email
python3 send_test_email.py
```

## What You'll Get

The test will send you **3 emails** with the top-scoring flight deals:

- Beautiful HTML emails with gradient headers
- Large price display
- Travel dates
- Direct "Book Now" button to Google Flights
- Quality score and confidence level
- Number of similar dates available

## Troubleshooting

### "Authentication failed"
- Make sure you're using an **App Password**, not your regular Gmail password
- App passwords are 16 characters with no spaces
- Get one at: https://myaccount.google.com/apppasswords

### "RECIPIENT_EMAIL is required"
- Make sure you created `.env` file (not just `env.example`)
- Check that `RECIPIENT_EMAIL` is set in `.env`

### "Connection refused"
- Check that `SMTP_HOST` is `smtp.gmail.com`
- Check that `SMTP_PORT` is `587`

### "No deals found"
- Run the scraper first to get deals in the database
- Try lowering `--min-quality` (e.g., `--min-quality 60`)

## Advanced Usage

### Send more deals
```bash
python3 send_test_email.py --num-deals 5
```

### Lower quality threshold
```bash
python3 send_test_email.py --min-quality 60
```

### Use different email
```bash
python3 send_test_email.py --to friend@example.com
```

### Preview without sending
```bash
python3 send_test_email.py --dry-run
open test_email_preview.html
```

## Security Notes

- ✅ `.env` is in `.gitignore` (won't be committed)
- ✅ Use App Passwords (not your main Gmail password)
- ✅ Never commit credentials to git
- ✅ Keep `.env` file private

## Next Steps

Once testing works:

1. **Set up daily automation** (see `TESTING_GUIDE.md`)
2. **Customize email templates** (edit `email_builder.py`)
3. **Add more recipients** (modify `send_daily_deals.py`)
4. **Schedule daily sends** (cron job)

---

**Need help?** Check `TESTING_GUIDE.md` or run with `--help`:
```bash
python3 send_test_email.py --help
```



