from elasticsearch import Elasticsearch
import time

def get_elasticsearch_client():
    retries = 3
    for attempt in range(retries):
        try:
            es = Elasticsearch(["http://localhost:9200"])
            if es.ping():
                return es
            else:
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            print(f"Attempt {attempt+1}/{retries} to connect to Elasticsearch failed: {str(e)}")
            if attempt == retries - 1:
                raise Exception("Failed to connect to Elasticsearch after several attempts")
            time.sleep(5)  # Esperar 5 segundos antes de reintentar
    raise Exception("Failed to connect to Elasticsearch after several attempts")