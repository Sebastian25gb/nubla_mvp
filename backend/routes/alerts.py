from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import extract_ip
from collections import defaultdict
import logging

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/alerts/{tenant_id}")
async def get_alerts(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=1, le=1000)
):
    es = get_elasticsearch_client()
    try:
        if not es.indices.exists(index="tenants"):
            raise HTTPException(status_code=404, detail="Tenants index not found")
        result = es.search(index="tenants", query={"match": {"id": tenant_id}}, size=1)
        if not isinstance(result.get("hits", {}).get("hits"), list) or not result["hits"]["hits"]:
            raise HTTPException(status_code=404, detail="Tenant not found")
        index_name = result["hits"]["hits"][0]["_source"]["index_name"]
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
    size: int = Query(50, ge=1, le=5000)
):
    es = get_elasticsearch_client()
    try:
        if not es.indices.exists(index="tenants"):
            raise HTTPException(status_code=404, detail="Tenants index not found")
        result = es.search(index="tenants", query={"match": {"id": tenant_id}}, size=1)
        if not isinstance(result.get("hits", {}).get("hits"), list) or not result["hits"]["hits"]:
            raise HTTPException(status_code=404, detail="Tenant not found")
        index_name = result["hits"]["hits"][0]["_source"]["index_name"]
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