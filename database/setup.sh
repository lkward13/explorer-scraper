#!/bin/bash
# PostgreSQL Database Setup Script for Flight Deals
# For macOS (adjust commands for Linux/Windows)

set -e  # Exit on error

echo "================================"
echo "Flight Deals Database Setup"
echo "================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew not installed. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    brew install postgresql@15
    echo "PostgreSQL installed successfully!"
else
    echo "✓ PostgreSQL already installed"
fi

# Start PostgreSQL service
echo ""
echo "Starting PostgreSQL service..."
if command -v brew &> /dev/null; then
    brew services start postgresql@15 || brew services restart postgresql@15
    echo "✓ PostgreSQL service started"
else
    echo "Note: Please start PostgreSQL manually if not already running"
fi

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 2

# Create database
echo ""
echo "Creating database 'flight_deals'..."
if psql -lqt | cut -d \| -f 1 | grep -qw flight_deals; then
    echo "⚠ Database 'flight_deals' already exists"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dropdb flight_deals
        createdb flight_deals
        echo "✓ Database recreated"
    else
        echo "Keeping existing database"
    fi
else
    createdb flight_deals
    echo "✓ Database 'flight_deals' created"
fi

# Run schema
echo ""
echo "Creating database tables..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
psql flight_deals < "$SCRIPT_DIR/schema.sql"
echo "✓ Tables created successfully"

# Show database info
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Database: flight_deals"
echo "Connection: postgresql://postgres@localhost:5432/flight_deals"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env (if needed)"
echo "  2. Update database credentials in .env"
echo "  3. Run a test: python worker/test_parallel.py --phase 1 --save-to-db"
echo ""
echo "Useful commands:"
echo "  psql flight_deals                    # Connect to database"
echo "  psql flight_deals -c 'SELECT COUNT(*) FROM expanded_deals;'  # Check deal count"
echo "  psql flight_deals -c '\\dt'          # List all tables"
echo ""

