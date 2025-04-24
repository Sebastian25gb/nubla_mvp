from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import extract_ip

router = APIRouter()

@router.get("/alerts/{tenant_id}")
async def get_alerts(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=1, le=1000)  # Reducimos el tamaño predeterminado a 50
):
    es = get_elasticsearch_client()
    try:
        if not es.indices.exists(index="tenants"):
            raise HTTPException(status_code=404, detail="Tenants index not found")
        result = es.search(index="tenants", query={"match": {"id": tenant_id}}, size=1)
        if not result["hits"]["hits"]:
            raise HTTPException(status_code=404, detail="Tenant not found")
        index_name = result["hits"]["hits"][0]["_source"]["index_name"]
        if not es.indices.exists(index=index_name):
            raise HTTPException(status_code=404, detail=f"Logs index {index_name} not found")
        
        query = {"match": {"message": "failed"}}
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        ip_counts = {}
        for log in logs:
            ip = extract_ip(log["message"])
            if ip:
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
        alerts = [
            {"ip": ip, "count": count}
            for ip, count in ip_counts.items()
            if count >= 3
        ]
        total = result["hits"]["total"]["value"]
        return {"alerts": alerts, "tenant": tenant_id, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")