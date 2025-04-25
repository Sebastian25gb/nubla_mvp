from fastapi import FastAPI
from routes import logs, threats, alerts, anomalies, tenants
from utils.elasticsearch import get_elasticsearch_client
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ingestion.generate_tenants import generate_tenants
from ingestion.generate_test_logs import generate_test_logs
from ingestion.ingest import ingest_logs
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    try:
        # Verificar y generar los tenants
        logger.info("Checking tenants initialization...")
        generate_tenants()
    except Exception as e:
        logger.error(f"Error initializing tenants: {str(e)}")
        # Continuar a pesar del error para no detener el servidor
    
    # Verificar si los índices de logs existen y tienen datos
    tenants = [
        {"id": "tenant1", "index_name": "logs-tenant1"},
        {"id": "tenant2", "index_name": "logs-tenant2"}
    ]
    # Usar una ruta absoluta para el archivo de logs
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
    
    should_generate_logs = False
    for tenant in tenants:
        index_name = tenant["index_name"]
        try:
            if not es.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist, it will be created...")
                should_generate_logs = True
            else:
                result = es.count(index=index_name)
                if result["count"] == 0:
                    logger.info(f"Index {index_name} is empty, it will be populated...")
                    should_generate_logs = True
                else:
                    logger.info(f"Index {index_name} already populated with {result['count']} documents, skipping initialization.")
        except Exception as e:
            logger.error(f"Error checking index {index_name}: {str(e)}")
            should_generate_logs = True
    
    # Generar e ingerir logs si es necesario
    if should_generate_logs:
        try:
            logger.info("Generating test logs...")
            generate_test_logs(logs_file, num_logs=5000, days_back=30)
            logger.info("Ingesting test logs into Elasticsearch...")
            ingest_logs(es, logs_file)
        except Exception as e:
            logger.error(f"Error generating/ingesting logs: {str(e)}")
            # Continuar a pesar del error para no detener el servidor