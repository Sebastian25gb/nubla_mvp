from elasticsearch import Elasticsearch
import re
import os

def ingest_logs(es, filename):
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    
    with open(filename, 'r') as f:
        logs = f.readlines()
    
    for log in logs:
        try:
            parts = log.strip().split(' ', 2)
            if len(parts) != 3:
                continue
            timestamp, tenant, message = parts
            index_name = f"logs-{tenant}"
            
            if not es.indices.exists(index=index_name):
                es.indices.create(index=index_name)
            
            log_entry = {
                "timestamp": timestamp,
                "tenant": tenant,
                "message": message
            }
            es.index(index=index_name, document=log_entry)
        except Exception as e:
            print(f"Error processing log: {log}, error: {str(e)}")
            continue
    
    for tenant in ["tenant1", "tenant2"]:
        index_name = f"logs-{tenant}"
        if es.indices.exists(index=index_name):
            es.indices.refresh(index=index_name)
    print(f"Ingested {len(logs)} logs into Elasticsearch")

if __name__ == "__main__":
    es = Elasticsearch(["http://localhost:9200"])
    if not es.ping():
        raise Exception("Failed to connect to Elasticsearch")
    # Usar una ruta absoluta para el archivo de logs
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
    ingest_logs(es, logs_file)