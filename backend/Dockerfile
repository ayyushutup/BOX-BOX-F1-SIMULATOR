FROM python:3.10-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (e.g., for compiled C extensions if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser

# Copy application code and gunicorn config
COPY app ./app
COPY data ./data
COPY gunicorn_conf.py .

# Create models directory and give appuser ownership
RUN mkdir -p /models && chown -R appuser:appuser /models /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Start Gunicorn with Uvicorn workers and dynamic CPU scaling config
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]
