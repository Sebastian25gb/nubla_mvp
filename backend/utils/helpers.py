from datetime import datetime
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_timestamp(timestamp_str):
    try:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing timestamp {timestamp_str}: {str(e)}")
        return None

def extract_ip(message):
    ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
    match = ip_pattern.search(message)
    return match.group(1) if match else None