FROM python:3.10

# Install system deps
RUN apt-get update && apt-get install -y ffmpeg

# Set workdir
WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot files
COPY . .

# Run bot
CMD ["python", "main.py"]
