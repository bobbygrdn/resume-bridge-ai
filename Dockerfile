# Dockerfile for Resume Bridge AI FastAPI app
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Set environment variables (OpenAI key must be set by user)
ENV PYTHONUNBUFFERED=1

# Run FastAPI app in production mode
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
