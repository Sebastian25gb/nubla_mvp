from fastapi import APIRouter, HTTPException, Query
from utils.elasticsearch import get_elasticsearch_client
from utils.helpers import parse_timestamp, extract_ip
import re
from collections import defaultdict
from datetime import datetime, timedelta
import logging

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/anomalies/{tenant_id}")
async def get_anomalies(
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

        # Obtener logs para procesar anomalías basadas en contenido
        query = {"match_all": {}}
        result = es.search(index=index_name, query=query, from_=from_, size=size)
        if not isinstance(result.get("hits", {}).get("hits"), list):
            raise HTTPException(status_code=500, detail="Invalid response format from Elasticsearch")
        logs = [hit["_source"] for hit in result["hits"]["hits"]]

        # Agregación para conteo de intentos fallidos por IP
        agg_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"regexp": {"message": ".*failed.*"}}  # Filtrar logs con "failed"
                    ]
                }
            },
            "aggs": {
                "by_ip": {
                    "terms": {
                        "field": "message",  # Usaremos un script para extraer IPs
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
                if ip:  # Ignorar si no se encuentra IP
                    ip_counts[ip] = bucket["doc_count"]

        # Agregación para picos de actividad no es práctica en Elasticsearch directamente,
        # así que mantendremos esta lógica en memoria, pero optimizaremos el resto
        anomalies = []
        ip_timestamps = defaultdict(list)
        ip_locations = defaultdict(set)
        malware_keywords = ["malware", "exploit", "ransomware"]
        sql_injection_patterns = [
            r"(?i)\b(select|union|drop|insert|update|delete)\b.*('|--|;)",  # Patrones comunes de SQL injection
            r"(?i)\b(or|and)\b\s+['\"]\d+['\"]\s*=\s*['\"]\d+['\"]"  # Ejemplo: ' OR '1'='1'
        ]

        for log in logs:
            try:
                timestamp = parse_timestamp(log["timestamp"])
                if not timestamp:
                    continue
                hour = timestamp.hour

                # Detección de acceso fuera de horario (00:00-06:00)
                if 0 <= hour <= 6:
                    anomalies.append({
                        "timestamp": log["timestamp"],
                        "tenant": log["tenant"],
                        "message": log["message"],
                        "reason": "Access outside normal hours (00:00-06:00)"
                    })

                # Detección de palabras clave sospechosas (malware)
                for keyword in malware_keywords:
                    if keyword.lower() in log["message"].lower():
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"Suspicious keyword: {keyword}"
                        })
                        break

                # Detección de intentos fallidos por IP (usando agregaciones)
                ip = extract_ip(log["message"])
                if ip and "failed" in log["message"].lower():
                    ip_timestamps[ip].append(timestamp)

                    # Extraer información de ubicación si está presente
                    location_match = re.search(r"\((\w+)\)", log["message"], re.IGNORECASE)
                    if location_match:
                        location = location_match.group(1)
                        ip_locations[ip].add(location)

                    # Usar el conteo de la agregación para detectar IPs sospechosas
                    if ip in ip_counts and ip_counts[ip] >= 5:
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"High failed attempts from IP {ip}: {ip_counts[ip]}"
                        })

                    # Detección de picos de actividad
                    if len(ip_timestamps[ip]) >= 5:
                        timestamps = sorted(ip_timestamps[ip])
                        time_window = timestamps[-1] - timestamps[-5]
                        if time_window <= timedelta(minutes=1):  # 5 intentos en 1 minuto
                            anomalies.append({
                                "timestamp": log["timestamp"],
                                "tenant": log["tenant"],
                                "message": log["message"],
                                "reason": f"Spike in activity from IP {ip}: {len(ip_timestamps[ip])} attempts in {time_window.total_seconds()} seconds"
                            })

                    # Detección de accesos desde múltiples ubicaciones
                    if len(ip_locations[ip]) > 1:
                        anomalies.append({
                            "timestamp": log["timestamp"],
                            "tenant": log["tenant"],
                            "message": log["message"],
                            "reason": f"Suspicious IP {ip}: Access from multiple locations: {', '.join(ip_locations[ip])}"
                        })

                # Detección de intentos de SQL injection
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