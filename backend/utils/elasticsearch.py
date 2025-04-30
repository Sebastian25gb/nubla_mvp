from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

def get_elasticsearch_client():
    try:
        es = Elasticsearch(
            ["http://localhost:9200"],
            http_auth=("elastic", "yourpassword")
        )
        if es.ping():
            logger.info("Successfully connected to Elasticsearch")
            return es
        else:
            raise Exception("Failed to connect to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        raise