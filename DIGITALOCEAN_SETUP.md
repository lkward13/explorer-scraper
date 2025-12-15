# DigitalOcean Droplet Setup Guide

Complete guide to deploy your flight deal scraper on a DigitalOcean droplet.

---

## Part 1: Create Droplet

### 1.1 Sign Up for DigitalOcean

- Go to https://www.digitalocean.com/
- Sign up (get $200 credit for 60 days with referral links)
- Add payment method

### 1.2 Create Droplet

1. Click **Create** → **Droplets**
2. Choose configuration:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic
   - **CPU Options:** Regular (Intel/AMD)
   - **Size:** $18/mo (2 vCPU, 4GB RAM, 80GB SSD) ← **Recommended**
   - **Datacenter:** Choose closest to you (Dallas or NYC)
   - **Authentication:** SSH Key (we'll set this up next)
   - **Hostname:** `flight-scraper` (or whatever you want)

### 1.3 Set Up SSH Key (if you don't have one)

**On your Mac:**

```bash
# Check if you already have an SSH key
ls -la ~/.ssh/id_*.pub

# If not, create one
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter for all prompts (use defaults)

# Copy your public key
cat ~/.ssh/id_ed25519.pub
```

**In DigitalOcean:**
- Click **New SSH Key**
- Paste your public key
- Name it (e.g., "MacBook Pro")
- Add to droplet

### 1.4 Create Droplet

- Click **Create Droplet**
- Wait ~60 seconds for it to spin up
- Note the IP address (e.g., `143.198.123.45`)

---

## Part 2: Initial Server Setup

### 2.1 Connect to Your Droplet

```bash
# Replace with your droplet's IP
ssh root@YOUR_DROPLET_IP

# First time you'll see a fingerprint warning - type 'yes'
```

### 2.2 Run Automated Setup Script

**On your droplet (as root):**

```bash
# Download and run the setup script
curl -o setup_server.sh https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/setup_server.sh
chmod +x setup_server.sh
./setup_server.sh
```

**Or manually copy the script:**

1. On your Mac, copy the contents of `setup_server.sh` (created below)
2. On droplet: `nano setup_server.sh`
3. Paste contents, save (Ctrl+X, Y, Enter)
4. Run: `chmod +x setup_server.sh && ./setup_server.sh`

**The script will:**
- Update system packages
- Install Docker
- Install PostgreSQL
- Install Python 3.11+
- Install Git
- Set up firewall
- Create database
- Configure system for Playwright

**Duration:** ~5-10 minutes

---

## Part 3: Deploy Your Scraper

### 3.1 Clone Your Repository

```bash
# If public repo
git clone https://github.com/YOUR_USERNAME/explorer-scraper.git
cd explorer-scraper

# If private repo (set up GitHub SSH key first)
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub: Settings → SSH Keys → New SSH key
git clone git@github.com:YOUR_USERNAME/explorer-scraper.git
cd explorer-scraper
```

### 3.2 Set Up Environment Variables

```bash
# Copy example env file
cp env.example .env

# Edit with your credentials
nano .env
```

**Add your credentials:**

```bash
# Database (already set up by setup script)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flight_deals
DB_USER=flight_user
DB_PASSWORD=your_secure_password_here

# Email (your Gmail app password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password_here
RECIPIENT_EMAIL=your_email@gmail.com
```

Save: `Ctrl+X`, `Y`, `Enter`

### 3.3 Initialize Database

```bash
# Run schema setup
psql -U flight_user -d flight_deals -f database/schema.sql

# Verify tables created
psql -U flight_user -d flight_deals -c "\dt"
```

You should see:
- `expanded_deals`
- `scrape_runs`
- `route_price_insights`
- `sent_deals`

### 3.4 Build Docker Image

```bash
# Build the scraper image
docker build -t explorer-scraper .

# Verify it built
docker images | grep explorer-scraper
```

---

## Part 4: Test Your Setup

### 4.1 Test Database Connection

```bash
python3 -c "from database.config import get_connection_string; import psycopg2; conn = psycopg2.connect(get_connection_string()); print('✅ Database connected!'); conn.close()"
```

### 4.2 Run a Small Test Scrape

```bash
# Test with 5 origins (~30 minutes)
docker run --rm \
  -e DISPLAY=:99 \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=flight_deals \
  -e DB_USER=flight_user \
  -e DB_PASSWORD='your_password_here' \
  --network host \
  explorer-scraper python3 -u test_5_origins.py
```

**Note:** Use `--network host` on Linux to access localhost PostgreSQL

### 4.3 Test Email Sending

```bash
# Load environment variables
source .env

# Send test email
python3 send_test_email.py
```

Check your inbox! 📧

---

## Part 5: Set Up Automated Daily Scraping

### 5.1 Create Cron Job

```bash
# Edit crontab
crontab -e

# If first time, choose editor (nano is easiest - usually option 1)
```

**Add this line:**

```bash
# Run daily at 6:00 AM server time
0 6 * * * cd /root/explorer-scraper && ./run_daily_pipeline.sh >> /root/scraper_cron.log 2>&1
```

**Or for different time:**

```bash
# 3 AM
0 3 * * * cd /root/explorer-scraper && ./run_daily_pipeline.sh >> /root/scraper_cron.log 2>&1

# 9 PM
0 21 * * * cd /root/explorer-scraper && ./run_daily_pipeline.sh >> /root/scraper_cron.log 2>&1

# Twice daily (6 AM and 6 PM)
0 6,18 * * * cd /root/explorer-scraper && ./run_daily_pipeline.sh >> /root/scraper_cron.log 2>&1
```

Save: `Ctrl+X`, `Y`, `Enter`

### 5.2 Verify Cron Job

```bash
# List cron jobs
crontab -l

# Check cron is running
systemctl status cron
```

### 5.3 Test Cron Job Manually

```bash
# Run the pipeline manually to test
cd /root/explorer-scraper
./run_daily_pipeline.sh
```

**This will:**
1. Build Docker image
2. Run 100-origin scrape (~3.5-4 hours)
3. Calculate price insights
4. Send email digest

---

## Part 6: Monitoring & Maintenance

### 6.1 Check Logs

```bash
# View cron log
tail -f /root/scraper_cron.log

# View today's scrape log
tail -f /root/explorer-scraper/daily_scrape_$(date +%Y%m%d).log

# View all scrape logs
ls -lh /root/explorer-scraper/daily_scrape_*.log
```

### 6.2 Check Database

```bash
# Connect to database
psql -U flight_user -d flight_deals

# Check deal counts
SELECT COUNT(*) FROM expanded_deals;

# Check recent scrapes
SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT 5;

# Check price insights
SELECT COUNT(*), data_quality FROM route_price_insights GROUP BY data_quality;

# Exit
\q
```

### 6.3 Monitor Resources

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check running Docker containers
docker ps

# Check system load
htop  # (press q to quit)
```

### 6.4 Update Your Code

```bash
cd /root/explorer-scraper

# Pull latest changes
git pull

# Rebuild Docker image
docker build -t explorer-scraper .

# Next cron run will use new code
```

---

## Part 7: Troubleshooting

### Issue: Scrape not saving to database

**Check:**
```bash
# Verify database connection
psql -U flight_user -d flight_deals -c "SELECT 1;"

# Check if Docker can reach database
docker run --rm --network host explorer-scraper python3 -c "from database.config import get_connection_string; import psycopg2; conn = psycopg2.connect(get_connection_string()); print('✅ Connected'); conn.close()"
```

**Fix:** Make sure you're using `--network host` in Docker run command

### Issue: Email not sending

**Check:**
```bash
# Verify SMTP credentials
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SMTP User:', os.getenv('SMTP_USER')); print('Has password:', bool(os.getenv('SMTP_PASS')))"

# Test email manually
python3 send_test_email.py
```

**Fix:** Regenerate Gmail app password if needed

### Issue: Out of disk space

**Check:**
```bash
df -h
du -sh /root/explorer-scraper/*
```

**Clean up:**
```bash
# Remove old Docker images
docker system prune -a

# Remove old log files (keep last 30 days)
find /root/explorer-scraper -name "daily_scrape_*.log" -mtime +30 -delete

# Vacuum database
psql -U flight_user -d flight_deals -c "VACUUM FULL;"
```

### Issue: Cron job not running

**Check:**
```bash
# Verify cron service is running
systemctl status cron

# Check cron log
grep CRON /var/log/syslog | tail -20

# Check your crontab
crontab -l
```

**Fix:**
```bash
# Restart cron service
systemctl restart cron

# Make sure script is executable
chmod +x /root/explorer-scraper/run_daily_pipeline.sh
```

### Issue: High memory usage

**Check:**
```bash
free -h
docker stats
```

**Fix:**
```bash
# Reduce parallel browsers in test_100_origins_v2.py
# Edit: max_explore_browsers=3, max_expansion_browsers=5

# Or upgrade to $24/mo droplet (8GB RAM)
```

---

## Part 8: Optimization Tips

### 8.1 Speed Up Scrapes

1. **Reduce origins:** Edit `test_100_origins_v2.py` to scrape fewer origins
2. **Increase parallelism:** If you have more RAM, increase browser counts
3. **Schedule during off-peak:** Run at night when Google Flights has less traffic

### 8.2 Reduce Costs

1. **Downgrade to $12/mo droplet** if scrapes work fine (test first)
2. **Use snapshots:** Take weekly snapshots ($1.20/mo) for backups
3. **Monitor bandwidth:** 2TB included, but watch usage

### 8.3 Improve Email Quality

1. **Adjust cooldown:** Edit `run_daily_pipeline.sh` → `COOLDOWN_DAYS=14` for less frequent deals
2. **Increase threshold:** Edit `deal_selector.py` regional thresholds for better deals only
3. **Filter by region:** Only send deals to specific regions

---

## Part 9: Security Best Practices

### 9.1 Set Up Firewall

```bash
# Already done by setup script, but verify:
ufw status

# Should show:
# 22/tcp (SSH) - OPEN
# 5432/tcp (PostgreSQL) - DENY (only localhost)
```

### 9.2 Secure PostgreSQL

```bash
# Change default password
psql -U flight_user -d flight_deals
\password flight_user
# Enter new password
\q

# Update .env with new password
nano .env
```

### 9.3 Keep System Updated

```bash
# Run monthly
apt update && apt upgrade -y

# Reboot if kernel updated
reboot
```

### 9.4 Set Up Automatic Backups

```bash
# Create backup script
nano /root/backup_db.sh
```

**Add:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U flight_user flight_deals | gzip > /root/backups/flight_deals_$DATE.sql.gz
# Keep last 7 days
find /root/backups -name "flight_deals_*.sql.gz" -mtime +7 -delete
```

**Set up:**
```bash
mkdir -p /root/backups
chmod +x /root/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /root/backup_db.sh
```

---

## Quick Reference

### Common Commands

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Check scraper status
tail -f /root/scraper_cron.log

# Run scraper manually
cd /root/explorer-scraper && ./run_daily_pipeline.sh

# Check database
psql -U flight_user -d flight_deals

# Update code
cd /root/explorer-scraper && git pull && docker build -t explorer-scraper .

# Check disk space
df -h

# Check memory
free -h

# Restart server
reboot
```

### Important Paths

- **Project:** `/root/explorer-scraper`
- **Logs:** `/root/explorer-scraper/daily_scrape_*.log`
- **Cron log:** `/root/scraper_cron.log`
- **Backups:** `/root/backups`
- **Environment:** `/root/explorer-scraper/.env`

### Support

- **DigitalOcean Docs:** https://docs.digitalocean.com/
- **Community:** https://www.digitalocean.com/community
- **Status:** https://status.digitalocean.com/

---

## Next Steps

1. ✅ Create droplet
2. ✅ Run setup script
3. ✅ Deploy code
4. ✅ Test scrape
5. ✅ Set up cron job
6. ✅ Monitor first run
7. 🎉 Enjoy automated deal alerts!

---

**Estimated Setup Time:** 30-45 minutes  
**Monthly Cost:** $18  
**Maintenance:** ~15 minutes/month  

Your scraper will now run automatically every day at 6 AM, scrape 100 origins, calculate price insights, and email you the best deals! 📧✈️
