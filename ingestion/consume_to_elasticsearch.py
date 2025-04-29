from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch, helpers
import json
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consume_to_elasticsearch(timeout_seconds=300):
    logger.info("Starting consume_to_elasticsearch script...")

    # Configuración del consumidor de Kafka
    logger.info("Configuring Kafka consumer...")
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'nubla-log-consumer',
        'auto.offset.reset': 'earliest'
    }
    try:
        consumer = Consumer(conf)
        logger.info("Kafka consumer created successfully.")
    except Exception as e:
        logger.error(f"Failed to create Kafka consumer: {str(e)}")
        raise

    try:
        consumer.subscribe(['network-logs'])
        logger.info("Subscribed to topic 'network-logs'.")
    except Exception as e:
        logger.error(f"Failed to subscribe to topic 'network-logs': {str(e)}")
        raise

    # Configuración de Elasticsearch
    logger.info("Connecting to Elasticsearch...")
    try:
        es = Elasticsearch(["http://localhost:9200"])
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
    tenant_counts = {"tenant1": 0, "tenant2": 0}  # Contador para cada tenant

    try:
        while True:
            current_time = time.time()
            if (current_time - start_time) > timeout_seconds and not message_processed:
                logger.info(f"No messages received after {timeout_seconds} seconds. Exiting consumer.")
                break

            if (current_time - last_message_time) > 30:
                logger.info("Waiting for messages in topic 'network-logs'...")
                last_message_time = current_time

            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    break

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
        consume_to_elasticsearch(timeout_seconds=300)  # 5 minutos de timeout
    except Exception as e:
        logger.error(f"Failed to execute consume_to_elasticsearch: {str(e)}")
        raise