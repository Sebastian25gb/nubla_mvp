from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import extract_ip
from utils.database import get_db_connection
from collections import defaultdict
import logging
import os

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/alerts/{tenant_id}")
async def get_alerts(
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
        
        query = {
            "bool": {
                "must": [
                    {"regexp": {"message": ".*failed.*"}}
                ]
            }
        }
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        
        ip_counts = defaultdict(int)
        for log in logs:
            ip = extract_ip(log["message"])
            if ip:
                ip_counts[ip] += 1
        
        alerts = []
        for ip, count in ip_counts.items():
            if count >= 3:
                alerts.append({"ip": ip, "count": count})
        
        total_result = es.count(index=index_name, query=query)
        if not isinstance(total_result.get("count"), (int, float)):
            raise HTTPException(status_code=500, detail="Invalid count result from Elasticsearch")
        total = total_result["count"]
        return {"alerts": alerts, "tenant": tenant_id, "total": total}
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.get("/alerts-stats/{tenant_id}")
async def get_alerts_stats(
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
        
        query = {
            "bool": {
                "must": [
                    {"regexp": {"message": ".*failed.*"}}
                ]
            }
        }
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        
        ip_counts = defaultdict(int)
        for log in logs:
            ip = extract_ip(log["message"])
            if ip:
                ip_counts[ip] += 1
        
        alert_chart_data = [{"ip": ip, "failedAttempts": count} for ip, count in ip_counts.items() if count >= 3]
        return {"alert_chart_data": alert_chart_data}
    except Exception as e:
        logger.error(f"Error fetching alerts stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching alerts stats: {str(e)}")