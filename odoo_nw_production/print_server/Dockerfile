FROM python:3.9-slim

# Install system dependencies
# libcups2-dev is needed for pycups
# gcc is needed for compiling pycups
RUN apt-get update && apt-get install -y \
    libcups2-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create mock output directory
RUN mkdir -p mock_output

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
