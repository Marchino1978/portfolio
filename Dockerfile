FROM python:3.12-slim

WORKDIR /app

# Copia solo requirements prima per sfruttare cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice
COPY . .

# Crea directory data (utile in caso di volume vuoto)
RUN mkdir -p data

# Variabili ambiente
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Timeout più alto: 5 minuti (300 secondi) per dare tempo a scraping + commit
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "300", "--log-level", "info", "app:app"]