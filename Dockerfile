# Use a minimal Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required to build dlib and PyAudio
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libx11-dev \
    libgtk-3-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    python3-dev \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your code into the container
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel

# Optional: Install dlib and PyAudio first (helps isolate issues)
RUN pip install dlib==19.24.0
RUN pip install PyAudio==0.2.14

# Install the rest of your requirements
RUN pip install --no-cache-dir -r requirements.txt

# Start your app (change `main.py` to your entry point)
CMD ["python", "main.py"]