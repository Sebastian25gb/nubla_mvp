from fastapi import FastAPI
from routes import logs, threats, alerts, anomalies, tenants
from utils.elasticsearch import get_elasticsearch_client
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ingestion.generate_tenants import generate_tenants
from ingestion.generate_test_logs import generate_test_logs
from ingestion.ingest import ingest_logs

app = FastAPI()

app.include_router(logs.router)
app.include_router(threats.router)
app.include_router(alerts.router)
app.include_router(anomalies.router)
app.include_router(tenants.router)

# Ejecutar la inicialización al iniciar el servidor
@app.on_event("startup")
async def startup_event():
    es = get_elasticsearch_client()
    
    # Verificar y generar los tenants
    print("Checking tenants initialization...")
    generate_tenants()
    
    # Verificar si los índices de logs existen y tienen datos
    tenants = [
        {"id": "tenant1", "index_name": "logs-tenant1"},
        {"id": "tenant2", "index_name": "logs-tenant2"}
    ]
    # Usar una ruta absoluta para el archivo de logs
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
    
    for tenant in tenants:
        index_name = tenant["index_name"]
        if not es.indices.exists(index=index_name):
            print(f"Index {index_name} does not exist, it will be created...")
        else:
            result = es.count(index=index_name)
            if result["count"] == 0:
                print(f"Index {index_name} is empty, it will be populated...")
            else:
                print(f"Index {index_name} already populated with {result['count']} documents, skipping initialization.")
                continue
    
    # Generar e ingerir logs si es necesario
    print("Generating test logs...")
    generate_test_logs(logs_file, num_logs=5000, days_back=30)
    print("Ingesting test logs into Elasticsearch...")
    ingest_logs(es, logs_file)