FROM python:3.10-slim

# Install system dependencies for OpenCV, MediaPipe, and ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /tmp/uploads

# Expose port
EXPOSE 52513

# Set environment variables
ENV NOTREALLY_DB_PATH=/tmp/notreally.db
ENV NOTREALLY_UPLOAD_DIR=/tmp/uploads
ENV PORT=52513

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:52513/ || exit 1

# Run the application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:52513", "--workers", "1", "--threads", "4", "--timeout", "600"]
