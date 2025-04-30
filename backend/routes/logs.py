from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import parse_timestamp
from utils.database import get_db_connection
import logging
import os

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/logs/{tenant_id}")
async def get_logs(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=0, le=1000)
):
    es = get_elasticsearch_client()
    try:
        # Obtener el index_name desde SQLite
        db_path = os.path.join(os.path.dirname(__file__), "..", "tenants.db")
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT index_name FROM tenants WHERE id = ?", (tenant_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")
        index_name = result[0]

        if not es.indices.exists(index=index_name):
            raise HTTPException(status_code=404, detail=f"Logs index {index_name} not found")
        
        query = {"match_all": {}}
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]
        return {"logs": logs, "tenant": tenant_id, "total": total}
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/logs-stats/{tenant_id}")
async def get_logs_stats(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=0, le=5000)
):
    es = get_elasticsearch_client()
    try:
        # Obtener el index_name desde SQLite
        db_path = os.path.join(os.path.dirname(__file__), "..", "tenants.db")
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT index_name FROM tenants WHERE id = ?", (tenant_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")
        index_name = result[0]

        if not es.indices.exists(index=index_name):
            raise HTTPException(status_code=404, detail=f"Logs index {index_name} not found")
        
        result = es.search(index=index_name, query={"match_all": {}}, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        
        logs_by_hour = {}
        for log in logs:
            timestamp = parse_timestamp(log["timestamp"])
            if timestamp:
                hour = timestamp.hour
                logs_by_hour[hour] = logs_by_hour.get(hour, 0) + 1
        
        logs_chart_data = [{"hour": f"{hour}:00", "count": count} for hour, count in logs_by_hour.items()]
        return {"logs_chart_data": logs_chart_data}
    except Exception as e:
        logger.error(f"Error fetching logs stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching logs stats: {str(e)}")