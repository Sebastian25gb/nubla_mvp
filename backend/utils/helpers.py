from dateutil.parser import parse as parse_date
import re

def parse_timestamp(timestamp):
    try:
        return parse_date(timestamp)
    except Exception as e:
        print(f"Error parsing timestamp {timestamp}: {str(e)}")
        return None

def extract_ip(message):
    ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
    match = ip_pattern.search(message)
    return match.group(1) if match else None