FROM python:3.11-slim

WORKDIR /app

# Systemdependencies
RUN apt-get update && apt-get install -y \
    gcc \
  && rm -rf /var/lib/apt/lists/*

# Requirements kopieren & installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source kopieren
COPY . .

# Port exposen
EXPOSE 8100

# Start der App: ZIEL IST core/main.py -> app
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8100"]
