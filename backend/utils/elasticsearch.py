from elasticsearch import Elasticsearch
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_elasticsearch_client():
    retries = 3
    for attempt in range(retries):
        try:
            # En producción, agregar credenciales si xpack.security.enabled=true
            # Ejemplo: es = Elasticsearch(["http://localhost:9200"], basic_auth=("username", "password"))
            es = Elasticsearch(["http://localhost:9200"])
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return es
            else:
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{retries} to connect to Elasticsearch failed: {str(e)}")
            if attempt == retries - 1:
                logger.error("Failed to connect to Elasticsearch after several attempts")
                raise Exception("Failed to connect to Elasticsearch after several attempts")
            time.sleep(5)  # Esperar 5 segundos antes de reintentar
    logger.error("Failed to connect to Elasticsearch after several attempts")
    raise Exception("Failed to connect to Elasticsearch after several attempts")