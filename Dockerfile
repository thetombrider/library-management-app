FROM python:3.10-alpine

WORKDIR /app

# Installa dipendenze di sistema necessarie
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    jpeg-dev \
    zlib-dev \
    cmake \
    ninja \
    git \
    # Dipendenze per pyarrow
    boost-dev \
    bzip2-dev \
    gflags-dev \
    lz4-dev \
    snappy-dev \
    zstd-dev

# Copia i requisiti
COPY requirements.txt .

# Installa le dipendenze in una singola istruzione RUN
# Usa la specifica di un package pre-compilato per pyarrow invece di compilarlo
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Installa streamlit senza pyarrow
    pip install --no-cache-dir streamlit --no-deps && \
    # Installa dipendenze di streamlit eccetto pyarrow
    pip install --no-cache-dir pillow pandas protobuf altair blinker cachetools click gitpython importlib_metadata jinja2 jsonschema \
    markdown_it markupsafe numpy packaging pydeck pygments toml toolz tornado tzlocal urllib3 watchdog && \
    # Pulisci la cache delle dipendenze di compilazione
    rm -rf /root/.cache

# Crea directory per i dati persistenti
RUN mkdir -p /data

# Copia l'intero progetto
COPY . .

# Configura variabili d'ambiente
ENV DATABASE_URL="sqlite:////data/books.db" 
ENV SECRET_KEY="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ENV API_URL="http://localhost:8000"
ENV PYTHONUNBUFFERED=1
# Imposta questa variabile per evitare errori relativi a PyArrow
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Inizializza il database se non esiste
RUN python -c "from backend.database import Base, engine; from backend.models import Book, User, Loan; Base.metadata.create_all(bind=engine)"

# Esponi le porte necessarie
EXPOSE 8000 8501

# Scrivi lo script di avvio
RUN echo '#!/bin/sh\n\
# Avvia il backend\n\
uvicorn main:app --host 0.0.0.0 --port 8000 & \n\
# Attendi che il backend sia pronto\n\
sleep 5\n\
# Avvia il frontend Streamlit\n\
cd frontend && exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n'\
> /app/start.sh && chmod +x /app/start.sh

# Usa una shell più leggera
CMD ["/bin/sh", "/app/start.sh"]