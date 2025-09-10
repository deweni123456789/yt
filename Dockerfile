FROM python:3.10-slim

# Install system deps (ffmpeg + others)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy files
COPY . .

# Install python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Run bot
CMD ["python", "main.py"]
