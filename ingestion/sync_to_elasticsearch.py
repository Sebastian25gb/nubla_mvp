import os
import logging
from elasticsearch import Elasticsearch, helpers
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "nubla_db"),
        user=os.getenv("POSTGRES_USER", "nubla_user"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    )

def get_es_connection():
    return Elasticsearch(
        [os.getenv("ELASTICSEARCH_HOST", "elasticsearch:9200")],
        basic_auth=(
            os.getenv("ELASTICSEARCH_USER", "elastic"),
            os.getenv("ELASTICSEARCH_PASSWORD", "yourpassword")
        )
    )

def sync_to_elasticsearch():
    # Conectar a PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()

    # Conectar a Elasticsearch
    es = get_es_connection()
    if not es.ping():
        raise ConnectionError("Failed to connect to Elasticsearch")

    # Obtener logs de PostgreSQL
    cursor.execute("""
    SELECT l.id, l.timestamp, c.tenant, l.user_id, l.action, l.status, l.bytes
    FROM logs l
    JOIN clients c ON l.client_id = c.id
    WHERE l.created_at > NOW() - INTERVAL '1 hour'
    """)
    logs = cursor.fetchall()

    actions = []
    for log in logs:
        log_id, timestamp, tenant, user_id, action, status, bytes = log
        index_name = f"logs-{tenant}"
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)
        action = {
            "_index": index_name,
            "_id": log_id,
            "_source": {
                "timestamp": timestamp,
                "tenant": tenant,
                "user_id": user_id,
                "action": action,
                "status": status,
                "bytes": bytes
            }
        }
        actions.append(action)

    if actions:
        success, failed = helpers.bulk(es, actions, raise_on_error=False)
        logger.info(f"Synced {success} logs to Elasticsearch, {len(failed)} failed")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    sync_to_elasticsearch()