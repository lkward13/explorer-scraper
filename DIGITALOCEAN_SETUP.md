# DigitalOcean Setup Guide for Explorer Scraper

DigitalOcean is very similar to Hetzner - same Linux server setup, just $3 more per month.

## Step 1: Create DigitalOcean Account & Droplet

1. **Go to DigitalOcean**: https://www.digitalocean.com/
2. **Sign up** (or login)
3. **Create a Droplet** (their name for a server):
   - Click "Create" → "Droplets"
   - **Image**: Ubuntu 22.04 LTS x64
   - **Droplet Type**: 
     - **Basic** plan
     - **Regular** CPU
     - **4 GB RAM / 2 vCPUs** - $12/month (best for testing)
     - **8 GB RAM / 4 vCPUs** - $24/month (production scale)
   - **Datacenter Region**: Choose closest to you (NYC, SF, etc.)
   - **Authentication**: 
     - **SSH Key** (recommended): Add your `~/.ssh/id_rsa.pub`
     - Or **Password**: They'll email you
   - **Hostname**: explorer-scraper-1
   - Click **"Create Droplet"**

4. **Wait 1-2 minutes** for droplet to provision

5. **Copy the IP address** shown in the dashboard

## Step 2: Connect to Your Server

```bash
# If you set up SSH key:
ssh root@YOUR_SERVER_IP

# If using password (emailed to you):
ssh root@YOUR_SERVER_IP
# Enter password when prompted
```

## Step 3: Set Up the Server (run these on the server)

```bash
# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3-pip git

# Install Playwright system dependencies
apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# Create app directory
mkdir -p /opt/explorer-scraper
cd /opt/explorer-scraper

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install playwright protobuf psutil beautifulsoup4 httpx

# Install Playwright browsers (downloads Chromium)
playwright install chromium
playwright install-deps chromium
```

## Step 4: Upload Your Code

### Option A: Using Git (Recommended)

**On your Mac:**
```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Commit recent changes
git add .
git commit -m "Remove Railway config, prepare for DigitalOcean"
git push
```

**On DigitalOcean server:**
```bash
cd /opt/explorer-scraper

# Clone from GitHub (use your actual repo URL)
git clone https://github.com/lkward13/explorer-scraper.git .

# Enter GitHub credentials when prompted
```

### Option B: Using SCP (Simpler)

**On your Mac:**
```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Upload everything
scp -r ./* root@YOUR_SERVER_IP:/opt/explorer-scraper/
```

## Step 5: Test the Scraper

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

cd /opt/explorer-scraper
source venv/bin/activate

# Test Phase 1 (1 origin, 1 browser)
python worker/test_parallel.py --phase 1
```

**Expected output:**
```
Exploring PHX...
  Total so far: ~52 cards

✓ Explore complete: 52 cards in ~20s (MUCH faster than Mac!)
✓ Expansion complete
```

## Step 6: Run Larger Tests

```bash
# Phase 2: 5 origins, 2 browsers
python worker/test_parallel.py --phase 2

# Phase 3: 10 origins, 4 browsers  
python worker/test_parallel.py --phase 3

# Monitor server resources
apt-get install -y htop
htop
```

## Step 7: Set Up Daily Cron Job (Optional)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM UTC:
0 6 * * * cd /opt/explorer-scraper && /opt/explorer-scraper/venv/bin/python worker/run_daily.py >> /var/log/explorer-scraper.log 2>&1
```

## DigitalOcean Pricing

| Plan | RAM | vCPU | Price | Best For |
|------|-----|------|-------|----------|
| Basic | 4 GB | 2 | $12/mo | Testing (Phase 1-3) |
| Basic | 8 GB | 4 | $24/mo | Production (100 origins) |

**vs Railway**: $12/mo vs $20/mo for same specs
**vs Hetzner**: $12/mo vs $9/mo (DigitalOcean easier US support)

## Troubleshooting

### If you get "chromium not found":
```bash
cd /opt/explorer-scraper
source venv/bin/activate
playwright install chromium
playwright install-deps chromium
```

### If you get permission errors:
```bash
chmod +x worker/*.py
chmod +x scripts/*.py
```

### To monitor running processes:
```bash
ps aux | grep python
```

### To kill a stuck process:
```bash
pkill -f test_parallel.py
```

## Security (Optional but Recommended)

```bash
# Set up firewall
ufw allow 22/tcp  # SSH
ufw enable

# Create non-root user (optional)
adduser scraper
usermod -aG sudo scraper
```

## Download Results

**From your Mac:**
```bash
# Download JSON results
scp root@YOUR_SERVER_IP:/opt/explorer-scraper/*.json ./

# Or view logs
ssh root@YOUR_SERVER_IP "tail -100 /var/log/explorer-scraper.log"
```

## Cost Comparison

| Provider | 4GB RAM | 8GB RAM | Support |
|----------|---------|---------|---------|
| **DigitalOcean** | $12/mo | $24/mo | US-based |
| **Hetzner** | $6/mo | $9/mo | Germany |
| **Railway** | N/A | $20/mo | Platform |

**DigitalOcean Pros:**
- ✅ US company, easier support
- ✅ Better documentation
- ✅ Large community
- ✅ Same speed as Hetzner

**DigitalOcean Cons:**
- ❌ $3-6/mo more than Hetzner
- ❌ Still more expensive than Hetzner

---

**Ready to start?** Create your DigitalOcean account and I'll walk you through the setup!

