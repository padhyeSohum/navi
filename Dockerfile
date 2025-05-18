FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
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
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    python3-dev \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip setuptools wheel

# Install dlib and PyAudio individually
RUN pip install dlib==19.24.0 --prefer-binary
RUN pip install PyAudio==0.2.14 --global-option=build_ext --global-option="-I/usr/include/portaudio19"

# Now install the rest
RUN pip install -r requirements.txt

CMD ["python", "main.py"]