import sqlite3
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear la tabla de tenants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                index_name TEXT NOT NULL
            )
        ''')

        # Verificar si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM tenants")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Tenants table is empty, populating with default tenants...")
            default_tenants = [
                ("tenant1", "Tenant 1", "logs-tenant1"),
                ("tenant2", "Tenant 2", "logs-tenant2")
            ]
            cursor.executemany("INSERT INTO tenants (id, name, index_name) VALUES (?, ?, ?)", default_tenants)
            conn.commit()
            logger.info("Default tenants inserted successfully.")
        else:
            logger.info(f"Tenants table already populated with {count} records, skipping initialization.")

        conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db_connection(db_path):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise