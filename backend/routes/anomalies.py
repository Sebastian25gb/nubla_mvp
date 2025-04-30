from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import parse_timestamp, extract_ip
from utils.database import get_db_connection
import re
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import os

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/anomalies/{tenant_id}")
async def get_anomalies(
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

        agg_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"regexp": {"message": ".*failed.*"}}
                    ]
                }
            },
            "aggs": {
                "by_ip": {
                    "terms": {
                        "field": "message",
                        "script": {
                            "source": "def ip = doc['message'].value =~ /\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/ ? doc['message'].value =~ /\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/[0] : null; ip",
                            "lang": "painless"
                        },
                        "size": 1000
                    }
                }
            }
        }
        agg_result = es.search(index=index_name, body=agg_query)
        ip_counts = {}
        if "aggregations" in agg_result and "by_ip" in agg_result["aggregations"]:
            for bucket in agg_result["aggregations"]["by_ip"]["buckets"]:
                ip = bucket["key"]
                if ip:
                    ip_counts[ip] = bucket["doc_count"]

        anomalies = []
        ip_timestamps = defaultdict(list)
        ip_locations = defaultdict(set)
        malware_keywords = ["malware", "exploit", "ransomware"]
        sql_injection_patterns = [
            r"(?i)\b(select|union|drop|insert|update|delete)\b.*('|--|;)",
            r"(?i)\b(or|and)\b\s+['\"]\d+['\"]\s*=\s*['\"]\d+['\"]"
        ]

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
                    ip_timestamps[ip].append(timestamp)

                    location_match = re.search(r"\((\w+)\)", log["message"], re.IGNORECASE)
                    if location_match:
                        location = location_match.group(1)
                        ip_locations[ip].add(location)

                    if ip in ip_counts and ip_counts[ip] >= 5:
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"High failed attempts from IP {ip}: {ip_counts[ip]}"
                        })

                    if len(ip_timestamps[ip]) >= 5:
                        timestamps = sorted(ip_timestamps[ip])
                        time_window = timestamps[-1] - timestamps[-5]
                        if time_window <= timedelta(minutes=1):
                            anomalies.append({
                                "timestamp": log["timestamp"],
                                "tenant": log["tenant"],
                                "message": log["message"],
                                "reason": f"Spike in activity from IP {ip}: {len(ip_timestamps[ip])} attempts in {time_window.total_seconds()} seconds"
                            })

                    if len(ip_locations[ip]) > 1:
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"Suspicious IP {ip}: Access from multiple locations: {', '.join(ip_locations[ip])}"
                        })

                for pattern in sql_injection_patterns:
                    if re.search(pattern, log["message"]):
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": "Possible SQL injection attempt detected"
                        })
                        break

            except Exception as e:
                logger.warning(f"Error processing log {log.get('message', 'unknown')}: {str(e)}")
                continue

        total_result = es.count(index=index_name, query=query)
        if not isinstance(total_result.get("count"), (int, float)):
            raise HTTPException(status_code=500, detail="Invalid count result from Elasticsearch")
        total = total_result["count"]

        return {"anomalies": anomalies, "tenant": tenant_id, "total": total}
    except Exception as e:
        logger.error(f"Error fetching anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies: {str(e)}")