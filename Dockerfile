# Usar Python 3.12 como imagen base
FROM python:3.12

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . /app

# Instalar dependencias
RUN pip install confluent-kafka==2.5.0 elasticsearch==8.15.1

# Comando por defecto (se ejecutará directamente)
CMD ["python", "ingestion/consume_to_elasticsearch.py"]