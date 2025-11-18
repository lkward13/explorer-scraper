# Hetzner Setup Guide for Explorer Scraper

## Step 1: Create Hetzner Account & Server

1. **Go to Hetzner Cloud**: https://console.hetzner.cloud/
2. **Sign up** (if you don't have an account)
3. **Create a new project**: "Explorer Scraper" or similar
4. **Create a server**:
   - **Location**: Choose closest to you (US: Ashburn, VA or Hillsboro, OR)
   - **Image**: Ubuntu 22.04 (or latest)
   - **Type**: 
     - **CX21** (2 vCPU, 4GB RAM) - €5.83/month - Good for testing
     - **CX31** (2 vCPU, 8GB RAM) - €9.40/month - Better for 12 parallel browsers
     - **CX41** (4 vCPU, 16GB RAM) - €17.35/month - Production scale (100 origins)
   - **SSH Key**: 
     - If you have one: Click "Add SSH Key" → paste your `~/.ssh/id_rsa.pub`
     - If not: Skip for now (use password, but SSH key is more secure)
   - **Backups**: Optional (adds 20% cost)
   - **Name**: explorer-scraper-1

5. **Click "Create & Buy Now"**

6. **Wait 1-2 minutes** for server to provision

7. **Copy the IP address** shown in the dashboard

## Step 2: Connect to Your Server

```bash
# If you set up SSH key:
ssh root@YOUR_SERVER_IP

# If using password (it was emailed to you):
ssh root@YOUR_SERVER_IP
# Enter password when prompted
```

## Step 3: Set Up the Server (run these commands on the server)

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

# Install Playwright browsers (this downloads Chromium)
playwright install chromium
playwright install-deps chromium
```

## Step 4: Upload Your Code to the Server

### Option A: Using Git (Recommended)

**On your Mac:**
```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# If you haven't already, initialize git repo
git init
git add .
git commit -m "Initial commit"

# Push to GitHub (private repo recommended)
# Create repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/explorer-scraper.git
git branch -M main
git push -u origin main
```

**On Hetzner server:**
```bash
cd /opt/explorer-scraper
git clone https://github.com/YOUR_USERNAME/explorer-scraper.git .
# Enter GitHub credentials when prompted
```

### Option B: Using SCP (Simpler, no GitHub needed)

**On your Mac:**
```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Upload everything (replace YOUR_SERVER_IP)
scp -r ./* root@YOUR_SERVER_IP:/opt/explorer-scraper/

# Or create a zip first to exclude unnecessary files
zip -r scraper.zip . -x "*.pyc" -x "__pycache__/*" -x "*.log" -x "*.html" -x "venv/*" -x "cursor_venv/*"
scp scraper.zip root@YOUR_SERVER_IP:/opt/explorer-scraper/
```

**On Hetzner server:**
```bash
cd /opt/explorer-scraper
apt-get install -y unzip
unzip scraper.zip
rm scraper.zip
```

## Step 5: Test the Scraper on Hetzner

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

cd /opt/explorer-scraper
source venv/bin/activate

# Test Phase 1 (1 origin, 1 browser)
python worker/test_parallel.py --phase 1

# If successful, you should see:
# - Explore complete: ~50 cards in ~20 seconds (much faster than Mac!)
# - Expansion complete
# - No browser windows popping up (headless)
```

## Step 6: Run Larger Tests

```bash
# Phase 2: 5 origins, 2 browsers
python worker/test_parallel.py --phase 2

# Phase 3: 10 origins, 4 browsers
python worker/test_parallel.py --phase 3

# Phase 4: 25 origins, 8 browsers
python worker/test_parallel.py --phase 4

# Monitor with htop (to see CPU/memory usage)
apt-get install -y htop
htop
```

## Step 7: Set Up Daily Cron Job (for production)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM UTC:
0 6 * * * cd /opt/explorer-scraper && /opt/explorer-scraper/venv/bin/python worker/run_daily.py >> /var/log/explorer-scraper.log 2>&1

# Save and exit (Ctrl+X, Y, Enter in nano)
```

## Step 8: View Results

**From your Mac, download results:**
```bash
# Download JSON results
scp root@YOUR_SERVER_IP:/opt/explorer-scraper/*.json ./

# Or view logs
ssh root@YOUR_SERVER_IP "tail -100 /var/log/explorer-scraper.log"
```

## Troubleshooting

### If you get "chromium not found" error:
```bash
cd /opt/explorer-scraper
source venv/bin/activate
playwright install chromium
```

### If you get permission errors:
```bash
chmod +x worker/*.py
chmod +x scripts/*.py
```

### To monitor running processes:
```bash
# See what's running
ps aux | grep python

# Kill a stuck process
pkill -f test_parallel.py
```

## Cost Estimates

**For 100 origins daily:**
- CX31 (8GB): €9.40/month - should be sufficient
- CX41 (16GB): €17.35/month - safer choice, more headroom
- Bandwidth: Included (20TB free)

**Additional costs:**
- Backups: +20% if enabled
- Snapshots: €0.0119/GB/month (optional)

Total: **€10-20/month for production**

## Security Notes

1. **Set up a firewall:**
```bash
ufw allow 22/tcp  # SSH
ufw enable
```

2. **Create a non-root user (optional but recommended):**
```bash
adduser scraper
usermod -aG sudo scraper
# Copy your SSH key to the new user
mkdir -p /home/scraper/.ssh
cp /root/.ssh/authorized_keys /home/scraper/.ssh/
chown -R scraper:scraper /home/scraper/.ssh
chmod 700 /home/scraper/.ssh
chmod 600 /home/scraper/.ssh/authorized_keys
```

3. **Disable root SSH login (after setting up user):**
```bash
nano /etc/ssh/sshd_config
# Change: PermitRootLogin no
systemctl restart sshd
```

## Next Steps After Setup

1. Test Phase 1-3 to confirm everything works
2. Adjust browser count based on server performance
3. Set up the daily cron job
4. Monitor for first few days
5. Scale up server size if needed

---

**Need help?** The Hetzner dashboard shows your server's IP, CPU, and network usage in real-time.

