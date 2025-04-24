from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import parse_timestamp

router = APIRouter()

@router.get("/logs/{tenant_id}")
async def get_logs(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=1, le=1000)
):
    es = get_elasticsearch_client()
    try:
        print(f"Checking if tenants index exists for tenant_id: {tenant_id}")
        if not es.indices.exists(index="tenants"):
            print("Tenants index not found")
            raise HTTPException(status_code=404, detail="Tenants index not found")
        
        print(f"Searching for tenant {tenant_id} in tenants index...")
        result = es.search(index="tenants", query={"match": {"id": tenant_id}}, size=1)
        print(f"Search result for tenant: {result}")
        if not result["hits"]["hits"]:
            print(f"Tenant {tenant_id} not found")
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        index_name = result["hits"]["hits"][0]["_source"]["index_name"]
        print(f"Tenant found, index_name: {index_name}")
        
        print(f"Checking if logs index {index_name} exists...")
        if not es.indices.exists(index=index_name):
            print(f"Logs index {index_name} not found")
            raise HTTPException(status_code=404, detail=f"Logs index {index_name} not found")
        
        print(f"Searching logs in index {index_name}...")
        query = {"match_all": {}}
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        print(f"Search result: {result}")
        
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]
        print(f"Retrieved {len(logs)} logs, total: {total}")
        
        return {"logs": logs, "tenant": tenant_id, "total": total}
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/logs-stats/{tenant_id}")
async def get_logs_stats(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(50, ge=1, le=5000)
):
    es = get_elasticsearch_client()
    try:
        print(f"Checking if tenants index exists for logs-stats, tenant_id: {tenant_id}")
        if not es.indices.exists(index="tenants"):
            print("Tenants index not found")
            raise HTTPException(status_code=404, detail="Tenants index not found")
        
        print(f"Searching for tenant {tenant_id} in tenants index for logs-stats...")
        result = es.search(index="tenants", query={"match": {"id": tenant_id}}, size=1)
        print(f"Search result for tenant: {result}")
        if not result["hits"]["hits"]:
            print(f"Tenant {tenant_id} not found")
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        index_name = result["hits"]["hits"][0]["_source"]["index_name"]
        print(f"Tenant found, index_name: {index_name}")
        
        print(f"Checking if logs index {index_name} exists for logs-stats...")
        if not es.indices.exists(index=index_name):
            print(f"Logs index {index_name} not found")
            raise HTTPException(status_code=404, detail=f"Logs index {index_name} not found")
        
        print(f"Searching logs in index {index_name} for stats...")
        result = es.search(index=index_name, query={"match_all": {}}, from_=from_, size=size)
        print(f"Search result: {result}")
        
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        print(f"Retrieved {len(logs)} logs for stats")
        
        logs_by_hour = {}
        for log in logs:
            timestamp = parse_timestamp(log["timestamp"])
            if timestamp:
                hour = timestamp.hour
                logs_by_hour[hour] = logs_by_hour.get(hour, 0) + 1
        
        logs_chart_data = [{"hour": f"{hour}:00", "count": count} for hour, count in logs_by_hour.items()]
        print(f"Logs chart data: {logs_chart_data}")
        return {"logs_chart_data": logs_chart_data}
    except Exception as e:
        print(f"Error fetching logs stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching logs stats: {str(e)}")