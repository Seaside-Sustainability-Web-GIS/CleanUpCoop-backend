# Use the official slim Python image
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (for GeoDjango and PostGIS support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    cmake \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    proj-bin \
    binutils \
    libproj-dev \
    postgresql-client \
    python3-gdal \
    libgeos-dev \
    wget \
    bzip2 \
     && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and run the geospatial dependencies installation script
COPY /scripts/install_geospatial.sh /app/install_geospatial.sh
RUN chmod +x /app/install_geospatial.sh && /app/install_geospatial.sh

# Install Python dependencies in a separate layer for caching
RUN pip install --upgrade pip
COPY ../requirements.txt /app/
RUN pip install --prefix /install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -r appuser && mkdir /app && chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy application code and dependencies
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose port 8000
EXPOSE 8000

# Make entry file executable
RUN chmod +x  /app/scripts/entrypoint.prod.sh

# Start the application using Uvicorn
CMD ["/app/scripts/entrypoint.prod.sh"]