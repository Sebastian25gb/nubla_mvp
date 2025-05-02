from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI()

# Habilitar CORS para que el frontend pueda acceder al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "nubla_db"),
        user=os.getenv("POSTGRES_USER", "nubla_user"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password_123"),
        cursor_factory=RealDictCursor
    )

# Endpoint para obtener logs
@app.get("/logs")
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id, l.timestamp, c.tenant, l.user_id, l.action, l.status, l.bytes
        FROM logs l
        JOIN clients c ON l.client_id = c.id
        ORDER BY l.timestamp DESC
        LIMIT 100
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs

# Endpoint para obtener estadísticas
@app.get("/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.tenant, 
               COUNT(*) as total_logs, 
               SUM(CASE WHEN l.status = 'success' THEN 1 ELSE 0 END) as success_logs,
               SUM(CASE WHEN l.status = 'failure' THEN 1 ELSE 0 END) as failure_logs
        FROM logs l
        JOIN clients c ON l.client_id = c.id
        GROUP BY c.tenant
    """)
    stats = cursor.fetchall()
    cursor.close()
    conn.close()
    return stats