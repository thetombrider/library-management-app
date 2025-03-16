FROM python:3.10-slim

WORKDIR /app

# Installa le dipendenze di sistema necessarie (più leggere rispetto alla versione Alpine)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia i file di requirements separati per backend e frontend
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crea directory per i dati persistenti
RUN mkdir -p /data

# Copia l'intero progetto
COPY . .

# Configura variabili d'ambiente
ENV DATABASE_URL="sqlite:////data/books.db" 
ENV SECRET_KEY="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ENV API_URL="http://100.73.156.78:8001"
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true

# Esponi le porte necessarie
EXPOSE 8000 8501

# Script di avvio semplificato senza creazione utente admin
RUN echo '#!/bin/bash\n\
# Controlla se il database esiste già\n\
if [ ! -f "/data/books.db" ]; then\n\
    echo "Inizializzazione del database..."\n\
    python init_db.py\n\
else\n\
    echo "Database esistente trovato in /data/books.db"\n\
fi\n\
\n\
echo "Avvio del backend..."\n\
uvicorn main:app --host 0.0.0.0 --port 8000 & \n\
BACKEND_PID=$!\n\
echo "Backend avviato con PID $BACKEND_PID"\n\
\n\
echo "Attendi che il backend sia pronto..."\n\
sleep 5\n\
\n\
echo "Avvio del frontend..."\n\
cd /app && streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0 & \n\
FRONTEND_PID=$!\n\
echo "Frontend avviato con PID $FRONTEND_PID"\n\
\n\
# Gestione dei segnali per terminare correttamente i processi\n\
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM\n\
\n\
# Mantieni il container in esecuzione\n\
wait\n\
' > /app/start.sh

# Rendi eseguibile lo script
RUN chmod +x /app/start.sh

# Comando di avvio
CMD ["/bin/bash", "/app/start.sh"]