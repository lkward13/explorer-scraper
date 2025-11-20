#!/bin/bash
# Start Xvfb (virtual display) in the background
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99

# Wait a moment for Xvfb to start
sleep 2

# Run the command passed as arguments
exec "$@"

