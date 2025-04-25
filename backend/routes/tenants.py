from fastapi import APIRouter, HTTPException
from utils.elasticsearch import get_elasticsearch_client
import logging

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/tenants")
async def get_tenants():
    es = get_elasticsearch_client()
    try:
        if not es.indices.exists(index="tenants"):
            raise HTTPException(status_code=404, detail="Tenants index not found")
        
        result = es.search(index="tenants", query={"match_all": {}}, size=10)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        
        tenants = [hit["_source"] for hit in result["hits"]["hits"]]
        logger.info(f"Retrieved tenants: {tenants}")
        return {"tenants": tenants}
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tenants: {str(e)}")