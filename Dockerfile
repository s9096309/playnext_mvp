FROM python:3.11-slim

WORKDIR /app

# System-Pakete installieren
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Port freigeben
EXPOSE 8000

# STARTBEFEHL (Hier ist der Fix: application:application)
CMD ["sh", "-c", "alembic upgrade head && uvicorn application:application --host 0.0.0.0 --port 8000"]