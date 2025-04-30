from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch, helpers
import json
import logging
import time
import socket
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_service(host, port, timeout=60, retries=12):
    """Espera a que un servicio esté disponible en el host y puerto especificados."""
    start_time = time.time()
    for i in range(retries):
        try:
            with socket.create_connection((host, port), timeout=5):
                logger.info(f"Successfully connected to {host}:{port}")
                return True
        except (socket.timeout, ConnectionRefusedError) as e:
            logger.warning(f"Attempt {i+1}/{retries}: Failed to connect to {host}:{port}, error: {str(e)}")
            if time.time() - start_time > timeout:
                logger.error(f"Timeout waiting for {host}:{port} after {timeout} seconds")
                return False
            time.sleep(5)
    logger.error(f"Failed to connect to {host}:{port} after {retries} attempts")
    return False

def consume_to_elasticsearch(timeout_seconds=300):
    logger.info("Starting consume_to_elasticsearch script...")

    # Esperar a que los brokers de Kafka estén disponibles
    kafka_brokers = ["kafka-1:9092", "kafka-2:9093", "kafka-3:9094"]
    for broker in kafka_brokers:
        host, port = broker.split(":")
        if not wait_for_service(host, int(port)):
            raise Exception(f"Failed to connect to Kafka broker {broker} after multiple attempts")

    # Configuración del consumidor de Kafka con SSL
    logger.info("Configuring Kafka consumer...")
    conf = {
        'bootstrap.servers': ','.join(kafka_brokers),
        'group.id': 'nubla-log-consumer',
        'auto.offset.reset': 'earliest',
        'security.protocol': 'SSL',
        'ssl.keystore.location': os.getenv('KAFKA_SSL_KEYSTORE_LOCATION', '/etc/kafka/secrets/kafka.server.keystore.jks'),
        'ssl.keystore.password': os.getenv('KAFKA_SSL_KEYSTORE_PASSWORD', 'password'),
        'ssl.key.password': os.getenv('KAFKA_SSL_KEY_PASSWORD', 'password'),
        'ssl.truststore.location': os.getenv('KAFKA_SSL_TRUSTSTORE_LOCATION', '/etc/kafka/secrets/kafka.server.truststore.jks'),
        'ssl.truststore.password': os.getenv('KAFKA_SSL_TRUSTSTORE_PASSWORD', 'password'),
    }
    try:
        consumer = Consumer(conf)
        logger.info("Kafka consumer created successfully.")
    except Exception as e:
        logger.error(f"Failed to create Kafka consumer: {str(e)}")
        raise

    # Suscribirse al tópico
    logger.info("Subscribing to topic 'network-logs'...")
    consumer.subscribe(['network-logs'])

    # Esperar a que los nodos de Elasticsearch estén disponibles
    es_nodes = ["elasticsearch-1:9200", "elasticsearch-2:9200", "elasticsearch-3:9200"]
    for node in es_nodes:
        host, port = node.split(":")
        if not wait_for_service(host, int(port)):
            raise Exception(f"Failed to connect to Elasticsearch node {node} after multiple attempts")

    # Configuración de Elasticsearch con credenciales y HTTPS
    logger.info("Connecting to Elasticsearch...")
    try:
        es = Elasticsearch(
            [f"https://{node}" for node in es_nodes],
            basic_auth=("elastic", "yourpassword"),
            ca_certs="/etc/elasticsearch/secrets/elastic-stack-ca.p12",
            verify_certs=True
        )
        if not es.ping():
            raise Exception("Failed to connect to Elasticsearch")
        logger.info("Connected to Elasticsearch successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        raise

    actions = []
    start_time = time.time()
    last_message_time = start_time
    message_processed = False
    tenant_counts = {"tenant1": 0, "tenant2": 0}

    try:
        while True:
            current_time = time.time()
            if (current_time - start_time) > timeout_seconds and not message_processed:
                logger.info(f"No messages received after {timeout_seconds} seconds. Continuing to wait...")
                start_time = current_time  # Resetear el temporizador para evitar salida

            if (current_time - last_message_time) > 30:
                logger.info("Waiting for messages in topic 'network-logs'...")
                last_message_time = current_time

            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue  # Seguir esperando más mensajes
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.warning(f"Topic 'network-logs' not available yet. Waiting for topic to be created...")
                    time.sleep(5)  # Esperar antes de reintentar
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    continue  # Continuar en lugar de salir

            try:
                message_processed = True
                log_entry = json.loads(msg.value().decode('utf-8'))
                tenant = log_entry["tenant"]
                index_name = f"logs-{tenant}"
                
                if tenant not in ["tenant1", "tenant2"]:
                    logger.warning(f"Invalid tenant {tenant} in message: {log_entry}")
                    continue

                tenant_counts[tenant] += 1

                if not es.indices.exists(index=index_name):
                    es.indices.create(index=index_name)
                
                action = {
                    "_index": index_name,
                    "_source": log_entry
                }
                actions.append(action)

                if len(actions) >= 100:
                    success, failed = helpers.bulk(es, actions, raise_on_error=False)
                    logger.info(f"Ingested {success} logs into Elasticsearch, {len(failed)} failed")
                    logger.info(f"Current counts: tenant1={tenant_counts['tenant1']}, tenant2={tenant_counts['tenant2']}")
                    actions = []

            except Exception as e:
                logger.warning(f"Error processing message: {msg.value()}, error: {str(e)}")
                continue

    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in consumer loop: {str(e)}")
        raise
    finally:
        if actions:
            success, failed = helpers.bulk(es, actions, raise_on_error=False)
            logger.info(f"Final batch: Ingested {success} logs into Elasticsearch, {len(failed)} failed")
        
        for tenant in ["tenant1", "tenant2"]:
            index_name = f"logs-{tenant}"
            if es.indices.exists(index=index_name):
                es.indices.refresh(index=index_name)
        
        consumer.close()
        logger.info(f"Consumer closed successfully. Final counts: tenant1={tenant_counts['tenant1']}, tenant2={tenant_counts['tenant2']}")

if __name__ == "__main__":
    try:
        logger.info("Executing consume_to_elasticsearch...")
        consume_to_elasticsearch(timeout_seconds=300)
    except Exception as e:
        logger.error(f"Failed to execute consume_to_elasticsearch: {str(e)}")
        raise