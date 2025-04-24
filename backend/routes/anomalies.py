from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import parse_timestamp, extract_ip

router = APIRouter()

@router.get("/anomalies/{tenant_id}")
async def get_anomalies(
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
        
        query = {"match_all": {}}
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        logs = [hit["_source"] for hit in result["hits"]["hits"]]
        
        anomalies = []
        ip_counts = {}
        malware_keywords = ["malware", "exploit", "ransomware"]
        
        for log in logs:
            try:
                timestamp = parse_timestamp(log["timestamp"])
                if not timestamp:
                    continue
                hour = timestamp.hour
                
                if 0 <= hour <= 6:
                    anomalies.append({
                        "timestamp": log["timestamp"],
                        "tenant": log["tenant"],
                        "message": log["message"],
                        "reason": "Access outside normal hours (00:00-06:00)"
                    })
                
                for keyword in malware_keywords:
                    if keyword.lower() in log["message"].lower():
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"Suspicious keyword: {keyword}"
                        })
                        break
                
                ip = extract_ip(log["message"])
                if ip and "failed" in log["message"].lower():
                    ip_counts[ip] = ip_counts.get(ip, 0) + 1
                    if ip_counts[ip] >= 5:
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"High failed attempts from IP {ip}: {ip_counts[ip]}"
                        })
            
            except Exception as e:
                print(f"Error processing log {log['message']}: {str(e)}")
                continue
        
        total_result = es.count(index=index_name, query=query)
        total = total_result["count"]
        
        return {"anomalies": anomalies, "tenant": tenant_id, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies: {str(e)}")