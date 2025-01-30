# Use the official slim Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies (for GeoDjango and PostGIS support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    gdal-bin \
    binutils \
    libproj-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a separate layer for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . /app/

# Expose port 8000
EXPOSE 8000

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]