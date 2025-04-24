from fastapi import APIRouter, HTTPException
from utils.elasticsearch import get_elasticsearch_client

router = APIRouter()

@router.get("/tenants")
async def get_tenants():
    es = get_elasticsearch_client()
    try:
        print("Checking if tenants index exists...")
        if not es.indices.exists(index="tenants"):
            print("Tenants index does not exist, creating it...")
            tenants = [
                {"id": "tenant1", "name": "Tenant 1", "index_name": "logs-tenant1"},
                {"id": "tenant2", "name": "Tenant 2", "index_name": "logs-tenant2"}
            ]
            es.indices.create(index="tenants")
            print("Tenants index created, indexing tenants...")
            for tenant in tenants:
                es.index(index="tenants", id=tenant["id"], document=tenant)
            print("Tenants indexed successfully.")
        else:
            print("Tenants index already exists.")
        
        print("Searching for tenants...")
        result = es.search(index="tenants", query={"match_all": {}}, size=10)
        print(f"Search result: {result}")
        tenants = [hit["_source"] for hit in result["hits"]["hits"]]
        print(f"Retrieved tenants: {tenants}")
        return {"tenants": tenants}
    except Exception as e:
        print(f"Error in get_tenants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tenants: {str(e)}")