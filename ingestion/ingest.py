import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.utils.elasticsearch import get_elasticsearch_client
from elasticsearch import helpers
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_logs(es, filename):
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Log file {filename} not found")

    with open(filename, 'r') as f:
        logs = f.readlines()
    
    actions = []
    for log in logs:
        try:
            parts = log.strip().split(' ', 2)
            if len(parts) != 3:
                continue
            timestamp, tenant, message = parts
            index_name = f"logs-{tenant}"
            
            log_entry = {
                "_index": index_name,
                "_source": {
                    "timestamp": timestamp,
                    "tenant": tenant,
                    "message": message
                }
            }
            actions.append(log_entry)
        except Exception as e:
            logger.warning(f"Error processing log: {log}, error: {str(e)}")
            continue
    
    try:
        # Crear índices si no existen
        for tenant in ["tenant1", "tenant2"]:
            index_name = f"logs-{tenant}"
            if not es.indices.exists(index=index_name):
                es.indices.create(index=index_name)
        
        # Usar bulk para ingerir logs
        success, failed = helpers.bulk(es, actions, raise_on_error=False)
        logger.info(f"Ingested {success} logs into Elasticsearch, {len(failed)} failed")
        
        # Forzar un refresh
        for tenant in ["tenant1", "tenant2"]:
            index_name = f"logs-{tenant}"
            if es.indices.exists(index=index_name):
                es.indices.refresh(index=index_name)
    except Exception as e:
        logger.error(f"Error ingesting logs: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        es = get_elasticsearch_client()
        # Usar una ruta absoluta para el archivo de logs
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
        ingest_logs(es, logs_file)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise