from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client

router = APIRouter()

@router.get("/threats/{tenant_id}")
async def get_threats(
    tenant_id: str,
    from_: int = Query(0, ge=0, alias="from"),
    size: int = Query(100, ge=1, le=1000)
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
        threats = [hit["_source"] for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]
        return {"threats": threats, "tenant": tenant_id, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching threats: {str(e)}")