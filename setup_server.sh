#!/bin/bash

###############################################################################
# DigitalOcean Droplet Setup Script
# 
# This script sets up a fresh Ubuntu 22.04 droplet for running the flight
# deal scraper. It installs all dependencies, configures PostgreSQL, and
# prepares the system for Docker-based scraping.
#
# Usage: 
#   chmod +x setup_server.sh
#   ./setup_server.sh
#
# Duration: ~5-10 minutes
###############################################################################

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║          Flight Deal Scraper - Server Setup Script                    ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo ""
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

###############################################################################
# Step 1: Update System
###############################################################################

print_step "Updating system packages..."
apt update
apt upgrade -y
print_success "System updated"

###############################################################################
# Step 2: Install Basic Dependencies
###############################################################################

print_step "Installing basic dependencies..."
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    unzip \
    software-properties-common \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release
print_success "Basic dependencies installed"

###############################################################################
# Step 3: Install Docker
###############################################################################

print_step "Installing Docker..."

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl start docker
systemctl enable docker

# Verify Docker installation
docker --version
print_success "Docker installed"

###############################################################################
# Step 4: Install Python 3.11+
###############################################################################

print_step "Installing Python 3.11..."

add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip

# Set Python 3.11 as default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify Python installation
python3 --version
print_success "Python 3.11 installed"

###############################################################################
# Step 5: Install PostgreSQL
###############################################################################

print_step "Installing PostgreSQL..."

apt install -y postgresql postgresql-contrib

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

print_success "PostgreSQL installed"

###############################################################################
# Step 6: Configure PostgreSQL
###############################################################################

print_step "Configuring PostgreSQL..."

# Generate a random password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE flight_deals;
CREATE USER flight_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE flight_deals TO flight_user;
\c flight_deals
GRANT ALL ON SCHEMA public TO flight_user;
EOF

print_success "PostgreSQL configured"
print_warning "Database password: $DB_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Save this password! You'll need it for your .env file"
echo ""
echo "Add to your .env file:"
echo "DB_HOST=localhost"
echo "DB_PORT=5432"
echo "DB_NAME=flight_deals"
echo "DB_USER=flight_user"
echo "DB_PASSWORD=$DB_PASSWORD"
echo ""
read -p "Press Enter to continue..."

###############################################################################
# Step 7: Install Python Dependencies
###############################################################################

print_step "Installing Python dependencies..."

pip3 install --upgrade pip
pip3 install \
    psycopg2-binary \
    python-dotenv \
    playwright

print_success "Python dependencies installed"

###############################################################################
# Step 8: Install Playwright Browsers
###############################################################################

print_step "Installing Playwright browsers (this may take a few minutes)..."

playwright install chromium
playwright install-deps chromium

print_success "Playwright browsers installed"

###############################################################################
# Step 9: Configure Firewall
###############################################################################

print_step "Configuring firewall..."

# Install UFW if not already installed
apt install -y ufw

# Allow SSH (important!)
ufw allow 22/tcp

# Deny external PostgreSQL access (only localhost)
ufw deny 5432/tcp

# Enable firewall
echo "y" | ufw enable

print_success "Firewall configured"

###############################################################################
# Step 10: System Optimizations
###############################################################################

print_step "Applying system optimizations..."

# Increase file descriptors for Playwright
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize PostgreSQL for small server
sudo -u postgres psql << EOF
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '1536MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '5242kB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
EOF

# Restart PostgreSQL to apply changes
systemctl restart postgresql

print_success "System optimizations applied"

###############################################################################
# Step 11: Set Timezone
###############################################################################

print_step "Setting timezone to America/Chicago (CST)..."

timedatectl set-timezone America/Chicago

print_success "Timezone set to $(timedatectl | grep 'Time zone')"

###############################################################################
# Step 12: Create Directory Structure
###############################################################################

print_step "Creating directory structure..."

mkdir -p /root/backups
mkdir -p /root/logs

print_success "Directory structure created"

###############################################################################
# Final Summary
###############################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║                    ✅ Setup Complete!                                  ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Installed:"
echo "  ✅ Docker $(docker --version | cut -d' ' -f3)"
echo "  ✅ Python $(python3 --version | cut -d' ' -f2)"
echo "  ✅ PostgreSQL $(psql --version | cut -d' ' -f3)"
echo "  ✅ Playwright (Chromium)"
echo ""
echo "Database:"
echo "  📦 Database: flight_deals"
echo "  👤 User: flight_user"
echo "  🔑 Password: $DB_PASSWORD"
echo ""
echo "Next Steps:"
echo "  1. Clone your repository:"
echo "     git clone https://github.com/YOUR_USERNAME/explorer-scraper.git"
echo ""
echo "  2. Set up .env file with database credentials above"
echo ""
echo "  3. Initialize database schema:"
echo "     cd explorer-scraper"
echo "     psql -U flight_user -d flight_deals -f database/schema.sql"
echo ""
echo "  4. Build Docker image:"
echo "     docker build -t explorer-scraper ."
echo ""
echo "  5. Run test scrape:"
echo "     ./run_daily_pipeline.sh"
echo ""
echo "  6. Set up cron job:"
echo "     crontab -e"
echo "     Add: 0 6 * * * cd /root/explorer-scraper && ./run_daily_pipeline.sh >> /root/scraper_cron.log 2>&1"
echo ""
echo "📚 Full guide: See DIGITALOCEAN_SETUP.md"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Save credentials to file for reference
cat > /root/db_credentials.txt << EOF
Database Credentials
====================
Created: $(date)

DB_HOST=localhost
DB_PORT=5432
DB_NAME=flight_deals
DB_USER=flight_user
DB_PASSWORD=$DB_PASSWORD

⚠️  Keep this file secure! Delete after copying to .env
EOF

print_warning "Database credentials saved to: /root/db_credentials.txt"
echo ""

