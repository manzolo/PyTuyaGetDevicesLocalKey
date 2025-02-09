# Usa un'immagine base di Python
FROM python:3.12-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file necessari
COPY ./requirements.txt .
COPY ./app.py .
COPY ./dump_redis.py .
# Copia config.json solo se esiste
COPY ./config* .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Comando di avvio
CMD ["python", "app.py"]