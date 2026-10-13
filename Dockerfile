FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8080/ || exit 1

# Start FastAPI Uvicorn Server
CMD ["uvicorn", "webapp.server:app", "--host", "0.0.0.0", "--port", "8080"]
