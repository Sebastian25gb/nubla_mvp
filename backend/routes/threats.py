from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
import logging

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/threats/{tenant_id}")
async def get_threats(
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
        threats = [hit["_source"] for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]
        return {"threats": threats, "tenant": tenant_id, "total": total}
    except Exception as e:
        logger.error(f"Error fetching threats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching threats: {str(e)}")

@router.get("/threats-stats/{tenant_id}")
async def get_threats_stats(
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
        
        result = es.search(index=index_name, query={"match_all": {}}, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        
        normal_logs = 0
        threat_logs = 0
        for log in logs:
            if "failed" in log["message"].lower():
                threat_logs += 1
            else:
                normal_logs += 1
        
        pie_data = [
            {"name": "Normal", "value": normal_logs, "color": "#00C49F"},
            {"name": "Threats", "value": threat_logs, "color": "#FF0000"}
        ]
        return {"pie_data": pie_data}
    except Exception as e:
        logger.error(f"Error fetching threats stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching threats stats: {str(e)}")