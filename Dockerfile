# Usar una versión específica de Python basada en Debian Bullseye para mayor estabilidad y seguridad
FROM python:3.12.7-slim-bullseye

# Establecer el directorio de trabajo
WORKDIR /app

# Actualizar los paquetes del sistema para mitigar vulnerabilidades
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del proyecto
COPY . .

# Definir el comando por defecto (será sobrescrito por docker-compose.yml)
CMD ["python", "ingestion/insert_logs_to_postgres.py"]