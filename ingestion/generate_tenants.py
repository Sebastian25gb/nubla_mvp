import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.utils.elasticsearch import get_elasticsearch_client
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_tenants():
    try:
        es = get_elasticsearch_client()

        # Lista de tenants
        tenants = [
            {"id": "tenant1", "name": "Tenant 1", "index_name": "logs-tenant1"},
            {"id": "tenant2", "name": "Tenant 2", "index_name": "logs-tenant2"}
        ]

        # Crear el índice tenants si no existe
        if not es.indices.exists(index="tenants"):
            logger.info("Creating tenants index...")
            es.indices.create(index="tenants")
        else:
            # Verificar si el índice tiene datos
            result = es.count(index="tenants")
            if not isinstance(result.get("count"), (int, float)):
                raise Exception("Invalid count result from Elasticsearch")
            if result["count"] == 0:
                logger.info("Tenants index is empty, populating with default tenants...")
            else:
                logger.info(f"Tenants index already populated with {result['count']} documents, skipping initialization.")
                return

        # Insertar los tenants
        for tenant in tenants:
            es.index(index="tenants", id=tenant["id"], document=tenant)
        logger.info("Tenants indexed successfully.")

        # Forzar un refresh
        es.indices.refresh(index="tenants")
        logger.info("Tenants index refreshed.")
    except Exception as e:
        logger.error(f"Error generating tenants: {str(e)}")
        raise

if __name__ == "__main__":
    generate_tenants()