# AudiencePulse - Creator Vetting Platform
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Cache directories for non-root user
ENV HOME=/home/appuser
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/sentence_transformers

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with UID 1000 (for Kubernetes runAsUser: 1000)
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g 1000 -m -s /bin/bash appuser && \
    mkdir -p /home/appuser/.cache/huggingface \
    /home/appuser/.cache/transformers \
    /home/appuser/.cache/sentence_transformers && \
    chown -R 1000:1000 /home/appuser

# Copy requirements first for better caching
COPY requirements.txt .

# Install CPU-Only Torch (Optimization: Reduces image size by 2GB+)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership of app directory to appuser
RUN chown -R 1000:1000 /app

# Switch to non-root user
USER 1000

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
