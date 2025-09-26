# OpenEarlyEducation Dockerfile
# Build with: docker build -t openearlyeducation .
# Run with: docker run -p 8000:8000 openearlyeducation

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Copy requirements first for better caching
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app main.py .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/templates

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main", "api", "--host", "0.0.0.0", "--port", "8000"]
