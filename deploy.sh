#!/bin/bash

###############################################################################
# Deploy Script - Update code on DigitalOcean droplet
# 
# This script pulls the latest code from Git and rebuilds the Docker image.
# Run this whenever you make changes to your scraper code.
#
# Usage (on your droplet):
#   ./deploy.sh
#
# Duration: ~2-3 minutes
###############################################################################

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo ""
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║                    Deploying Latest Code                               ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

###############################################################################
# Step 1: Check for uncommitted changes
###############################################################################

print_step "Checking Git status..."

if [[ -n $(git status -s) ]]; then
    echo ""
    echo "⚠️  You have uncommitted changes:"
    git status -s
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
fi

print_success "Git status checked"

###############################################################################
# Step 2: Pull latest code
###############################################################################

print_step "Pulling latest code from Git..."

CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

git pull origin "$CURRENT_BRANCH"

print_success "Code updated"

###############################################################################
# Step 3: Rebuild Docker image
###############################################################################

print_step "Rebuilding Docker image..."

docker build -t explorer-scraper .

print_success "Docker image rebuilt"

###############################################################################
# Step 4: Clean up old images
###############################################################################

print_step "Cleaning up old Docker images..."

docker image prune -f

print_success "Cleanup complete"

###############################################################################
# Step 5: Verify deployment
###############################################################################

print_step "Verifying deployment..."

# Check if image exists
if docker images | grep -q explorer-scraper; then
    print_success "Docker image verified"
else
    print_error "Docker image not found!"
    exit 1
fi

# Check if .env exists
if [[ ! -f .env ]]; then
    print_error ".env file not found!"
    echo "Create .env file with your credentials"
    exit 1
fi

print_success "Environment verified"

###############################################################################
# Final Summary
###############################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║                    ✅ Deployment Complete!                             ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Latest commit:"
git log -1 --oneline
echo ""
echo "Docker image:"
docker images | grep explorer-scraper | head -1
echo ""
echo "Next scrape will use the updated code automatically."
echo ""
echo "To test immediately:"
echo "  ./run_daily_pipeline.sh"
echo ""

