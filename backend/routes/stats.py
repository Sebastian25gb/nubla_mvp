from fastapi import APIRouter
from backend.database import get_db_connection

router = APIRouter()

@router.get("/stats")
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