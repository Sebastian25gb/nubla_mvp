from confluent_kafka import Producer
import re
import os
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delivery_report(err, msg):
    """ Callback para reportar el resultado de la entrega del mensaje """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def ingest_logs(filename):
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    
    # Convertir filename a una ruta absoluta si no lo es
    if not os.path.isabs(filename):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        filename = os.path.join(base_dir, "ingestion", filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Log file {filename} not found")

    # Configuración del productor de Kafka
    conf = {
        'bootstrap.servers': 'kafka:9092',  # Usar el nombre del servicio kafka y el puerto interno
        'client.id': 'nubla-log-producer'
    }
    producer = Producer(conf)

    with open(filename, 'r') as f:
        logs = f.readlines()
    
    for log in logs:
        try:
            parts = log.strip().split(' ', 2)
            if len(parts) != 3:
                continue
            timestamp, tenant, message = parts
            
            log_entry = {
                "timestamp": timestamp,
                "tenant": tenant,
                "message": message
            }
            
            # Enviar el log al tópico de Kafka
            producer.produce(
                'network-logs',
                key=tenant.encode('utf-8'),
                value=json.dumps(log_entry).encode('utf-8'),
                callback=delivery_report
            )
            producer.poll(0)  # Procesar callbacks de entrega

        except Exception as e:
            logger.warning(f"Error processing log: {log}, error: {str(e)}")
            continue
    
    # Asegurarse de que todos los mensajes se entreguen antes de cerrar
    producer.flush()
    logger.info(f"Sent {len(logs)} logs to Kafka topic 'network-logs'")

if __name__ == "__main__":
    try:
        # Usar una ruta absoluta para el archivo de logs
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
        ingest_logs(logs_file)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise