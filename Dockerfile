# Use official Playwright image with pre-installed browsers
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install build dependencies for psutil and Xvfb for non-headless mode
RUN apt-get update && apt-get install -y gcc python3-dev xvfb && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install protobuf compiler if needed for flights_pb2.py
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

# Compile protobuf files if not already compiled
RUN if [ ! -f "flights_pb2.py" ]; then protoc --python_out=. flights_pb2.proto; fi

# Set environment variable to prevent Playwright from trying to download browsers again
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Copy and make executable the Xvfb wrapper script
COPY start_with_xvfb.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start_with_xvfb.sh

# Set DISPLAY for Xvfb
ENV DISPLAY=:99

# Default command - can be overridden
CMD ["start_with_xvfb.sh", "python", "worker/test_parallel.py", "--phase", "1"]

