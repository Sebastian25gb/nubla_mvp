import sys
import json
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_logs(output_file, num_logs, days_back):
    tenants = ["tenant1", "tenant2"]
    actions = ["login", "logout", "file_access", "data_transfer"]
    statuses = ["success", "failure"]
    start_time = datetime.now() - timedelta(days=days_back)

    logs = []
    for i in range(num_logs):
        timestamp = start_time + timedelta(seconds=i * (days_back * 24 * 3600 // num_logs))
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "tenant": random.choice(tenants),
            "user_id": f"user_{random.randint(100, 999)}",
            "action": random.choice(actions),
            "status": random.choice(statuses),
            "bytes": random.randint(0, 1048576) if "data_transfer" in actions else 0
        }
        logs.append(log_entry)

    with open(output_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    logger.info(f"Generated {num_logs} test logs in {output_file} covering the last {days_back} days.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_test_logs.py <output_file> <num_logs> <days_back>")
        sys.exit(1)

    output_file = sys.argv[1]
    num_logs = int(sys.argv[2])
    days_back = int(sys.argv[3])
    generate_test_logs(output_file, num_logs, days_back)