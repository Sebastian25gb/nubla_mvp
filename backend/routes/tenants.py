from fastapi import APIRouter, HTTPException
from utils.database import get_db_connection
import logging
import os

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/tenants")
async def get_tenants():
    db_path = os.path.join(os.path.dirname(__file__), "..", "tenants.db")
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, index_name FROM tenants")
        tenants = [{"id": row[0], "name": row[1], "index_name": row[2]} for row in cursor.fetchall()]
        conn.close()
        return {"tenants": tenants}
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tenants: {str(e)}")