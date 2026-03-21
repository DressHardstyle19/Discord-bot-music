FROM python:3.11-slim

# Instalar ffmpeg, libopus y dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libopus-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo del bot
COPY . .

# Ejecutar el bot
CMD ["python", "main.py"]
