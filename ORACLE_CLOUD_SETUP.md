# Oracle Cloud Free Tier Setup Guide for Explorer Scraper

Oracle Cloud offers a **completely FREE** tier that includes:
- ✅ 4 vCPU ARM processor
- ✅ 24GB RAM (more than you need!)
- ✅ 200GB storage
- ✅ **FREE forever** (not a trial)

**Warning**: Oracle sometimes randomly terminates accounts, but it's worth trying since it's free.

## Step 1: Create Oracle Cloud Account

1. **Go to Oracle Cloud**: https://www.oracle.com/cloud/free/
2. **Click "Start for free"**
3. **Fill in account details**:
   - Email address
   - Country/Region (select your country)
   - First/Last name
4. **Verify email**
5. **Add payment method**:
   - ⚠️ They require a credit card for verification
   - ⚠️ You won't be charged for free tier
   - They may charge $1 to verify, then refund it
6. **Wait for account approval** (can take a few minutes to hours)

## Step 2: Create a Compute Instance

Once your account is approved:

1. **Go to Console**: https://cloud.oracle.com/
2. **Click "Create a VM instance"** (or navigate to Compute → Instances)
3. **Configure the instance**:

   **Name**: `explorer-scraper`
   
   **Image and shape**:
   - Click "Change image"
   - Select **"Canonical Ubuntu 22.04"**
   - Click "Select image"
   
   **Shape**:
   - Click "Change shape"
   - Select **"Ampere" (ARM processor)**
   - Select **"VM.Standard.A1.Flex"**
   - Set: **4 OCPUs, 24GB RAM** (this is free!)
   - Click "Select shape"
   
   **Networking**:
   - Create new Virtual Cloud Network (VCN): Yes
   - Assign public IPv4 address: Yes
   
   **Add SSH keys**:
   - **Option A**: Upload your public key (`~/.ssh/id_rsa.pub`)
   - **Option B**: Generate new key pair (Oracle will download it)
   
   **Boot volume**: 
   - Leave default (50GB is fine)

4. **Click "Create"**

5. **Wait 1-2 minutes** for instance to provision

6. **Copy the Public IP address** from the instance details

## Step 3: Configure Firewall (Important!)

Oracle's firewall blocks everything by default. You need to open ports:

1. **On the instance page**, click on the **VCN name** (under "Primary VNIC")
2. **Click "Security Lists"** on the left
3. **Click the default security list**
4. **Click "Add Ingress Rules"**:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port Range: `22`
   - Description: `SSH`
   - Click "Add Ingress Rules"

## Step 4: Connect to Your Instance

```bash
# If you uploaded your SSH key:
ssh ubuntu@YOUR_PUBLIC_IP

# If Oracle generated the key for you:
chmod 400 ~/Downloads/ssh-key-*.key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

**Note**: Default user is `ubuntu` (not `root` like other providers)

## Step 5: Set Up the Server

Once connected:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Install Playwright system dependencies
sudo apt-get install -y \
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
sudo mkdir -p /opt/explorer-scraper
sudo chown ubuntu:ubuntu /opt/explorer-scraper
cd /opt/explorer-scraper

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install playwright protobuf psutil beautifulsoup4 httpx

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

## Step 6: Upload Your Code

```bash
# On Oracle Cloud instance:
cd /opt/explorer-scraper

# Clone from GitHub
git clone https://github.com/lkward13/explorer-scraper.git .

# If prompted for credentials, use your GitHub username and personal access token
```

## Step 7: Test the Scraper

```bash
# Activate virtual environment
source /opt/explorer-scraper/venv/bin/activate

# Run Phase 1 test
python worker/test_parallel.py --phase 1
```

**Expected output:**
```
Exploring PHX...
  Total so far: ~52 cards

✓ Explore complete: 52 cards in ~20-30s
```

**Note**: ARM processors are slightly slower than Intel/AMD, but still much faster than your Mac.

## Step 8: Run Larger Tests

```bash
# Phase 2: 5 origins, 2 browsers
python worker/test_parallel.py --phase 2

# Phase 3: 10 origins, 4 browsers
python worker/test_parallel.py --phase 3
```

## Troubleshooting

### Can't SSH (Connection refused)

1. Check security list has port 22 open
2. Check instance is running (not stopped)
3. Try adding `ubuntu` before the IP: `ssh ubuntu@IP`

### Playwright fails to install

```bash
# ARM architecture needs special handling
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
pip install playwright
playwright install chromium
playwright install-deps chromium
```

### Out of memory (unlikely with 24GB)

```bash
# Check memory usage
free -h
htop
```

### Oracle terminates your account

- This happens randomly to some users
- No recourse - Oracle doesn't explain why
- If this happens, switch to Vultr or Linode ($12/mo)

## Download Results

**From your Mac:**
```bash
# Download results (replace with your key path if needed)
scp ubuntu@YOUR_IP:/opt/explorer-scraper/*.json ./

# View logs
ssh ubuntu@YOUR_IP "tail -100 /opt/explorer-scraper/*.log"
```

## Cost: $0 Forever! 🎉

As long as you stay within free tier limits:
- ✅ VM.Standard.A1.Flex up to 4 OCPUs, 24GB RAM
- ✅ 200GB block storage
- ✅ 10TB/month outbound data transfer

**Your scraper will easily stay within these limits.**

## If Oracle Doesn't Work

Don't worry - we have backups:

1. **Vultr** - $12/month: https://www.vultr.com/
2. **Linode** - $12/month: https://www.linode.com/
3. **Contabo** - $7/month: https://contabo.com/

Setup is nearly identical to this guide, just change the username from `ubuntu` to `root`.

---

## Quick Start Summary

```bash
# 1. Sign up at: https://www.oracle.com/cloud/free/
# 2. Create Ubuntu 22.04 VM.Standard.A1.Flex (4 OCPU, 24GB)
# 3. Open port 22 in security list
# 4. SSH in and run setup commands above
# 5. Clone your code and test!
```

**Good luck!** Oracle's free tier is amazing if you get approved. If not, Vultr is your next best option at $12/month.

