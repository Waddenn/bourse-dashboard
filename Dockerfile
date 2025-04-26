# Utilise une image Python légère
FROM python:3.11-slim

# Empêche Python de bufferiser la sortie
ENV PYTHONUNBUFFERED=1

# Dépendances système utiles
RUN apt-get update && apt-get install -y \
    build-essential \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Crée un dossier pour l'app
WORKDIR /app

# Copie les fichiers dans le conteneur
COPY . /app

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port utilisé par Flask
EXPOSE 5000

# Lance le serveur Flask
CMD ["sh", "-c", "redis-server & gunicorn -w 4 -b 0.0.0.0:5000 app:app"]
