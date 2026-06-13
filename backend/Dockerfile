FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (libs de MySQL para PyMySQL/cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY . .

# Carpetas para uploads y facturas (persistidas por volumen en docker-compose)
RUN mkdir -p /var/vetesia/uploads /var/vetesia/invoices

EXPOSE 5000

# Comando de produccion: primero crea y rellena la BBDD (usuarios, productos,
# proveedores, pedidos de ejemplo) y luego arranca gunicorn.
CMD ["sh", "-c", "python scripts/init_db.py && gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 run:app"]