import json
import os
import logging
import psycopg2
from psycopg2.extras import execute_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "nubla_db"),
        user=os.getenv("POSTGRES_USER", "nubla_user"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    )

def insert_logs_to_postgres(log_file):
    # Verificar si el archivo existe y no está vacío
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        logger.error(f"Log file {log_file} does not exist or is empty")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Mapear tenants a client_ids
    cursor.execute("SELECT id, tenant FROM clients")
    client_map = {row[1]: row[0] for row in cursor.fetchall()}

    logs = []
    failed_lines = 0
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # Ignorar líneas vacías
                continue
            try:
                log_entry = json.loads(line)
                tenant = log_entry["tenant"]
                if tenant not in client_map:
                    logger.warning(f"Tenant {tenant} not found in clients table")
                    continue
                client_id = client_map[tenant]
                logs.append((
                    client_id,
                    log_entry["timestamp"],
                    log_entry["user_id"],
                    log_entry["action"],
                    log_entry["status"],
                    log_entry["bytes"]
                ))
            except json.JSONDecodeError as e:
                failed_lines += 1
                logger.warning(f"Failed to parse line: {line}, error: {str(e)}")
                continue

    if failed_lines > 0:
        logger.warning(f"Skipped {failed_lines} invalid lines")

    if not logs:
        logger.warning("No valid logs to insert")
        cursor.close()
        conn.close()
        return

    # Insertar logs en lotes
    insert_query = """
    INSERT INTO logs (client_id, timestamp, user_id, action, status, bytes)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_batch(cursor, insert_query, logs, page_size=100)
    conn.commit()

    logger.info(f"Inserted {len(logs)} logs into PostgreSQL")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python insert_logs_to_postgres.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    insert_logs_to_postgres(log_file)