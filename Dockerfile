# Use official Playwright image with pre-installed browsers
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

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

# Default command - can be overridden
CMD ["python", "worker/test_parallel.py", "--phase", "1"]

